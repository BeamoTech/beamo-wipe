"""Formatting inference cannot replace an uncertain or aliased boot source."""

import os
import errno

import pytest

from beamo_wipe.discover import discover, normalize_mount_source
from test_excluded_inventory import node


def _scan(source):
    payload = {"blockdevices": [
        node("sda", children=[node("sda1", type="part", pkname="sda")]),
        node("sdb", tran="usb", label="BEAMO_WIPE", children=[
            node("sdb1", type="part", pkname="sdb"),
        ]),
    ]}
    return discover(
        lsblk_payload=payload, mount_sources=[source], cmdline="",
        env={"BEAMO_WIPE_DRY_RUN": "1"},
    )


@pytest.mark.parametrize("prefix", ["sda1", "/dev/sda1"])
@pytest.mark.parametrize("suffix", ["[unfinished", "[subvolume]junk", "[]"])
def test_malformed_annotation_cannot_invent_boot_identity(prefix, suffix):
    source = prefix + suffix
    assert normalize_mount_source(source) == source
    result = _scan(source)
    assert not result.boot_identified
    assert result.error
    assert result.selectable == ()


@pytest.mark.parametrize("prefix", ["sda1", "/dev/sda1"])
@pytest.mark.parametrize("suffix", ["[data]", "[/live/image]", "[/name[rev2]]"])
def test_complete_subvolume_annotation_keeps_kernel_source(prefix, suffix):
    source = prefix + suffix
    assert normalize_mount_source(source) == "/dev/sda1"
    result = _scan(source)
    assert result.boot_identified
    assert result.boot.path == "/dev/sda"
    assert [disk.path for disk in result.selectable] == ["/dev/sdb"]


@pytest.mark.parametrize("suffix", ["[rev2]", "[unfinished", "[subvolume]junk"])
def test_actual_kernel_prefixed_alias_wins_over_annotation_guess(monkeypatch, suffix):
    source = "/dev/sda1" + suffix
    original_realpath = os.path.realpath

    def resolve(path):
        return "/dev/sdb1" if str(path) == source else original_realpath(path)

    monkeypatch.setattr(os.path, "realpath", resolve)
    assert normalize_mount_source(source) == source
    result = _scan(source)
    assert result.boot_identified
    assert result.boot.path == "/dev/sdb"
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]


def test_alias_resolution_error_cannot_fall_back_to_shortened_source(monkeypatch):
    source = "/dev/sda1[rev2]"
    original_realpath = os.path.realpath

    def resolve(path):
        if str(path) == source:
            raise OSError("fake unreadable alias")
        return original_realpath(path)

    monkeypatch.setattr(os.path, "realpath", resolve)
    result = _scan(source)
    assert not result.boot_identified
    assert result.error
    assert result.selectable == ()


def test_existing_source_with_unchanged_realpath_is_not_an_annotation(tmp_path, monkeypatch):
    source = "/dev/sda1[rev2]"
    fixture = tmp_path / "existing-source"
    fixture.write_text("fake source path")
    original_lstat, original_realpath = os.lstat, os.path.realpath

    def lstat(path, *args, **kwargs):
        return original_lstat(fixture) if str(path) == source else original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(
        os.path, "realpath",
        lambda path: source if str(path) == source else original_realpath(path),
    )
    assert normalize_mount_source(source) == source
    result = _scan(source)
    assert not result.boot_identified
    assert result.selectable == ()


def test_source_lookup_permission_error_cannot_invent_annotation(monkeypatch):
    source = "/dev/sda1[rev2]"
    original_lstat, original_realpath = os.lstat, os.path.realpath

    def lstat(path, *args, **kwargs):
        if str(path) == source:
            raise PermissionError(errno.EACCES, "fake source lookup denied")
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(
        os.path, "realpath",
        lambda path: source if str(path) == source else original_realpath(path),
    )
    result = _scan(source)
    assert not result.boot_identified
    assert result.error
    assert result.selectable == ()
