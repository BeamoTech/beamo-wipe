"""Portable exact-AST controls; diagnostic/audio effects are entirely fake."""

from __future__ import annotations

import ast
import builtins
import io
import json
import posixpath
import re
import stat
import sys
import unittest
import unicodedata
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1]
_DIAG_SOURCE = _ROOT / "src/beamo_wipe/diagnostics.py"
_SOUND_SOURCE = _ROOT / "src/beamo_wipe/sound.py"


class DiagnosticOS:
    O_RDONLY, O_DIRECTORY, O_NOFOLLOW, O_NONBLOCK, O_CLOEXEC = 1, 2, 4, 8, 16
    O_WRONLY, O_RDWR, O_CREAT, O_APPEND, SEEK_SET = 32, 64, 128, 256, 0
    SEEK_END = 2

    def __init__(self):
        self.path = SimpleNamespace(basename=posixpath.basename)
        self.opened, self.closed = [], []
        self.handles = {}
        self.close_error = self.read_error = self.write_error = None
        self.verify_error = None
        self.verify_at = 0
        self.verifies = 0
        self.payload = b'{"code":"INERT"}\n'
        self.position = 0
        self.release_on_error = True
        self.directory_mode = stat.S_IFDIR | 0o700

    def open(self, path, flags, *args, **kwargs):
        fd = len(self.opened)
        self.opened.append(fd)
        self.handles[fd] = (
            "directory"
            if flags & self.O_DIRECTORY
            else "serial"
            if str(path) == "/dev/ttyS0"
            else "file"
        )
        return fd

    def close(self, fd):
        self.closed.append(fd)
        if fd not in self.handles:
            raise AssertionError("descriptor close retried")
        if self.close_error is None or self.release_on_error:
            del self.handles[fd]
        if self.close_error is not None:
            raise self.close_error

    def fstat(self, fd):
        kind = self.handles[fd]
        mode = (
            self.directory_mode
            if kind == "directory"
            else stat.S_IFCHR | 0o600
            if kind == "serial"
            else stat.S_IFREG | 0o600
        )
        return SimpleNamespace(
            st_dev=1,
            st_ino=5 if kind == "directory" else 6,
            st_mode=mode,
            st_uid=0,
            st_nlink=1,
            st_size=len(self.payload),
        )

    def stat(self, path, *, follow_symlinks):
        self.verifies += 1
        if self.verify_error is not None and self.verifies == self.verify_at:
            raise self.verify_error
        return SimpleNamespace(
            st_dev=1, st_ino=5, st_mode=self.directory_mode, st_uid=0
        )

    def getuid(self):
        return 0

    def getpid(self):
        return 1

    def read(self, fd, count):
        if self.read_error is not None:
            raise self.read_error
        data = self.payload[self.position : self.position + count]
        self.position += len(data)
        return data

    def write(self, fd, data):
        if self.write_error is not None:
            raise self.write_error
        count = min(17, len(data))
        self.payload += bytes(data[:count])
        return count

    def lseek(self, fd, offset, origin):
        self.position = (
            offset if origin == self.SEEK_SET else len(self.payload) + offset
        )
        return self.position

    def fchmod(self, fd, mode):
        pass

    def fsync(self, fd):
        pass

    def ftruncate(self, fd, size):
        self.payload = self.payload[:size]


