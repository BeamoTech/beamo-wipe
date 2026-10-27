"""Raw whole disks need root ancestry at discovery and the final rescan.

All inventories and path aliases are fixtures. Nothing probes a device or starts
an engine; the final authorization check is followed by a Boolean sentinel.
"""

import builtins
import io
import os
from copy import deepcopy

import pytest

from beamo_wipe import discover as discovery_module
from beamo_wipe.discover import discover, parse_lsblk_json
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import (
    SafetyError,
    disk_identity,
    listed_disks,
    selectable_disks,
)


CASES = (
    "pk_boot", "pk_unknown", "pk_self", "pk_clean", "pk_mounted", "cycle",
    "nested_clean", "nested_mounted", "nested_unknown", "tree_disagrees",
    "nested_boot",
)
BOOT_CASES = (
    "direct", "unknown", "self", "transitive", "cycle", "nested",
    "nested_conflict", "nested_unknown",
)


@pytest.fixture(autouse=True)
def inert_paths(monkeypatch):
    """Resolve only invented aliases and fail if a fixture reaches host I/O."""
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    aliases = {}
    realpath = os.path.realpath

    def fixture_realpath(path, *args, **kwargs):
        text = os.fsdecode(path)
        if text.startswith("/dev/"):
            return aliases.get(text, text)
        return realpath(path, *args, **kwargs)

    def guard(operation):
        def call(path, *args, **kwargs):
            if isinstance(path, (str, bytes, os.PathLike)) and os.fsdecode(path).startswith(
                ("/dev/", "/sys/", "/proc/")
            ):
                raise AssertionError("fixture attempted host I/O")
            return operation(path, *args, **kwargs)

        return call

    def no_inventory(*_args, **_kwargs):
        raise AssertionError("fixture attempted real inventory")

    monkeypatch.setattr(os.path, "realpath", fixture_realpath)
    for name in ("stat", "lstat", "readlink", "listdir", "scandir"):
        monkeypatch.setattr(os, name, guard(getattr(os, name)))
    monkeypatch.setattr(builtins, "open", guard(builtins.open))
    monkeypatch.setattr(io, "open", guard(io.open))
    monkeypatch.setattr(discovery_module, "run_lsblk", no_inventory)
    monkeypatch.setattr(discovery_module, "read_mount_sources", no_inventory)
    monkeypatch.setattr(discovery_module, "read_cmdline", no_inventory)
    return aliases


def _disk(name, **fields):
    suffix = {"sda": "01", "sdb": "02", "sdc": "03", "sdz": "ff"}.get(name, "04")
    node = dict(
        name=name, path=f"/dev/{name}", type="disk", size=500_000_000_000,
        tran="sata", rota=False, ro=False, model=f"Fixture {name}",
        serial=f"UNIQUE-{name}", wwn=f"0x50000000000000{suffix}", mountpoints=[None],
    )
    node.update(fields)
    return node


def _clean():
    return {"blockdevices": [
        _disk("sdz", size=16_000_000_000, tran="usb"), _disk("sda"), _disk("sdc"),
    ]}


def _mutated(case):
    payload = _clean()
    boot, target, _other = payload["blockdevices"]
    if case.startswith("pk_"):
        target["pkname"] = {
            "pk_boot": "sdz", "pk_unknown": "missing", "pk_self": "sda",
            "pk_clean": "sdc", "pk_mounted": "sdb",
        }[case]
        if case == "pk_mounted":
            payload["blockdevices"].append(_disk("sdb", mountpoints=["/fixture/mounted"]))
    elif case == "cycle":
        target["pkname"] = "sdb"
        payload["blockdevices"].append(_disk("sdb", pkname="sda"))
    elif case in {"nested_clean", "nested_mounted", "nested_unknown", "tree_disagrees"}:
        payload["blockdevices"].remove(target)
        parent = _disk("sdb", children=[target])
        if case == "nested_mounted":
            parent["mountpoints"] = ["/fixture/mounted"]
        if case == "nested_unknown":
            parent = dict(name="mystery", path="/dev/mystery", type="mystery", children=[target])
        if case == "tree_disagrees":
            target["pkname"] = "sdz"
        payload["blockdevices"].append(parent)
    elif case == "nested_boot":
        payload["blockdevices"].remove(target)
        boot["children"] = [target]
    else:
        raise AssertionError(case)
    return payload


def _parse(payload):
    return parse_lsblk_json(payload, boot_path="/dev/sdz")


