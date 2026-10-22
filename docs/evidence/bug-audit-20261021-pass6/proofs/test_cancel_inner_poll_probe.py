"""Fake lifecycle probe using CPython's actual no-signal terminate branch."""

import os
import subprocess

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


STAMP = "[2026/10/21 12:00:00] error: "
COMPLETE = (
    module.NWIPE_DRIVE_STATUS_HEADER + "\n"
    " vda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)
CASES = (
    (STAMP + "/dev/vda: >>> FAILURE! <<<: code 1\n", 1, "engine_failed"),
    (STAMP + "Verification mismatch on '/dev/vda'\n", 1, "verification_failed"),
    ("Nwipe successfully completed.\n", 0, "completion_missing"),
    ("", 5, "process_failed"),
    (COMPLETE, 0, "completed"),
)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("timing", ("before-stop", "inside-terminate", "signal-delivered"))
@pytest.mark.parametrize("log,code,reason", CASES)
def test_inner_popen_poll_exit_is_not_an_owner_cancellation(
    tmp_path, monkeypatch, method, timing, log, code, reason
):
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    logfile = tmp_path / "fake.log"
    logfile.write_text(log, encoding="utf-8")
    request = WipeRequest("/dev/vda", method, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner()
    runner._active_request = request
    runner._last_logfile = str(logfile)
    events = []

    class Process:
        # Real stdlib signal-delivery logic, without creating any process.
        terminate = subprocess.Popen.terminate
        send_signal = subprocess.Popen.send_signal
        returncode = None
        pid = 987654321
        polls = 0

        def poll(self):
            self.polls += 1
            if timing == "before-stop" or (
                timing == "inside-terminate" and self.polls >= 2
            ):
                self.returncode = code
            events.append(("poll", self.returncode))
            return self.returncode

        def wait(self, timeout):
            events.append(("wait", timeout))
            assert self.returncode is not None
            return self.returncode

    proc = runner._proc = Process()

    def fake_kill(pid, sig):
        assert pid == proc.pid
        events.append(("signal", sig))
        proc.returncode = -15

    monkeypatch.setattr(os, "kill", fake_kill)
    runner.cancel()
    signals = [event for event in events if event[0] == "signal"]
    assert bool(signals) is (timing == "signal-delivered"), events
    expected = "cancelled" if timing == "signal-delivered" else reason
    assert runner.result is not None
    assert runner.result.reason == expected, {
        "expected": expected, "actual": runner.result.reason, "events": events,
    }
    assert runner.result.exit_code == (-15 if timing == "signal-delivered" else code)
    assert runner.result.ok is (expected == "completed")
    assert runner._proc is None and runner._cancelling is None