class DiagnosticCleanup(unittest.TestCase):
    def setUp(self):
        self.os = DiagnosticOS()
        self.stderr = io.StringIO()

        def fake_import(name, *args, **kwargs):
            if name == "beamo_wipe.safety":
                return SimpleNamespace(default_log_dir=lambda: PurePosixPath("/inert"))
            if name == "sys":
                return SimpleNamespace(stderr=self.stderr)
            raise AssertionError("unprovided import: " + name)

        self.env = dict(
            __builtins__=dict(vars(builtins), __import__=fake_import),
            Path=PurePosixPath,
            os=self.os,
            stat=stat,
            re=re,
            json=json,
            unicodedata=unicodedata,
            time=SimpleNamespace(monotonic=lambda: 1),
        )
        tree = ast.parse(_DIAG_SOURCE.read_bytes(), filename=str(_DIAG_SOURCE))
        body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Assign))]
        exec(
            compile(ast.Module(body=body, type_ignores=[]), str(_DIAG_SOURCE), "exec"),
            self.env,
        )
        self.env["_iso_now"] = lambda: "2026-10-26T00:00:00Z"

    def call(self, name):
        if name == "_open_diagnostics":
            return self.env[name](PurePosixPath("/inert"), self.os.O_RDONLY)
        if name == "log_diag":
            return self.env[name]("inert", "INERT", "line\nwith\u202econtrol")
        if name == "emit_serial_marker":
            return self.env[name]("BEAMO_WIPE_INERT")
        return self.env[name]()

    def assert_closed_once(self):
        self.assertEqual(self.os.handles, {})
        self.assertCountEqual(self.os.closed, self.os.opened)

    def test_normal_directory_handoff_transfers_both_handles(self):
        handles = self.call("_open_diagnostics")
        self.assertEqual(handles, (0, 1))
        self.assertEqual(self.os.closed, [])
        for fd in reversed(handles):
            self.os.close(fd)
        self.assert_closed_once()

    def test_reader_returns_decoded_rows_and_closes_both(self):
        self.assertEqual(self.call("read_diagnostics"), [{"code": "INERT"}])
        self.assert_closed_once()

    def test_logger_sanitizes_json_and_closes_both(self):
        self.assertTrue(self.call("log_diag"))
        row = json.loads(self.os.payload.splitlines()[-1])
        self.assertEqual(row["detail"], "line with control")
        self.assert_closed_once()

    def test_serial_success_and_invalid_marker_refusal(self):
        self.assertTrue(self.call("emit_serial_marker"))
        self.assert_closed_once()
        self.setUp()
        for marker in ("bad", "BEAMO_WIPE_X\n", "BEAMO_WIPE_" + "X" * 65, None):
            self.assertFalse(self.env["emit_serial_marker"](marker))
        self.assertEqual(self.os.opened, [])

    def test_constructor_preserves_primary_and_closes_remaining_handles(self):
        for kind in (OSError, KeyboardInterrupt, SystemExit):
            for after in (1, 2):
                with self.subTest(kind=kind, after=after):
                    self.setUp()
                    primary = kind("verify")
                    self.os.verify_error = primary
                    self.os.verify_at = after
                    self.os.close_error = OSError("close")
                    with self.assertRaises(kind) as caught:
                        self.call("_open_diagnostics")
                    self.assertIs(caught.exception, primary)
                    self.assert_closed_once()

    def test_body_interrupt_is_not_swallowed_by_cleanup_error(self):
        for name in ("read_diagnostics", "log_diag", "emit_serial_marker"):
            for kind in (KeyboardInterrupt, SystemExit):
                with self.subTest(name=name, kind=kind):
                    self.setUp()
                    primary = kind("body")
                    if name == "read_diagnostics":
                        self.os.read_error = primary
                    else:
                        self.os.write_error = primary
                    self.os.close_error = OSError("close")
                    with self.assertRaises(kind) as caught:
                        self.call(name)
                    self.assertIs(caught.exception, primary)
                    self.assert_closed_once()

    def test_ordinary_io_and_cleanup_failures_keep_best_effort_refusal(self):
        for name in ("read_diagnostics", "log_diag", "emit_serial_marker"):
            for body_fails in (False, True):
                with self.subTest(name=name, body_fails=body_fails):
                    self.setUp()
                    self.os.close_error = OSError("close")
                    if body_fails:
                        self.os.read_error = self.os.write_error = OSError("body")
                    self.assertEqual(
                        self.call(name), [] if name == "read_diagnostics" else False
                    )
                    self.assert_closed_once()

    def test_failed_close_is_not_retried_when_os_retains_descriptor(self):
        self.os.close_error = OSError("close")
        self.os.release_on_error = False
        self.assertEqual(self.call("read_diagnostics"), [])
        self.assertEqual(self.os.closed, [1, 0])
        self.assertEqual(set(self.os.handles), {0, 1})

    def test_unsafe_directory_refused_before_file_open(self):
        self.os.directory_mode = stat.S_IFDIR | 0o777
        self.assertEqual(self.call("read_diagnostics"), [])
        self.assertEqual(self.os.opened, [0])
        self.assert_closed_once()

    def test_post_acquisition_interrupt_closes_all_owned_handles(self):
        for name in (
            "_open_diagnostics",
            "read_diagnostics",
            "log_diag",
            "emit_serial_marker",
        ):
            for kind in (KeyboardInterrupt, SystemExit):
                with self.subTest(name=name, kind=kind):
                    self.setUp()
                    primary = kind("after acquisition")
                    armed = True
                    previous = sys.gettrace()

                    def interrupt(frame, event, arg):
                        nonlocal armed
                        if (
                            armed
                            and event == "line"
                            and frame.f_code.co_filename == str(_DIAG_SOURCE)
                            and frame.f_code.co_name == name
                        ):
                            local = frame.f_locals
                            if self.os.handles and (
                                local.get("owned")
                                or any(
                                    local.get(key, -1) >= 0
                                    for key in ("fd", "directory_fd")
                                )
                            ):
                                armed = False
                                raise primary
                        return interrupt

                    try:
                        sys.settrace(interrupt)
                        with self.assertRaises(kind) as caught:
                            self.call(name)
                        self.assertIs(caught.exception, primary)
                    finally:
                        sys.settrace(previous)
                    self.assertFalse(armed)
                    self.assert_closed_once()


