# SPDX-License-Identifier: GPL-3.0-or-later
"""Production boot aliases must name a stable, live block-device link."""

from __future__ import annotations

import os
import stat
from types import SimpleNamespace

import pytest

from beamo_wipe.discover import identify_boot_path


ALIASES = (
    ("/dev/disk/by-label/", "label"),
    ("/dev/disk/by-uuid/", "uuid"),
    ("/dev/disk/by-partuuid/", "partuuid"),
    ("/dev/disk/by-partlabel/", "partlabel"),
)


def _inventory(field: str):
    partition = {
        "name": "sdb1",
        "path": "/dev/sdb1",
        "type": "part",
        "pkname": "sdb",
        "mountpoints": [],
        field: "LIVE-ID",
    }
    return [
        {
            "name": "sda",
            "path": "/dev/sda",
            "type": "disk",
            "size": 500_000_000_000,
            "tran": "sata",
            "serial": "TARGET",
            "ro": 0,
            "mountpoints": [],
            "children": [
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "type": "part",
                    "pkname": "sda",
                    "mountpoints": [],
                }
            ],
        },
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "type": "disk",
            "size": 16_000_000_000,
            "tran": "usb",
            "serial": "BOOT",
            "ro": 0,
            "mountpoints": [],
            "children": [partition],
        },
    ]


def _stat_result(
    kind: int,
    *,
    inode: int,
    rdev: int = 0,
    nlink: int = 1,
    uid: int = 0,
    mtime_ns: int = 1,
    ctime_ns: int = 1,
):
    return SimpleNamespace(
        st_mode=kind | 0o600,
        st_ino=inode,
        st_dev=1,
        st_nlink=nlink,
        st_uid=uid,
        st_gid=0,
        st_size=0,
        st_rdev=rdev,
        st_mtime_ns=mtime_ns,
        st_ctime_ns=ctime_ns,
    )


def _install_link_fakes(monkeypatch, alias: str, state: str, *, owner: str = "sdb"):
    real_realpath = os.path.realpath
    real_lstat = os.lstat
    real_stat = os.stat
    real_readlink = os.readlink
    target = f"/dev/{owner}1"
    link_stat = _stat_result(stat.S_IFLNK, inode=41)
    regular_stat = _stat_result(stat.S_IFREG, inode=42)
    block_stat = _stat_result(stat.S_IFBLK, inode=43, rdev=2049)
    replaced_block = _stat_result(stat.S_IFBLK, inode=44, rdev=2050)
    mutated_block = _stat_result(
        stat.S_IFBLK,
        inode=43,
        rdev=2049,
        nlink=2,
        uid=7,
        mtime_ns=2,
        ctime_ns=2,
    )
    target_stat_calls = 0
    realpath_calls = 0

    def fake_realpath(path):
        nonlocal realpath_calls
        if str(path) == alias:
            realpath_calls += 1
            if state == "late_resolve" and realpath_calls > 1:
                return "/dev/sda1"
            return target
        return real_realpath(path)

    def fake_lstat(path, *args, **kwargs):
        if str(path) != alias:
            return real_lstat(path, *args, **kwargs)
        if state == "missing":
            raise FileNotFoundError(alias)
        if state == "regular":
            return regular_stat
        return link_stat

    def fake_stat(path, *args, **kwargs):
        nonlocal target_stat_calls
        if str(path) not in {alias, target}:
            return real_stat(path, *args, **kwargs)
        target_stat_calls += 1
        if state == "dangling":
            raise FileNotFoundError(target)
        if state == "nonblock":
            return regular_stat
        if state == "late_replace" and target_stat_calls > 2:
            return replaced_block
        if state == "late_metadata" and target_stat_calls > 2:
            return mutated_block
        return block_stat

    def fake_readlink(path, *args, **kwargs):
        if str(path) == alias:
            if state == "missing":
                raise FileNotFoundError(alias)
            if state == "regular":
                raise OSError("not a symbolic link")
            return f"../../{owner}1"
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_realpath)
    monkeypatch.setattr(os, "lstat", fake_lstat)
    monkeypatch.setattr(os, "stat", fake_stat)
    monkeypatch.setattr(os, "readlink", fake_readlink)


@pytest.mark.parametrize("prefix,field", ALIASES)
@pytest.mark.parametrize("state", ("missing", "dangling", "regular", "nonblock"))
def test_production_typed_boot_source_requires_live_block_symlink(
    monkeypatch, prefix, field, state
):
    alias = prefix + "LIVE-ID"
    _install_link_fakes(monkeypatch, alias, state)

    assert (
        identify_boot_path(
            _inventory(field),
            mount_sources=[alias],
            cmdline="boot=live",
            require_device_link=True,
        )
        is None
    )


@pytest.mark.parametrize("prefix,field", ALIASES)
def test_valid_typed_boot_source_link_still_identifies_its_block_owner(
    monkeypatch, prefix, field
):
    alias = prefix + "LIVE-ID"
    _install_link_fakes(monkeypatch, alias, "valid")

    assert (
        identify_boot_path(
            _inventory(field),
            mount_sources=[alias],
            cmdline="boot=live",
            require_device_link=True,
        )
        == "/dev/sdb"
    )


@pytest.mark.parametrize("prefix,field", ALIASES)
def test_valid_typed_link_must_still_agree_with_reported_identifier_owner(
    monkeypatch, prefix, field
):
    alias = prefix + "LIVE-ID"
    _install_link_fakes(monkeypatch, alias, "valid", owner="sda")

    assert (
        identify_boot_path(
            _inventory(field),
            mount_sources=[alias],
            cmdline="boot=live",
            require_device_link=True,
        )
        is None
    )


@pytest.mark.parametrize("prefix,field", ALIASES[:2])
@pytest.mark.parametrize("state", ("late_replace", "late_metadata", "late_resolve"))
def test_typed_boot_target_must_survive_the_final_snapshot_boundary(
    monkeypatch, prefix, field, state
):
    alias = prefix + "LIVE-ID"
    _install_link_fakes(monkeypatch, alias, state)

    assert (
        identify_boot_path(
            _inventory(field),
            mount_sources=[alias],
            cmdline="boot=live",
            require_device_link=True,
        )
        is None
    )
