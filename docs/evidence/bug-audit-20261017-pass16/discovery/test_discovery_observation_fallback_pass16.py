"""Unusable duplicate rows and optical fallback cannot manufacture safe identity."""

import builtins
import copy
import importlib
import io
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
ROUTES = ("direct", "injected", "production-metadata-stub")
PUBLIC_ROUTES = ROUTES[1:]
ORDERS = (False, True)
MALFORMED = {
    "long-model": ("model", "M" * 129),
    "long-vendor": ("vendor", "V" * 129),
    "long-label": ("label", "L" * 129),
    "control-model": ("model", "Fake\nmodel"),
    "control-vendor": ("vendor", "Fake\nvendor"),
    "control-label": ("label", "Fake\nlabel"),
}
# Every conflict survives in a different, valid field from the malformed one.
PAIRS = (
    ("long-model", "vendor", "Another vendor"),
    ("long-model", "uuid", "another-uuid"),
    ("long-model", "partuuid", "another-partuuid"),
    ("long-model", "label", "another-label"),
    ("long-model", "partlabel", "another-partlabel"),
    ("long-model", "fstype", "ext4"),
    ("long-model", "parttype", "another-parttype"),
    ("long-vendor", "model", "Another model"),
    ("long-vendor", "uuid", "another-uuid"),
    ("long-label", "model", "Another model"),
    ("long-label", "vendor", "Another vendor"),
    ("control-model", "uuid", "another-uuid"),
    ("control-vendor", "uuid", "another-uuid"),
    ("control-label", "uuid", "another-uuid"),
)


@pytest.fixture
def fake_machine(monkeypatch):
    """Every route has fake metadata and cannot acquire a host device/process."""
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("native acquisition")
        raise AssertionError("Fake discovery reached native acquisition")

    realpath = os.path.realpath

    def fake_realpath(path, *args, **kwargs):
        text = os.fspath(path)
        if text.startswith(("/dev/", "/sys/", "/proc/")):
            return text
        return realpath(path, *args, **kwargs)

    def guarded(original):
        def checked(path, *args, **kwargs):
            if not isinstance(path, int):
                text = os.fsdecode(path)
                if text in {"/dev", "/sys", "/proc"} or text.startswith(
                    ("/dev/", "/sys/", "/proc/")
                ):
                    attempted.append(text)
                    raise AssertionError("Fake discovery read a native path")
            return original(path, *args, **kwargs)
        return checked

    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
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

    def scan(payload, route, *, boot="/dev/sdz", mounts=None, cmdline=""):
        payload = copy.deepcopy(payload)
        mounts = [boot] if mounts is None else mounts
        if route == "direct":
            return discovery.parse_lsblk_json(payload, boot_path=boot)
        if route == "injected":
            return discovery.discover(
                lsblk_payload=payload, mount_sources=mounts, cmdline=cmdline, env={},
            )
        assert route == "production-metadata-stub"
        # env={} deliberately runs the production schema gate. The process-wide
        # preview guard and acquisition guards prevent sysfs/device effects.
        checked = []
        validate = discovery._validate_real_lsblk_metadata

        def validate_and_record(value):
            checked.append(value)
            validate(value)

        with monkeypatch.context() as local:
            local.setattr(discovery, "run_lsblk", lambda: payload)
            local.setattr(discovery, "_validate_real_lsblk_metadata", validate_and_record)
            result = discovery.discover(mount_sources=mounts, cmdline=cmdline, env={})
        assert checked == [payload]
        return result

    yield scan
    assert not attempted


def _disk(name, **changes):
    row = dict(
        name=name, path="/dev/" + name, type="disk", tran="sata", rota=False,
        size=128_000_000_000, serial="FAKE-" + name, wwn="50014ee20" + name,
        model="Fake disk", vendor="Fake vendor", ro=False, mountpoints=[],
    )
    row.update(changes)
    return row


def _boot():
    return _disk(
        "sdz", size=16_000_000_000, tran="usb", mountpoints=["/run/live/medium"],
    )


def _target():
    return _disk(
        "sda", fstype="ntfs", uuid="original-uuid", partuuid="original-partuuid",
        label="original-label", partlabel="original-partlabel", parttype="original-parttype",
    )


def _assert_duplicate_refused(scan, payload, route):
    try:
        result = scan(payload, route)
    except ValueError:
        # The low-level parser may reject malformed inventory. Public discover
        # owns exception-to-empty-result handling and must return normally.
        assert route == "direct"
        return
    assert "/dev/sda" not in {disk.path for disk in result.selectable}
    if result.error:
        assert not result.boot_identified and not result.selectable


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("reverse", ORDERS)
@pytest.mark.parametrize("omission,field,value", PAIRS)
def test_malformed_duplicate_cannot_hide_another_identity_conflict(
    fake_machine, route, reverse, omission, field, value,
):
    first = _target()
    second = copy.deepcopy(first)
    second[field] = value
    malformed_field, malformed_value = MALFORMED[omission]
    assert malformed_field != field
    second[malformed_field] = malformed_value
    pair = [first, second]
    if reverse:
        pair.reverse()
    _assert_duplicate_refused(fake_machine, {"blockdevices": [_boot(), *pair]}, route)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("reverse", ORDERS)
