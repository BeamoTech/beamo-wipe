"""Public safety refusal for a hidden tmpfs child; ordinary temporary files."""
from pathlib import Path
import pytest
from beamo_wipe import discover as discovery
from beamo_wipe.safety import SafetyError, assert_log_not_on_target, is_live_environment

@pytest.mark.parametrize("cover", [False, True], ids=["normal", "ancestor-cover"])
def test_public_log_refusal(tmp_path, monkeypatch, cover):
    monkeypatch.delenv("BEAMO_WIPE_DRY_RUN", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_DEMO", raising=False)
    root = tmp_path / "logs"
    root.mkdir()
    table = tmp_path / "mountinfo"
    table.write_text(
        "1 0 0:1 / / rw - overlay overlay rw\n"
        f"3 1 0:3 / {root} rw - tmpfs tmpfs rw\n"
        + (f"4 1 8:2 / {tmp_path} rw - ext4 /dev/sda1 rw\n" if cover else ""),
        encoding="utf-8",
    )
    monkeypatch.setattr(discovery, "MOUNTINFO_PATH", str(table))
    if cover:
        with pytest.raises(SafetyError, match="target disk"):
            assert_log_not_on_target(str(root / "engine.log"), "/dev/sda", log_dir=root)
    else:
        assert_log_not_on_target(str(root / "engine.log"), "/dev/sda", log_dir=root)

@pytest.mark.parametrize("cover", [False, True], ids=["normal", "ancestor-cover"])
def test_public_live_refusal(cover):
    table = (
        "1 0 0:1 / / rw - overlay overlay rw\n"
        "3 1 8:1 / /run/live/medium rw - ext4 /dev/sdz1 rw\n"
        + ("4 1 0:4 / /run/live rw - tmpfs tmpfs rw\n" if cover else "")
    )
    assert is_live_environment(cmdline="boot=live", mountinfo_text=table) is (not cover)
