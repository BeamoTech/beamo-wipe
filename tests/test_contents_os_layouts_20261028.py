# SPDX-License-Identifier: GPL-3.0-or-later
"""System disks without the usual Windows/EFI marks are not called data.

The pick row names a recognised system and stays silent otherwise, so a
legacy-BIOS install or an Intel Mac must not be shown as a disk without an
operating system. Fake lsblk nodes only; nothing is opened or erased."""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.discover import classify_contents, node_to_disk

EFI_TYPE = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
BIOS_BOOT_TYPE = "21686148-6449-6e6f-744e-656564454649"


def _part(path, **fields):
    node = {"name": path.rsplit("/", 1)[-1], "path": path, "type": "part", "size": 1_000_000_000}
    node.update(fields)
    return node


def _disk(*children, **fields):
    node = {
        "name": "sda", "path": "/dev/sda", "type": "disk", "size": 500_000_000_000,
        "tran": "sata", "rota": False, "model": "Fake Disk", "serial": "FAKE-SERIAL",
        "children": list(children),
    }
    node.update(fields)
    return node


def _efi(path="/dev/sda1"):
    return _part(path, fstype="vfat", label="EFI", parttype=EFI_TYPE)


SYSTEM_LAYOUTS = {
    "intel-mac-apfs": _disk(_efi(), _part("/dev/sda2", fstype="apfs")),
    "intel-mac-hfsplus": _disk(_efi(), _part("/dev/sda2", fstype="hfsplus", label="Macintosh HD")),
    "bios-linux-mbr-swap": _disk(
        _part("/dev/sda1", fstype="ext4"), _part("/dev/sda2", fstype="swap"),
    ),
    "bios-linux-gpt-bios-boot": _disk(
        _part("/dev/sda1", parttype=BIOS_BOOT_TYPE), _part("/dev/sda2", fstype="ext4"),
    ),
    "linux-vendor-recovery": _disk(
        _efi(), _part("/dev/sda2", fstype="vfat", label="RECOVERY"),
        _part("/dev/sda3", fstype="ext4"),
    ),
    "bios-linux-vendor-recovery": _disk(
        _part("/dev/sda1", fstype="vfat", label="RECOVERY"), _part("/dev/sda2", fstype="ext4"),
    ),
}

WINDOWS_LAYOUTS = {
    # A Windows recovery drive made by Windows itself: FAT32 "RECOVERY" only.
    "windows-recovery-drive": _disk(_part("/dev/sda1", fstype="vfat", label="RECOVERY")),
    "ntfs-recovery-beside-linux": _disk(
        _part("/dev/sda1", fstype="ntfs", label="Recovery"), _part("/dev/sda2", fstype="ext4"),
    ),
    "windows-efi": _disk(_efi(), _part("/dev/sda2", fstype="ntfs")),
}

DATA_LAYOUTS = {
    "ext4-only": _disk(_part("/dev/sda1", fstype="ext4", label="backup")),
    "exfat-photos": _disk(_part("/dev/sda1", fstype="exfat", label="PHOTOS")),
    "swap-without-root": _disk(_part("/dev/sda1", fstype="swap")),
    "apfs-without-efi": _disk(_part("/dev/sda1", fstype="apfs")),
    "whole-disk-ntfs": _disk(fstype="ntfs", label="Windows"),
}


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


@pytest.mark.parametrize("name", sorted(SYSTEM_LAYOUTS))
def test_system_layouts_are_named_as_an_operating_system(name):
    node = SYSTEM_LAYOUTS[name]
    assert classify_contents(node) == "system"
    disk = node_to_disk(node, False)
    assert C.contents_hint(disk) == C.CONTENTS_HINT_SYSTEM
    assert C.prepare_selected(disk) == C.PREPARE_SYSTEM


@pytest.mark.parametrize("name", sorted(WINDOWS_LAYOUTS))
def test_windows_marks_still_name_windows(name):
    node = WINDOWS_LAYOUTS[name]
    assert classify_contents(node) == "windows"
    assert C.contents_hint(node_to_disk(node, False)) == C.CONTENTS_HINT_WINDOWS


@pytest.mark.parametrize("name", sorted(DATA_LAYOUTS))
def test_unrecognised_layouts_stay_data_and_claim_nothing(name):
    node = DATA_LAYOUTS[name]
    assert classify_contents(node) == "data"
    disk = node_to_disk(node, False)
    # The confirm text stays detection-relative; the pick row says nothing.
    assert C.prepare_selected(disk) == C.PREPARE_DATA
    assert C.contents_hint(disk) == ""


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_no_pick_hint_claims_that_a_disk_has_no_system(code):
    lang.set_language(code)
    hints = [C.contents_hint(node_to_disk(node, False)) for node in DATA_LAYOUTS.values()]
    assert hints == [""] * len(DATA_LAYOUTS)
    for name in ("CONTENTS_HINT_WINDOWS", "CONTENTS_HINT_SYSTEM"):
        text = getattr(C, name).casefold()
        assert not text.startswith(("no ", "aucun", "kein", "nessun")), text
