"""A block-looking source label cannot make a pseudo filesystem live media."""
from types import SimpleNamespace

import pytest

import beamo_wipe.app
import beamo_wipe.nwipe_runner
from beamo_wipe import discover as D
from beamo_wipe import safety as S


BLOCK_FILESYSTEMS = (
    "iso9660", "udf", "squashfs", "erofs", "ext2", "ext3", "ext4",
    "vfat", "exfat", "ntfs3", "fuseblk", "xfs", "btrfs", "f2fs", "gfs2",
)
UNPROVEN_FILESYSTEMS = (
    "tmpfs", "ramfs", "overlay", "proc", "sysfs", "nfs4", "cifs",
    "fuse.sshfs", "ubifs", "unknown-filesystem",
)


def _row(filesystem, source="/dev/sdb1", point="/run/live/medium", mount_id=2):
    dev = "8:17" if filesystem in BLOCK_FILESYSTEMS else "0:48"
    return f"{mount_id} 1 {dev} / {point} rw - {filesystem} {source} rw\n"


def _table(filesystem, source="/dev/sdb1"):
    return "1 0 0:1 / / rw - overlay overlay rw\n" + _row(filesystem, source)


@pytest.fixture(autouse=True)
def fake_machine(monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native process, inventory, erase or power action forbidden")

    for name in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover._run_findmnt", "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.app._shutdown", "beamo_wipe.nwipe_runner.NwipeRunner.start",
    ):
        monkeypatch.setattr(name, forbidden)
    yield
    assert not effects


def _check_unproven(text):
    assert not D.live_medium_is_mounted(text=text)
    assert not S.is_live_environment(env={}, cmdline="boot=live", mountinfo_text=text)
    with pytest.raises(ValueError):
        D.read_mountinfo_sources(text=text)


@pytest.mark.parametrize("filesystem", BLOCK_FILESYSTEMS)
def test_known_block_filesystem_families_remain_live_media(filesystem):
    text = _table(filesystem)
    assert D.live_medium_is_mounted(text=text)
    assert S.is_live_environment(env={}, cmdline="boot=live", mountinfo_text=text)
    assert D.read_mountinfo_sources(text=text) == ["/dev/sdb1"]


@pytest.mark.parametrize("filesystem,source", [
    ("ext4", "/dev/sdb1"), ("iso9660", "/dev/sr0"),
    ("squashfs", "/dev/loop0"), ("ext4", "sdb1"),
    ("ext4", "UUID=FAKE-LIVE"), ("vfat", "LABEL=BEAMO_WIPE"),
    ("ext4", "PARTUUID=FAKE-PART"), ("ext4", "/dev/disk/by-uuid/FAKE-LIVE"),
])
def test_existing_source_spellings_keep_their_block_filesystem_proof(filesystem, source):
    # A loop-backed mount remains visible to this pure gate. Boot discovery
    # separately rejects unresolved loop ownership, as before this repair.
    text = _table(filesystem, source)
    assert D.live_medium_is_mounted(text=text)
    assert D.read_mountinfo_sources(text=text) == [source]


@pytest.mark.parametrize("filesystem", UNPROVEN_FILESYSTEMS)
@pytest.mark.parametrize("source", ["/dev/sdb1", "UUID=FAKE-LIVE"])
def test_pseudo_network_and_unknown_filesystems_cannot_impersonate_media(filesystem, source):
    _check_unproven(_table(filesystem, source))


@pytest.mark.parametrize("filesystem,expected", [
    ("tmpfs", False), ("overlay", False), ("iso9660", True), ("ext4", True),
])
def test_actual_live_requirement_uses_filesystem_kind(monkeypatch, tmp_path, filesystem, expected):
    path = tmp_path / "mountinfo"
    path.write_text(_table(filesystem))
    monkeypatch.setattr(D, "MOUNTINFO_PATH", str(path))
    monkeypatch.setattr(D, "read_cmdline", lambda: "boot=live")
    if expected:
        S.require_real_live_for_nwipe(env={})
    else:
        with pytest.raises(S.SafetyError):
            S.require_real_live_for_nwipe(env={})


