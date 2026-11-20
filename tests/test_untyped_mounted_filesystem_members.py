"""A mounted row that reports a filesystem UUID but no FSTYPE.

lsblk can show a filesystem UUID before it fills in FSTYPE. When that row is
the mounted one, a typed member with the same UUID cannot be proven to be a
different filesystem, so it must not be offered for erase. A typed Btrfs
member with that UUID keeps the whole-inventory Btrfs refusal.
"""

import importlib

import pytest


discovery = importlib.import_module("beamo_wipe.discover")


def disk(name, **changes):
    row = {
        "name": name, "path": f"/dev/{name}", "type": "disk",
        "size": 32_000_000_000, "model": "Fake disk", "serial": name,
        "tran": "usb", "rota": False, "ro": False,
        "mountpoints": [None], "mountpoint": None,
    }
    row.update(changes)
    return row


def part(name, pk, **changes):
    return disk(name, type="part", pkname=pk, tran="sata", **changes)


def probe(monkeypatch, rows, boot="/dev/sdc"):
    monkeypatch.setattr(discovery, "run_lsblk", lambda: {"blockdevices": rows})
    return discovery.discover(mount_sources=[boot], cmdline="", env={})


def inventory(mounted_fstype, member_fstype, member_uuid="FS"):
    return [
        disk("sda", tran="sata", children=[
            part("sda1", "sda", fstype=mounted_fstype, uuid="FS", mountpoints=["/data"]),
        ]),
        disk("sdb", tran="sata", children=[
            part("sdb1", "sdb", fstype=member_fstype, uuid=member_uuid),
        ]),
        disk("sdd", tran="sata"),
        disk("sdc"),
    ]


@pytest.mark.parametrize("member_fstype", ["xfs", "ext4", "XFS"])
def test_typed_member_of_an_untyped_mounted_filesystem_is_not_offered(monkeypatch, member_fstype):
    result = probe(monkeypatch, inventory("", member_fstype))
    assert result.boot_identified
    assert [d.path for d in result.selectable] == ["/dev/sdd"]
    member = next(d for d in result.disks if d.path == "/dev/sdb")
    assert "/data" in member.mountpoints


@pytest.mark.parametrize("member_fstype", ["btrfs", "BTRFS"])
def test_btrfs_member_of_an_untyped_mounted_filesystem_refuses_the_inventory(monkeypatch, member_fstype):
    result = probe(monkeypatch, inventory("", member_fstype))
    assert not result.boot_identified
    assert result.selectable == ()


def test_untyped_mount_with_another_uuid_still_offers_the_other_disk(monkeypatch):
    # Only the same filesystem UUID ties a member to the mount.
    result = probe(monkeypatch, inventory("", "xfs", member_uuid="OTHER"))
    assert result.boot_identified
    assert [d.path for d in result.selectable] == ["/dev/sdb", "/dev/sdd"]


@pytest.mark.parametrize("member_fstype", ["", "xfs"])
def test_typed_mount_rules_are_unchanged(monkeypatch, member_fstype):
    # A typed mount still covers a same-type or untyped member ...
    result = probe(monkeypatch, inventory("xfs", member_fstype))
    assert result.boot_identified
    assert [d.path for d in result.selectable] == ["/dev/sdd"]


def test_typed_mount_does_not_cover_a_member_of_a_different_type(monkeypatch):
    # ... and a different reported type is still a different filesystem.
    result = probe(monkeypatch, inventory("xfs", "ext4"))
    assert result.boot_identified
    assert [d.path for d in result.selectable] == ["/dev/sdb", "/dev/sdd"]
