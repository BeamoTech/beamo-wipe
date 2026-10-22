"""Fake by-label link controls; no device or inventory acquisition."""
import os
import posixpath

import pytest

from beamo_wipe import discover as discovery


@pytest.fixture(autouse=True)
def fake_machine_only(monkeypatch):
    realpath = os.path.realpath
    lstat = os.lstat
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **kw:
        posixpath.normpath(os.fspath(p)) if os.fspath(p).startswith(("/dev/", "/sys/"))
        else realpath(p, *a, **kw))
    def fake_lstat(path, *args, **kwargs):
        if os.fspath(path).startswith(("/dev/", "/sys/")):
            raise FileNotFoundError(os.fspath(path))
        return lstat(path, *args, **kwargs)
    monkeypatch.setattr(os, "lstat", fake_lstat)
    def forbidden(*args, **kwargs):
        raise AssertionError("native acquisition forbidden")
    for name in ("run_lsblk", "read_mount_sources", "read_cmdline"):
        monkeypatch.setattr(discovery, name, forbidden)
    monkeypatch.setattr("beamo_wipe.safety.assert_local_device_transport", forbidden)
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *a, **kw: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *a, **kw: None)


def payload(label):
    return {"blockdevices": [
        dict(name="sda", path="/dev/sda", type="disk", size=128_000_000_000,
             tran="sata", serial="TARGET-123", model="Fake target"),
        dict(name="sdb", path="/dev/sdb", type="disk", size=16_000_000_000,
             tran="usb", serial="BOOT-123", model="Fake boot", children=[
                 dict(name="sdb1", path="/dev/sdb1", type="part", pkname="sdb",
                      size=16_000_000_000, label=label, fstype="iso9660")])
    ]}


@pytest.mark.parametrize(("label", "encoded"), [
    ("Live USB", r"Live\x20USB"),
    ("Live-é", r"Live-\xc3\xa9"),
    ("Live-中", r"Live-\xe4\xb8\xad"),
    ("Live-💾", r"Live-\xf0\x9f\x92\xbe"),
])
def test_valid_utf8_udev_label_with_agreeing_link_identifies_boot(monkeypatch, label, encoded):
    source = "/dev/disk/by-label/" + encoded
    synthetic_realpath = os.path.realpath
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **kw:
        "/dev/sdb1" if os.fspath(p) == source else synthetic_realpath(p, *a, **kw))
    found = discovery.discover(lsblk_payload=payload(label), mount_sources=[source], cmdline="", env={})
    assert found.boot_identified, (label, source, discovery._udev_decode(encoded))
    assert found.boot is not None and found.boot.path == "/dev/sdb"
    assert {disk.path for disk in found.selectable} == {"/dev/sda"}
