"""Optional inhibitor logging must preserve cleanup and process ownership."""

import fcntl
import os
import subprocess

import pytest

from beamo_wipe import diagnostics, sleep_inhibit
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner, SafetyError


DIAGNOSTIC_ERRORS = [KeyboardInterrupt, SystemExit, OSError, None]


def diagnostic_stub(monkeypatch, error):
    calls = []

    def emit(*args):
        calls.append(args)
        if error is not None:
            raise error("owned optional diagnostic failure")

    monkeypatch.setattr(diagnostics, "log_diag", emit)
    return calls


def live_environment(monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_LIVE", "1")
    monkeypatch.delenv("BEAMO_WIPE_DRY_RUN", raising=False)


def no_escape(call):
    try:
        return call()
    except BaseException as exc:
        pytest.fail(f"optional diagnostic interrupted ownership: {type(exc).__name__}")


class RefusedHelper:
    def __init__(self, exited_on_recheck=False):
        self.exited_on_recheck = exited_on_recheck
        self.polls = 0
        self.stop_calls = []

    def poll(self):
        self.polls += 1
        return 7 if self.exited_on_recheck and self.polls > 1 else None

    def terminate(self):
        self.stop_calls.append("terminate")
        raise PermissionError("owned helper terminate denied")

    def kill(self):
        self.stop_calls.append("kill")
        raise PermissionError("owned helper kill denied")


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
@pytest.mark.parametrize("spawn_error", [OSError, ValueError])
def test_unavailable_inhibitor_keeps_start_optional(
    monkeypatch, diagnostic_error, spawn_error
):
    live_environment(monkeypatch)
    calls = diagnostic_stub(monkeypatch, diagnostic_error)
    spawned = []

    def unavailable(argv, **kwargs):
        spawned.append((argv, kwargs))
        raise spawn_error("owned unavailable helper")

    monkeypatch.setattr(sleep_inhibit.subprocess, "Popen", unavailable)
    inhibitor = sleep_inhibit.SleepInhibit()
    no_escape(inhibitor.start)
    assert inhibitor._proc is None and not inhibitor.active
    assert len(spawned) == 1 and spawned[0][0] == sleep_inhibit.inhibit_argv()
    assert calls == [("power", "sleep_inhibit_unavailable", sleep_inhibit.INHIBIT_BIN)]


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
@pytest.mark.parametrize("exited_on_recheck", [False, True])
def test_stop_rechecks_helper_ownership_despite_optional_diagnostic(
    monkeypatch, diagnostic_error, exited_on_recheck
):
    calls = diagnostic_stub(monkeypatch, diagnostic_error)
    inhibitor = sleep_inhibit.SleepInhibit()
    helper = RefusedHelper(exited_on_recheck)
    inhibitor._proc = helper
    no_escape(inhibitor.stop)
    assert inhibitor._proc is (None if exited_on_recheck else helper)
    assert helper.stop_calls == ["terminate", "kill"]
    assert calls == [("power", "sleep_inhibit_stop_failed", "terminate")]


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
@pytest.mark.parametrize("entry", ["poll", "cancel"])
@pytest.mark.parametrize("code", [0, 7])
def test_exited_engine_retires_owned_descriptors_despite_helper_diagnostic(
    tmp_path, monkeypatch, diagnostic_error, entry, code
):
    diagnostic_stub(monkeypatch, diagnostic_error)
    log = tmp_path / "owned.log"
    log.write_text(
        "/dev/vda: 100.00%, round 1 of 1, pass 1 of 1, "
        "eta 00:00:00, [verifying]\n"
    )
    request = WipeRequest("/dev/vda", MethodId.EVERYDAY, "/dev/sr0", str(log))

    class ExitedEngine:
        returncode = code

        def poll(self):
            return self.returncode

    runner = NwipeRunner()
    runner._proc = ExitedEngine()
    runner._active_request = request
    helper = RefusedHelper()
    runner._sleep_inhibit._proc = helper
    runner._lock_fd = os.open(tmp_path / "owned.lock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(runner._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    runner._log_fd = os.open(log, os.O_RDONLY)
    try:
        no_escape(lambda: runner.poll(request) if entry == "poll" else runner.cancel())
        result = runner.result
        assert result is not None and result.ok is (code == 0)
        assert result.exit_code == code
        assert result.reason == ("completed" if code == 0 else "process_failed")
        assert runner._proc is None and runner._active_request is None
        assert runner._lock_fd is None and runner._log_fd is None
        assert not runner._cleanup_failed
        assert runner._sleep_inhibit._proc is helper
        assert runner._cancelling is None and runner._status_polling is None
        assert runner.poll(request) is result
        runner.cancel()
        assert runner.result is result
    finally:
        # Exact owned fixture handles only, including the red baseline paths.
        if runner._lock_fd is not None:
            fcntl.flock(runner._lock_fd, fcntl.LOCK_UN)
            os.close(runner._lock_fd)
            runner._lock_fd = None
        if runner._log_fd is not None:
            os.close(runner._log_fd)
            runner._log_fd = None


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
def test_uncertain_engine_stays_owned_and_never_stops_inhibitor(
    tmp_path, monkeypatch, diagnostic_error
):
    diagnostic_stub(monkeypatch, diagnostic_error)
    request = WipeRequest(
        "/dev/vda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "unused.log")
    )

    class UnstoppableEngine(RefusedHelper):
        returncode = None

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("owned fake engine", timeout)

    engine = UnstoppableEngine()
    helper = RefusedHelper()
    runner = NwipeRunner()
    runner._proc = engine
    runner._active_request = request
    runner._sleep_inhibit._proc = helper
    with pytest.raises(SafetyError, match="Could not stop nwipe"):
        runner.cancel()
    assert runner._proc is engine and runner._active_request is request
    assert runner.result is None and runner._cancelling is None
    assert runner._sleep_inhibit._proc is helper and helper.stop_calls == []


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
def test_start_does_not_replace_an_uncertain_previous_helper(monkeypatch, diagnostic_error):
    live_environment(monkeypatch)
    diagnostic_stub(monkeypatch, diagnostic_error)
    spawned = []
    monkeypatch.setattr(sleep_inhibit.subprocess, "Popen", lambda *a, **kw: spawned.append(a))
    helper = RefusedHelper()
    inhibitor = sleep_inhibit.SleepInhibit()
    inhibitor._proc = helper
    no_escape(inhibitor.start)
    assert inhibitor._proc is helper and spawned == []


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
@pytest.mark.parametrize("mode", ["desktop", "dry_run"])
def test_inactive_boundaries_do_not_spawn_or_log(monkeypatch, diagnostic_error, mode):
    live_environment(monkeypatch)
    if mode == "desktop":
        monkeypatch.delenv("BEAMO_WIPE_LIVE")
    else:
        monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    calls = diagnostic_stub(monkeypatch, diagnostic_error)
    spawned = []
    monkeypatch.setattr(sleep_inhibit.subprocess, "Popen", lambda *a, **kw: spawned.append(a))
    inhibitor = sleep_inhibit.SleepInhibit()
    no_escape(inhibitor.start)
    assert inhibitor._proc is None and spawned == calls == []


@pytest.mark.parametrize("diagnostic_error", DIAGNOSTIC_ERRORS)
def test_normal_helper_cleanup_does_not_depend_on_diagnostics(monkeypatch, diagnostic_error):
    live_environment(monkeypatch)
    calls = diagnostic_stub(monkeypatch, diagnostic_error)

    class NormalHelper:
        code = None

        def poll(self):
            return self.code

        def terminate(self):
            self.code = -15

        def wait(self, timeout):
            return self.code

    helper = NormalHelper()
    monkeypatch.setattr(sleep_inhibit.subprocess, "Popen", lambda *a, **kw: helper)
    inhibitor = sleep_inhibit.SleepInhibit()
    inhibitor.start()
    assert inhibitor.active
    inhibitor.stop()
    assert inhibitor._proc is None and not inhibitor.active and calls == []


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("entry", ["start", "stop"])
def test_actual_process_control_interrupts_still_propagate(monkeypatch, interrupt, entry):
    live_environment(monkeypatch)
    calls = diagnostic_stub(monkeypatch, None)

    def interrupted(*args, **kwargs):
        raise interrupt("owned process control interrupted")

    inhibitor = sleep_inhibit.SleepInhibit()
    helper = RefusedHelper()
    if entry == "start":
        monkeypatch.setattr(sleep_inhibit.subprocess, "Popen", interrupted)
    else:
        helper.terminate = interrupted
        inhibitor._proc = helper
    with pytest.raises(interrupt, match="owned process control interrupted"):
        getattr(inhibitor, entry)()
    assert inhibitor._proc is (None if entry == "start" else helper)
    assert calls == []
