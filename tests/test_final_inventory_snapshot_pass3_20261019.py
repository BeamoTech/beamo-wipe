"""Inventory-bound consent survives unchanged rescans, never a changed peer."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult, MethodId, WipeRequest
from beamo_wipe.safety import (
    SafetyError,
    assert_ready_to_wipe,
    assert_rediscovered_identity,
    confirm_spec,
    disk_identity,
    listed_disks,
)


CHANGES = (
    "add", "remove", "serial", "size", "wwn", "model", "raw-model", "layout",
    "vendor", "bus", "kind", "boot-alias",
)


@pytest.fixture
def fake_machine(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    # All physical predicates are explicit fixture values. Neither request
    # construction nor the complete runner path may touch a real device.
    for module in ("beamo_wipe.safety", "beamo_wipe.nwipe_runner"):
        for name in ("assert_not_boot", "assert_existing_is_block_device", "assert_size_unchanged", "assert_local_device_transport"):
            monkeypatch.setattr(module + "." + name, lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module + ".block_rdev", lambda path: 16 if path == "/dev/sdz" else 8)
    for name in ("require_real_live_for_nwipe", "_verify_pinned_nwipe", "_reserve_target_under_lock"):
        monkeypatch.setattr(runner_module, name, lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", lambda **_kwargs: False)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)
    monkeypatch.setattr(
        runner_module.subprocess, "run",
        lambda *_args, **_kwargs: pytest.fail("fixture attempted a subprocess"),
    )
    spawn = Mock(return_value=SimpleNamespace())
    monkeypatch.setattr(runner_module.subprocess, "Popen", spawn)
    boot = Disk(
        "/dev/sdz", "sdz", "Fake boot", "BOOT-1", 16_000_000_000, "16",
        DiskKind.SSD, "USB", "", is_boot=True, wwn="50014ee2aa000001",
        raw_model="Fake boot", mountpoints=("/run/live/medium",),
    )
    target = Disk(
        "/dev/sda", "sda", "Fake target", "TARGET-1", 128_000_000_000, "128",
        DiskKind.SSD, "SATA", "", wwn="50014ee2aa000002", raw_model="Fake target",
    )
    peer = replace(
        target, path="/dev/sdc", name="sdc", serial="PEER-1", wwn="50014ee2aa000003",
        model="Fake peer", raw_model="Fake peer", size_bytes=512_000_000_000,
        size_gb_label="512", vendor="Fake vendor", layout_id="peer-layout",
    )
    initial = DiscoveryResult(
        disks=(boot, target, peer), selectable=(target, peer), boot=boot,
        boot_identified=True,
    )
    return initial, target, peer, spawn


def request_for(discovery, target, method):
    return assert_ready_to_wipe(
        owner_ok=True, disk=target, discovery=discovery,
        typed_token=confirm_spec(target, listed_disks(discovery)).token,
        countdown_complete=True, method=method,
    )


def changed_inventory(initial, peer, change):
    if change == "add":
        added = replace(peer, path="/dev/sde", name="sde", serial="PEER-NEW", wwn="50014ee2aa000004")
        return replace(initial, disks=(*initial.disks, added), selectable=(*initial.selectable, added))
    if change == "remove":
        return replace(initial, disks=tuple(d for d in initial.disks if d.path != peer.path), selectable=tuple(d for d in initial.selectable if d.path != peer.path))
    if change == "boot-alias":
        alias = replace(initial.boot, path="/dev/sdf", name="sdf")
        return replace(initial, disks=(*initial.disks, alias))
    mutation = {
        "serial": {"serial": "PEER-NEW"},
        "size": {"size_bytes": 513_000_000_000, "size_gb_label": "513"},
        "wwn": {"wwn": "50014ee2aa000004"},
        "model": {"model": "Changed display model"},
        "raw-model": {"raw_model": "Changed raw model"},
        "layout": {"layout_id": "new-layout"},
        "vendor": {"vendor": "Changed vendor"},
        "bus": {"bus": "USB"},
        "kind": {"kind": DiskKind.HDD},
    }[change]
    replacement = replace(peer, **mutation)
    return replace(
        initial,
        disks=tuple(replacement if d.path == peer.path else d for d in initial.disks),
        selectable=tuple(replacement if d.path == peer.path else d for d in initial.selectable),
    )


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("change", CHANGES)
@pytest.mark.parametrize("runner_start", (False, True))
def test_final_rescan_rejects_changed_authorized_inventory(fake_machine, monkeypatch, method, change, runner_start):
    initial, target, peer, spawn = fake_machine
    request = request_for(initial, target, method)
    fresh = changed_inventory(initial, peer, change)
    monkeypatch.setattr("beamo_wipe.discover.discover", lambda: fresh)
    runner = runner_module.NwipeRunner()
    runner._sleep_inhibit = SimpleNamespace(start=lambda: None, stop=lambda: None)
    try:
        with pytest.raises(SafetyError, match="identity|inventory|authorization"):
            if runner_start:
                runner.start(request)
            else:
                assert_rediscovered_identity(request, fresh)
        spawn.assert_not_called()
        assert runner.start_not_spawned()
    finally:
        runner._release_wipe_lock()


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("reorder", (False, True))
@pytest.mark.parametrize("runner_start", (False, True))
def test_unchanged_inventory_and_reordering_remain_authorized(fake_machine, monkeypatch, method, reorder, runner_start):
    initial, target, _peer, spawn = fake_machine
    request = request_for(initial, target, method)
    fresh = replace(initial, disks=tuple(reversed(initial.disks)), selectable=tuple(reversed(initial.selectable))) if reorder else replace(initial)
    monkeypatch.setattr("beamo_wipe.discover.discover", lambda: fresh)
    runner = runner_module.NwipeRunner()
    runner._sleep_inhibit = SimpleNamespace(start=lambda: None, stop=lambda: None)
    try:
        if runner_start:
            runner.start(request)
            spawn.assert_called_once()
        else:
            assert_rediscovered_identity(request, fresh)
            spawn.assert_not_called()
    finally:
        runner._release_wipe_lock()


def test_boundary_request_captures_nonempty_canonical_inventory(fake_machine):
    initial, target, _peer, _spawn = fake_machine
    request = request_for(initial, target, MethodId.EVERYDAY)
    assert request.inventory_identity
    assert request.inventory_identity == tuple(sorted(disk_identity(item) for item in listed_disks(initial)))
    minimal = replace(initial, disks=(initial.boot, target), selectable=(target,))
    assert len(request_for(minimal, target, MethodId.EVERYDAY).inventory_identity) == 2


def test_legacy_constructor_keeps_target_and_boot_identity_guards(fake_machine):
    initial, target, _peer, _spawn = fake_machine
    request = WipeRequest(
        target.path, MethodId.EVERYDAY, initial.boot.path, "/tmp/beamo-wipe/fake.log",
        device_identity=disk_identity(target), boot_identity=disk_identity(initial.boot),
    )
    assert_rediscovered_identity(request, initial)
    changed = replace(target, serial="OTHER-TARGET")
    fresh = replace(initial, disks=tuple(changed if d.path == target.path else d for d in initial.disks), selectable=tuple(changed if d.path == target.path else d for d in initial.selectable))
    with pytest.raises(SafetyError, match="identity changed"):
        assert_rediscovered_identity(request, fresh)
