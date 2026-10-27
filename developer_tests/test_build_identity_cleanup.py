"""Identity descriptor regressions with exact AST and inert OS boundaries.

These portable controls do not import the product or qualify Linux syscalls.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import posixpath
import re
import sys
import unittest
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

_SOURCE = Path(__file__).resolve().parents[1] / "src/beamo_wipe/build_identity.py"


class FakeOS:
    O_RDONLY, O_DIRECTORY, O_NOFOLLOW = 1, 2, 4
    O_RDWR, O_CREAT, O_EXCL = 8, 16, 32

    def __init__(self):
        self.path = SimpleNamespace(abspath=lambda path: posixpath.normpath(str(path)))
        self.active = set()
        self.opened = []
        self.closes = []
        self.close_errors = {}
        self.open_errors = {}
        self.operations = []
        self.write_error = None

    def open(self, path, flags, *args, **kwargs):
        index = len(self.opened)
        if index in self.open_errors:
            raise self.open_errors[index]
        fd = 10 + index
        self.opened.append(fd)
        self.active.add(fd)
        return fd

    def close(self, fd):
        self.closes.append(fd)
        if fd not in self.active:
            raise AssertionError("descriptor close retried")
        self.active.remove(fd)
        if fd in self.close_errors:
            raise self.close_errors[fd]

    def mkdir(self, *args, **kwargs):
        pass

    def write(self, fd, data):
        if self.write_error is not None:
            raise self.write_error
        self.operations.append("write")
        return len(data)

    def fchmod(self, *args):
        self.operations.append("chmod")

    def fsync(self, *args):
        self.operations.append("sync")

    def replace(self, *args, **kwargs):
        self.operations.append("replace")

    def fstat(self, fd):
        return SimpleNamespace(st_dev=1, st_ino=9)


class IdentityCleanup(unittest.TestCase):
    def setUp(self):
        self.os = FakeOS()
        self.read_error = None
        self.token_error = None
        self.payload = b"inert source\n"
        self.verified = []

        class LexicalPath(PurePosixPath):
            def rglob(path, pattern):
                return [path / "fixture.py"]

            def is_symlink(path):
                return False

            def is_file(path):
                return True

        def read_at(*args, **kwargs):
            if self.read_error is not None:
                raise self.read_error
            return self.payload

        def token_hex(size):
            if self.token_error is not None:
                raise self.token_error
            return "f" * (size * 2)

        def fake_import(name, *args, **kwargs):
            self.assertEqual(name, "beamo_wipe.support_export")
            return SimpleNamespace(_read_at=read_at)

        tree = ast.parse(_SOURCE.read_bytes(), filename=str(_SOURCE))
        body = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.Assign, ast.AnnAssign))
        ]
        self.env = {
            "__builtins__": dict(vars(builtins), __import__=fake_import),
            "__file__": "/inert/pkg/build_identity.py",
            "Path": LexicalPath,
            "os": self.os,
            "hashlib": hashlib,
            "re": re,
            "json": json,
            "SafetyError": RuntimeError,
            "secrets": SimpleNamespace(token_hex=token_hex),
        }
        exec(
            compile(ast.Module(body=body, type_ignores=[]), str(_SOURCE), "exec"),
            self.env,
        )

    def directory(self):
        return self.env["_identity_directory"](PurePosixPath("/inert"), create=False)

    def publish(self):
        self.env["_identity_directory"] = lambda *a, **kw: self.os.open("directory", 0)
        self.env["_verify_identity_publication"] = lambda *args: self.verified.append(
            args[1]
        )
        return self.env["_publish_identity"](
            PurePosixPath("/inert/build.json"), b"INERT"
        )

    def assert_closed_once(self):
        self.assertEqual(self.os.active, set())
        self.assertCountEqual(self.os.closes, self.os.opened)

    def test_directory_normal_transfers_one_handle(self):
        fd = self.directory()
        self.assertEqual(self.os.active, {fd})
        self.os.close(fd)
        self.assert_closed_once()

    def test_directory_handoff_close_failure_closes_successor_once(self):
        failure = OSError("close")
        self.os.close_errors[10] = failure
        with self.assertRaises(OSError) as caught:
            self.directory()
        self.assertIs(caught.exception, failure)
        self.assert_closed_once()

    def test_directory_child_open_failure_preserves_primary(self):
        for kind in (OSError, KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind):
                self.setUp()
                primary = kind("primary")
                self.os.open_errors[1] = primary
                self.os.close_errors[10] = OSError("close")
                with self.assertRaises(kind) as caught:
                    self.directory()
                self.assertIs(caught.exception, primary)
                self.assert_closed_once()

    def test_publisher_token_failure_closes_directory(self):
        for kind in (OSError, KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind):
                self.setUp()
                primary = kind("token")
                self.token_error = primary
                self.os.close_errors[10] = OSError("close")
                with self.assertRaises(kind) as caught:
                    self.publish()
                self.assertIs(caught.exception, primary)
                self.assert_closed_once()
                self.assertEqual(self.os.operations, [])

    def test_publisher_write_failure_preserves_primary_and_closes_all(self):
        for kind in (OSError, KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind):
                self.setUp()
                primary = kind("write")
                self.os.write_error = primary
                self.os.close_errors[11] = OSError("file close")
                self.os.close_errors[10] = OSError("directory close")
                with self.assertRaises(kind) as caught:
                    self.publish()
                self.assertIs(caught.exception, primary)
                self.assert_closed_once()
                self.assertNotIn("replace", self.os.operations)

    def test_publisher_success_checks_both_names_and_closes_all(self):
        self.publish()
        self.assertEqual(self.verified, [".build-identity-" + "f" * 32, "build.json"])
        self.assertEqual(
            self.os.operations, ["write", "chmod", "sync", "replace", "sync"]
        )
        self.assert_closed_once()

    def test_publisher_cleanup_failure_refuses_success_and_attempts_every_close(self):
        failure = OSError("current-directory close")
        self.os.close_errors.update(
            {12: failure, 11: OSError("file"), 10: OSError("parent")}
        )
        with self.assertRaises(OSError) as caught:
            self.publish()
        self.assertIs(caught.exception, failure)
        self.assert_closed_once()

    def test_reader_primary_interrupt_is_not_swallowed_by_close_failure(self):
        for function in ("load_injected_build", "runtime_source_sha256"):
            for kind in (KeyboardInterrupt, SystemExit):
                with self.subTest(function=function, kind=kind):
                    self.setUp()
                    primary = kind("read")
                    self.read_error = primary
                    self.os.close_errors[10] = OSError("close")
                    with self.assertRaises(kind) as caught:
                        self.env[function]()
                    self.assertIs(caught.exception, primary)
                    self.assert_closed_once()

    def test_reader_ordinary_read_and_close_failures_still_refuse_identity(self):
        for function in ("load_injected_build", "runtime_source_sha256"):
            for read_fails in (False, True):
                with self.subTest(function=function, read_fails=read_fails):
                    self.setUp()
                    if read_fails:
                        self.read_error = OSError("read")
                    self.os.close_errors[10] = OSError("close")
                    self.assertIsNone(self.env[function]())
                    self.assert_closed_once()

    def test_reader_normal_hash_and_payload(self):
        self.assertIsInstance(self.env["runtime_source_sha256"](), str)
        self.assert_closed_once()
        self.setUp()
        record = dict(
            source_commit="a" * 40,
            source_sha256="b" * 64,
            build_id="local",
            source_dirty=False,
        )
        self.payload = json.dumps(record).encode()
        self.assertEqual(self.env["load_injected_build"](), record)
        self.assert_closed_once()

    def test_post_acquisition_line_interrupt_cleans_owned_handle(self):
        for function in (
            "_identity_directory",
            "_publish_identity",
            "load_injected_build",
            "runtime_source_sha256",
        ):
            with self.subTest(function=function):
                self.setUp()
                primary = KeyboardInterrupt("after acquisition")
                armed = True
                previous = sys.gettrace()

                def interrupt(frame, event, arg):
                    nonlocal armed
                    if (
                        armed
                        and event == "line"
                        and frame.f_code.co_filename == str(_SOURCE)
                        and frame.f_code.co_name == function
                    ):
                        local = frame.f_locals
                        owned = local.get("owned", {})
                        if self.os.active and (
                            owned or local.get("fd", -1) >= 0 or "directory_fd" in local
                        ):
                            armed = False
                            raise primary
                    return interrupt

                try:
                    sys.settrace(interrupt)
                    with self.assertRaises(KeyboardInterrupt) as caught:
                        if function == "_identity_directory":
                            self.directory()
                        elif function == "_publish_identity":
                            self.publish()
                        else:
                            self.env[function]()
                    self.assertIs(caught.exception, primary)
                finally:
                    sys.settrace(previous)
                self.assertFalse(armed, "probe must reach the acquisition boundary")
                self.assert_closed_once()


if __name__ == "__main__":
    unittest.main()
