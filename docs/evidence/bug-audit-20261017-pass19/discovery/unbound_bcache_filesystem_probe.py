"""Unrun source-derived proof candidate for type=disk bcache ancestry.

Root owns execution. Every inventory and acquisition guard is fake. No product
or canonical test was changed to prepare this source-only audit candidate.
"""

import pytest

from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


def _holder(**changes):
    row = _disk("sdc")
    row.update(
        name="bcache0", path="/dev/bcache0", tran=None,
        serial="FAKE-BCACHE", wwn="50014ee2000000044",
    )
    row.update(changes)
    return row


def _payload(ancestry, evidence):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    peer = _disk("sdc")
    holder = _holder(**evidence)
    rows = [boot, target, peer]
    if ancestry == "missing-parent":
        rows.append(holder)
    elif ancestry == "unknown-parent":
        holder["pkname"] = "not-present"
        rows.append(holder)
    elif ancestry == "cycle":
        holder["pkname"] = "dm-77"
        rows.extend((holder, {
            "name": "dm-77", "path": "/dev/dm-77", "type": "crypt",
            "pkname": "bcache0", "mountpoints": [],
        }))
    elif ancestry == "contradictory-tree":
        holder["pkname"] = "sdc"
        target["children"] = [holder]
    elif ancestry == "flat-bound":
        holder["pkname"] = "sda"
        rows.append(holder)
    elif ancestry == "tree-bound":
        target["children"] = [holder]
    else:
        raise AssertionError("unknown fixture ancestry")
    return {"blockdevices": rows}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("ancestry", ("missing-parent", "unknown-parent", "cycle", "contradictory-tree"))
@pytest.mark.parametrize("evidence", (
    {"fstype": "ext4", "uuid": "fake-open-volume", "label": "root"},
    {"uuid": "fake-open-volume"},
    {"partlabel": "fake-open-volume"},
), ids=("opened-filesystem", "uuid-only", "partition-label-only"))
def test_unmounted_bcache_filesystem_requires_proven_ancestry(
    fake_machine, route, ancestry, evidence  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(ancestry, evidence), route)
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("ancestry", ("flat-bound", "tree-bound"))
def test_unmounted_bound_bcache_keeps_filesystem_in_raw_disk_identity(
    fake_machine, route, ancestry  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload(ancestry, {
        "fstype": "ext4", "uuid": "fake-open-volume", "label": "root",
    }), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
    target = next(disk for disk in result.selectable if disk.path == "/dev/sda")
    assert target.layout_id
    assert not next(disk for disk in result.selectable if disk.path == "/dev/sdc").layout_id
    assert "/dev/bcache0" not in {disk.path for disk in result.selectable}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
def test_blank_unmounted_orphan_bcache_has_no_unbound_filesystem_claim(
    fake_machine, route  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_payload("missing-parent", {}), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
