# SPDX-License-Identifier: GPL-3.0-or-later
"""Pick-list order (#151): internal disks first, then external, stable.

Presentation order only. Every view lists eligible disks in this order and
Up/Down follows it, but selection, confirmation and launch stay bound to the
disk itself (its path and recorded identity), never to a list position. The
protected Beamo USB is not part of this list; each view keeps it where it was.

The key depends only on facts about each disk, never on the order lsblk
returned them in, so "Check disks again" over the same disks gives the same
order. Groups, in order:

0. a proven internal transport (NVMe, SATA, SAS, virtio) that the kernel does
   not report as removable or hot-pluggable;
1. the same transports reported removable/hot-pluggable: an eSATA dock, a
   USB-to-SATA/NVMe enclosure or a hot-swap bay; location is not guessed
   (identity.py says so on the card), so they follow the proven internal disks;
2. any other transport that is still eligible (not proven either way);
3. USB.

Within a group: bus (NVMe, SATA, SAS, virtio, then others by name), model,
serial, WWN, capacity, and the device path last so the order is total even for
two disks that report identical identity.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from beamo_wipe.models import Disk

INTERNAL_BUSES: Tuple[str, ...] = ("NVMe", "SATA", "SAS", "virtio")
EXTERNAL_BUSES: Tuple[str, ...] = ("USB",)

GROUP_INTERNAL = 0
GROUP_HOTPLUG = 1
GROUP_OTHER = 2
GROUP_EXTERNAL = 3


def location_group(disk: Disk) -> int:
    bus = disk.bus or ""
    if bus in EXTERNAL_BUSES:
        return GROUP_EXTERNAL
    if bus in INTERNAL_BUSES:
        return GROUP_HOTPLUG if disk.hotplug else GROUP_INTERNAL
    return GROUP_OTHER


def pick_sort_key(disk: Disk) -> tuple:
    bus = disk.bus or ""
    rank = INTERNAL_BUSES.index(bus) if bus in INTERNAL_BUSES else len(INTERNAL_BUSES)
    return (
        location_group(disk),
        rank,
        bus.casefold(),
        (disk.model or "").casefold(),
        disk.serial or "",
        disk.wwn or "",
        disk.size_bytes,
        disk.path,
    )


def pick_order(disks: Iterable[Disk]) -> Tuple[Disk, ...]:
    """The eligible disks in pick-list order. Never filters or adds a disk."""
    return tuple(sorted(disks, key=pick_sort_key))
