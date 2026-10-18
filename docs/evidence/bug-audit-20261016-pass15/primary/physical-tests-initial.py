"""Display filtering cannot discard boot, mounted or conflicting disk evidence."""

import builtins
import copy
from dataclasses import replace
import importlib
import io
import itertools
import os

import pytest

from beamo_wipe.safety import (
    SafetyError,
    assert_boot_excluded,
    assert_disk_identity,
    confirm_spec,
    listed_disks,
)


discovery = importlib.import_module("beamo_wipe.discover")
X, Y = "50014ee20aa00001", "50014ee20aa00002"
CHAINS = {
    "root_missing": (("FAKE-A", ""), ("FAKE-A", X), ("FAKE-C", X)),
    "leaf_missing": (("FAKE-A", X), ("FAKE-B", X), ("FAKE-B", "")),
    "contrary": (("FAKE-A", X), ("FAKE-A", ""), ("FAKE-A", Y)),
    "unrelated": (("FAKE-A", ""), ("FAKE-B", X), ("FAKE-C", X)),
}
BRIDGES = (
    "visible", "rom", "emmc_boot", "hidden_name", "overlong_model", "overlong_layout_label",
)
ORDERS = tuple(itertools.permutations(range(3)))


@pytest.fixture
def fake_machine(monkeypatch):
    """Injected machine metadata never consults devices or native inventory."""
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("native acquisition")
        raise AssertionError("Injected inventory reached native acquisition")

    realpath = os.path.realpath

    def fake_realpath(path, *args, **kwargs):
        text = os.fspath(path)
        if text.startswith(("/dev/", "/sys/")):
            return text
        return realpath(path, *args, **kwargs)

    def guarded(original):
        def checked(path, *args, **kwargs):
            if not isinstance(path, int):
                text = os.fsdecode(path)
                if text in {"/dev", "/proc", "/sys"} or text.startswith(("/dev/", "/proc/", "/sys/")):
                    attempted.append(text)
                    raise AssertionError("Injected inventory consulted a native path")
            return original(path, *args, **kwargs)
        return checked

    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr(os.path, "realpath", fake_realpath)
    for name in ("run_lsblk", "read_mount_sources", "read_cmdline"):
        monkeypatch.setattr(discovery, name, forbidden)
    for name in ("run", "Popen"):
        monkeypatch.setattr(discovery.subprocess, name, forbidden)
    monkeypatch.setattr(builtins, "open", guarded(builtins.open))
    monkeypatch.setattr(io, "open", guarded(io.open))
    monkeypatch.setattr(os, "open", guarded(os.open))
    monkeypatch.setattr(os, "lstat", guarded(os.lstat))
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None)

    def scan(payload, boot="/dev/sdz"):
        return discovery.discover(
            lsblk_payload=copy.deepcopy(payload), mount_sources=[boot], cmdline="", env={},
        )

    yield scan
    assert not attempted


def _disk(name, *, serial="", wwn="", **changes):
    row = dict(
        name=name, path="/dev/" + name, type="disk", tran="sata",
        size=128_000_000_000, serial=serial, wwn=wwn, model="Fake disk",
        ro=False, mountpoints=[],
    )
    row.update(changes)
    return row


def _boot():
    return _disk(
        "sdz", serial="FAKE-BOOT", wwn="50014ee20aa00009", tran="usb",
        size=16_000_000_000, mountpoints=["/run/live/medium"],
    )


def _alias_payload(kind, bridge, chain, order):
    rows = [_disk(name, serial=serial, wwn=wwn)
            for name, (serial, wwn) in zip(("sdb", "sdc", "sdd"), CHAINS[chain])]
    rows[0]["mountpoints"] = ["/run/live/medium" if kind == "boot" else "/media/fake-data"]
    if kind == "boot":
        rows[0]["tran"] = "usb"
    if bridge == "rom":
        rows[1].update(name="sr0", path="/dev/sr0", type="rom", tran="usb", ro=True)
    elif bridge == "emmc_boot":
        rows[1].update(name="mmcblk0boot0", path="/dev/mmcblk0boot0", tran="", ro=True)
    elif bridge == "hidden_name":
        rows[1].update(name="sdlive", path="/dev/sdlive")
    elif bridge == "overlong_model":
        rows[1]["model"] = "M" * 129
    elif bridge == "overlong_layout_label":
        rows[1]["label"] = "L" * 129
    ordered = [rows[index] for index in order]
    boot = rows[0] if kind == "boot" else _boot()
    if kind == "mounted":
        ordered.append(boot)
    return {"blockdevices": ordered}, boot["path"], rows[1]["path"]


