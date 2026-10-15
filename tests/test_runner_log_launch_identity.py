"""Completion cannot come from a logfile substituted after process launch."""

from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


COMPLETE = (
    "********************************* Drive Status *********************************\n"
    "      sda | Erased |  120MB/s | 01:25:04 | FAKE/DISK\n"
)


@pytest.mark.parametrize("replace_log", [False, True])
def test_completion_remains_bound_to_launch_log(tmp_path, monkeypatch, replace_log):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    process = Mock()
    process.poll.return_value = 0
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: process)
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    runner.start(request)
    if replace_log:
        logfile.rename(tmp_path / "original-engine.log")
    logfile.write_text(COMPLETE)
    result = runner.poll(request)
    assert result is not None
    assert result.ok is (not replace_log)
    assert result.reason == ("indeterminate" if replace_log else "completed")


def test_replaced_live_log_cannot_arm_signals_or_supply_progress(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: process)
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    runner.start(request)
    try:
        logfile.rename(tmp_path / "original-engine.log")
        logfile.write_text(
            "Program options are set as follows\n"
            "/dev/sda: 050.00%, round 1 of 1, pass 1 of 1, "
            "eta 00:00:10, [writing]\n"
        )
        assert runner.poll(request) is None
        assert runner.progress is None
        assert runner.progress_observation is None
        process.send_signal.assert_not_called()
    finally:
        runner._release_wipe_lock()


def test_log_replaced_during_preflight_blocks_spawn(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    spawn = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", spawn)
    logfile = tmp_path / "engine.log"
    request = WipeRequest(
        "/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile),
        device_rdev=1, device_size_bytes=1_000_000, boot_rdev=2,
    )
    runner = module.NwipeRunner()
    # Exercise the real-engine preflight branch with every device/binary and
    # inhibitor boundary replaced. Rediscovery is where the filename changes.
    monkeypatch.setattr(module, "require_real_live_for_nwipe", lambda: None)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", lambda **_kw: False)
    monkeypatch.setattr(module, "_verify_pinned_nwipe", lambda _path: None)
    monkeypatch.setattr(module, "assert_existing_is_block_device", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "assert_not_boot", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "assert_size_unchanged", lambda *_a: None)
    monkeypatch.setattr(module, "assert_local_device_transport", lambda _path: None)
    monkeypatch.setattr(module, "block_rdev", lambda path: 1 if path == "/dev/sda" else 2)
    monkeypatch.setattr(runner._sleep_inhibit, "start", lambda: None)

    def replace_during_rediscovery(_request):
        logfile.rename(tmp_path / "original-engine.log")
        logfile.write_text(COMPLETE)

    monkeypatch.setattr(module, "_recheck_identity_under_lock", replace_during_rediscovery)
    try:
        with pytest.raises(module.SafetyError, match="Log file changed"):
            runner.start(request)
        spawn.assert_not_called()
        assert runner.start_not_spawned()
    finally:
        runner._release_wipe_lock()


def test_log_replaced_as_truncation_returns_is_not_adopted(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    spawn = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", spawn)
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    truncate = module.truncate_log_file

    def replace_after_truncation(path, target, **kwargs):
        identity = truncate(path, target, **kwargs)
        logfile.rename(tmp_path / "original-engine.log")
        logfile.write_text(COMPLETE)
        return identity

    monkeypatch.setattr(module, "truncate_log_file", replace_after_truncation)
    try:
        with pytest.raises(module.SafetyError, match="Log file changed"):
            runner.start(request)
        spawn.assert_not_called()
        assert runner.start_not_spawned()
    finally:
        runner._release_wipe_lock()


def test_unlinked_log_inode_cannot_be_reused_as_completion(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    process = Mock()
    process.poll.return_value = 0
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: process)
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    runner.start(request)
    logfile.unlink()
    logfile.write_text(COMPLETE)
    result = runner.poll(request)
    assert result is not None
    assert result.ok is False
    assert result.reason == "indeterminate"