def _boot_mutated(case):
    payload = _clean()
    boot, target, _other = payload["blockdevices"]
    if case in {"direct", "unknown", "self"}:
        boot["pkname"] = {"direct": "sda", "unknown": "missing", "self": "sdz"}[case]
    elif case == "transitive":
        boot["pkname"] = "bridge"
        payload["blockdevices"].append(
            dict(name="bridge", path="/dev/bridge", type="crypt", pkname="sda")
        )
    elif case == "cycle":
        boot["pkname"] = "sda"
        target["pkname"] = "sdz"
    elif case in {"nested", "nested_conflict", "nested_unknown"}:
        payload["blockdevices"].remove(boot)
        if case == "nested_unknown":
            payload["blockdevices"].append(
                dict(name="mystery", path="/dev/mystery", type="mystery", children=[boot])
            )
        else:
            target["children"] = [boot]
            if case == "nested_conflict":
                boot["pkname"] = "sdc"
    else:
        raise AssertionError(case)
    return payload


def _assert_boot_ancestry_refused(result):
    assert result.error
    assert not result.boot_identified
    assert result.diagnostic == "lsblk raw boot disk ancestry is unresolved"
    assert result.boot is not None
    assert result.boot.is_boot
    assert result.disks and all(d.is_boot for d in result.disks)
    assert result.selectable == ()
    assert selectable_disks(result) == ()
    assert "/dev/sda" not in {d.path for d in selectable_disks(result)}
    assert any(d.path == "/dev/sdz" and d.is_boot for d in result.disks)
    assert {d.path for d in result.physical_observations} == {
        "/dev/sda", "/dev/sdc", "/dev/sdz",
    }
    assert {"/dev/sda", "/dev/sdc", "/dev/sdz"}.issubset(
        {d.path for d in result.excluded}
    )


def _request(result):
    target = next(d for d in selectable_disks(result) if d.path == "/dev/sda")
    assert result.boot is not None
    return WipeRequest(
        device=target.path, method=MethodId.EVERYDAY, boot_device=result.boot.path,
        logfile="/tmp/beamo-wipe/inert.log", device_identity=disk_identity(target),
        boot_identity=disk_identity(result.boot),
        inventory_identity=tuple(sorted(disk_identity(d) for d in listed_disks(result))),
    )


@pytest.mark.parametrize("case", CASES)
def test_raw_disk_with_unexpected_ancestry_is_ineligible(case):
    payload = _mutated(case)
    original = deepcopy(payload)
    result = _parse(payload)
    assert payload == original
    assert result.error is None
    assert result.boot_identified
    assert "/dev/sda" not in {d.path for d in result.disks}
    assert "/dev/sda" not in {d.path for d in selectable_disks(result)}
    assert "/dev/sdc" in {d.path for d in selectable_disks(result)}
    assert any(d.path == "/dev/sda" for d in result.physical_observations)
    assert any(d.path == "/dev/sda" for d in result.excluded)


@pytest.mark.parametrize("case", CASES)
def test_final_rediscovery_refuses_new_raw_disk_ancestry(case, monkeypatch):
    from beamo_wipe.nwipe_runner import _recheck_identity_under_lock

    request = _request(_parse(_clean()))
    fresh = discover(lsblk_payload=_mutated(case), boot_path="/dev/sdz", env={})
    assert fresh.error is None
    monkeypatch.setattr(discovery_module, "discover", lambda: fresh)
    fake_launch_reached = False
    with pytest.raises(SafetyError, match="Disk identity changed"):
        _recheck_identity_under_lock(request)
        fake_launch_reached = True
    assert not fake_launch_reached


@pytest.mark.parametrize("pkname", [None, ""])
def test_root_raw_disks_remain_eligible(pkname):
    payload = _clean()
    payload["blockdevices"][1]["pkname"] = pkname
    result = _parse(payload)
    assert {d.path for d in selectable_disks(result)} == {"/dev/sda", "/dev/sdc"}


def test_directly_mounted_raw_disk_stays_ineligible():
    payload = _clean()
    payload["blockdevices"][1]["mountpoints"] = ["/fixture/mounted"]
    result = _parse(payload)
    assert {d.path for d in selectable_disks(result)} == {"/dev/sdc"}


@pytest.mark.parametrize("pkname", ["missing", "sdz", "sda"])
def test_confirmed_boot_row_remains_protected_with_unexpected_ancestry(pkname):
    payload = _clean()
    payload["blockdevices"][0]["pkname"] = pkname
    result = _parse(payload)
    _assert_boot_ancestry_refused(result)
    assert result.boot.path == "/dev/sdz"


