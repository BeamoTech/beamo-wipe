"""Failed stop delivery preserves terminal engine evidence and retry ownership."""

from dataclasses import replace
import errno
import subprocess

import pytest

from beamo_wipe import nwipe_runner
from beamo_wipe.models import MethodId
from beamo_wipe.safety import SafetyError
from test_cancel_after_exit_regression import COMPLETE_LOG, _runner


STAMP = "[2026/10/19 05:00:00] error: "
CASES = (
    (STAMP + "/dev/vda: >>> FAILURE! <<<\n", 1, "engine_failed"),
    (STAMP + "Verification mismatch on '/dev/vda'\n", 1, "verification_failed"),
    ("Nwipe successfully completed.\n", 0, "completion_missing"),
    ("", 5, "process_failed"),
    (COMPLETE_LOG, 0, "completed"),
)


@pytest.fixture(autouse=True)
def no_native_actions(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Cancellation fixture attempted a native action")

    monkeypatch.setattr(nwipe_runner.subprocess, "Popen", forbidden)
    monkeypatch.setattr(nwipe_runner.subprocess, "run", forbidden)
    monkeypatch.setattr(nwipe_runner, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(nwipe_runner, "_try_log_diag", lambda *_args: None)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("delivery", ("permission", "lookup", "delivered"))
@pytest.mark.parametrize("log,exit_code,reason", CASES)
def test_stop_without_delivery_keeps_natural_terminal_result(
    tmp_path, method, delivery, log, exit_code, reason
):
    runner = _runner(tmp_path, log)
    runner._active_request = replace(runner._active_request, method=method)
    events = []

    class Process:
        returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            events.append("terminate")
            if delivery == "permission":
                raise PermissionError(errno.EPERM, "injected signal refusal")
            if delivery == "lookup":
                raise ProcessLookupError("exited before signal")

        def wait(self, timeout=None):
            events.append("wait")
            self.returncode = exit_code
            return exit_code

    runner._proc = Process()
    runner.cancel()
    assert events == ["terminate", "wait"]
    assert runner.result is not None
    # A normally returning terminate is ambiguous at an exit race; the existing
    # contract retains cancellation except when complete natural proof survives.
    expected = "cancelled" if delivery == "delivered" and reason != "completed" else reason
    assert runner.result.reason == expected
    assert runner.result.exit_code == exit_code
    assert runner.result.ok is (expected == "completed")
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
    assert runner._cancelling is None


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("kill_delivery", ("delivered", "denied", "still_alive"))
def test_failed_terminate_retains_kill_and_retry_semantics(
    tmp_path, monkeypatch, method, kill_delivery
):
    runner = _runner(tmp_path, CASES[0][0])
    runner._active_request = replace(runner._active_request, method=method)
    events = []

    class Process:
        returncode = None
        waits = 0

        def poll(self):
            return self.returncode

        def terminate(self):
            events.append("terminate")
            raise PermissionError(errno.EPERM, "injected signal refusal")

        def kill(self):
            events.append("kill")
            if kill_delivery != "delivered":
                raise PermissionError(errno.EPERM, "injected kill refusal")

        def wait(self, timeout=None):
            self.waits += 1
            if self.waits == 1 or kill_delivery == "still_alive":
                raise subprocess.TimeoutExpired("fake child", timeout)
            self.returncode = -9 if kill_delivery == "delivered" else 1
            return self.returncode

    proc = runner._proc = Process()
    if kill_delivery == "still_alive":
        released = []
        monkeypatch.setattr(runner, "_release_wipe_lock", lambda: released.append(True))
        with pytest.raises(SafetyError, match="may still be erasing"):
            runner.cancel()
        assert not released and runner._proc is proc and runner.result is None
    else:
        runner.cancel()
        assert runner._proc is None
        assert runner.result.reason == ("cancelled" if kill_delivery == "delivered" else "engine_failed")
    assert events == ["terminate", "kill"]
    assert runner._cancelling is None
