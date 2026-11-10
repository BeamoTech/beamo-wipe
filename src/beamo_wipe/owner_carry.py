# SPDX-License-Identifier: GPL-3.0-or-later
"""Ownership confirmation carried to the next erase in the same app run (#187).

The owner box says "I own this computer and these disks…": it vouches for
the disks that were listed when it was ticked. After Erase another disk, the
next wizard may treat the box as ticked only when its own fresh discovery
lists no erasable disk outside that set. The confirmation lives in memory
in the app's session loop only: a crash, kiosk restart, recovery or reboot
starts unticked. It never replaces a per-disk gate (selection, exact token,
five-second review, Erase now, rediscovery before launch).

Disks are matched by identity (serial, hardware ID, size and model), never
by /dev path. Any disk without a serial or hardware ID, or two disks with
the same identity, fails closed: the box must be ticked again.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from beamo_wipe.models import Disk

DiskKey = Tuple[str, str, int, str]

# Where the tick of the current erase came from (evidence: authorization).
SOURCE_ON_SCREEN = "on_screen"
SOURCE_CARRIED = "carried_over"
SOURCES = frozenset({SOURCE_ON_SCREEN, SOURCE_CARRIED})

# Earlier erases in this app run, shown as a tag on Pick a disk.
ERASED_CHECKED = "checked"  # verified read-back
ERASED_UNCHECKED = "unchecked"  # Quick zero finished, never "verified"
ERASED_UNCONFIRMED = "unconfirmed"  # failed, interrupted or unknown
ERASED_STATES = frozenset({ERASED_CHECKED, ERASED_UNCHECKED, ERASED_UNCONFIRMED})


def _clean(value: object) -> str:
    return " ".join(value.split()).casefold() if isinstance(value, str) else ""


def disk_key(disk: Optional[Disk]) -> Optional[DiskKey]:
    """Identity of a whole disk, or None when it cannot be told apart."""
    if disk is None or disk.is_boot:
        return None
    serial, wwn = _clean(disk.serial), _clean(disk.wwn)
    if not serial and not wwn:
        return None
    try:
        size = int(disk.size_bytes)
    except (TypeError, ValueError):
        return None
    if size <= 0:
        return None
    model = _clean(disk.raw_model if disk.raw_model is not None else disk.model)
    return (serial, wwn, size, model)


def _keys(disks: Iterable[Disk]) -> Optional[list[DiskKey]]:
    keys = []
    for disk in disks:
        key = disk_key(disk)
        if key is None:
            return None
        keys.append(key)
    if not keys or len(set(keys)) != len(keys):
        return None
    return keys


@dataclass(frozen=True)
class OwnerCarry:
    """The disks one on-screen ownership confirmation covered."""

    covered: frozenset[DiskKey]

    def covers(self, disks: Iterable[Disk]) -> bool:
        """True only if every erasable disk listed now was covered."""
        keys = _keys(disks)
        return keys is not None and set(keys) <= self.covered


def capture(disks: Iterable[Disk]) -> Optional[OwnerCarry]:
    """Record what an on-screen tick covered; None when it cannot carry."""
    keys = _keys(disks)
    return None if keys is None else OwnerCarry(frozenset(keys))


@dataclass(frozen=True)
class ErasedMark:
    key: DiskKey
    state: str


def erased_state(result_code: str) -> Optional[str]:
    """Tag state for a finished erase; None when nothing was erased."""
    from beamo_wipe.outcomes import may_have_erased

    if result_code == "verified":
        return ERASED_CHECKED
    if result_code == "unverified":
        return ERASED_UNCHECKED
    if not may_have_erased(result_code):
        return None
    return ERASED_UNCONFIRMED


def add_mark(history: Tuple[ErasedMark, ...], disk: Optional[Disk],
             result_code: str) -> Tuple[ErasedMark, ...]:
    """History plus this erase; the latest erase of a disk wins."""
    key = disk_key(disk)
    state = erased_state(result_code)
    if key is None or state is None:
        return history
    return tuple(m for m in history if m.key != key) + (ErasedMark(key, state),)


def mark_for(history: Tuple[ErasedMark, ...], disk: Optional[Disk]) -> Optional[str]:
    key = disk_key(disk)
    if key is None:
        return None
    for mark in reversed(history):
        if mark.key == key:
            return mark.state
    return None
