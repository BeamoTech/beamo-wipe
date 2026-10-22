"""CPython intentionally suppresses ESRCH; the runner must not call it delivered."""

import errno
import os
import signal
import subprocess

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("stop_stage", ("terminate", "kill"))
@pytest.mark.parametrize("failure", ("inner-poll", "suppressed-esrch"))
def test_natural_failure_when_stdlib_stop_delivered_no_signal(
    tmp_path, monkeypatch, method, stop_stage, failure
):
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    log = tmp_path / "fake.log"
    log.write_text("[2026/10/21 12:00:00] error: /dev/vda: >>> FAILURE! <<<: code 1\n")
    request = WipeRequest("/dev/vda", method, "/dev/sr0", str(log))
    runner = module.NwipeRunner()
    runner._active_request = request
    runner._last_logfile = str(log)
    events = []

    class Process:
        terminate = subprocess.Popen.terminate
        kill = subprocess.Popen.kill
        send_signal = subprocess.Popen.send_signal
        returncode = None
        pid = 987654321
        polls = 0
        waits = 0

        def poll(self):
            self.polls += 1
            boundary = 3 if stop_stage == "kill" else 2
            if failure == "inner-poll" and self.polls >= boundary:
                self.returncode = 1
            events.append(("poll", self.returncode))
            return self.returncode

        def wait(self, timeout):
            self.waits += 1
            events.append(("wait", timeout))
            if stop_stage == "kill" and self.waits == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            self.returncode = 1
            return 1

    proc = runner._proc = Process()

    def fake_kill(pid, sig):
        assert pid == proc.pid
        events.append(("refused-signal", sig))
        if stop_stage == "kill" and sig == signal.SIGTERM:
            raise PermissionError(errno.EPERM, "injected refusal")
        assert failure == "suppressed-esrch"
        raise ProcessLookupError(errno.ESRCH, "process exited before delivery")

    monkeypatch.setattr(os, "kill", fake_kill)
    runner.cancel()
    assert runner.result is not None
    assert runner.result.reason == "engine_failed", events
    assert runner.result.exit_code == 1
    assert not runner.result.ok
    assert runner._proc is None and runner._cancelling is None
