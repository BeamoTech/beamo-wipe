"""Negative-only skip context remains contradictory without proving no erasure."""

import os

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, WipeRequest


STAMP = "[2026/10/17 12:00:00] info: "
GUARDS = (
    "/dev/sda is reported as IN USE\n",
    "Unable to open device '/dev/sda'.\n",
    "/dev/sda: No sane device geometry\n",
)


@pytest.fixture(autouse=True)
def only_fake_log_actions(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("negative-origin proof attempted a native action")

    monkeypatch.setattr(module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(module.subprocess, "run", forbidden)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(module, "_recheck_identity_under_lock", forbidden)
    monkeypatch.setattr(module, "_reserve_target_under_lock", forbidden)
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    realpath = os.path.realpath

    def fake_device_realpath(path, *args, **kwargs):
        if os.fsdecode(path).startswith("/dev/"):
            return os.fspath(path)
        return realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_device_realpath)
    original_open = os.open

    def ordinary_open(path, *args, **kwargs):
        if os.fsdecode(path).startswith(("/dev/", "/sys/", "/proc/")):
            forbidden()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", ordinary_open)


class ExitedFakeProcess:
    returncode = 0

    def poll(self):
        return self.returncode


def activity_record(kind, method):
    if kind == "progress":
        total = METHODS[method].overwrite_passes
        return (
            STAMP + "/dev/sda: 5.00%, round 1 of 1, pass 1 of "
            + str(total) + ", eta 00:00:01, [writing]\n"
        )
    if kind == "error_summary":
        return (
            "******************************** Error Summary *********************************\n"
            + STAMP + "! sda | 1 | 0 | 0\n" + "*" * 80 + "\n"
        )
    assert kind == "status_table"
    return (
        STAMP + "Program options are set as follows\n"
        + module.NWIPE_DRIVE_STATUS_HEADER + "\n"
        + " sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
        + "*" * 80 + "\n"
    )


@pytest.mark.parametrize("guard", GUARDS)
@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("activity", ("progress", "error_summary", "status_table"))
@pytest.mark.parametrize("guard_first", (False, True))
@pytest.mark.parametrize("large", (False, True))
def test_unattributed_skip_is_negative_context_for_actual_erase_activity(
    tmp_path, guard, method, activity, guard_first, large
):
    other = activity_record(activity, method)
    first, second = (guard, other) if guard_first else (other, guard)
    if not large:
        result = module.completion_for_method(0, first + second, "/dev/sda", method)
        assert not result[0] and result[2] == "indeterminate", result
        return
    text = first + ("p" * 65535 + "\n") * 18 + second
    logfile = tmp_path / "fake-negative-origin.log"
    logfile.write_text(text, encoding="ascii")
    assert logfile.stat().st_size > module.NWIPE_COMPLETION_LOG_BYTES
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner()
    runner._proc = ExitedFakeProcess()
    runner._active_request = request
    runner._last_logfile = str(logfile)
    runner._sleep_inhibit.stop = lambda: None
    result = runner.poll(request)
    assert result is not None
    assert not result.ok and result.reason == "indeterminate", result
    assert logfile.read_text(encoding="ascii") == text
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
