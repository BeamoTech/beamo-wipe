# SPDX-License-Identifier: GPL-3.0-or-later
"""Unrecognized device types must not hide unbound filesystem evidence."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError, assert_rediscovered_identity, disk_identity
from test_discovery_observation_fallback_pass16 import (
    _boot,
    _disk,
    fake_machine,  # noqa: F401 - guarded fake-machine pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
UNKNOWN_TYPES = (None, "", "unknown", "unexpected-volume")


def _payload(kind, uuid, *, bound=False, nested=False):
    volume = dict(
        name="sda1", path="/dev/sda1", type=kind, size=120_000_000_000,
        fstype="ext4", uuid=uuid, model="", ro=False, mountpoints=[],
    )
    if bound:
        volume["pkname"] = "sda"
    target = _disk("sda")
    if nested:
        target["children"] = [volume]
        return {"blockdevices": [_boot(), target]}
    return {"blockdevices": [_boot(), target, volume]}


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", UNKNOWN_TYPES)
@pytest.mark.parametrize("uuid", ("VOLUME-A", "VOLUME-B"))
def test_unknown_type_cannot_discard_unbound_filesystem_evidence(
    fake_machine, route, kind, uuid,  # noqa: F811
):
    try:
        result = fake_machine(_payload(kind, uuid), route)
    except ValueError:
        assert route == "direct"
        return
    assert not result.selectable
    assert not result.boot_identified
    assert result.error


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", UNKNOWN_TYPES)
@pytest.mark.parametrize("nested", (False, True))
def test_proven_unknown_type_ancestry_preserves_changed_filesystem_identity(
    fake_machine, route, kind, nested,  # noqa: F811
):
    old = fake_machine(_payload(kind, "VOLUME-A", bound=not nested, nested=nested), route)
    new = fake_machine(_payload(kind, "VOLUME-B", bound=not nested, nested=nested), route)
    assert old.boot_identified and new.boot_identified
    assert old.selectable[0].contents == new.selectable[0].contents == "data"
    assert disk_identity(old.selectable[0]) != disk_identity(new.selectable[0])


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", ("part", "crypt", "dm", "lvm"))
def test_recognized_unbound_type_remains_refused(fake_machine, route, kind):  # noqa: F811
    try:
        result = fake_machine(_payload(kind, "VOLUME-A"), route)
    except ValueError:
        assert route == "direct"
        return
    assert not result.selectable


@pytest.mark.parametrize("route", ROUTES[1:])
@pytest.mark.parametrize("kind", (0, False, [], {}, 1, True, ["disk"], {"type": "disk"}))
def test_malformed_type_schema_cannot_hide_unbound_layout(
    fake_machine, route, kind,  # noqa: F811
):
    result = fake_machine(_payload(kind, "VOLUME-A"), route)
    assert result.error and not result.boot_identified and not result.selectable


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("size", (0, -1, True, "not-a-size", float("nan")))
def test_unknown_unbound_volume_size_does_not_erase_filesystem_evidence(
    fake_machine, route, size,  # noqa: F811
):
    payload = _payload("unknown", "VOLUME-A")
    payload["blockdevices"][-1]["size"] = size
    try:
        result = fake_machine(payload, route)
    except ValueError:
        assert route == "direct"
        return
    assert result.error and not result.selectable


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", ("loop", "rom", "ram", "unknown"))
def test_unrelated_display_inventory_does_not_remove_valid_targets(
    fake_machine, route, kind,  # noqa: F811
):
    extra = dict(
        name={"loop": "loop0", "rom": "sr0", "ram": "ram0", "unknown": "other0"}[kind],
        type=kind, size=4_194_304, ro=False, mountpoints=[],
    )
    extra["path"] = "/dev/" + extra["name"]
    if kind != "unknown":
        extra.update(fstype="ext4", uuid="irrelevant-standalone-volume")
    result = fake_machine({"blockdevices": [_boot(), _disk("sda"), extra]}, route)
    assert result.boot_identified
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]


@pytest.mark.parametrize("route", ROUTES)
def test_valid_whole_disk_filesystem_keeps_its_layout(fake_machine, route):  # noqa: F811
    payload = {"blockdevices": [_boot(), _disk("sda", fstype="ext4", uuid="VOLUME-A")]}
    result = fake_machine(payload, route)
    assert result.boot_identified
    assert result.selectable[0].contents == "data"
    assert result.selectable[0].layout_id


@pytest.mark.parametrize("route", ROUTES)
def test_null_identity_display_row_keeps_valid_boot_and_target(fake_machine, route):  # noqa: F811
    null_row = dict(
        name=None, path=None, size=None, type=None, label="BEAMO_WIPE",
        ro=False, mountpoints=[],
    )
    result = fake_machine({"blockdevices": [_boot(), _disk("sda"), null_row]}, route)
    assert result.boot_identified and result.boot.path == "/dev/sdz"
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", UNKNOWN_TYPES)
def test_missing_path_cannot_hide_actual_unbound_filesystem_evidence(
    fake_machine, route, kind,  # noqa: F811
):
    payload = _payload(kind, "VOLUME-A")
    payload["blockdevices"][-1].update(name=None, path=None)
    try:
        result = fake_machine(payload, route)
    except ValueError:
        assert route == "direct"
        return
    assert result.error and not result.selectable


@pytest.mark.parametrize("kind", UNKNOWN_TYPES)
def test_locked_final_rescan_refuses_new_unbound_volume_before_process_spawn(
    fake_machine, tmp_path, monkeypatch, kind,  # noqa: F811
):
    before = fake_machine({"blockdevices": [_boot(), _disk("sda")]}, "direct")
    after = fake_machine(_payload(kind, "new-volume"), "production-metadata-stub")
    target = before.selectable[0]
    request = WipeRequest(
        target.path, MethodId.EVERYDAY, before.boot.path, str(tmp_path / "fake.log"),
        device_rdev=8, boot_rdev=16, device_size_bytes=target.size_bytes,
        device_identity=disk_identity(target), boot_identity=disk_identity(before.boot),
    )
    with pytest.raises(SafetyError):
        assert_rediscovered_identity(request, after)
    monkeypatch.setattr("beamo_wipe.discover.discover", lambda: after)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr("beamo_wipe.safety.assert_not_boot", lambda *_a, **_k: None)
    for name in (
        "require_real_live_for_nwipe", "_verify_pinned_nwipe",
        "assert_existing_is_block_device", "assert_size_unchanged",
        "assert_local_device_transport", "assert_not_boot",
    ):
        monkeypatch.setattr(nwipe_runner, name, lambda *_a, **_k: None)
    monkeypatch.setattr(nwipe_runner, "pinned_nwipe_already_running", lambda **_k: False)
    monkeypatch.setattr(nwipe_runner, "block_rdev", lambda path: 8 if path == "/dev/sda" else 16)
    spawn = Mock(return_value=SimpleNamespace())
    monkeypatch.setattr(nwipe_runner.subprocess, "Popen", spawn)
    runner = nwipe_runner.NwipeRunner()
    runner._sleep_inhibit = SimpleNamespace(start=lambda: None, stop=lambda: None)
    try:
        with pytest.raises(SafetyError):
            runner.start(request)
        spawn.assert_not_called()
        assert runner.start_not_spawned()
    finally:
        runner._release_wipe_lock()
