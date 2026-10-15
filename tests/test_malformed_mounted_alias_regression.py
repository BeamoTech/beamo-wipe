"""Malformed mounted observations must not expose another path to that disk."""

import pytest

from beamo_wipe.discover import discover


def disk(name, *, wwn="", serial="", mounts=None):
    return {
        "name": name, "path": f"/dev/{name}", "type": "disk",
        "size": 100_000_000_000, "tran": "usb" if name == "sdb" else "sata",
        "rota": False, "model": "Ordinary disk", "vendor": "Vendor",
        "serial": serial, "wwn": wwn, "ro": False,
        "mountpoints": mounts or [], "mountpoint": None,
    }


def scan(monkeypatch, malformed):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    boot = disk("sdb", serial="BOOT", mounts=["/run/live/medium"])
    target = disk("sda", wwn="0x5000abc", serial="SHARED")
    return discover(
        lsblk_payload={"blockdevices": [boot, target, malformed]},
        mount_sources=["/dev/sdb"], env={},
    )


@pytest.mark.parametrize("alias", ["wwn", "serial"])
@pytest.mark.parametrize("field,bad", [("model", "bad\nmodel"), ("vendor", "v" * 129)])
@pytest.mark.parametrize("mounted_child", [False, True])
def test_malformed_mounted_alias_cannot_disappear(monkeypatch, alias, field, bad, mounted_child):
    observed = disk("sdc", wwn="0x5000abc" if alias == "wwn" else "", serial="SHARED")
    observed[field] = bad
    if mounted_child:
        observed["children"] = [{
            "name": "sdc1", "path": "/dev/sdc1", "type": "part", "pkname": "sdc",
            "size": 99_000_000_000, "mountpoint": "/media/data", "mountpoints": [None],
        }]
    else:
        observed["mountpoints"] = ["/media/data"]
    result = scan(monkeypatch, observed)
    assert not result.selectable
    assert result.error


def test_case_variant_type_cannot_hide_mounted_alias(monkeypatch):
    observed = disk("sdc", wwn="0x5000abc", mounts=["/media/data"])
    observed["type"] = "DISK"
    result = scan(monkeypatch, observed)
    assert not result.selectable


@pytest.mark.parametrize("field,value", [("mountpoint", "\n"), ("mountpoints", [" "])])
def test_nonempty_malformed_mount_is_not_repaired_into_unmounted(monkeypatch, field, value):
    observed = disk("sdc", wwn="0x5000abc")
    observed[field] = value
    result = scan(monkeypatch, observed)
    assert "/dev/sdc" not in {item.path for item in result.selectable}
    assert "/dev/sda" not in {item.path for item in result.selectable}


def test_unmounted_unrelated_malformed_row_preserves_valid_target(monkeypatch):
    observed = disk("sdc", serial="UNRELATED")
    observed["model"] = "bad\nmodel"
    result = scan(monkeypatch, observed)
    assert not result.error
    assert [item.path for item in result.selectable] == ["/dev/sda"]


@pytest.mark.parametrize("name,kind", [("sr1", "rom"), ("mmcblk0boot0", "disk")])
@pytest.mark.parametrize("malformed", [False, True])
def test_hidden_mounted_physical_alias_remains_exclusion_evidence(monkeypatch, name, kind, malformed):
    observed = disk(name, wwn="0x5000abc", mounts=["/media/data"])
    observed["type"] = kind
    if malformed:
        observed["model"] = "bad\nmodel"
    result = scan(monkeypatch, observed)
    assert not result.selectable
    if malformed:
        assert result.error
    else:
        assert not result.error
        assert observed["path"] not in {item.path for item in result.disks}


@pytest.mark.parametrize("name,kind", [("sr1", "rom"), ("mmcblk0boot0", "disk")])
def test_unmounted_hidden_observation_does_not_expand_targets(monkeypatch, name, kind):
    observed = disk(name, wwn="0x5000abc")
    observed["type"] = kind
    result = scan(monkeypatch, observed)
    assert not result.error
    assert [item.path for item in result.selectable] == ["/dev/sda"]
    assert observed["path"] not in {item.path for item in result.disks}


@pytest.mark.parametrize("alias", ["wwn", "serial"])
@pytest.mark.parametrize("malformed", [False, True])
def test_flat_mounted_child_preserves_physical_alias_exclusion(monkeypatch, alias, malformed):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    boot = disk("sdb", serial="BOOT", mounts=["/run/live/medium"])
    target = disk("sda", wwn="0x5000abc", serial="SHARED")
    observed = disk("sdc", wwn="0x5000abc" if alias == "wwn" else "", serial="SHARED")
    if malformed:
        observed["model"] = "bad\nmodel"
    child = {
        "name": "sdc1", "path": "/dev/sdc1", "type": "part", "pkname": "sdc",
        "size": 99_000_000_000, "mountpoints": ["/media/data"], "mountpoint": None,
    }
    result = discover(
        lsblk_payload={"blockdevices": [boot, target, observed, child]},
        mount_sources=["/dev/sdb"], env={},
    )
    assert not result.selectable
    if malformed:
        assert result.error
    else:
        assert not result.error


@pytest.mark.parametrize("kind", ["loop", "ram"])
def test_virtual_type_cannot_hide_mounted_kernel_disk_alias(monkeypatch, kind):
    observed = disk("sdc", wwn="0x5000abc", mounts=["/media/data"])
    observed["type"] = kind
    result = scan(monkeypatch, observed)
    assert not result.selectable
    assert result.error


@pytest.mark.parametrize("name,kind", [("loop0", "loop"), ("ram0", "ram")])
def test_legitimate_unrelated_virtual_mounts_preserve_normal_target(monkeypatch, name, kind):
    observed = disk(name, mounts=["/mnt/virtual"])
    observed["type"] = kind
    result = scan(monkeypatch, observed)
    assert not result.error
    assert [item.path for item in result.selectable] == ["/dev/sda"]