class AudioReaperAcceptance(unittest.TestCase):
    def setup_audio(self, *, failure=None, fail_start=False):
        self.events, self.reapers, self.calls = [], [], []
        owner = self

        class Event:
            def __init__(self):
                self.flag = False
                self.reject = len(owner.events) == 1 and failure is not None
                owner.events.append(self)

            def set(self):
                self.flag = True
                if self.reject:
                    self.reject = False
                    raise failure("acceptance")

            def clear(self):
                self.flag = False

            def is_set(self):
                return self.flag

            def wait(self):
                owner.assertTrue(self.flag)

        class Thread:
            def __init__(self, *, target, daemon):
                owner.assertTrue(daemon)
                self.target = target
                owner.reapers.append(self)

            def start(self):
                if fail_start:
                    raise RuntimeError("start")

        self.process = SimpleNamespace(
            terminate=lambda: self.calls.append("terminate"),
            wait=lambda **kw: self.calls.append("wait"),
        )

        def fake_import(name, *args, **kwargs):
            owner.assertEqual(name, "beamo_wipe.safety")
            return SimpleNamespace(
                resolve_system_binary=lambda tool: "/inert/" + tool,
                session_exec_env=lambda: {},
            )

        env = dict(
            __builtins__=dict(vars(builtins), __import__=fake_import),
            _ALLOWED_BINARIES={"paplay"},
            _audio_context=SimpleNamespace(),
            _PLAY_TIMEOUT=1,
            threading=SimpleNamespace(Event=Event, Thread=Thread),
            subprocess=SimpleNamespace(
                Popen=lambda *a, **kw: self.process,
                DEVNULL=-1,
                TimeoutExpired=type("TimeoutExpired", (Exception,), {}),
                SubprocessError=type("SubprocessError", (Exception,), {}),
            ),
        )
        tree = ast.parse(_SOUND_SOURCE.read_bytes(), filename=str(_SOUND_SOURCE))
        node = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "_popen"
        )
        exec(
            compile(
                ast.Module(body=[node], type_ignores=[]), str(_SOUND_SOURCE), "exec"
            ),
            env,
        )
        return env["_popen"]

    def test_failed_acceptance_revokes_reaper_before_cleanup(self):
        for failure in (RuntimeError, KeyboardInterrupt, SystemExit):
            with self.subTest(failure=failure):
                spawn = self.setup_audio(failure=failure)
                self.assertIsNone(spawn("paplay", ["inert.wav"]))
                self.assertEqual(self.calls, ["terminate", "wait"])
                self.assertFalse(self.events[1].is_set())
                self.reapers[0].target()
                self.assertEqual(self.calls, ["terminate", "wait"])

    def test_failed_thread_start_owns_cleanup_without_reaper(self):
        spawn = self.setup_audio(fail_start=True)
        self.assertIsNone(spawn("paplay", ["inert.wav"]))
        self.reapers[0].target()
        self.assertEqual(self.calls, ["terminate", "wait"])

    def test_success_has_one_reaper_and_one_wait(self):
        spawn = self.setup_audio()
        self.assertIs(spawn("paplay", ["inert.wav"]), self.process)
        self.reapers[0].target()
        self.assertEqual(self.calls, ["wait"])


if __name__ == "__main__":
    unittest.main()
