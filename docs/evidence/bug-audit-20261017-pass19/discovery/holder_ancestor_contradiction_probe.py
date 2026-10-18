"""Unrun source candidate for a blank holder's contradictory ancestor edge."""

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


def _payload(kind, placement, depth, *, contradictory, filesystem=True):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    peer = _disk("sdc")
    holder = _row(
        NAMES[kind], "disk" if kind == "bcache-disk" else kind,
        pkname="sdc" if contradictory else "sda",
    )
    leaf_parent = holder
    middle = None
    if depth == 2:
        middle = _row("dm-88", "crypt", pkname=holder["name"])
        leaf_parent = middle
    leaf = _row(leaf_parent["name"] + "p1", "part", pkname=leaf_parent["name"])
    if filesystem:
        leaf.update(fstype="ext4", uuid="fake-descendant-volume", label="root")
    target["children"] = [holder]
    rows = [boot, target, peer]
    if placement == "nested":
        if middle is not None:
            holder["children"] = [middle]
        leaf_parent["children"] = [leaf]
    else:
        if middle is not None:
            rows.append(middle)
        rows.append(leaf)
    return {"blockdevices": rows}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("kind", HOLDERS)
@pytest.mark.parametrize("placement", ("nested", "flat"))
@pytest.mark.parametrize("depth", (1, 2))
def test_descendant_filesystem_cannot_cross_a_contradictory_holder_edge(
    fake_machine, route, kind, placement, depth  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(kind, placement, depth, contradictory=True), route)
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("kind", HOLDERS)
@pytest.mark.parametrize("placement", ("nested", "flat"))
@pytest.mark.parametrize("depth", (1, 2))
@pytest.mark.parametrize("filesystem", (False, True))
def test_consistent_holder_edge_keeps_descendant_layout_on_one_raw_disk(
    fake_machine, route, kind, placement, depth, filesystem  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(
        kind, placement, depth, contradictory=False, filesystem=filesystem,
    ), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
    target = next(disk for disk in result.selectable if disk.path == "/dev/sda")
    peer = next(disk for disk in result.selectable if disk.path == "/dev/sdc")
    assert target.layout_id
    assert not peer.layout_id
