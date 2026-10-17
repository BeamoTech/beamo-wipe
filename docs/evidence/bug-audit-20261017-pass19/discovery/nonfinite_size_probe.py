"""Unrun source-derived probe: numeric overflow must not escape discovery.

Root owns execution. This uses only the retained native-acquisition guard
fixture and canned inventory; importing this file does not run the application.
"""

import pytest

from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("placement", ("boot", "target", "unrelated"))
@pytest.mark.parametrize(
    "value", (float("inf"), float("-inf"), "1e309", "-1e309", "not-a-size"),
    ids=("numeric-positive-infinity", "numeric-negative-infinity", "text-positive-overflow",
         "text-negative-overflow", "text-malformed"),
)
def test_nonfinite_size_does_not_escape_public_discovery(
    fake_machine, route, placement, value  # noqa: F811 - imported pytest fixture
):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    unrelated = _disk("sdc")
    rows = {"boot": boot, "target": target, "unrelated": unrelated}
    rows[placement]["size"] = value
    result = fake_machine({"blockdevices": [boot, target, unrelated]}, route)
    # Refusal of malformed inventory and omission of an unusable node are both
    # fail-closed outcomes. A numeric size exception must never escape the API.
    if result.error:
        assert not result.boot_identified
        assert result.disks == ()
        assert result.selectable == ()
    else:
        assert result.boot_identified
        assert result.boot.path == "/dev/sdz"
        assert "/dev/sdz" not in {disk.path for disk in result.selectable}
        if placement != "boot":
            assert rows[placement]["path"] not in {disk.path for disk in result.selectable}


@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
@pytest.mark.parametrize("value", (128_000_000_000, 128_000_000_000.0, "128000000000", "1.28e11"))
def test_finite_sizes_retain_normal_fake_target(
    fake_machine, route, value  # noqa: F811 - imported pytest fixture
):
    result = fake_machine({"blockdevices": [
        _disk("sdz", tran="usb", mountpoints=["/run/live/medium"]),
        _disk("sda", size=value),
    ]}, route)
    assert not result.error
    assert result.boot_identified
    assert [(disk.path, disk.size_bytes) for disk in result.selectable] == [
        ("/dev/sda", 128_000_000_000)
    ]
