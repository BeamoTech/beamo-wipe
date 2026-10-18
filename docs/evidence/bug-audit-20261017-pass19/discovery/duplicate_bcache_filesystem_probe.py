"""Unrun shared-holder ancestry probe with only synthetic guarded metadata."""

import pytest

from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


MODES = (
    "identical-filesystem",
    "identical-uuid-only",
    "populated-empty",
    "populated-empty-left-bad-model",
    "populated-empty-right-bad-model",
    "identical-explicit-parents",
)


def _holder(name="bcache0", **changes):
    row = _disk("sdc")
    row.update(
        name=name, path="/dev/" + name, tran=None,
        serial="FAKE-" + name, wwn="50014ee2000000044", size=2_000_000_000,
    )
    row.update(changes)
    return row


def _shared_payload(mode, reverse):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    left = _disk("sda")
    right = _disk("sdc")
    evidence = {"uuid": "fake-shared-volume"}
    if mode != "identical-uuid-only":
        evidence.update(fstype="ext4", label="root")
    left_copy = _holder(**evidence)
    right_copy = _holder(**(evidence if mode.startswith("identical") else {}))
    if mode == "populated-empty-left-bad-model":
        left_copy["model"] = "M" * 129
    if mode == "populated-empty-right-bad-model":
        right_copy["model"] = "M" * 129
    if mode == "identical-explicit-parents":
        left_copy["pkname"] = "sda"
        right_copy["pkname"] = "sdc"
    left["children"] = [left_copy]
    right["children"] = [right_copy]
    return {"blockdevices": [boot, *([right, left] if reverse else [left, right])]}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("reverse", (False, True))
def test_one_bcache_filesystem_cannot_claim_two_physical_owners(
    fake_machine, route, mode, reverse  # noqa: F811 - imported pytest fixture
):
    result = fake_machine(_shared_payload(mode, reverse), route)
    assert result.error
    assert not result.boot_identified
    assert result.disks == ()
    assert result.selectable == ()


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("shape", ("one-parent-repeat", "distinct-devices", "blank-shared-holder"))
def test_unmounted_holder_controls_keep_proven_layout_behavior(
    fake_machine, route, shape  # noqa: F811 - imported pytest fixture
):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    left = _disk("sda")
    right = _disk("sdc")
    evidence = {"fstype": "ext4", "uuid": "fake-shared-volume", "label": "root"}
    if shape == "one-parent-repeat":
        left["children"] = [_holder(**evidence), _holder(**evidence)]
    elif shape == "distinct-devices":
        left["children"] = [_holder(**evidence)]
        right["children"] = [_holder("bcache1", **evidence)]
    else:
        left["children"] = [_holder()]
        right["children"] = [_holder()]
    result = fake_machine({"blockdevices": [boot, left, right]}, route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}
    identities = {disk.path: disk.layout_id for disk in result.selectable}
    assert bool(identities["/dev/sda"]) is (shape != "blank-shared-holder")
    assert bool(identities["/dev/sdc"]) is (shape == "distinct-devices")
