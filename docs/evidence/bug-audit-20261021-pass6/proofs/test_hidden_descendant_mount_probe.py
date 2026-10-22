"""Read-only proof: hidden child mounts are not effective live/log evidence."""
from pathlib import Path

import pytest

from beamo_wipe import discover as discovery
from beamo_wipe.safety import is_live_environment, log_location_is_tmpfs

ROOT = "1 0 0:1 / / rw - overlay overlay rw\n"


def _table(kind, cover):
    if kind == "live":
        child = "3 1 8:1 / /run/live/medium rw - ext4 /dev/sdz1 rw\n"
        covering = "4 1 0:4 / /run/live rw - tmpfs tmpfs rw\n"
    else:
        child = "3 1 0:3 / /tmp/beamo-wipe rw - tmpfs tmpfs rw\n"
        covering = "4 1 8:2 / /tmp rw - ext4 /dev/sda1 rw\n"
    # Child and covering ancestor share root mount 1 as their parent. The
    # child's old mount stays listed, but path lookup enters covering mount 4.
    return ROOT + child + (covering if cover else "")


@pytest.mark.parametrize("kind", ["live", "log"])
@pytest.mark.parametrize("cover", [False, True], ids=["normal", "hidden-child"])
def test_mount_evidence_is_reachable(tmp_path, monkeypatch, kind, cover):
    mountinfo = _table(kind, cover)
    if kind == "live":
        assert discovery.live_medium_is_mounted(text=mountinfo) is (not cover)
        assert is_live_environment(cmdline="boot=live", mountinfo_text=mountinfo) is (not cover)
    else:
        table = tmp_path / "mountinfo"
        table.write_text(mountinfo, encoding="utf-8")
        monkeypatch.setattr(discovery, "MOUNTINFO_PATH", str(table))
        assert log_location_is_tmpfs(Path("/tmp/beamo-wipe/nwipe-sda.log")) is (not cover)
