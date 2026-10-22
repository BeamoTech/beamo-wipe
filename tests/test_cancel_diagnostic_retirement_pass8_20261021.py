"""Optional diagnostics cannot interrupt Stop or terminal ownership retirement."""

import json
import os
import sys
from types import SimpleNamespace

import pytest

import beamo_wipe.app as app
from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


RUNTIME_FAILURES = (
    (None, None),
    (OSError, None),
    (KeyboardInterrupt, None),
    (SystemExit, None),
    (OSError, KeyboardInterrupt),
    (OSError, SystemExit),
)
RUNTIME_IDS = (
    "normal", "log-io-error", "log-keyboard-interrupt", "log-system-exit",
    "fallback-keyboard-interrupt", "fallback-system-exit",
)
HELPER_FAILURES = [(None, None)] + [
    (log_error, stderr_error)
    for log_error in (OSError, KeyboardInterrupt, SystemExit)
    for stderr_error in (None, OSError, KeyboardInterrupt, SystemExit)
]


@pytest.fixture(autouse=True)
def fake_machine(monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native inventory, engine, signal or power forbidden")

    realpath = os.path.realpath

    def fake_realpath(path, *args, **kwargs):
        if os.fsdecode(path).startswith("/dev/"):
            return os.fspath(path)
        return realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_realpath)
    monkeypatch.setattr(module.subprocess, "run", forbidden)
    monkeypatch.setattr(module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(module.os, "kill", forbidden)
    monkeypatch.setattr(app, "_shutdown", forbidden)
    monkeypatch.setattr(module.NwipeRunner, "start", forbidden)
    for name in ("run_lsblk", "read_cmdline", "read_mount_sources"):
        monkeypatch.setattr("beamo_wipe.discover." + name, forbidden)
    yield
    assert not effects


def _invoke(monkeypatch, callback, log_error, stderr_error):
    diagnostic_calls, fallback_calls = [], []

    def diagnostic(*args):
        diagnostic_calls.append(args)
        if log_error is not None:
            raise log_error("Fake optional logging failure")

    def write(data):
        fallback_calls.append(data)
        if stderr_error is not None:
            raise stderr_error("Fake optional stderr failure")
        return len(data)

    escaped, result = None, None
    with monkeypatch.context() as patch:
        patch.setattr("beamo_wipe.diagnostics.log_diag", diagnostic)
        patch.setattr(sys, "stderr", SimpleNamespace(write=write, flush=lambda: None))
        try:
            result = callback()
        except BaseException as error:
            escaped = type(error).__name__
    return SimpleNamespace(
        escaped=escaped, result=result, diagnostic_calls=diagnostic_calls,
        fallback_calls=fallback_calls,
    )


def _trace(request, result, **extra):
    trace = {"escaped": result.escaped, "diagnostic_calls": len(result.diagnostic_calls),
             "fallback_calls": len(result.fallback_calls), **extra}
    request.node.user_properties.append(("diagnostic_retirement_trace", json.dumps(trace)))
    return trace


@pytest.mark.parametrize("log_error,stderr_error", HELPER_FAILURES)
def test_optional_diagnostic_helper_never_escapes(
    monkeypatch, request, log_error, stderr_error,
):
    result = _invoke(
        monkeypatch, lambda: module._try_log_diag("nwipe", "fake_status"),
        log_error, stderr_error,
    )
    trace = _trace(request, result)
    assert result.escaped is None, trace
    assert len(result.diagnostic_calls) == 1
    assert bool(result.fallback_calls) == (log_error is not None)


@pytest.mark.parametrize("log_error,stderr_error", RUNTIME_FAILURES, ids=RUNTIME_IDS)
def test_optional_diagnostics_do_not_prevent_requested_stop(
    tmp_path, monkeypatch, request, log_error, stderr_error,
):
    logfile = tmp_path / "fake-active.log"
    logfile.write_text("Fake engine in progress\n")
    calls = []

    class FakeProcess:
        returncode = None

        def poll(self):
            calls.append("poll-error")
            raise OSError("Fake process status failure")

        def terminate(self):
            calls.append("terminate")
            self.returncode = -15

        def wait(self, timeout):
            calls.append("wait")
            return self.returncode

    proc = FakeProcess()
    runner = module.NwipeRunner()
    runner._proc = proc
    runner._active_request = WipeRequest(
        "/dev/FAKE-DATA", MethodId.EVERYDAY, "/dev/FAKE-BOOT", str(logfile),
    )
    runner._last_logfile = str(logfile)
    result = _invoke(monkeypatch, runner.cancel, log_error, stderr_error)
    trace = _trace(request, result, calls=calls, process_retained=runner._proc is proc)
    assert "terminate" in calls, trace
    assert result.escaped is None, trace
    assert runner._proc is None
    assert runner.result is not None and runner.result.reason == "cancelled"
    assert runner._cancelling is None and runner._status_polling is None
    assert runner._active_request is None
    assert runner.start_not_spawned()
    runner.cancel()
    assert calls.count("terminate") == 1
    assert logfile.read_text() == "Fake engine in progress\n"


@pytest.mark.parametrize("log_error,stderr_error", RUNTIME_FAILURES, ids=RUNTIME_IDS)
def test_optional_diagnostics_cannot_strand_completed_process(
    tmp_path, monkeypatch, request, log_error, stderr_error,
):
    logfile = tmp_path / "fake-completed.log"
    text = (
        "/dev/FAKE-DATA: 100.00%, round 1 of 1, pass 1 of 1, "
        "eta 00:00:00, [verifying]\n"
    )
    logfile.write_text(text)

    class ExitedProcess:
        returncode = 0

        def poll(self):
            return self.returncode

    runner = module.NwipeRunner()
    runner._proc = ExitedProcess()
    run = WipeRequest(
        "/dev/FAKE-DATA", MethodId.EVERYDAY, "/dev/FAKE-BOOT", str(logfile),
    )
    runner._active_request = run
    result = _invoke(monkeypatch, lambda: runner.poll(run), log_error, stderr_error)
    trace = _trace(request, result, process_retained=runner._proc is not None)
    assert result.escaped is None, trace
    assert result.result is runner.result
    assert runner.result is not None and runner.result.ok
    assert runner.result.reason == "completed" and runner.progress == 100.0
    assert runner._proc is None and runner._active_request is None
    assert runner._status_polling is None and runner.start_not_spawned()
    assert logfile.read_text() == text
