"""Root-owned 32-case proof for malformed pathless identity boundaries."""

import pytest

from test_physical_observation_context_pass15 import (
    _boot,
    _disk,
    fake_machine,  # noqa: F401 - imported pytest fixture
)

X, Y = "50014ee20aa00001", "50014ee20aa00002"
PATHLESS = (("", ""), (None, None))


def _uncertain_bridge(field, defect, *, overlap, identity=("", "")):
    serial = "FAKE-A" if overlap else "FAKE-UNRELATED"
    bridge = _disk("sdc", serial=serial, wwn=X)
    expected = serial if field == "serial" else X
    bridge.update(name=identity[0], path=identity[1])
    if defect == "malformed":
        bridge[field] = []
        values = [expected]
    else:
        bridge[field] = ""
        values = [expected, "FAKE-OTHER" if field == "serial" else Y]
    bridge["children"] = [
        {"name": f"dm-{700 + index}", "path": f"/dev/dm-{700 + index}",
         "type": "crypt", field: value}
        for index, value in enumerate(values)
    ]
    return bridge


def _scan(scan, kind, rows):
    anchor = _disk("sdb", serial="FAKE-A")
    anchor["mountpoints"] = [
        "/run/live/medium" if kind == "boot" else "/media/fake-data"
    ]
    if kind == "boot":
        anchor["tran"] = "usb"
    boot = anchor if kind == "boot" else _boot()
    payload = {"blockdevices": [anchor, *rows]}
    if kind == "mounted":
        payload["blockdevices"].append(boot)
    return scan(payload, boot["path"]), boot["path"]


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("defect", ("malformed", "conflicting"))
@pytest.mark.parametrize("identity", PATHLESS)
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_malformed_pathless_overlap_cannot_expose_alias(
    fake_machine, kind, identity, defect, field  # noqa: F811 - imported pytest fixture
):
    bridge = _uncertain_bridge(field, defect, overlap=True, identity=identity)
    leaf = _disk("sdd", serial="FAKE-LEAF", wwn=X)
    result, _boot_path = _scan(fake_machine, kind, [bridge, leaf])
    assert leaf["path"] not in {disk.path for disk in result.selectable}


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("defect", ("malformed", "conflicting"))
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_unrelated_malformed_pathless_observation_does_not_hide_target(
    fake_machine, kind, defect, field  # noqa: F811 - imported pytest fixture
):
    bridge = _uncertain_bridge(field, defect, overlap=False)
    leaf = _disk("sdd", serial="FAKE-LEAF", wwn=Y)
    result, boot_path = _scan(fake_machine, kind, [bridge, leaf])
    assert result.boot_identified and result.boot.path == boot_path
    assert not result.error
    assert leaf["path"] in {disk.path for disk in result.selectable}


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("identity", PATHLESS)
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_two_pathless_observations_are_not_one_device_path(
    fake_machine, kind, identity, field  # noqa: F811 - imported pytest fixture
):
    connected = _disk("sdc", serial="FAKE-A", wwn=X)
    connected.update(name=identity[0], path=identity[1])
    unrelated = _uncertain_bridge(
        field, "malformed", overlap=False, identity=identity,
    )
    unrelated["wwn"] = Y if field == "serial" else []
    if field == "wwn":
        unrelated["children"][0]["wwn"] = Y
    leaf = _disk("sdd", serial="FAKE-LEAF", wwn=Y)
    result, boot_path = _scan(fake_machine, kind, [connected, unrelated, leaf])
    assert result.boot_identified and result.boot.path == boot_path
    assert not result.error
    assert leaf["path"] in {disk.path for disk in result.selectable}
