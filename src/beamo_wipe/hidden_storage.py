# SPDX-License-Identifier: GPL-3.0-or-later
"""Why the disk list is empty: Intel VMD or RST RAID mode (#185). Advisory only.

When no disk can be selected, an Intel storage controller in VMD or RAID
(RST) mode is a common reason the computer's own disk is missing. This
module names that case so the empty screen can show specific BIOS/UEFI
steps instead of the generic paragraph.

Read-only and display-only:

- It reads PCI identity files from sysfs (``vendor``, ``device``, ``class``
  and the ``driver`` link under ``/sys/bus/pci/devices/*``) and nothing
  else. It never writes sysfs, changes driver binding, kernel parameters or
  firmware, and it starts no process. The live image deliberately ships
  without ``pciutils`` (``scripts/qemu-verify.sh``), so ``lspci`` output is
  only parsed when a caller already has it (preview fixtures, tests).
- It never creates, removes or changes a disk. ``safety.py`` and
  ``discover.py`` own eligibility and boot exclusion; this result is only a
  choice between two texts on a screen that already lists no disk.
- It fails closed to the generic text: an unreadable or malformed entry, a
  visible NVMe controller, another RAID controller, an unknown Intel RAID
  device, or any disk other than the Beamo USB in discovery all give "".

Device IDs come from the Linux kernel's own driver tables:

- Intel VMD: ``vmd_ids[]`` in ``drivers/pci/controller/vmd.c``. v6.12 (the
  live image's LTS kernel line) lists 201d, 28c0, 467f, 4c3d, a77f, 7d0b,
  ad0b and 9a0b (named IDs from ``include/linux/pci_ids.h``). Mainline
  (torvalds/linux a41e364995bb, 2026-11-07) adds 28c1, b60b, b06f, b07f,
  d70b and d73b. A VMD controller newer than the running kernel has no
  driver at all, so its disks are hidden; those IDs are included.
- Intel SATA controllers: every ``PCI_VDEVICE(INTEL, ...)`` entry of
  ``ahci_pci_tbl[]`` in ``drivers/ata/ahci.c`` (identical in v6.12 and
  mainline a41e364995bb). One of these reporting the RAID class
  (``PCI_CLASS_STORAGE_RAID`` 0x0104) is the controller in RST RAID mode;
  ``ahci_remap_check()`` in the same file warns that NVMe disks remapped
  behind it need "Switch your BIOS from RAID to AHCI mode".
- Classes: ``PCI_CLASS_STORAGE_RAID`` 0x0104 and
  ``PCI_CLASS_STORAGE_EXPRESS`` 0x0108 (NVMe) from ``pci_ids.h``.

See docs/storage-and-controller-limits.md, "Disk hidden by Intel VMD or RST".
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple

INTEL_VENDOR = 0x8086
PCI_CLASS_STORAGE_RAID = 0x0104
PCI_CLASS_STORAGE_EXPRESS = 0x0108

# drivers/pci/controller/vmd.c vmd_ids[] (v6.12 plus mainline a41e364995bb).
VMD_DEVICE_IDS = frozenset({
    0x201D, 0x28C0, 0x28C1, 0x467F, 0x4C3D, 0x7D0B, 0x9A0B, 0xA77F,
    0xAD0B, 0xB06F, 0xB07F, 0xB60B, 0xD70B, 0xD73B,
})

# drivers/ata/ahci.c ahci_pci_tbl[]: every PCI_VDEVICE(INTEL, id) entry
# (163 IDs, identical in v6.12 and mainline a41e364995bb).
AHCI_INTEL_DEVICE_IDS = frozenset({
    0x02D3, 0x02D7, 0x06D6, 0x06D7, 0x0F22, 0x0F23, 0x19B0, 0x19B1, 0x19B2,
    0x19B3, 0x19B4, 0x19B5, 0x19B6, 0x19B7, 0x19C0, 0x19C1, 0x19C2, 0x19C3,
    0x19C4, 0x19C5, 0x19C6, 0x19C7, 0x1C02, 0x1C03, 0x1C04, 0x1C05, 0x1C06,
    0x1C07, 0x1D02, 0x1D04, 0x1D06, 0x1E02, 0x1E03, 0x1E04, 0x1E05, 0x1E06,
    0x1E07, 0x1E0E, 0x1F22, 0x1F23, 0x1F24, 0x1F25, 0x1F26, 0x1F27, 0x1F2E,
    0x1F2F, 0x1F32, 0x1F33, 0x1F34, 0x1F35, 0x1F36, 0x1F37, 0x1F3E, 0x1F3F,
    0x22A3, 0x2323, 0x23A3, 0x2652, 0x2653, 0x2681, 0x2682, 0x2683, 0x27C1,
    0x27C3, 0x27C5, 0x27C6, 0x2821, 0x2822, 0x2823, 0x2824, 0x2826, 0x2827,
    0x2829, 0x282A, 0x282F, 0x2922, 0x2923, 0x2924, 0x2925, 0x2927, 0x2929,
    0x292A, 0x292B, 0x292C, 0x292F, 0x294D, 0x294E, 0x34D3, 0x3A05, 0x3A22,
    0x3A25, 0x3B22, 0x3B23, 0x3B24, 0x3B25, 0x3B29, 0x3B2B, 0x3B2C, 0x3B2F,
    0x43D4, 0x43D5, 0x43D6, 0x43D7, 0x4B63, 0x502A, 0x502B, 0x5AE3, 0x8C02,
    0x8C03, 0x8C04, 0x8C05, 0x8C06, 0x8C07, 0x8C0E, 0x8C0F, 0x8C82, 0x8C83,
    0x8C84, 0x8C85, 0x8C86, 0x8C87, 0x8C8E, 0x8C8F, 0x8D02, 0x8D04, 0x8D06,
    0x8D0E, 0x8D62, 0x8D64, 0x8D66, 0x8D6E, 0x9C02, 0x9C03, 0x9C04, 0x9C05,
    0x9C06, 0x9C07, 0x9C0E, 0x9C0F, 0x9C83, 0x9C85, 0x9C87, 0x9C8F, 0x9D03,
    0x9D05, 0x9D07, 0x9DD3, 0xA102, 0xA103, 0xA105, 0xA106, 0xA107, 0xA10F,
    0xA182, 0xA186, 0xA1D2, 0xA1D6, 0xA202, 0xA206, 0xA252, 0xA256, 0xA356,
    0xA386,
})

# Result kinds. Both show the same owner text; the kind is for the log.
HINT_NONE = ""
HINT_VMD = "vmd"
HINT_RST = "rst"

SYSFS_ROOT = "/sys"
# A real computer has tens to a few hundred PCI functions. More is not a
# shape this check understands, so it gives up (generic text).
MAX_FUNCTIONS = 1024
_ADDRESS_RE = re.compile(r"^(?:[0-9a-f]{4,8}:)?[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
_HEX_RE = re.compile(r"^0x[0-9a-fA-F]{1,6}$")
_DRIVER_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
# Devices that are never the computer's own disk: the live image's loop
# devices, optical drives and memory disks.
_NON_DISK_RE = re.compile(r"^/dev/(?:loop|sr|zram|ram)[0-9]+(?:p[0-9]+)?$")


@dataclass(frozen=True)
class PciFunction:
    address: str
    vendor: int
    device: int
    class_code: int  # base class and subclass, e.g. 0x0104
    driver: str = ""  # bound driver name; "" when unbound


@dataclass(frozen=True)
class Hint:
    kind: str = HINT_NONE  # HINT_VMD, HINT_RST, or "" for the generic text
    reason: str = ""  # why the generic text stays (log only)
    driver: str = ""  # driver state of the matched controller (log only)

    def log_detail(self) -> str:
        if self.kind:
            return f"kind={self.kind} driver={self.driver or 'unbound'}"
        return f"kind=generic reason={self.reason}"


def _read_text(path: str) -> str:
    with open(path, "r", encoding="ascii") as fh:
        return fh.read(64)


def _hex_field(path: str, limit: int) -> int:
    raw = _read_text(path).strip()
    if not _HEX_RE.match(raw):
        raise ValueError("not a sysfs hex value")
    value = int(raw, 16)
    if value > limit:
        raise ValueError("out of range")
    return value


def read_sysfs(root: str = SYSFS_ROOT) -> Optional[Tuple[PciFunction, ...]]:
    """PCI functions from ``<root>/bus/pci/devices``. None if anything is off.

    Opens files for reading only. A missing ``driver`` link means unbound;
    any other read error, a malformed value or an unexpected entry name
    returns None so the caller keeps the generic text.
    """
    base = os.path.join(root, "bus", "pci", "devices")
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return None
    if len(names) > MAX_FUNCTIONS:
        return None
    functions = []
    for name in names:
        if not _ADDRESS_RE.match(name):
            return None
        entry = os.path.join(base, name)
        try:
            vendor = _hex_field(os.path.join(entry, "vendor"), 0xFFFF)
            device = _hex_field(os.path.join(entry, "device"), 0xFFFF)
            pci_class = _hex_field(os.path.join(entry, "class"), 0xFFFFFF)
        except (OSError, ValueError, UnicodeDecodeError):
            return None
        driver_link = os.path.join(entry, "driver")
        driver = ""
        if os.path.lexists(driver_link):
            try:
                driver = os.path.basename(os.readlink(driver_link).rstrip("/"))
            except OSError:
                return None
            if not _DRIVER_RE.match(driver):
                return None
        functions.append(PciFunction(name, vendor, device, pci_class >> 8, driver))
    return tuple(functions)


_LSPCI_LINE = re.compile(
    r"^(?P<address>(?:[0-9a-f]{4,8}:)?[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]) "
    r".*\[(?P<cls>[0-9a-f]{4})\]: "
    r".*\[(?P<vendor>[0-9a-f]{4}):(?P<device>[0-9a-f]{4})\]"
    r"(?: \(rev [0-9a-f]{2}\))?(?: \(prog-if [0-9a-f]{2}(?: \[[^\]]*\])?\))?$"
)
_LSPCI_DRIVER = re.compile(r"^\s+Kernel driver in use: (?P<driver>\S+)$")


def parse_lspci(text: str) -> Optional[Tuple[PciFunction, ...]]:
    """Functions from ``lspci -nn`` or ``lspci -nnk`` text. None if malformed.

    Not run on the live image (no pciutils there); used for preview
    fixtures and tests so the same classifier reads the format support
    staff are likely to have.
    """
    if not isinstance(text, str):
        return None
    functions: list[PciFunction] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line[0].isspace():
            match = _LSPCI_DRIVER.match(line)
            if match is None:
                continue  # Subsystem / Kernel modules lines
            if not functions or functions[-1].driver or not _DRIVER_RE.match(match["driver"]):
                return None
            last = functions[-1]
            functions[-1] = PciFunction(last.address, last.vendor, last.device,
                                        last.class_code, match["driver"])
            continue
        match = _LSPCI_LINE.match(line)
        if match is None:
            return None
        functions.append(PciFunction(
            match["address"], int(match["vendor"], 16), int(match["device"], 16),
            int(match["cls"], 16),
        ))
        if len(functions) > MAX_FUNCTIONS:
            return None
    return tuple(functions)


def _boot_related(path: str, parent: str, boot_paths: set) -> bool:
    return path in boot_paths or parent in boot_paths or bool(_NON_DISK_RE.match(path))


def _only_beamo_usb_observed(discovery: Any) -> bool:
    """True when discovery saw no disk at all besides the Beamo USB.

    Any other disk node (listed, mounted, read-only, unsupported or with an
    unknown parent) means the computer's disk is not simply hidden, so the
    generic text stays.
    """
    boot = getattr(discovery, "boot", None)
    if (
        getattr(discovery, "error", None)
        or not getattr(discovery, "boot_identified", False)
        or boot is None
        or getattr(discovery, "selectable", None)
    ):
        return False
    boot_paths = {boot.path}
    for disk in discovery.disks:
        # Paths marked as the Beamo USB (including its aliases) only.
        if not disk.is_boot:
            return False
        boot_paths.add(disk.path)
    for disk in discovery.physical_observations:
        if disk.path not in boot_paths:
            return False

    def walk(items: Iterable[Any], inside: bool) -> bool:
        for item in items:
            if not (inside or _boot_related(item.path, item.parent_path, boot_paths)):
                return False
            # Everything nested under the Beamo USB (or a loop device) is
            # part of it, so its children are accepted as well.
            if not walk(item.children, True):
                return False
        return True

    # A partition of the Beamo USB lists the USB as its parent. Any other
    # top-level entry, or one without a path, keeps the generic text.
    return walk(discovery.excluded, False)


def classify(functions: Optional[Iterable[PciFunction]], discovery: Any) -> Hint:
    """The hint for an empty disk list, or Hint(reason=...) for the generic text."""
    if not _only_beamo_usb_observed(discovery):
        return Hint(reason="disk_observed")
    if functions is None:
        return Hint(reason="unreadable")
    functions = tuple(functions)
    if not functions:
        return Hint(reason="no_pci")
    vmd = []
    rst = []
    for fn in functions:
        if fn.class_code == PCI_CLASS_STORAGE_EXPRESS:
            # An NVMe controller is visible (outside VMD, or behind a working
            # vmd driver). Its disk is not hidden by VMD/RST.
            return Hint(reason="nvme_visible")
        if fn.vendor == INTEL_VENDOR and fn.device in VMD_DEVICE_IDS:
            vmd.append(fn)
        elif fn.class_code == PCI_CLASS_STORAGE_RAID:
            if fn.vendor == INTEL_VENDOR and fn.device in AHCI_INTEL_DEVICE_IDS:
                rst.append(fn)
            else:
                # Another vendor's RAID, or an Intel RAID device the kernel
                # tables do not name: the steps may be wrong for it.
                return Hint(reason="other_raid")
    if vmd:
        return Hint(HINT_VMD, driver=vmd[0].driver)
    if rst:
        return Hint(HINT_RST, driver=rst[0].driver)
    return Hint(reason="no_vmd_rst")
