"""Portable exact-source ownership controls; all journal effects are fake."""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re
import stat
import sys
import unittest

import pytest
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

_SOURCE = Path(__file__).resolve().parents[1] / "src/beamo_wipe/session_recovery.py"


class SafetyError(RuntimeError):
    pass


class Directory(PurePosixPath):
    def mkdir(self, **kwargs):
        pass


class FakeOS:
    O_RDONLY, O_NOFOLLOW, O_NONBLOCK = 1, 2, 4
    O_RDWR, O_CREAT, O_EXCL, O_DIRECTORY = 8, 16, 32, 64

    def __init__(self):
        self.closed = []
        self.opened = []
        self.unlinked = []
        self.bindings = {}
        self.close_error = self.metadata_error = self.read_error = None
        self.write_error = self.cleanup_error = self.dir_sync_error = None
        self.payload = b"abc"
        self.position = 0
        self.published = False
        self.foreign_temporary = False

    def open(self, path, *args, **kwargs):
        fd = 77 if str(path) == "/inert" else 88 if path == "interface.lock" else 17
        self.opened.append(fd)
        self.bindings[str(path)] = fd
        return fd

    def close(self, fd):
        if fd in self.closed:
            raise AssertionError("descriptor close retried")
        self.closed.append(fd)
        if fd == 17 and self.close_error is not None:
            raise self.close_error

    def fstat(self, fd):
        if fd == 17 and self.metadata_error is not None:
            raise self.metadata_error
        return SimpleNamespace(
            st_mode=(stat.S_IFDIR | 0o700) if fd in {1, 77} else stat.S_IFREG | 0o600,
            st_uid=0,
            st_nlink=1,
            st_dev=1,
            st_ino=fd,
            st_size=len(self.payload),
            st_mtime_ns=1,
            st_ctime_ns=1,
        )

    def stat(self, name, **kwargs):
        if self.cleanup_error is not None:
            raise self.cleanup_error
        if name not in self.bindings:
            raise FileNotFoundError(name)
        return SimpleNamespace(
            st_dev=1, st_ino=99 if self.foreign_temporary else self.bindings[name]
        )

    def unlink(self, name, **kwargs):
        self.unlinked.append(name)
        del self.bindings[name]

    def replace(self, source, destination, **kwargs):
        self.bindings[destination] = self.bindings.pop(source)
        self.published = True

    def read(self, fd, count):
        if self.read_error is not None:
            raise self.read_error
        result = self.payload[self.position : self.position + count]
        self.position += len(result)
        return result

    def write(self, fd, pending):
        if self.write_error is not None:
            raise self.write_error
        return min(7, len(pending))

    def fsync(self, fd):
        if fd == 1 and self.dir_sync_error is not None:
            raise self.dir_sync_error

    def getuid(self):
        return 0


def load_store(source, fake):
    tree = ast.parse(source)
    selected_names = {
        "_file",
        "read",
        "save",
        "is_quiescent",
        "open",
        "_open_owned",
        "close",
    }
    owner = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SessionStore"
    )
    selected = [
        n
        for n in owner.body
        if isinstance(n, ast.FunctionDef) and n.name in selected_names
    ]
    functions = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name in {"_bytes", "_object", "_cleanup_recovery_file"}
    ]
    constants = [n for n in tree.body if isinstance(n, ast.Assign)]
    namespace = {
        "os": fake,
        "stat": stat,
        "Path": Directory,
        "SafetyError": SafetyError,
        "json": json,
        "hashlib": hashlib,
        "re": re,
        "time": SimpleNamespace(monotonic=lambda: 1),
        "secrets": SimpleNamespace(token_hex=lambda count: "a" * (count * 2)),
        "fcntl": SimpleNamespace(LOCK_EX=1, LOCK_NB=2, flock=lambda *args: None),
    }
    logs = []

    def fake_import(name, *args, **kwargs):
        if name == "beamo_wipe.diagnostics":
            return SimpleNamespace(log_diag=lambda *args: logs.append(args))
        raise AssertionError("unexpected product import: " + name)

    namespace["__builtins__"] = dict(vars(builtins), __import__=fake_import)
    module = ast.Module(
        body=constants
        + functions
        + [
            ast.ClassDef(
                name="Store", bases=[], keywords=[], body=selected, decorator_list=[]
            )
        ],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(_SOURCE), "exec"), namespace)
    return namespace["Store"], namespace, logs


class _UnittestAssertions:
    """unittest's assertion methods for a plain pytest class.

    pytest cannot parametrize unittest.TestCase methods, and pytest 9 reports
    unittest subTest() results in a way the CI evidence check rejects, so these
    classes are plain pytest classes that keep the original assertions.
    """

    _checker = unittest.TestCase()

    def __getattr__(self, name):
        if name.startswith("assert") or name == "fail":
            return getattr(self._checker, name)
        raise AttributeError(name)


