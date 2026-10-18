"""Inherited physical IDs must not discard competing descendant observations."""

import builtins
import copy
import importlib
import io
import os

import pytest


discovery = importlib.import_module("beamo_wipe.discover")


@pytest.fixture
def fake_inventory(monkeypatch):
    """All disk/sysfs/process operations are forbidden for these injected scans."""
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("native acquisition")
        raise AssertionError("Injected discovery reached native acquisition")

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
                if text in {"/dev", "/proc", "/sys"} or text.startswith(
                    ("/dev/", "/proc/", "/sys/")
                ):
                    attempted.append(text)
                    raise AssertionError("Injected discovery consulted a native path")
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
    for name in ("open", "lstat"):
        monkeypatch.setattr(os, name, guarded(getattr(os, name)))
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None)

    def scan(payload):
        return discovery.discover(
            lsblk_payload=copy.deepcopy(payload), mount_sources=["/dev/sdz"],
            cmdline="", env={},
        )

    yield scan
    assert not attempted


def _disk(name, size, **changes):
    row = dict(
        name=name, path="/dev/" + name, type="disk", tran="sata", rota=False,
        size=size, model="Fake disk", serial="", wwn="", ro=False,
        mountpoints=[],
    )
    row.update(changes)
    return row


def _children(name, field, values, nested):
    children = []
    for number, value in enumerate(values, 1):
        partition = dict(
            name=f"{name}{number}", path=f"/dev/{name}{number}", type="part",
            pkname=name, size=1_000_000_000, mountpoints=[],
        )
        if nested:
            mapper = f"fake_{name}_{number}"
            partition["children"] = [dict(
                name=mapper, path="/dev/mapper/" + mapper, type="crypt",
                pkname=partition["name"], mountpoints=[], **{field: value},
            )]
        else:
            partition[field] = value
        children.append(partition)
    return children


def _machine(anchor, field, values, *, missing="", nested=False, parent=None):
    boot = _disk("sdz", 16_000_000_000, tran="usb", serial="FAKE-BOOT")
    name = "sdz" if anchor == "boot" else "sda"
    observed = _disk(
        name, 16_000_000_000 if anchor == "boot" else 128_000_000_000,
        **{field: missing},
    )
    if parent is not None:
        observed[field] = parent
    observed["children"] = _children(name, field, values, nested)
    if anchor == "boot":
        observed["tran"] = "usb"
        boot = observed
    elif anchor == "mounted":
        observed["mountpoints"] = ["/media/in-use"]
    alias = _disk("sdc", 128_000_000_000, **{field: "SIDE-B"})
    unrelated = _disk("sdb", 256_000_000_000, serial="FAKE-UNRELATED")
    rows = [boot, alias, unrelated]
    if anchor != "boot":
        rows.append(observed)
    return {"blockdevices": rows}, observed, alias


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("missing", (None, ""))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("reverse", (False, True))
def test_conflicting_inherited_ids_cannot_expose_a_target(
    fake_inventory, anchor, field, missing, nested, reverse,
):
    values = ["SIDE-A", "SIDE-B"]
    if reverse:
        values.reverse()
    payload, observed, alias = _machine(
        anchor, field, values, missing=missing, nested=nested,
    )
    result = fake_inventory(payload)
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        assert observed["path"] not in paths
        # A malformed target must not erase an independent sibling's identity.
        assert "/dev/sdb" in paths
    else:
        assert alias["path"] not in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("bad", ("X" * 129, "bad\nidentity", 7, ["SIDE-B"]))
@pytest.mark.parametrize("bad_first", (False, True))
def test_later_malformed_inherited_id_is_not_silently_dropped(
    fake_inventory, anchor, field, nested, bad, bad_first,
):
    values = [bad, "SIDE-A"] if bad_first else ["SIDE-A", bad]
    payload, observed, _alias = _machine(anchor, field, values, nested=nested)
    result = fake_inventory(payload)
    paths = {disk.path for disk in result.selectable}
    if anchor == "boot":
        assert not result.boot_identified
        assert not paths
    elif anchor == "mounted":
        assert not paths
    else:
        assert observed["path"] not in paths
        assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("values", (("", "SIDE-B"), ("SIDE-B", "SIDE-B")))
def test_consistent_fallback_keeps_normal_physical_identity(
    fake_inventory, anchor, field, nested, values,
):
    payload, observed, alias = _machine(anchor, field, values, nested=nested)
    result = fake_inventory(payload)
    assert result.boot_identified and not result.error
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        selected = next(disk for disk in result.selectable if disk.path == observed["path"])
        assert getattr(selected, field) == "SIDE-B"
    else:
        assert alias["path"] not in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("reverse", (False, True))
def test_reported_parent_id_remains_authoritative(
    fake_inventory, anchor, field, nested, reverse,
):
    values = ["SIDE-A", "SIDE-B"]
    if reverse:
        values.reverse()
    payload, observed, alias = _machine(
        anchor, field, values, nested=nested, parent="PARENT-ID",
    )
    alias[field] = "PARENT-ID"
    result = fake_inventory(payload)
    assert result.boot_identified and not result.error
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        selected = next(disk for disk in result.selectable if disk.path == observed["path"])
        assert getattr(selected, field) == "PARENT-ID"
    else:
        assert alias["path"] not in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("placeholder", ("0000", "0x0000", "unknown", "N/A"))
@pytest.mark.parametrize("placeholder_first", (False, True))
def test_placeholder_sibling_does_not_mask_meaningful_fallback(
    fake_inventory, anchor, field, nested, placeholder, placeholder_first,
):
    values = [placeholder, "SIDE-B"] if placeholder_first else ["SIDE-B", placeholder]
    payload, observed, alias = _machine(anchor, field, values, nested=nested)
    result = fake_inventory(payload)
    assert result.boot_identified and not result.error
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        selected = next(disk for disk in result.selectable if disk.path == observed["path"])
        assert getattr(selected, field) == "SIDE-B"
    else:
        assert alias["path"] not in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("field,values", (
    ("serial", ("SIDE-B", "side-b")),
    ("wwn", ("SIDE-B", "side-b")),
    ("wwn", ("0xSIDE-B", "SIDE-B")),
))
def test_equivalent_child_wwns_do_not_create_false_ambiguity(
    fake_inventory, anchor, field, nested, values,
):
    payload, observed, alias = _machine(anchor, field, values, nested=nested)
    result = fake_inventory(payload)
    assert result.boot_identified and not result.error
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        assert observed["path"] in paths
    else:
        assert alias["path"] not in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted", "target"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("placeholder", ("0000", "0x0000", "unknown", "N/A"))
def test_placeholder_parent_does_not_hide_meaningful_descendant_identity(
    fake_inventory, anchor, field, nested, placeholder,
):
    payload, observed, alias = _machine(
        anchor, field, ("SIDE-B", "SIDE-B"), nested=nested, parent=placeholder,
    )
    result = fake_inventory(payload)
    assert result.boot_identified and not result.error
    paths = {disk.path for disk in result.selectable}
    if anchor == "target":
        selected = next(disk for disk in result.selectable if disk.path == observed["path"])
        assert getattr(selected, field) == "SIDE-B"
    else:
        assert alias["path"] not in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("placeholder", ("0000", "0x0000", "unknown", "N/A"))
def test_parent_placeholder_raw_identity_survives_without_better_descendants(
    fake_inventory, field, placeholder,
):
    payload, observed, _alias = _machine(
        "target", field, (None, ""), parent=placeholder,
    )
    result = fake_inventory(payload)
    selected = next(disk for disk in result.selectable if disk.path == observed["path"])
    assert getattr(selected, field) == placeholder
