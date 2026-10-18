"""Unrun adjacent candidate: real descendant FS needs a physical holder owner.

Root owns runtime. This intentionally preserves unrelated orphan partitions and
blank unmounted holder subtrees as controls; it does not broaden their contract.
"""

import pytest

from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


HOLDERS = ("bcache-disk", "lvm", "linear")
NAMES = {"bcache-disk": "bcache0", "lvm": "dm-77", "linear": "md0"}


def _row(name, kind, **changes):
    row = _disk("sdc")
    row.update(
        name=name, path="/dev/" + name, type=kind, tran=None,
        serial="FAKE-" + name, wwn="", size=2_000_000_000,
    )
    row.update(changes)
    return row


def _payload(kind, depth, ancestry, *, filesystem=True):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    peer = _disk("sdc")
    holder = _row(NAMES[kind], "disk" if kind == "bcache-disk" else kind)
    leaf_parent = holder
    if depth == 2:
        middle = _row("dm-88", "crypt", pkname=holder["name"])
        holder["children"] = [middle]
        leaf_parent = middle
    leaf = _row(
        leaf_parent["name"] + "p1", "part", pkname=leaf_parent["name"],
    )
    if filesystem:
        leaf.update(fstype="ext4", uuid="fake-descendant-volume", label="root")
    leaf_parent["children"] = [leaf]
    rows = [boot, target, peer]
    if ancestry == "tree-bound":
        target["children"] = [holder]
    else:
        if ancestry == "unknown-parent":
            holder["pkname"] = "not-present"
        elif ancestry == "cycle":
            holder["pkname"] = "dm-99"
            rows.append(_row("dm-99", "crypt", pkname=holder["name"]))
        elif ancestry == "flat-bound":
            holder["pkname"] = "sda"
        elif ancestry != "missing-parent":
            raise AssertionError("unknown fixture ancestry")
        rows.append(holder)
    return {"blockdevices": rows}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("kind", HOLDERS)
@pytest.mark.parametrize("depth", (1, 2))
@pytest.mark.parametrize("ancestry", ("missing-parent", "unknown-parent", "cycle"))
def test_descendant_filesystem_requires_proven_physical_holder_ancestry(
    fake_machine, route, kind, depth, ancestry  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(kind, depth, ancestry), route)
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("kind", HOLDERS)
@pytest.mark.parametrize("depth", (1, 2))
@pytest.mark.parametrize("ancestry", ("flat-bound", "tree-bound"))
def test_bound_descendant_filesystem_still_binds_raw_target_layout(
    fake_machine, route, kind, depth, ancestry  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(kind, depth, ancestry), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
    target = next(disk for disk in result.selectable if disk.path == "/dev/sda")
    peer = next(disk for disk in result.selectable if disk.path == "/dev/sdc")
    assert target.layout_id
    assert not peer.layout_id


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("kind", HOLDERS)
@pytest.mark.parametrize("depth", (1, 2))
def test_blank_unmounted_holder_subtree_is_not_an_opened_filesystem_claim(
    fake_machine, route, kind, depth  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(kind, depth, "missing-parent", filesystem=False), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
def test_unrelated_orphan_partition_remains_inventory_only(
    fake_machine, route  # noqa: F811 - imported pytest fixture
):
    payload = {"blockdevices": [
        _disk("sdz", tran="usb", mountpoints=["/run/live/medium"]),
        _disk("sda"),
        _row("sdy1", "part", fstype="ext4", uuid="fake-unrelated-volume"),
    ]}
    result = fake_machine(payload, route)
    assert result.boot_identified
    assert not result.error
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]
    assert not result.selectable[0].layout_id
