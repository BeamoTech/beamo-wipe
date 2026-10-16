"""Explicit malformed topology cannot masquerade as an empty child list."""

import pytest

from beamo_wipe.discover import discover
from test_excluded_inventory import node


def _payload(children, *, placement):
    target = node("sda")
    nodes = [node("sdb", tran="usb", mountpoints=["/run/live/medium"]), target]
    owner = target
    if placement != "disk":
        owner = node("sda1", type="part", pkname="sda")
        if placement == "nested":
            target["children"] = [owner]
        else:
            nodes.append(owner)
    if children != "absent":
        owner["children"] = children
    return {"blockdevices": nodes}


@pytest.mark.parametrize("placement", ["disk", "nested", "flat"])
@pytest.mark.parametrize("children", [{}, False, 0, ""])
def test_falsey_malformed_children_refuse_the_inventory(children, placement):
    result = discover(
        lsblk_payload=_payload(children, placement=placement),
        mount_sources=["/dev/sdb"], cmdline="",
        env={"BEAMO_WIPE_DRY_RUN": "1"},
    )
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("placement", ["disk", "nested", "flat"])
@pytest.mark.parametrize("children", ["absent", None, [], ()])
def test_supported_empty_children_keep_normal_discovery(children, placement):
    result = discover(
        lsblk_payload=_payload(children, placement=placement),
        mount_sources=["/dev/sdb"], cmdline="",
        env={"BEAMO_WIPE_DRY_RUN": "1"},
    )
    assert not result.error
    assert result.boot_identified
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]
