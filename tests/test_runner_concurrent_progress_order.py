"""An older concurrent log read cannot replace a newer accepted observation."""

import threading
from unittest.mock import Mock

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner


@pytest.mark.parametrize("newer_available", [True, False])
def test_late_progress_read_does_not_rewind_phase_or_freshness(monkeypatch, newer_available):
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", "fake-log")

    class Running:
        def poll(self):
            return None

        def send_signal(self, _signal):
            pass

    runner = NwipeRunner()
    runner._proc = Running()
    runner._active_request = request
    runner._sigusr1_armed = True
    waiting, resume = threading.Event(), threading.Event()
    errors = []

    def read_log(*_args):
        if threading.current_thread() is older:
            waiting.set()
            assert resume.wait(5)
            percent, phase = "020.00", "writing"
        else:
            if not newer_available:
                return ""  # empty, missing and failed reads all expose no observation
            percent, phase = "080.00", "verifying"
        return (
            f"/dev/sda: {percent}%, round 1 of 1, pass 1 of 1, "
            f"eta 00:00:10, [{phase}]\n"
        )

    def poll_older():
        try:
            runner.poll(request)
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(runner, "_read_log_tail", read_log)
    older = threading.Thread(target=poll_older)
    older.start()
    try:
        assert waiting.wait(5)
        assert runner.poll(request) is None
        if newer_available:
            assert runner.progress_observation.phase == "Verifying"
        else:
            assert runner.progress_observation is None
        resume.set()
        older.join(5)
        assert not older.is_alive() and not errors
        if newer_available:
            assert runner.progress == 80
            assert runner.progress_observation.phase == "Verifying"
            assert runner.progress_observation.percent == 80
        else:
            assert runner.progress is None
            assert runner.progress_observation is None
    finally:
        resume.set()
        older.join(5)


def test_direct_refresh_remains_ordered_across_new_start(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    process = Mock(returncode=None)
    process.poll.return_value = None
    monkeypatch.setattr("beamo_wipe.nwipe_runner.subprocess.Popen", lambda *_a, **_kw: process)
    runner = NwipeRunner(binary=str(tmp_path / "fake-engine"))
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "new.log"))
    waiting, resume = threading.Event(), threading.Event()
    errors = []

    def read_log(*_args):
        if threading.current_thread() is older:
            waiting.set()
            assert resume.wait(5)
            percent, phase = "020.00", "writing"
        else:
            percent, phase = "080.00", "verifying"
        return (
            f"/dev/sda: {percent}%, round 1 of 1, pass 1 of 1, "
            f"eta 00:00:10, [{phase}]\n"
        )

    def direct_refresh():
        try:
            runner._refresh_progress("old-log", "/dev/sda")
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(runner, "_read_log_tail", read_log)
    older = threading.Thread(target=direct_refresh)
    older.start()
    try:
        assert waiting.wait(5)
        runner.start(request)
        runner._refresh_progress(request.logfile, request.device)
        resume.set()
        older.join(5)
        assert not older.is_alive() and not errors
        assert runner.progress == 80
        assert runner.progress_observation.phase == "Verifying"
        assert runner.progress_observation.percent == 80
    finally:
        resume.set()
        older.join(5)
        runner._release_wipe_lock()  # only fake process/ordinary-file fixtures exist


def test_normal_direct_refreshes_can_advance_phase(monkeypatch):
    runner = NwipeRunner()
    for percent, phase in [(20, "writing"), (40, "writing"), (80, "verifying")]:
        text = (
            f"/dev/sda: {percent}.00%, round 1 of 1, pass 1 of 1, "
            f"eta 00:00:10, [{phase}]\n"
        )
        monkeypatch.setattr(runner, "_read_log_tail", lambda *_args: text)
        runner._refresh_progress("fake-log", "/dev/sda")
        assert runner.progress == percent
        assert runner.progress_observation.phase.casefold() == phase
