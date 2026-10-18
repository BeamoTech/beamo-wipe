"""A pathless physical observation still carries protected alias evidence."""

import itertools

import pytest

from test_physical_observation_context_pass15 import (
    CHAINS,
    _boot,
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)


PATHLESS = (
    ("", ""),
    (None, None),
    ("", None),
    ("", "/dev/"),
)
ORDERS = tuple(itertools.permutations(range(3)))


@pytest.mark.parametrize("order", ORDERS)
@pytest.mark.parametrize("chain", tuple(CHAINS))
@pytest.mark.parametrize("identity", PATHLESS)
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_pathless_physical_bridge_preserves_exclusion(
    fake_machine, kind, identity, chain, order  # noqa: F811 - imported pytest fixture
):
    rows = [
        _disk(name, serial=serial, wwn=wwn)
        for name, (serial, wwn) in zip(("sdb", "sdc", "sdd"), CHAINS[chain])
    ]
    rows[0]["mountpoints"] = [
        "/run/live/medium" if kind == "boot" else "/media/fake-data"
    ]
    if kind == "boot":
        rows[0]["tran"] = "usb"
    rows[1].update(name=identity[0], path=identity[1])
    ordered = [rows[index] for index in order]
    boot = rows[0] if kind == "boot" else _boot()
    if kind == "mounted":
        ordered.append(boot)
    result = fake_machine({"blockdevices": ordered}, boot["path"])
    paths = {disk.path for disk in result.selectable}
    if chain in {"root_missing", "leaf_missing"}:
        assert "/dev/sdd" not in paths
    else:
        # A pathless row with unrelated or proven contrary hardware facts
        # must not suppress a valid separate target by itself.
        assert result.boot_identified and result.boot.path == boot["path"]
        assert not result.error
        assert "/dev/sdd" in paths


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("identity", PATHLESS)
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_pathless_parent_hardware_field_remains_authoritative(
    fake_machine, kind, identity, field  # noqa: F811 - imported pytest fixture
):
    if field == "serial":
        anchor = _disk("sdb", serial="FAKE-A")
        bridge = _disk("sdc", serial="FAKE-B", wwn="50014ee20aa00001")
        leaf = _disk("sdd", serial="FAKE-C", wwn="50014ee20aa00001")
        descendant_value = "FAKE-A"
    else:
        anchor = _disk("sdb", serial="FAKE-A", wwn="50014ee20aa00001")
        bridge = _disk("sdc", serial="FAKE-A", wwn="50014ee20aa00002")
        leaf = _disk("sdd", serial="FAKE-C", wwn="50014ee20aa00002")
        descendant_value = "50014ee20aa00001"
    anchor["mountpoints"] = [
        "/run/live/medium" if kind == "boot" else "/media/fake-data"
    ]
    if kind == "boot":
        anchor["tran"] = "usb"
    bridge.update(name=identity[0], path=identity[1])
    bridge["children"] = [{
        "name": "dm-77", "path": "/dev/dm-77", "type": "crypt",
        field: descendant_value,
    }]
    boot = anchor if kind == "boot" else _boot()
    rows = [anchor, bridge, leaf]
    if kind == "mounted":
        rows.append(boot)
    result = fake_machine({"blockdevices": rows}, boot["path"])
    assert result.boot_identified and result.boot.path == boot["path"]
    assert not result.error
    assert "/dev/sdd" in {disk.path for disk in result.selectable}