@pytest.mark.parametrize("omission", tuple(MALFORMED))
def test_unusable_same_path_copy_cannot_manufacture_unique_target(
    fake_machine, route, reverse, omission,
):
    first = _target()
    second = copy.deepcopy(first)
    field, value = MALFORMED[omission]
    second[field] = value
    pair = [first, second]
    if reverse:
        pair.reverse()
    _assert_duplicate_refused(fake_machine, {"blockdevices": [_boot(), *pair]}, route)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("reverse", ORDERS)
@pytest.mark.parametrize("duplicate_kind", ("target", "boot", "read-only"))
def test_identical_valid_duplicates_preserve_existing_refusal_and_peer_behavior(
    fake_machine, route, reverse, duplicate_kind,
):
    rows = [_boot(), _target()]
    if duplicate_kind == "target":
        rows.append(copy.deepcopy(rows[1]))
    elif duplicate_kind == "boot":
        rows.append(copy.deepcopy(rows[0]))
    else:
        readonly = _disk("sdc", ro=True)
        rows.extend([readonly, copy.deepcopy(readonly)])
    if reverse:
        rows.reverse()
    result = fake_machine({"blockdevices": rows}, route)
    assert result.boot_identified and not result.error
    assert_boot_excluded(result)
    targets = [disk for disk in result.selectable if disk.path == "/dev/sda"]
    assert len(targets) == (2 if duplicate_kind == "target" else 1)
    if duplicate_kind == "target":
        with pytest.raises(SafetyError):
            assert_disk_identity(targets[0], result)
    else:
        assert_disk_identity(targets[0], result)
        assert confirm_spec(targets[0], listed_disks(result)).token


@pytest.mark.parametrize("route", ROUTES)
def test_clean_retry_after_filtered_duplicate_recovers(fake_machine, route):
    first = _target()
    second = copy.deepcopy(first)
    second.update(uuid="different-uuid", model="M" * 129)
    _assert_duplicate_refused(fake_machine, {"blockdevices": [_boot(), first, second]}, route)
    clean = fake_machine({"blockdevices": [_boot(), _target()]}, route)
    assert clean.boot_identified and not clean.error
    assert [disk.path for disk in clean.selectable] == ["/dev/sda"]
    assert_disk_identity(clean.selectable[0], clean)
    assert_boot_excluded(clean)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("omission", tuple(MALFORMED))
def test_unrelated_malformed_observation_does_not_hide_a_unique_target(
    fake_machine, route, omission,
):
    malformed = _disk("sdc")
    field, value = MALFORMED[omission]
    malformed[field] = value
    result = fake_machine({"blockdevices": [_boot(), _target(), malformed]}, route)
    assert result.boot_identified and not result.error
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]
    assert_disk_identity(result.selectable[0], result)
    assert_boot_excluded(result)


@pytest.mark.parametrize("route", PUBLIC_ROUTES)
@pytest.mark.parametrize("reverse", ORDERS)
@pytest.mark.parametrize("mounted", (False, True))
@pytest.mark.parametrize("source_form", ("device", "label", "uuid"))
@pytest.mark.parametrize("competitor_size", (0, 128_000_000_000))
@pytest.mark.parametrize("competitor_kind", ("disk", "rom"))
@pytest.mark.parametrize("hit_kind", ("disk", "rom"))
def test_cmdline_fallback_considers_every_physical_medium(
    fake_machine, route, reverse, mounted, source_form, competitor_size,
    competitor_kind, hit_kind,
):
    hit_name = "sdz" if hit_kind == "disk" else "sr0"
    other_name = "sda" if competitor_kind == "disk" else "sr1"
    hit = _disk(
        hit_name, type=hit_kind, tran="usb", ro=hit_kind == "rom",
        size=16_000_000_000, label="FAKE-LIVE", uuid="fake-live-uuid",
    )
    other = _disk(other_name, type=competitor_kind, size=competitor_size,
                  ro=competitor_kind == "rom")
    source = {
        "device": hit["path"], "label": "LABEL=FAKE-LIVE", "uuid": "UUID=fake-live-uuid",
    }[source_form]
    rows = [hit, other]
    if reverse:
        rows.reverse()
    mounts = [hit["path"]] if mounted else []
    cmdline = "boot=live live-media=" + source
    expected = mounted or competitor_size == 0
    # Contrast the resolver's direct contract with both public parsing routes.
    identified = discovery.identify_boot_path(
        rows, mount_sources=mounts, cmdline=cmdline, require_device_link=False,
    )
    assert identified == (hit["path"] if expected else None)
    result = fake_machine(
        {"blockdevices": rows}, route, boot=hit["path"], mounts=mounts, cmdline=cmdline,
    )
    assert result.boot_identified is expected
    if expected:
        assert result.boot is not None and result.boot.path == hit["path"]
        assert not result.error
        allowed = [other["path"]] if competitor_kind == "disk" and competitor_size else []
        assert [disk.path for disk in result.selectable] == allowed
        assert_boot_excluded(result)
        for target in result.selectable:
            assert_disk_identity(target, result)
            assert confirm_spec(target, listed_disks(result)).token
    else:
        assert result.boot is None and result.error and not result.selectable
