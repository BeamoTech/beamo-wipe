"""Pre-exec work cannot outlive ownership of the named wipe lock."""

from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize("replace_directory", [False, True])
def test_start_rejects_coordination_replacement_after_acquisition(
    tmp_path, monkeypatch, replace_directory
):
    directory = tmp_path / "logs"
    directory.mkdir(mode=0o700)
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: directory)
    request = WipeRequest(
        "/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(directory / "fake.log")
    )
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    second = module.NwipeRunner()
    spawn = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", spawn)
    truncate = module.truncate_log_file

    def replace_while_preparing_log(*args, **kwargs):
        if replace_directory:
            directory.rename(tmp_path / "old-logs")
            directory.mkdir(mode=0o700)
        else:
            (directory / "wipe.lock").rename(directory / "old-wipe.lock")
        # The replacement slot really admits another owner while the first
        # runner still retains its acquired descriptor.
        second._acquire_wipe_lock(request)
        assert second._lock_fd is not None
        assert runner._lock_fd is not None
        return truncate(*args, **kwargs)

    monkeypatch.setattr(module, "truncate_log_file", replace_while_preparing_log)
    try:
        with pytest.raises(SafetyError, match="changed"):
            runner.start(request)
        spawn.assert_not_called()
        assert runner.start_not_spawned()
    finally:
        runner._release_wipe_lock()
        second._release_wipe_lock()
