"""Unresolved physical identities cannot hide protected alias bridges."""

import builtins
import copy
import importlib
import io
import os

import pytest


discovery = importlib.import_module("beamo_wipe.discover")


@pytest.fixture
def scan_fake(monkeypatch):
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("native acquisition")
        raise AssertionError("Injected bridge probe reached native acquisition")

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
                    raise AssertionError("Injected bridge probe consulted a native path")
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

    def scan(rows):
        return discovery.discover(
            lsblk_payload={"blockdevices": copy.deepcopy(rows)},
            mount_sources=["/dev/sdz"], cmdline="", env={},
        )

    yield scan
    assert not attempted


def _disk(name, **changes):
    row = dict(
        name=name, path="/dev/" + name, type="disk", tran="sata", rota=False,
        size=128_000_000_000, model="Fake disk", serial="", wwn="", ro=False,
        mountpoints=[],
    )
    row.update(changes)
    return row


def _bridge(field, values, nested):
    bridge = _disk("sda")
    children = []
    for number, value in enumerate(values, 1):
        partition = dict(
            name=f"sda{number}", path=f"/dev/sda{number}", type="part",
            pkname="sda", size=1_000_000_000, mountpoints=[],
        )
        if nested:
            mapper = f"fake_bridge_{number}"
            partition["children"] = [dict(
                name=mapper, path="/dev/mapper/" + mapper, type="crypt",
                pkname=partition["name"], mountpoints=[], **{field: value},
            )]
        else:
            partition[field] = value
        children.append(partition)
    bridge["children"] = children
    return bridge


def _rows(anchor, field, values, nested, *, protected="SIDE-A", leaf="SIDE-B"):
    boot = _disk("sdz", tran="usb", serial="FAKE-BOOT", size=16_000_000_000)
    source = boot if anchor == "boot" else _disk("sdd", mountpoints=["/media/in-use"])
    source[field] = protected
    bridge = _bridge(field, values, nested)
    target = _disk("sdc", **{field: leaf})
    unrelated = _disk("sdb", serial="FAKE-UNRELATED", size=256_000_000_000)
    rows = [boot, bridge, target, unrelated]
    if anchor == "mounted":
        rows.append(source)
    return rows, source, bridge, target


@pytest.mark.parametrize("anchor", ("boot", "mounted"))
@pytest.mark.parametrize("field", ("serial", "wwn"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("mode", ("protected-conflict", "unrelated", "parent", "consistent"))
def test_ambiguous_descendant_bridge_cannot_discard_exclusion_facts(
    scan_fake, anchor, field, nested, reverse, mode,
):
    values = ["SIDE-A", "SIDE-B"] if mode != "consistent" else ["SIDE-A", "SIDE-A"]
    if reverse:
        values.reverse()
    rows, _source, bridge, target = _rows(
        anchor, field, values, nested,
        protected="PROTECTED" if mode == "unrelated" else "SIDE-A",
        leaf="SIDE-A" if mode == "consistent" else "SIDE-B",
    )
    if mode == "parent":
        bridge[field] = "AUTHORITATIVE-PARENT"
    result = scan_fake(rows)
    paths = {disk.path for disk in result.selectable}
    if mode in {"protected-conflict", "consistent"}:
        assert target["path"] not in paths
    else:
        assert result.boot_identified and not result.error
        assert target["path"] in paths
    if mode != "protected-conflict":
        assert "/dev/sdb" in paths
    if mode == "parent":
        selected = next(d for d in result.selectable if d.path == bridge["path"])
        assert getattr(selected, field) == "AUTHORITATIVE-PARENT"


@pytest.mark.parametrize("anchor", ("boot", "mounted"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("reverse", (False, True))
def test_distinct_authoritative_wwns_still_disambiguate_serial_bridge(
    scan_fake, anchor, nested, reverse,
):
    values = ["SIDE-A", "SIDE-B"]
    if reverse:
        values.reverse()
    rows, source, bridge, target = _rows(anchor, "serial", values, nested)
    source["wwn"] = "0x50014ee20aa00001"
    bridge["wwn"] = "0x50014ee20aa00002"
    result = scan_fake(rows)
    paths = {disk.path for disk in result.selectable}
    assert result.boot_identified and not result.error
    assert target["path"] in paths
    assert "/dev/sdb" in paths


@pytest.mark.parametrize("anchor", ("boot", "mounted"))
@pytest.mark.parametrize("nested", (False, True))
@pytest.mark.parametrize("bad", ("X" * 129, "bad\nidentity", 7, ["SIDE-B"]))
@pytest.mark.parametrize("bad_first", (False, True))
@pytest.mark.parametrize("mode", ("protected", "unrelated", "parent", "contrary-wwn"))
def test_malformed_descendant_does_not_discard_a_valid_cross_field_bridge(
    scan_fake, anchor, nested, bad, bad_first, mode,
):
    values = [bad, "SIDE-A"] if bad_first else ["SIDE-A", bad]
    rows, source, bridge, target = _rows(
        anchor, "serial", values, nested,
        protected="PROTECTED" if mode == "unrelated" else "SIDE-A",
        leaf="OTHER-SERIAL",
    )
    bridge["wwn"] = target["wwn"] = "0x50014ee20aa00002"
    if mode == "parent":
        bridge["serial"] = "AUTHORITATIVE-PARENT"
    elif mode == "contrary-wwn":
        source["wwn"] = "0x50014ee20aa00001"
    result = scan_fake(rows)
    paths = {disk.path for disk in result.selectable}
    if mode == "protected":
        assert target["path"] not in paths
    else:
        assert result.boot_identified and not result.error
        assert target["path"] in paths
        assert "/dev/sdb" in paths
    if mode == "parent":
        selected = next(d for d in result.selectable if d.path == bridge["path"])
        assert selected.serial == "AUTHORITATIVE-PARENT"
