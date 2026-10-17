"""UNRUN source-only candidate: mounted mapping type must establish member rules.

Root owns all execution. This reuses the already guarded fake-machine fixture;
both routes are synthetic and native inventory/process/device acquisition is
forbidden. No assertion below is runtime evidence until root executes it.
"""

import pytest

from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


def _payload(kind, placement, *, mounted=True, filesystem=True):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    backing = _disk("sda")
    other_possible_member = _disk("sdc")
    holder = {
        "name": "dm-77", "path": "/dev/dm-77", "type": kind,
        "size": 128_000_000_000, "pkname": "sda", "ro": False,
        "mountpoints": ["/data"] if mounted else [],
    }
    if filesystem:
        holder.update(fstype="ext4", uuid="fake-opened-fs")
    rows = [boot, backing, other_possible_member]
    if placement == "flat":
        rows.append(holder)
    else:
        assert placement == "nested"
        backing["children"] = [holder]
    return {"blockdevices": rows}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
@pytest.mark.parametrize("kind", ("dm", " lvm ", "linear ", " mpath"))
def test_unknown_or_padded_mounted_mapping_cannot_prove_other_disk_is_outside_it(
    fake_machine, route, placement, kind  # noqa: F811 - imported pytest fixture
):
    # One PKNAME identifies a backing leg, not a complete generic mapping.
    # A padded known multi-member token must not acquire weaker rules than
    # its unpadded form. The second disk intentionally has no member signature:
    # stale/empty metadata cannot establish that it is outside this mapping.
    result = fake_machine(_payload(kind, placement), route)
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
def test_known_crypt_mount_keeps_unrelated_disk_selectable(
    fake_machine, route, placement  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload("crypt", placement), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sdc"}
    assert next(d for d in result.disks if d.path == "/dev/sda").mountpoints == ("/data",)


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
def test_known_lvm_mount_already_refuses_unproven_membership(
    fake_machine, route, placement  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload("lvm", placement), route)
    assert result.error
    assert not result.boot_identified
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
def test_blank_unmounted_generic_mapping_has_no_mount_or_filesystem_claim(
    fake_machine, route, placement  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload("dm", placement, mounted=False, filesystem=False), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