@pytest.mark.parametrize("case", BOOT_CASES)
def test_raw_boot_ancestry_refuses_all_targets_and_retains_physical_facts(case):
    payload = _boot_mutated(case)
    original = deepcopy(payload)
    _assert_boot_ancestry_refused(_parse(payload))
    assert payload == original


@pytest.mark.parametrize("case", BOOT_CASES)
@pytest.mark.parametrize("through_discover", [False, True])
def test_final_rediscovery_refuses_new_raw_boot_ancestry(case, through_discover, monkeypatch):
    from beamo_wipe.nwipe_runner import _recheck_identity_under_lock

    request = _request(_parse(_clean()))
    payload = _boot_mutated(case)
    fresh = (
        discover(lsblk_payload=payload, boot_path="/dev/sdz", env={})
        if through_discover else _parse(payload)
    )
    assert fresh.error
    assert fresh.selectable == ()
    monkeypatch.setattr(discovery_module, "discover", lambda: fresh)
    fake_launch_reached = False
    with pytest.raises(SafetyError, match="Boot device identity changed"):
        _recheck_identity_under_lock(request)
        fake_launch_reached = True
    assert not fake_launch_reached


@pytest.mark.parametrize("pkname", [None, ""])
def test_normal_boot_partition_preserves_clean_targets(pkname):
    payload = _clean()
    payload["blockdevices"][0]["pkname"] = pkname
    payload["blockdevices"][0]["children"] = [dict(
        name="sdz1", path="/dev/sdz1", type="part", pkname="sdz",
        size=8_000_000_000, mountpoints=["/run/live/medium"],
    )]
    result = _parse(payload)
    assert result.error is None
    assert result.boot_identified
    assert result.boot.path == "/dev/sdz"
    assert result.boot.is_boot
    assert {d.path for d in selectable_disks(result)} == {"/dev/sda", "/dev/sdc"}


@pytest.mark.parametrize("pkname", [None, "", "sda"])
def test_verified_boot_path_alias_preserves_protection(pkname, inert_paths):
    payload = _clean()
    alias = "/dev/disk/by-id/fixture-boot"
    payload["blockdevices"][0].update(path=alias, pkname=pkname)
    inert_paths[alias] = "/dev/sdz"
    result = _parse(payload)
    assert result.boot is not None
    assert result.boot.path == alias
    assert result.boot.is_boot
    assert alias not in {d.path for d in selectable_disks(result)}
    if pkname:
        assert result.error
        assert not result.boot_identified
        assert result.selectable == ()
        assert selectable_disks(result) == ()
        assert any(d.path == alias for d in result.physical_observations)
    else:
        assert result.error is None
        assert result.boot_identified
        assert {d.path for d in selectable_disks(result)} == {"/dev/sda", "/dev/sdc"}


@pytest.mark.parametrize("flat", [False, True])
def test_unmounted_bcache_holder_preserves_clean_backing_disk(flat):
    payload = _clean()
    holder = dict(name="bcache0", path="/dev/bcache0", type="disk", pkname="sda",
                  size=500_000_000_000, mountpoints=[None])
    if flat:
        payload["blockdevices"].append(holder)
    else:
        payload["blockdevices"][1]["children"] = [holder]
    result = _parse(payload)
    assert {d.path for d in selectable_disks(result)} == {"/dev/sda", "/dev/sdc"}
    assert "/dev/bcache0" in {d.path for d in result.disks}


def test_verified_whole_disk_path_alias_remains_eligible(inert_paths):
    payload = _clean()
    alias = "/dev/disk/by-id/fixture-sda"
    payload["blockdevices"][1]["path"] = alias
    inert_paths[alias] = "/dev/sda"
    result = _parse(payload)
    assert {d.path for d in selectable_disks(result)} == {alias, "/dev/sdc"}


@pytest.mark.parametrize("pkname", ["sdz", "missing", "sda"])
def test_clean_duplicate_cannot_hide_conflicting_raw_disk_ancestry(pkname):
    payload = _clean()
    payload["blockdevices"].append(_disk("sda", pkname=pkname))
    result = discover(lsblk_payload=payload, boot_path="/dev/sdz", env={})
    assert result.error
    assert selectable_disks(result) == ()


def test_unchanged_final_rediscovery_reaches_only_inert_sentinel(monkeypatch):
    from beamo_wipe.nwipe_runner import _recheck_identity_under_lock

    initial = _parse(_clean())
    request = _request(initial)
    fresh = discover(lsblk_payload=_clean(), boot_path="/dev/sdz", env={})
    monkeypatch.setattr(discovery_module, "discover", lambda: fresh)
    fake_launch_reached = False
    _recheck_identity_under_lock(request)
    fake_launch_reached = True
    assert fake_launch_reached
