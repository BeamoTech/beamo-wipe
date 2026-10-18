# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression: disk name layout."""

import copy

import pytest

from beamo_wipe.models import CONTENTS_WINDOWS
from beamo_wipe.safety import disk_identity
from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported guarded fake-machine pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
NAME_FORMS = ("present", "empty", "null", "omitted")


def _payload(name_form, placement, *, uuid="fake-partition-before"):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    if name_form == "empty":
        target["name"] = ""
    elif name_form == "null":
        target["name"] = None
    elif name_form == "omitted":
        del target["name"]
    else:
        assert name_form == "present"
    part = {
        "name": "sda1", "path": "/dev/sda1", "type": "part",
        "pkname": "sda", "size": 120_000_000_000,
        "fstype": "ntfs", "uuid": uuid, "partuuid": "fake-gpt-id",
        "partlabel": "Windows Recovery", "ro": False, "mountpoints": [],
    }
    rows = [boot, target]
    if placement == "flat":
        rows.append(part)
    else:
        assert placement == "nested"
        target["children"] = [part]
    return {"blockdevices": rows}


def _target(scan, name_form, placement, route, *, uuid="fake-partition-before"):
    try:
        result = scan(_payload(name_form, placement, uuid=uuid), route)
    except ValueError:
        assert route == "direct"
        return None
    candidates = [disk for disk in result.selectable if disk.path == "/dev/sda"]
    assert len(candidates) <= 1
    if candidates:
        assert result.boot_identified and not result.error
        assert result.boot is not None and result.boot.path == "/dev/sdz"
        assert "/dev/sdz" not in {disk.path for disk in result.selectable}
        return candidates[0]
    # Refusing uncertain identity is a valid safe outcome, whether the parser
    # excludes just the target or public discover rejects the inventory.
    return None


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("name_form", NAME_FORMS)
@pytest.mark.parametrize("placement", ("flat", "nested"))
def test_name_gap_cannot_drop_observed_windows_and_layout_evidence(
    fake_machine, route, name_form, placement,  # noqa: F811 - imported fixture
):
    target = _target(fake_machine, name_form, placement, route)
    if target is not None:
        assert target.contents == CONTENTS_WINDOWS
        assert target.layout_id


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("name_form", NAME_FORMS)
@pytest.mark.parametrize("placement", ("flat", "nested"))
def test_name_gap_cannot_merge_changed_partition_identity(
    fake_machine, route, name_form, placement,  # noqa: F811 - imported fixture
):
    before = _target(fake_machine, name_form, placement, route)
    after = _target(
        fake_machine, name_form, placement, route, uuid="fake-partition-after",
    )
    assert before is None or after is None or disk_identity(before) != disk_identity(after)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("name_form", NAME_FORMS)
def test_missing_name_cannot_drop_mount_on_flat_partition(
    fake_machine, route, name_form,  # noqa: F811 - imported fixture
):
    payload = copy.deepcopy(_payload(name_form, "flat"))
    payload["blockdevices"][-1]["mountpoints"] = ["/data"]
    try:
        result = fake_machine(payload, route)
    except ValueError:
        assert route == "direct"
        return
    assert "/dev/sda" not in {disk.path for disk in result.selectable}
