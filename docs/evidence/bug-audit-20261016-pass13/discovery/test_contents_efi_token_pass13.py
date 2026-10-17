# SPDX-License-Identifier: GPL-3.0-or-later
"""Ordinary GPT names cannot manufacture EFI/operating-system evidence."""

from __future__ import annotations

import importlib

import pytest

from beamo_wipe import copy as C
from beamo_wipe.models import CONTENTS_DATA, CONTENTS_SYSTEM, CONTENTS_WINDOWS

discovery = importlib.import_module("beamo_wipe.discover")


def _scan(monkeypatch, *, field, name, fstype, shape):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")

    def forbidden(*args, **kwargs):
        raise AssertionError("Injected inventories must not acquire native metadata")

    for acquisition in ("run_lsblk", "read_mount_sources", "read_cmdline"):
        monkeypatch.setattr(discovery, acquisition, forbidden)
    part = {
        "name": "sda1", "path": "/dev/sda1", "type": "part", "pkname": "sda",
        "size": 100_000_000_000, "fstype": fstype, "mountpoints": [], field: name,
    }
    target = {
        "name": "sda", "path": "/dev/sda", "type": "disk", "tran": "sata",
        "size": 128_000_000_000, "serial": "FAKE-TARGET", "ro": False,
        "mountpoints": [],
    }
    boot = {
        "name": "sdb", "path": "/dev/sdb", "type": "disk", "tran": "usb",
        "size": 16_000_000_000, "serial": "FAKE-BOOT", "ro": False,
        "mountpoints": [],
    }
    rows = [target, boot]
    if shape == "tree":
        target["children"] = [part]
    else:
        rows.append(part)
    result = discovery.discover(
        lsblk_payload={"blockdevices": rows}, mount_sources=["/dev/sdb"],
        cmdline="", env={"BEAMO_WIPE_DRY_RUN": "1"},
    )
    assert result.boot_identified and result.boot.path == "/dev/sdb"
    assert [disk.path for disk in result.selectable] == ["/dev/sda"]
    return result.selectable[0]


@pytest.mark.parametrize("shape", ["tree", "flat"])
@pytest.mark.parametrize("fstype", ["ntfs", "ext4"])
@pytest.mark.parametrize("field", ["partlabel", "parttypename"])
@pytest.mark.parametrize("name", ["Benefits", "Definitions"])
def test_efi_letters_inside_ordinary_names_remain_data(monkeypatch, shape, fstype, field, name):
    disk = _scan(monkeypatch, field=field, name=name, fstype=fstype, shape=shape)
    assert disk.contents == CONTENTS_DATA
    assert C.prepare_selected(disk) == C.PREPARE_DATA
    assert C.confirm_warning(disk).endswith(C.PREPARE_DATA)


@pytest.mark.parametrize("shape", ["tree", "flat"])
@pytest.mark.parametrize("fstype,expected", [("ntfs", CONTENTS_WINDOWS), ("ext4", CONTENTS_SYSTEM)])
@pytest.mark.parametrize("field", ["partlabel", "parttypename"])
@pytest.mark.parametrize("name", ["EFI system partition", "UEFI System"])
def test_explicit_efi_names_keep_operating_system_guidance(monkeypatch, shape, fstype, expected, field, name):
    disk = _scan(monkeypatch, field=field, name=name, fstype=fstype, shape=shape)
    assert disk.contents == expected
    expected_copy = C.PREPARE_WINDOWS if expected == CONTENTS_WINDOWS else C.PREPARE_SYSTEM
    assert C.prepare_selected(disk) == expected_copy
    assert C.confirm_warning(disk).endswith(expected_copy)