def _name(kind):
    return "none" if kind is None else kind.__name__


class TestJournalCleanup(_UnittestAssertions):
    @classmethod
    def setup_class(cls):
        cls.source = _SOURCE.read_bytes()

    def setup_method(self, _method=None):
        self.setUp()

    def setUp(self):
        self.fake = FakeOS()
        cls, self.namespace, self.logs = load_store(self.source, self.fake)
        self.store = cls()
        self.store.fd, self.store.owner, self.store.quiescent = 1, 88, -1
        self.store.directory = Directory("/inert")
        self.store._production_directory = False
        self.store.boot = "00000000-0000-0000-0000-000000000001"
        self.store.build = "b" * 64
        self.store.invalid = self.store.previous = False
        self.store.record = None
        self.store._verify_directory = lambda: None
        self.store._verify_named_lock = lambda *args: None
        self.store._verify_named_read = lambda *args: None
        self.store._verify_publication = lambda *args: None
        self.store.validate = lambda record: None

    def stub_file(self):
        def acquire(name, *args):
            return self.fake.open(name)

        self.store._file = acquire

    def assert_primary(self, action, primary):
        caught = None
        try:
            action()
        except BaseException as error:
            caught = error
        self.assertIs(caught, primary)
        self.assertEqual(self.fake.closed.count(17), 1)

    @pytest.mark.parametrize(
        "cleanup_kind", (None, OSError, KeyboardInterrupt), ids=_name
    )
    @pytest.mark.parametrize(
        "kind", (KeyboardInterrupt, SystemExit, SafetyError, OSError), ids=_name
    )
    @pytest.mark.parametrize("operation", ("file", "read"))
    def test_file_and_read_preserve_primary(self, operation, kind, cleanup_kind):
        primary = kind("private operation details")
        self.fake.close_error = (
            None if cleanup_kind is None else cleanup_kind("private close details")
        )
        if operation == "file":
            self.fake.metadata_error = primary

            def action():
                return self.store._file("fixture")
        else:
            self.stub_file()
            self.fake.read_error = primary

            def action():
                return self.store.read("fixture")

        self.assert_primary(action, primary)

    @pytest.mark.parametrize("kind", (KeyboardInterrupt, SystemExit), ids=_name)
    def test_open_does_not_swallow_cancellation(self, kind):
        self.stub_file()
        self.store.fd = self.store.owner = -1
        primary = kind("cancel journal")
        self.fake.read_error, self.fake.close_error = primary, OSError("close")
        self.assert_primary(self.store.open, primary)
        self.assertEqual(
            (self.store.fd, self.store.owner, self.store.quiescent),
            (-1, -1, -1),
        )
        self.assertEqual(self.fake.closed, [17, 88, 77])

    def test_read_success_and_cleanup_only_refusal(self):
        self.stub_file()
        self.assertEqual(self.store.read("fixture"), b"abc")
        self.assertEqual(self.fake.closed, [17])
        self.setUp()
        self.stub_file()
        error = OSError("close")
        self.fake.close_error = error
        self.assert_primary(lambda: self.store.read("fixture"), error)

    @pytest.mark.parametrize("cleanup_stage", ("close", "metadata", "both"))
    @pytest.mark.parametrize(
        "kind", (KeyboardInterrupt, SystemExit, SafetyError, OSError), ids=_name
    )
    def test_save_primary_and_cleanup_combinations(self, kind, cleanup_stage):
        self.stub_file()
        primary = kind("write refusal")
        self.fake.write_error = primary
        if cleanup_stage in {"close", "both"}:
            self.fake.close_error = OSError("close")
        if cleanup_stage in {"metadata", "both"}:
            self.fake.cleanup_error = OSError("cleanup metadata")
        self.assert_primary(lambda: self.store.save({"phase": "preflight"}), primary)
        self.assertFalse(self.fake.published)
        self.assertFalse(self.store.invalid)

    @pytest.mark.parametrize("foreign", (False, True))
    def test_temporary_cleanup_respects_identity(self, foreign):
        self.stub_file()
        self.fake.foreign_temporary = foreign
        primary = SafetyError("write refusal")
        self.fake.write_error = primary
        self.assert_primary(lambda: self.store.save({}), primary)
        self.assertEqual(len(self.fake.unlinked), 0 if foreign else 1)
        self.assertEqual(len(self.fake.bindings), 1 if foreign else 0)

    @pytest.mark.parametrize("failure", ("none", "directory_sync", "close"))
    def test_save_publication_durability_and_cleanup_refusals(self, failure):
        self.stub_file()
        error = OSError(failure)
        if failure == "directory_sync":
            self.fake.dir_sync_error = error
        if failure == "close":
            self.fake.close_error = error
        if failure == "none":
            self.store.save({"phase": "terminal"})
            self.assertFalse(self.store.invalid)
        else:
            self.assert_primary(lambda: self.store.save({"phase": "terminal"}), error)
            self.assertTrue(self.store.invalid)
        self.assertTrue(self.fake.published)
        self.assertEqual(self.store.record["phase"], "terminal")
        self.assertEqual(self.fake.closed, [17])

    @pytest.mark.parametrize(
        "kind", (KeyboardInterrupt, SystemExit, SafetyError, OSError), ids=_name
    )
    def test_quiescent_primary_keeps_no_ownership(self, kind):
        self.stub_file()
        primary = kind("lock refusal")
        self.fake.close_error = OSError("close")

        def fail(*args):
            raise primary

        self.namespace["fcntl"].flock = fail
        self.assert_primary(self.store.is_quiescent, primary)
        self.assertEqual(self.store.quiescent, -1)

    def test_quiescent_busy_and_retained_ownership(self):
        self.stub_file()

        def busy(*args):
            raise BlockingIOError("busy")

        self.namespace["fcntl"].flock = busy
        self.assertFalse(self.store.is_quiescent())
        self.assertEqual(self.fake.closed, [17])
        self.setUp()
        self.stub_file()
        self.assertTrue(self.store.is_quiescent())
        self.assertTrue(self.store.is_quiescent())
        self.assertEqual(self.fake.closed, [])
        self.assertEqual(self.fake.opened, [17])
        self.store.close()
        self.assertEqual(self.fake.closed, [17, 88, 1])

    def test_cleanup_logs_fixed_stage_and_type_only(self):
        self.stub_file()
        primary = KeyboardInterrupt("SECRET operation")
        self.fake.read_error, self.fake.close_error = primary, OSError("SECRET cleanup")
        self.assert_primary(lambda: self.store.read("fixture"), primary)
        self.assertEqual(self.logs, [("session_recovery", "file_close", "OSError")])

    def test_acquisition_refusal_is_distinct_from_lock_contention(self):
        primary = BlockingIOError("acquisition refused")

        def refuse(*args):
            raise primary

        self.store._file = refuse
        with self.assertRaises(BlockingIOError) as result:
            self.store.is_quiescent()
        self.assertIs(result.exception, primary)
        self.assertEqual(self.fake.closed, [])
        self.assertEqual(self.store.quiescent, -1)

    def test_busy_lock_cannot_hide_close_only_failure(self):
        self.stub_file()

        def busy(*args):
            raise BlockingIOError("lock held")

        self.namespace["fcntl"].flock = busy
        error = OSError("close only")
        self.fake.close_error = error
        self.assert_primary(self.store.is_quiescent, error)
        self.assertEqual(self.store.quiescent, -1)

    def test_cleanup_only_preserves_first_error_and_attempts_close(self):
        error = OSError("temporary metadata")
        self.fake.metadata_error = error
        self.fake.close_error = OSError("later close")
        self.assert_primary(
            lambda: self.namespace["_cleanup_recovery_file"](1, 17, "temporary"),
            error,
        )
        self.assertEqual(
            self.logs,
            [
                ("session_recovery", "temporary_cleanup", "OSError"),
                ("session_recovery", "file_close", "OSError"),
            ],
        )

    def test_failed_diagnostic_logger_preserves_primary(self):
        self.stub_file()
        primary = KeyboardInterrupt("PRIVATE operation")
        self.fake.read_error = primary
        self.fake.close_error = OSError("PRIVATE cleanup")

        def log(*args):
            self.logs.append(args)
            raise SystemExit("PRIVATE diagnostic")

        self.namespace["__builtins__"]["__import__"] = lambda *args: SimpleNamespace(
            log_diag=log
        )
        self.assert_primary(lambda: self.store.read("fixture"), primary)
        self.assertEqual(self.logs, [("session_recovery", "file_close", "OSError")])

    @pytest.mark.parametrize("method", ("_file", "read", "save", "is_quiescent"))
    def test_interruption_at_first_line_after_acquisition(self, method):
        tree = ast.parse(self.source)
        cls = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "SessionStore"
        )
        if method != "_file":
            self.stub_file()
        node = next(
            n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method
        )
        statements = sorted(
            (n for n in ast.walk(node) if isinstance(n, ast.stmt)),
            key=lambda n: n.lineno,
        )
        acquisition = next(
            n
            for n in statements
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "fd" for t in n.targets)
            and isinstance(n.value, ast.Call)
        )
        line = next(n.lineno for n in statements if n.lineno > acquisition.lineno)
        primary = KeyboardInterrupt("inert line event")

        def trace(frame, event, argument):
            if (
                event == "line"
                and frame.f_code.co_name == method
                and frame.f_lineno == line
            ):
                raise primary
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            action = (
                (lambda: self.store._file("fixture"))
                if method == "_file"
                else (lambda: self.store.read("fixture"))
                if method == "read"
                else (lambda: self.store.save({}))
                if method == "save"
                else self.store.is_quiescent
            )
            self.assert_primary(action, primary)
        finally:
            sys.settrace(previous)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