@pytest.mark.parametrize("filesystem,expected", [
    ("tmpfs", False), ("ramfs", False), ("overlay", False), ("proc", False),
    ("iso9660", True), ("vfat", True), ("ext4", True),
])
def test_production_discovery_cannot_fall_back_to_findmnt_on_pseudo_media(
    monkeypatch, tmp_path, filesystem, expected,
):
    path = tmp_path / "mountinfo"
    path.write_text(_table(filesystem))
    monkeypatch.setattr(D, "MOUNTINFO_PATH", str(path))
    monkeypatch.setattr(D, "read_cmdline", lambda: "boot=live")
    payload = {"blockdevices": [
        {"name": "sdb", "path": "/dev/sdb", "type": "disk", "size": 16_000_000_000,
         "tran": "usb", "rota": False, "ro": False, "mountpoints": [],
         "serial": "FAKE-BOOT", "model": "Fake boot", "children": [
             {"name": "sdb1", "path": "/dev/sdb1", "type": "part", "size": 15_000_000_000,
              "pkname": "sdb", "ro": False, "mountpoints": [], "fstype": filesystem},
         ]},
        {"name": "sda", "path": "/dev/sda", "type": "disk", "size": 256_000_000_000,
         "tran": "sata", "rota": False, "ro": False, "mountpoints": [],
         "serial": "FAKE-DATA", "model": "Fake data"},
    ]}
    monkeypatch.setattr(D, "run_lsblk", lambda: payload)

    def findmnt(point):
        matched = point == "/run/live/medium"
        return SimpleNamespace(returncode=0 if matched else 1,
                               stdout="/dev/sdb1\n" if matched else "", stderr="")

    monkeypatch.setattr(D, "_run_findmnt", findmnt)
    result = D.discover(env={})
    if expected:
        assert result.boot_identified and result.boot.path == "/dev/sdb"
        assert [disk.path for disk in result.selectable] == ["/dev/sda"]
    else:
        assert not result.boot_identified and not result.selectable


@pytest.mark.parametrize("filesystem", ["tmpfs", "fuse.sshfs"])
@pytest.mark.parametrize("reverse", [False, True])
def test_one_real_mount_does_not_establish_a_second_pseudo_live_path(filesystem, reverse):
    rows = [_row("iso9660"), _row(filesystem, point="/lib/live/mount/medium", mount_id=3)]
    if reverse:
        rows.reverse()
    text = "1 0 0:1 / / rw - overlay overlay rw\n" + "".join(rows)
    _check_unproven(text)


@pytest.mark.parametrize("reverse", [False, True])
def test_valid_nested_media_and_unrelated_pseudo_rows_preserve_visibility(reverse):
    rows = [
        "1 0 0:1 / / rw - overlay overlay rw\n",
        "7 1 0:2 / /run rw - tmpfs tmpfs rw\n",
        "3 7 8:17 / /run/live/medium rw - iso9660 /dev/sdb1 rw\n",
        "9 1 0:4 / /media/info rw - tmpfs /dev/sdc1 rw\n",
    ]
    if reverse:
        rows.reverse()
    text = "".join(rows)
    assert D.live_medium_is_mounted(text=text)
    assert D.read_mountinfo_sources(text=text) == ["/dev/sdb1"]


@pytest.mark.parametrize("broken", [
    "bad mount row\n", "8 1 0:2 / /run/live/medium rw - tmpfs\n",
    "8 1 / /run/live/medium rw - tmpfs /dev/sdc1 rw\n",
])
def test_incomplete_mountinfo_cannot_leave_findmnt_as_accepted_media(broken):
    _check_unproven(_table("iso9660") + broken)


def test_public_mountinfo_tuple_api_keeps_pseudo_rows_for_other_callers():
    text = _table("tmpfs")
    assert D.parse_mountinfo(text) == [("overlay", "/"), ("/dev/sdb1", "/run/live/medium")]