@pytest.mark.parametrize("order", ORDERS)
@pytest.mark.parametrize("chain", tuple(CHAINS))
@pytest.mark.parametrize("bridge", BRIDGES)
@pytest.mark.parametrize("kind", ("boot", "mounted"))
def test_omitted_physical_bridge_keeps_boot_and_mount_protection(fake_machine, kind, bridge, chain, order):
    payload, boot_path, bridge_path = _alias_payload(kind, bridge, chain, order)
    result = fake_machine(payload, boot_path)
    assert result.boot_identified and result.boot.path == boot_path and not result.error
    assert boot_path not in {disk.path for disk in result.selectable}
    leaf = next(disk for disk in result.disks if disk.path == "/dev/sdd")
    protected = chain in {"root_missing", "leaf_missing"}
    assert (leaf.path in {disk.path for disk in result.selectable}) is not protected
    if protected:
        assert leaf.mountpoints
        assert leaf.is_boot is (kind == "boot")
        with pytest.raises(SafetyError):
            assert_disk_identity(leaf, result)
    else:
        assert not leaf.is_boot and not leaf.mountpoints
        assert_disk_identity(leaf, result)
        assert confirm_spec(leaf, listed_disks(result)).token
    if bridge != "visible":
        assert bridge_path not in {disk.path for disk in result.disks}
        assert bridge_path not in {disk.path for disk in result.selectable}
        assert bridge_path not in {disk.path for disk in listed_disks(result)}
    assert_boot_excluded(result)


@pytest.mark.parametrize("order", ORDERS)
@pytest.mark.parametrize("chain", ("root_missing", "leaf_missing"))
@pytest.mark.parametrize("bridge", BRIDGES)
def test_final_boot_guard_rechecks_retained_physical_evidence(fake_machine, bridge, chain, order):
    payload, boot_path, _bridge_path = _alias_payload("boot", bridge, chain, order)
    result = fake_machine(payload, boot_path)
    assert result.boot_identified and not result.error
    leaf = next(disk for disk in result.disks if disk.path == "/dev/sdd")
    reset = replace(leaf, is_boot=False, mountpoints=())
    injected = replace(
        result, disks=tuple(reset if disk.path == reset.path else disk for disk in result.disks),
        selectable=(reset,),
    )
    with pytest.raises(SafetyError, match="Boot USB appeared"):
        assert_boot_excluded(injected)


CONFLICTS = {
    "read_only": ("ro", True),
    "serial": ("serial", "OTHER-SERIAL"),
    "wwn": ("wwn", Y),
    "size": ("size", 256_000_000_000),
    "bus": ("tran", "iscsi"),
    "mounted": ("mountpoints", ["/media/fake-data"]),
}


def _duplicate_payload(conflict, display, order):
    first = _disk("sda", serial="FAKE-TARGET", wwn=X)
    second = copy.deepcopy(first)
    field, value = CONFLICTS[conflict]
    second[field] = value
    if display == "overlong_model":
        second["model"] = "M" * 129
    elif display == "overlong_layout_label":
        second["label"] = "L" * 129
    rows = [first, second]
    return {"blockdevices": [rows[index] for index in order] + [_boot()]}


@pytest.mark.parametrize("order", ((0, 1), (1, 0)))
@pytest.mark.parametrize("display", ("valid", "overlong_model", "overlong_layout_label"))
@pytest.mark.parametrize("conflict", tuple(CONFLICTS))
def test_display_error_cannot_hide_conflicting_physical_observation(fake_machine, conflict, display, order):
    result = fake_machine(_duplicate_payload(conflict, display, order))
    assert "/dev/sda" not in {disk.path for disk in result.selectable}


def test_conflicting_observation_refusal_can_recover_on_clean_retry(fake_machine):
    first = fake_machine(_duplicate_payload("read_only", "overlong_model", (0, 1)))
    assert not first.selectable
    clean = fake_machine({"blockdevices": [_boot(), _disk("sda", serial="FAKE-TARGET", wwn=X)]})
    assert clean.boot_identified and not clean.error
    assert [disk.path for disk in clean.selectable] == ["/dev/sda"]
    assert_boot_excluded(clean)
    assert_disk_identity(clean.selectable[0], clean)
    assert confirm_spec(clean.selectable[0], listed_disks(clean)).token


def test_isolated_pathless_row_preserves_a_valid_separate_target(fake_machine):
    payload = {"blockdevices": [
        _disk("", path="", serial="UNRELATED"), _boot(), _disk("sda", serial="FAKE-TARGET", wwn=X),
    ]}
    result = fake_machine(payload)
    assert result.boot_identified and not result.error
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]
    assert "/dev/" not in {disk.path for disk in result.disks}
    assert_boot_excluded(result)


@pytest.mark.parametrize("field", ("serial", "wwn"))
def test_partition_hardware_identity_fallback_still_protects_alias_chain(fake_machine, field):
    chain = "root_missing" if field == "serial" else "leaf_missing"
    payload, boot_path, _bridge_path = _alias_payload("boot", "visible", chain, (0, 1, 2))
    bridge = payload["blockdevices"][1]
    child = dict(name="sdc1", path="/dev/sdc1", type="part", pkname="sdc", mountpoints=[])
    child[field] = bridge[field]
    bridge[field] = ""
    bridge["children"] = [child]
    result = fake_machine(payload, boot_path)
    assert result.boot_identified and not result.error
    assert "/dev/sdd" not in {disk.path for disk in result.selectable}
    assert_boot_excluded(result)
