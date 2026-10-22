"""Mount evidence must belong to the tree reachable through its pathname.

Only supplied mountinfo, fake inventory callbacks and ordinary temporary files
are used.  No mount or block-device operations run.
"""
from pathlib import Path

import pytest

from beamo_wipe import discover as discovery
from beamo_wipe import safety


TOPOLOGIES = (
    ("nested", True),
    ("hidden_sibling", False),
    ("hidden_stacked_ancestor", False),
    ("child_above_stack", True),
    ("unrelated_sibling", True),
    ("namespace_boundary", True),
    ("namespace_root_self_parent", True),
    ("duplicate_mount_id", False),
    ("parent_cycle", False),
    ("malformed_mount_id", False),
    ("contradictory_parent_path", False),
    ("same_path_stack", False),
    ("partial_table", False),
)


def _table(parent: str, child: str, topology: str, *, log: bool, reverse: bool) -> str:
    fs, source = ("tmpfs", "tmpfs") if log else ("iso9660", "/dev/sdz1")
    root = "101 0 0:1 / / rw - overlay overlay rw"
    ancestor = f"7 101 8:2 / {parent} rw - ext4 /dev/sda1 rw"
    volume = f"42 7 0:3 / {child} rw - {fs} {source} rw"
    rows = [root, ancestor, volume]
    if topology == "hidden_sibling":
        rows = [root, volume.replace("42 7 ", "42 101 "), ancestor]
    elif topology == "hidden_stacked_ancestor":
        rows.append(f"9 7 8:4 / {parent} rw - ext4 /dev/sdb1 rw")
    elif topology == "child_above_stack":
        rows[2] = volume.replace("42 7 ", "42 9 ")
        rows.append(f"9 7 8:4 / {parent} rw - ext4 /dev/sdb1 rw")
    elif topology == "unrelated_sibling":
        rows.append("9 101 8:4 / /unrelated rw - ext4 /dev/sdb1 rw")
    elif topology == "namespace_boundary":
        rows = [volume.replace("42 7 ", "42 999 ")]
    elif topology == "namespace_root_self_parent":
        rows[0] = root.replace("101 0 ", "101 101 ")
    elif topology == "duplicate_mount_id":
        rows.append("42 101 8:4 / /unrelated rw - ext4 /dev/sdb1 rw")
    elif topology == "parent_cycle":
        rows[1] = ancestor.replace("7 101 ", "7 42 ")
    elif topology == "malformed_mount_id":
        rows[2] = volume.replace("42 7 ", "invalid 7 ")
    elif topology == "contradictory_parent_path":
        rows[1] = ancestor.replace(parent, "/unrelated", 1)
    elif topology == "same_path_stack":
        rows.append(f"9 42 8:4 / {child} rw - ext4 /dev/sdb1 rw")
    elif topology == "partial_table":
        rows.append("truncated mountinfo row")
    if reverse:
        rows.reverse()
    return "\n".join(rows) + "\n"


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reordered"])
@pytest.mark.parametrize("topology,visible", TOPOLOGIES)
def test_live_mount_evidence_requires_visible_parent_tree(topology, visible, reverse):
    table = _table("/run/live", "/run/live/medium", topology, log=False, reverse=reverse)
    assert discovery.live_medium_is_mounted(text=table) is visible
    assert safety.is_live_environment(cmdline="boot=live", mountinfo_text=table) is visible
    if visible:
        assert discovery.read_mountinfo_sources(text=table) == ["/dev/sdz1"]
    else:
        with pytest.raises(ValueError):
            discovery.read_mountinfo_sources(text=table)


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reordered"])
@pytest.mark.parametrize("topology,visible", TOPOLOGIES)
def test_log_guard_requires_visible_tmpfs_parent_tree(tmp_path: Path, monkeypatch, topology, visible, reverse):
    monkeypatch.delenv("BEAMO_WIPE_DRY_RUN", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_DEMO", raising=False)
    directory = tmp_path / "logs"
    directory.mkdir()
    table = tmp_path / "mountinfo"
    table.write_text(_table(str(tmp_path), str(directory), topology, log=True, reverse=reverse))
    monkeypatch.setattr(discovery, "MOUNTINFO_PATH", str(table))
    logfile = directory / "engine.log"
    assert safety.log_location_is_tmpfs(logfile) is visible
    if visible:
        safety.assert_log_not_on_target(str(logfile), "/dev/sda", log_dir=directory)
    else:
        with pytest.raises(safety.SafetyError, match="target disk"):
            safety.assert_log_not_on_target(str(logfile), "/dev/sda", log_dir=directory)


def _disk(name: str, serial: str, tran: str) -> dict:
    return dict(name=name, path="/dev/" + name, type="disk", serial=serial,
                tran=tran, size=16_000_000_000 if tran == "usb" else 128_000_000_000,
                ro=False, mountpoints=[], model="Fake disk", rota=False)


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reordered"])
@pytest.mark.parametrize("topology,visible", [TOPOLOGIES[index] for index in (0, 1, 5)])
def test_production_discovery_refuses_hidden_live_evidence(tmp_path: Path, monkeypatch, topology, visible, reverse):
    boot = _disk("sdz", "FAKE-BOOT", "usb")
    boot["children"] = [dict(name="sdz1", path="/dev/sdz1", type="part", pkname="sdz",
                             size=16_000_000_000, ro=False, mountpoints=[], fstype="iso9660")]
    payload = {"blockdevices": [boot, _disk("sda", "FAKE-TARGET", "sata")]}
    table = tmp_path / "mountinfo"
    table.write_text(_table("/run/live", "/run/live/medium", topology, log=False, reverse=reverse))
    monkeypatch.setattr(discovery, "MOUNTINFO_PATH", str(table))
    monkeypatch.setattr(discovery, "run_lsblk", lambda: payload)
    monkeypatch.setattr(discovery, "_run_findmnt", lambda path: None)
    monkeypatch.setattr(discovery, "read_cmdline", lambda: "boot=live")
    monkeypatch.setattr(safety, "assert_local_device_transport", lambda path: None)
    result = discovery.discover(env={})
    assert [disk.path for disk in result.selectable] == (["/dev/sda"] if visible else [])
    assert result.boot_identified is visible


def test_mountinfo_pair_api_keeps_decoding_and_return_shape():
    table = "7 999 8:1 / /run/live\\040medium rw - ext4 /dev/sdz1 rw\n"
    assert discovery.parse_mountinfo(table) == [("/dev/sdz1", "/run/live medium")]


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reordered"])
@pytest.mark.parametrize("log", [False, True], ids=["live", "log"])
def test_visible_new_child_is_not_confused_with_old_hidden_submount(tmp_path: Path, monkeypatch, log, reverse):
    parent, old_sub, child = (
        ("/tmp", "/tmp/beamo-wipe", "/tmp/beamo-wipe/logs")
        if log else ("/run", "/run/live", "/run/live/medium")
    )
    filesystem, source = ("tmpfs", "tmpfs") if log else ("iso9660", "/dev/sdz1")
    rows = [
        "101 0 0:1 / / rw - overlay overlay rw",
        f"7 101 0:7 / {parent} rw - tmpfs tmpfs rw",
        f"13 7 8:13 / {old_sub} rw - ext4 /dev/sdb1 rw",
        f"9 7 0:9 / {parent} rw - tmpfs tmpfs rw",
        f"42 9 0:42 / {child} rw - {filesystem} {source} rw",
    ]
    if reverse:
        rows.reverse()
    text = "\n".join(rows) + "\n"
    if log:
        table = tmp_path / "mountinfo"
        table.write_text(text)
        monkeypatch.setattr(discovery, "MOUNTINFO_PATH", str(table))
        assert safety.log_location_is_tmpfs(Path(child) / "engine.log")
    else:
        assert discovery.live_medium_is_mounted(text=text)
        assert discovery.read_mountinfo_sources(text=text) == ["/dev/sdz1"]
