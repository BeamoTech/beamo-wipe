"""Preserve terminal evidence when POSIX Popen stop sends no signal."""

from dataclasses import replace
import errno
import os
import signal
import subprocess

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError


_TERMINATE = subprocess.Popen.terminate
_KILL = subprocess.Popen.kill
_SEND_SIGNAL = subprocess.Popen.send_signal
_STAMP = "[2026/10/21 12:00:00] error: "
_COMPLETE = (
    module.NWIPE_DRIVE_STATUS_HEADER + "\n"
    " vda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)
_OUTCOMES = (
    (_STAMP + "/dev/vda: >>> FAILURE! <<<: code 1\n", 1, "engine_failed"),
    (_STAMP + "Verification mismatch on '/dev/vda'\n", 1, "verification_failed"),
    ("Nwipe successfully completed.\n", 0, "completion_missing"),
    ("", 5, "process_failed"),
    (_COMPLETE, 0, "completed"),
)


@pytest.fixture(autouse=True)
def fake_native_boundaries(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Receipt fixture attempted a native action")

    monkeypatch.setattr(module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(module.subprocess, "run", forbidden)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(module, "_recheck_identity_under_lock", forbidden)
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    monkeypatch.setattr(os, "kill", forbidden)
    original_realpath, original_open = os.path.realpath, os.open

    def fake_realpath(path, *args, **kwargs):
        if os.fsdecode(path).startswith("/dev/"):
            return os.fspath(path)
        return original_realpath(path, *args, **kwargs)

    def ordinary_open(path, *args, **kwargs):
        if os.fsdecode(path).startswith(("/dev/", "/sys/", "/proc/")):
            forbidden()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_realpath)
    monkeypatch.setattr(os, "open", ordinary_open)


@pytest.fixture
def owned_runner(tmp_path, monkeypatch):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    logfile = tmp_path / "fake-engine.log"
    logfile.write_text("", encoding="utf-8")
    logfile.chmod(0o600)
    request = WipeRequest("/dev/vda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner()
    runner._active_request = request
    runner._last_logfile = str(logfile)
    runner._acquire_wipe_lock(request)
    runner._log_fd = os.open(logfile, os.O_RDONLY)
    opened = os.fstat(runner._log_fd)
    runner._active_log_identity = (str(logfile), opened.st_dev, opened.st_ino)
    held = (runner._lock_fd, runner._log_fd)
    try:
        yield runner, request, logfile, held
    finally:
        runner._release_wipe_lock()


class _StandardProcess:
    """Real POSIX Popen methods; every status/wait/signal callback is fake."""

    terminate = _TERMINATE
    kill = _KILL
    send_signal = _SEND_SIGNAL
    returncode = None
    pid = 987654321


def _assert_terminal(runner, reason, code, held):
    assert runner.result is not None
    assert runner.result.reason == reason
    assert runner.result.exit_code == code
    assert runner.result.ok is (reason == "completed")
    assert runner._proc is None and runner._cancelling is None
    assert runner._lock_fd is None and runner._log_fd is None
    for fd in held:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("stop_stage", ("terminate", "kill"))
@pytest.mark.parametrize("no_delivery", ("inner-poll", "esrch"))
@pytest.mark.parametrize("log,code,reason", _OUTCOMES)
def test_stdlib_no_delivery_keeps_terminal_engine_result(
    owned_runner, monkeypatch, method, stop_stage, no_delivery, log, code, reason
):
    runner, request, logfile, held = owned_runner
    runner._active_request = replace(request, method=method)
    logfile.write_text(log, encoding="utf-8")
    events = []

    class Process(_StandardProcess):
        polls = waits = 0

        def poll(self):
            self.polls += 1
            boundary = 3 if stop_stage == "kill" else 2
            if no_delivery == "inner-poll" and self.polls >= boundary:
                self.returncode = code
            events.append(("poll", self.returncode))
            return self.returncode

        def wait(self, timeout):
            self.waits += 1
            events.append(("wait", timeout))
            if stop_stage == "kill" and self.waits == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            self.returncode = code
            return code

    proc = runner._proc = Process()

    def refused_signal(pid, sig):
        assert pid == proc.pid
        events.append(("refused", sig))
        if stop_stage == "kill" and sig == signal.SIGTERM:
            raise PermissionError(errno.EPERM, "injected refusal")
        assert no_delivery == "esrch"
        raise ProcessLookupError(errno.ESRCH, "exited before delivery")

    monkeypatch.setattr(os, "kill", refused_signal)
    runner.cancel()
    _assert_terminal(runner, reason, code, held)
    assert ("wait", 8) in events
    assert (("wait", 2) in events) is (stop_stage == "kill")


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("log,code,reason", _OUTCOMES)
def test_exit_observed_before_stop_never_calls_signal(
    owned_runner, method, log, code, reason
):
    runner, request, logfile, held = owned_runner
    runner._active_request = replace(request, method=method)
    logfile.write_text(log, encoding="utf-8")

    class Process(_StandardProcess):
        returncode = code

        def poll(self):
            return self.returncode

    runner._proc = Process()
    runner.cancel()
    _assert_terminal(runner, reason, code, held)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("stop_stage", ("terminate", "kill"))
@pytest.mark.parametrize("late_result", ("signal", "caught-signal", "complete"))
def test_delivered_stop_retains_cancellation_or_proven_completion(
    owned_runner, monkeypatch, method, stop_stage, late_result
):
    runner, request, logfile, held = owned_runner
    runner._active_request = replace(request, method=method)
    logfile.write_text(_COMPLETE if late_result == "complete" else _OUTCOMES[0][0])
    delivered = []

    class Process(_StandardProcess):
        waits = 0

        def poll(self):
            return self.returncode

        def wait(self, timeout):
            self.waits += 1
            if stop_stage == "kill" and self.waits == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            self.returncode = {"signal": -15, "caught-signal": 1, "complete": 0}[late_result]
            return self.returncode

    proc = runner._proc = Process()

    def delivered_signal(pid, sig):
        assert pid == proc.pid
        if stop_stage == "kill" and sig == signal.SIGTERM:
            raise PermissionError(errno.EPERM, "injected refusal")
        delivered.append(sig)

    monkeypatch.setattr(os, "kill", delivered_signal)
    runner.cancel()
    assert delivered == [signal.SIGTERM if stop_stage == "terminate" else signal.SIGKILL]
    expected = "completed" if late_result == "complete" else "cancelled"
    _assert_terminal(runner, expected, proc.returncode, held)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("later_noop", ("inner-poll", "esrch"))
def test_later_kill_noop_does_not_erase_delivered_term_receipt(
    owned_runner, monkeypatch, method, later_noop
):
    runner, request, logfile, held = owned_runner
    runner._active_request = replace(request, method=method)
    logfile.write_text(_OUTCOMES[0][0])
    events = []

    class Process(_StandardProcess):
        polls = waits = 0

        def poll(self):
            self.polls += 1
            if later_noop == "inner-poll" and self.polls >= 3:
                self.returncode = 1
            return self.returncode

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            self.returncode = 1
            return 1

    proc = runner._proc = Process()

    def signal_boundary(pid, sig):
        assert pid == proc.pid
        events.append(sig)
        if sig == signal.SIGKILL:
            assert later_noop == "esrch"
            raise ProcessLookupError(errno.ESRCH, "natural exit after TERM")

    monkeypatch.setattr(os, "kill", signal_boundary)
    runner.cancel()
    assert signal.SIGTERM in events
    _assert_terminal(runner, "cancelled", 1, held)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("override", ("terminate", "send_signal", "kill"))
def test_custom_process_delivery_stays_conservative(owned_runner, method, override):
    runner, request, logfile, held = owned_runner
    runner._active_request = replace(request, method=method)
    logfile.write_text(_OUTCOMES[0][0])
    events = []

    class Process(_StandardProcess):
        waits = 0

        def poll(self):
            return self.returncode

        def wait(self, timeout):
            self.waits += 1
            if override == "kill" and self.waits == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            return self.returncode

    def custom_stop(self):
        events.append(override)
        self.returncode = 1

    def custom_send(self, sig):
        events.append(sig)
        self.returncode = 1

    if override == "send_signal":
        Process.send_signal = custom_send
    elif override == "terminate":
        Process.terminate = custom_stop
    else:
        def denied_term(self):
            raise PermissionError(errno.EPERM, "injected refusal")

        Process.terminate = denied_term
        Process.kill = custom_stop
    runner._proc = Process()
    runner.cancel()
    assert events
    _assert_terminal(runner, "cancelled", 1, held)


@pytest.mark.parametrize("method", tuple(MethodId))
def test_unstoppable_process_keeps_both_owned_handles_and_retry(owned_runner, method):
    runner, request, _logfile, held = owned_runner
    runner._active_request = replace(request, method=method)

    class Process(_StandardProcess):
        def poll(self):
            return None

        def terminate(self):
            raise PermissionError(errno.EPERM, "injected refusal")

        def kill(self):
            raise PermissionError(errno.EPERM, "injected refusal")

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("fake", timeout)

    proc = runner._proc = Process()
    for _attempt in range(2):
        with pytest.raises(SafetyError, match="may still be erasing"):
            runner.cancel()
        assert runner._proc is proc and runner.result is None
        assert (runner._lock_fd, runner._log_fd) == held
        assert runner._cancelling is None
        assert not runner.start_not_spawned()
        for fd in held:
            os.fstat(fd)
