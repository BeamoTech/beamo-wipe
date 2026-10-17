"""UNRUN fake-only probe: malformed numeric sizes must fail normally and closed.

No source imports or test execution were performed during preparation. Root
owns every runtime. The process/file/device guards come from the existing
fake-machine fixture. JSON literal parsing below uses the product entry point.
"""

import pytest

from beamo_wipe.discover import load_lsblk_json_text
from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported guarded fake-machine pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
LOCATIONS = ("boot", "target", "partition")
NONFINITE_JSON = ("NaN", "Infinity", "-Infinity", "1e999")
FINITE_JSON = ("128000000000", "128000000000.0", "1.28e11", str(1 << 100))


def _payload(location, raw_size):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    part = {
        "name": "sda1", "path": "/dev/sda1", "type": "part",
        "pkname": "sda", "size": 120_000_000_000,
        "fstype": "ext4", "uuid": "fake-partition",
        "ro": False, "mountpoints": [],
    }
    size = load_lsblk_json_text('{"size":' + raw_size + '}')["size"]
    {"boot": boot, "target": target, "partition": part}[location]["size"] = size
    return {"blockdevices": [boot, target, part]}, size


def _scan(scan, payload, route):
    try:
        return scan(payload, route)
    except ValueError:
        # parse_lsblk_json is the explicit lower-level API: it may reject bad
        # numeric metadata. Public discover must convert that into its usual
        # failed/empty outcome. OverflowError is intentionally not swallowed.
        assert route == "direct"
        return None


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("raw_size", NONFINITE_JSON)
def test_nonfinite_size_does_not_escape_discovery_or_authorize_target(
    fake_machine, route, location, raw_size,  # noqa: F811 - imported fixture
):
    try:
        payload, _size = _payload(location, raw_size)
    except ValueError:
        # Rejecting the invalid numeric JSON at its loading boundary is also
        # safe. This path is not used by the current source candidate.
        return
    result = _scan(fake_machine, payload, route)
    if result is not None:
        assert "/dev/sda" not in {disk.path for disk in result.selectable}
        if location == "boot":
            assert not result.boot_identified


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("raw_size", FINITE_JSON)
def test_finite_integer_float_exponent_and_large_integer_controls(
    fake_machine, route, location, raw_size,  # noqa: F811 - imported fixture
):
    payload, size = _payload(location, raw_size)
    result = fake_machine(payload, route)
    assert result.boot_identified and not result.error
    targets = [disk for disk in result.selectable if disk.path == "/dev/sda"]
    assert len(targets) == 1
    assert result.boot is not None
    assert "/dev/sdz" not in {disk.path for disk in result.selectable}
    if location == "boot":
        assert result.boot.size_bytes == int(size)
    elif location == "target":
        assert targets[0].size_bytes == int(size)
    else:
        assert targets[0].layout_id
