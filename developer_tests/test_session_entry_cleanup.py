"""Portable entry cleanup policy tests with exact AST and inert dependencies."""

from __future__ import annotations

import ast
import builtins
import io
import unittest
from pathlib import Path
from types import SimpleNamespace

_SOURCE = Path(__file__).resolve().parents[1] / "src/beamo_wipe/app.py"
_STORE_SOURCE = (
    Path(__file__).resolve().parents[1] / "src/beamo_wipe/session_recovery.py"
)


class SafetyError(RuntimeError):
    pass


class EntryCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _SOURCE.read_bytes()
        cls.store_source = _STORE_SOURCE.read_bytes()

    def setUp(self):
        self.closed, self.logs, self.markers = [], [], []
        self.body_error = self.close_error = self.open_error = None
        self.diagnostic_error = None
        self.live = True
        self.calls = 0
        owner = next(
            n
            for n in ast.parse(self.store_source).body
            if isinstance(n, ast.ClassDef) and n.name == "SessionStore"
        )
        close = next(
            n
            for n in owner.body
            if isinstance(n, ast.FunctionDef) and n.name == "close"
        )

        def close_fd(fd):
            self.assertNotIn(fd, self.closed)
            self.closed.append(fd)
            if fd == 17 and self.close_error is not None:
                raise self.close_error

        ns = {"os": SimpleNamespace(close=close_fd)}
        exec(
            compile(
                ast.fix_missing_locations(ast.Module(body=[close], type_ignores=[])),
                str(_STORE_SOURCE),
                "exec",
            ),
            ns,
        )
        self.store = SimpleNamespace(fd=1, owner=17, quiescent=-1)
        self.store.close = lambda close=ns["close"]: close(self.store)

        def open_store():
            if self.open_error is not None:
                raise self.open_error
            return self.store

        self.store.open = open_store

        def main_body(*args, **kwargs):
            self.calls += 1
            if self.live:
                self.assertIs(kwargs["session_store"], self.store)
            if self.body_error is not None:
                raise self.body_error
            return 9

        def log(*args):
            self.logs.append(args)
            if self.diagnostic_error is not None:
                raise self.diagnostic_error

        def importer(name, *args, **kwargs):
            if name == "beamo_wipe.session_recovery":
                return SimpleNamespace(
                    SessionStore=lambda: self.store,
                    RECOVERY_DIRECTORY_NOT_VOLATILE="not volatile",
                )
            if name == "beamo_wipe.diagnostics":
                return SimpleNamespace(
                    log_diag=log,
                    emit_serial_marker=lambda marker: self.markers.append(marker),
                )
            raise AssertionError(name)

        main = next(
            n
            for n in ast.parse(self.source).body
            if isinstance(n, ast.FunctionDef) and n.name == "main"
        )
        ns = {
            "__builtins__": dict(vars(builtins), __import__=importer),
            "SafetyError": SafetyError,
            "_parser": lambda: SimpleNamespace(parse_args=lambda argv: object()),
            "running_on_live_usb": lambda: self.live,
            "_main": main_body,
            "RECOVERY_UNAVAILABLE": "unavailable",
            "sys": SimpleNamespace(stderr=io.StringIO()),
        }
        exec(
            compile(ast.Module(body=[main], type_ignores=[]), str(_SOURCE), "exec"), ns
        )
        self.main = ns["main"]

    def assert_raised(self, expected):
        caught = None
        try:
            self.main([])
        except BaseException as error:
            caught = error
        self.assertIs(caught, expected)
        self.assertEqual(self.closed, [17, 1])
        self.assertEqual(
            (self.store.fd, self.store.owner, self.store.quiescent), (-1, -1, -1)
        )

    def test_escaping_primary_survives_all_cleanup_and_diagnostic_errors(self):
        for primary_type in (KeyboardInterrupt, SystemExit, RuntimeError):
            for cleanup_type in (None, OSError, KeyboardInterrupt):
                with self.subTest(
                    primary=primary_type.__name__, cleanup=str(cleanup_type)
                ):
                    self.setUp()
                    primary = primary_type("PRIVATE original")
                    self.body_error = primary
                    self.close_error = (
                        None
                        if cleanup_type is None
                        else cleanup_type("PRIVATE cleanup")
                    )
                    self.diagnostic_error = SystemExit("PRIVATE diagnostic")
                    self.assert_raised(primary)
                    if cleanup_type is not None:
                        self.assertEqual(
                            self.logs,
                            [
                                (
                                    "session_recovery",
                                    "store_close",
                                    cleanup_type.__name__,
                                )
                            ],
                        )

    def test_handled_startup_refusals_keep_failure_status(self):
        for source in ("open", "body"):
            for error_type in (OSError, SafetyError, ValueError):
                with self.subTest(source=source, error=error_type.__name__):
                    self.setUp()
                    primary = error_type("PRIVATE refusal")
                    if source == "open":
                        self.open_error = primary
                    else:
                        self.body_error = primary
                    self.close_error = OSError("PRIVATE cleanup")
                    self.assertEqual(self.main([]), 3)
                    self.assertEqual(self.closed, [17, 1])
                    self.assertEqual(self.calls, 0 if source == "open" else 1)
                    self.assertEqual(self.markers, ["BEAMO_WIPE_RECOVERY_UNAVAILABLE"])
                    self.assertEqual(
                        self.logs, [("session_recovery", "store_close", "OSError")]
                    )

    def test_success_and_close_only_refusal(self):
        self.assertEqual(self.main([]), 9)
        self.assertEqual(self.closed, [17, 1])
        for kind in (OSError, KeyboardInterrupt):
            with self.subTest(kind=kind.__name__):
                self.setUp()
                error = kind("close only")
                self.close_error = error
                self.assert_raised(error)

    def test_preview_route_does_not_open_or_close_journal(self):
        self.live = False
        self.assertEqual(self.main([]), 9)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.closed, [])


if __name__ == "__main__":
    unittest.main()
