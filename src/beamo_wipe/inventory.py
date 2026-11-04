# SPDX-License-Identifier: GPL-3.0-or-later
"""Display-only explanations; eligibility remains owned by safety.py."""

import os
import unicodedata
from dataclasses import replace
from typing import Any, Iterable, Mapping, Optional

from beamo_wipe.models import Disk, DiscoveryResult, ExcludedDevice, VolumeFacts


TITLE = "Other detected devices"
INTRO = "Information only. These devices cannot be selected for erasure."
NESTED_INTRO = "On this disk (cannot be erased separately):"
REASON_UNSUPPORTED = "unsupported device"
REASON_PROTECTED = "boot or system protected"
REASON_MOUNTED = "mounted or in use"
REASON_READ_ONLY = "read-only"
REASON_CAPACITY_UNKNOWN = "capacity could not be confirmed"
REASON_ZERO_CAPACITY = "zero capacity"
REASON_ELIGIBILITY = "eligibility could not be confirmed"
REASON_UNPROVEN_TRANSPORT = "local connection could not be confirmed"
CANNOT_ERASE = "Cannot erase: {reasons}."
# Nested cards already say they cannot be erased separately. Keep other
# reasons (mounted, protected) visible; drop the generic whole-disk label.
NESTED_SILENT_REASONS = frozenset({REASON_UNSUPPORTED})
EMPTY_STEPS = (
    "No eligible disk is available. Review the reasons below. Keep the Beamo USB "
    "connected. Shut down before checking drive connections. If a disk remains "
    "unavailable or its identity is uncertain, contact support. Do not bypass protection. "
    "If the computer's own drive is missing, its storage may be set to Intel RST, VMD "
    "or RAID mode, which this USB cannot use. Ask support before changing firmware settings."
)

KIND_PART = "Partition"
KIND_CRYPT = "Encrypted volume"
KIND_MAPPED = "Mapped volume"
KIND_LOOP = "Loop device"
KIND_ROM = "Optical disc"
KIND_RAID = "RAID volume"
KIND_DISK = "Disk"
KIND_TECHNICAL = "Technical component"

# Partition names and file systems on a disk card (#147). Display only:
# built from the lsblk JSON discovery already read (LABEL, PARTLABEL,
# FSTYPE, FSVER, PARTTYPE, PARTTYPENAME); nothing is mounted or probed.
ROLE_EFI = "EFI system"
ROLE_MSR = "Microsoft reserved"
ROLE_RECOVERY = "Recovery"
FORMAT_UNKNOWN = "Unknown format"
FORMAT_BITLOCKER = "BitLocker encrypted"
FORMAT_LUKS = "LUKS encrypted"
# A volume name is untrusted text. It is always quoted and followed by the
# format and size, so it cannot pass for a role, a reason or a banner.
ITEM_NAMED = '"{name}" ({format}) {size}'
MORE_COUNT = "+{count} more"


def _build_kind_labels() -> dict[str, str]:
    return {
        "part": KIND_PART,
        "crypt": KIND_CRYPT,
        "lvm": KIND_MAPPED,
        "dm": KIND_MAPPED,
        "loop": KIND_LOOP,
        "rom": KIND_ROM,
        "md": KIND_RAID,
        "mpath": KIND_RAID,
        "disk": KIND_DISK,
    }


_KIND_LABELS = _build_kind_labels()


def _apply_language() -> None:
    global _KIND_LABELS, NESTED_SILENT_REASONS
    _KIND_LABELS = _build_kind_labels()
    NESTED_SILENT_REASONS = frozenset({REASON_UNSUPPORTED})


def kind_label_for_type(node_type: str) -> str:
    key = (node_type or "").lower().strip()
    if key in _KIND_LABELS:
        return _KIND_LABELS[key]
    if key.startswith("raid"):
        return KIND_RAID
    return KIND_TECHNICAL


def component_summary(disk: Disk, kind_label: str) -> str:
    """Plain nested label. Parent serial/model stay on the parent card."""
    from beamo_wipe.identity import UNKNOWN_MODEL

    heading = kind_label or KIND_TECHNICAL
    parts = [heading]
    parts.append(disk.size_phrase)
    label = (disk.label or "").strip()
    title = (disk.model or "").strip()
    extra = label
    if not extra and title and title != UNKNOWN_MODEL:
        extra = title
    if extra and extra not in parts:
        parts.append(extra)
    return " · ".join(parts)


def excluded_device(
    disk: Disk,
    *,
    unsupported: bool = False,
    capacity_unknown: bool = False,
    parent_path: str = "",
    node_type: str = "",
    node: Optional[Mapping[str, Any]] = None,
) -> ExcludedDevice:
    from beamo_wipe.safety import (
        SafetyError,
        assert_local_device_transport,
        has_any_mount,
        has_protected_mount,
        is_preview_env,
        is_remote_disk,
        is_unproven_scsi_transport,
        normalize_whole_disk,
    )

    reasons = []
    if disk.is_boot or has_protected_mount(disk):
        reasons.append(REASON_PROTECTED)
    if has_any_mount(disk):
        reasons.append(REASON_MOUNTED)
    if disk.read_only:
        reasons.append(REASON_READ_ONLY)
    if disk.size_bytes <= 0:
        reasons.append(
            REASON_CAPACITY_UNKNOWN if capacity_unknown else REASON_ZERO_CAPACITY
        )
    whole_disk = True
    try:
        normalize_whole_disk(disk.path)
    except SafetyError:
        unsupported = True
        whole_disk = False
    if unsupported or is_remote_disk(disk):
        reasons.append(REASON_UNSUPPORTED)
    unproven_transport = is_unproven_scsi_transport(disk)
    if whole_disk and not is_preview_env() and not is_remote_disk(disk):
        try:
            assert_local_device_transport(disk.path)
        except SafetyError:
            unproven_transport = True
    if unproven_transport:
        reasons.append(REASON_UNPROVEN_TRANSPORT)
    if not reasons:
        reasons.append(REASON_ELIGIBILITY)
    from beamo_wipe.identity import present_disk

    view = present_disk(disk)
    identity = (
        f"{view.title} | {view.capacity} | {view.connection} | "
        f"{view.id_label}: {view.id_value}"
    )
    kind = kind_label_for_type(node_type) if node_type else (
        KIND_DISK if not parent_path else KIND_TECHNICAL
    )
    return ExcludedDevice(
        identity,
        tuple(reasons),
        path=disk.path,
        parent_path=parent_path,
        kind_label=kind,
        summary=component_summary(disk, kind),
        # Display only (#147): computed after every reason above, from facts
        # that never reach eligibility or identity.
        volume=volume_facts(node, disk) if node is not None else None,
    )


# A discovery snapshot keeps the language that was active when discovery ran,
# often before the owner picked one. Its reasons and kind labels are shown in
# the current language, and a silent reason stays silent after a switch.
_REASON_NAMES = (
    ("inventory", "REASON_UNSUPPORTED"),
    ("inventory", "REASON_PROTECTED"),
    ("inventory", "REASON_MOUNTED"),
    ("inventory", "REASON_READ_ONLY"),
    ("inventory", "REASON_CAPACITY_UNKNOWN"),
    ("inventory", "REASON_ZERO_CAPACITY"),
    ("inventory", "REASON_ELIGIBILITY"),
    ("inventory", "REASON_UNPROVEN_TRANSPORT"),
    ("discover", "IDENTITY_UNCONFIRMED"),
)
_KIND_NAMES = tuple(
    ("inventory", name)
    for name in (
        "KIND_PART", "KIND_CRYPT", "KIND_MAPPED", "KIND_LOOP",
        "KIND_ROM", "KIND_RAID", "KIND_DISK", "KIND_TECHNICAL",
    )
)
# The translated parts of an identity line; model names and capacities stay.
_IDENTITY_NAMES = tuple(
    ("identity", name)
    for name in (
        "UNKNOWN_MODEL", "CONNECTION_UNKNOWN", "CONNECTION_OTHER",
        "SERIAL_NOT_REPORTED", "HARDWARE_ID_LABEL", "SERIAL_LABEL",
    )
)


def _in_current_language(text: str, names: tuple[tuple[str, str], ...]) -> str:
    """text, or the current-language value of the label it is in any language."""
    import importlib

    from beamo_wipe import lang

    for module, name in names:
        variants = {lang.english(module, name)}
        for code in lang.LANGUAGE_ORDER:
            if code != "en" and name in lang.keys(code, module):
                variants.add(lang.translated(code, module, name))
        if text in variants:
            return getattr(importlib.import_module(f"beamo_wipe.{module}"), name)
    return text


def current_reason(reason: str) -> str:
    return _in_current_language(reason, _REASON_NAMES)


def current_identity(identity: str) -> str:
    """A snapshot identity line ("title | capacity | connection | label: value")
    with its translated labels in the current language."""
    parts = []
    for part in identity.split(" | "):
        label, sep, value = part.partition(": ")
        if sep:
            part = (
                _in_current_language(label, _IDENTITY_NAMES)
                + sep
                + _in_current_language(value, _IDENTITY_NAMES)
            )
        else:
            part = _in_current_language(part, _IDENTITY_NAMES)
        parts.append(part)
    return " | ".join(parts)


def nested_heading(device: ExcludedDevice) -> str:
    item = _volume_item(device)
    if item:
        return item
    if not device.summary:
        return current_identity(device.identity)
    kind, sep, rest = device.summary.partition(" · ")
    return _in_current_language(kind, _KIND_NAMES) + sep + rest


def nested_reason_text(device: ExcludedDevice) -> str:
    reasons = (current_reason(reason) for reason in device.reasons)
    return "; ".join(reason for reason in reasons if reason not in NESTED_SILENT_REASONS)


def explanation(device: ExcludedDevice) -> str:
    """Identity and every reason, in the current language. Display only."""
    reasons = "; ".join(current_reason(reason) for reason in device.reasons)
    return f"{current_identity(device.identity)}\n" + CANNOT_ERASE.format(reasons=reasons)


def nested_under(
    parent_path: str, devices: Iterable[ExcludedDevice]
) -> tuple[ExcludedDevice, ...]:
    """Children whose known physical parent is parent_path. Display only."""
    if not parent_path:
        return ()
    aliases = _path_aliases(parent_path)
    return tuple(
        device
        for device in devices
        if device.parent_path and _path_aliases(device.parent_path) & aliases
    )


def card_nesting_text(children: Iterable[ExcludedDevice]) -> str:
    """The intro, then one compact line naming what is on the disk (#147)."""
    summary = contents_summary(children)
    if not summary:
        return ""
    return f"{NESTED_INTRO}\n{summary}"


# --- Partition names and file systems (#147). Display only. -------------------

_LABEL_MAX = 24
# Quote marks inside a name would let it close its own quotes.
_QUOTES = str.maketrans(
    {ch: "'" for ch in '"\u201c\u201d\u201e\u201f\u00ab\u00bb\u2039\u203a\u300c\u300d'}
)
_FORMAT_NAMES = {
    "ntfs": "NTFS", "exfat": "exFAT", "ext2": "ext2", "ext3": "ext3", "ext4": "ext4",
    "xfs": "XFS", "btrfs": "Btrfs", "f2fs": "F2FS", "apfs": "APFS", "hfsplus": "HFS+",
    "hfs": "HFS", "swap": "Swap", "refs": "ReFS", "udf": "UDF", "iso9660": "ISO 9660",
    "zfs_member": "ZFS", "lvm2_member": "LVM", "linux_raid_member": "RAID member",
}
_FAT_VERSIONS = {"fat12": "FAT12", "fat16": "FAT16", "fat32": "FAT32"}
# Partition types the OS set, from PARTTYPE (GPT GUID or MBR id) or the
# name lsblk derives from it. PARTLABEL is owner text and never a role.
_ROLE_TYPES = (
    ("efi", frozenset({"c12a7328-f81f-11d2-ba4b-00a0c93ec93b", "0xef"}),
     frozenset({"efi system"})),
    ("msr", frozenset({"e3c9e316-0b5c-4db8-817d-f92df00215ae"}),
     frozenset({"microsoft reserved"})),
    ("recovery", frozenset({"de94bba4-06d1-4d40-a16a-bfd50179d6ac", "0x27"}),
     frozenset({"windows recovery environment"})),
)
# Default GPT names that say nothing an owner would recognise.
_GENERIC_PARTLABELS = frozenset({
    "basic data partition", "microsoft basic data", "msftdata", "msftres",
    "microsoft reserved partition", "efi system partition", "efi system", "esp",
    "primary", "logical", "extended", "linux", "linux filesystem",
    "linux filesystem data", "linux swap",
})
_ROLE_WINDOWS = "Windows"  # product name, never translated
_SUMMARY_SHOWN = 2


def clean_volume_text(value: Any, limit: int = _LABEL_MAX) -> str:
    """Untrusted volume text, safe to show as one short line on every surface.

    Normalises Unicode (NFKC), drops control, format (bidi overrides,
    zero-width) and line/paragraph separator characters, collapses spaces,
    replaces quote marks, limits stacked combining marks and caps the
    length with an ellipsis. Toolkits still escape it (HTML preview).
    """
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKC", value)
    out = []
    marks = 0
    for ch in text:
        if ch.isspace():  # tabs, newlines, line separators: one space
            marks = 0
            out.append(" ")
            continue
        category = unicodedata.category(ch)
        if category.startswith("C"):
            continue
        if category == "Mn":
            marks += 1
            if marks > 2:
                continue
        else:
            marks = 0
        out.append(ch)
    text = " ".join("".join(out).split()).translate(_QUOTES)
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"
    return text


def volume_facts(
    node: Optional[Mapping[str, Any]], disk: Optional[Disk] = None
) -> VolumeFacts:
    """Display facts for one lsblk node. Never raises; never mounts."""
    if not isinstance(node, Mapping):
        node = {}

    def raw(key: str) -> str:
        return clean_volume_text(node.get(key), 128)

    return VolumeFacts(
        node_type=raw("type").casefold(),
        fstype=raw("fstype").casefold(),
        fsver=raw("fsver").casefold(),
        label=clean_volume_text(node.get("label")),
        partlabel=clean_volume_text(node.get("partlabel")),
        parttype=raw("parttype").casefold(),
        parttypename=raw("parttypename"),
        size_bytes=disk.size_bytes if disk is not None else 0,
        size_gb_label=disk.size_gb_label if disk is not None else "",
    )


def _role(volume: VolumeFacts) -> str:
    typename = volume.parttypename.casefold()
    for role, types, names in _ROLE_TYPES:
        if volume.parttype in types or typename in names:
            return role
    return ""


def _role_text(role: str) -> str:
    return {"efi": ROLE_EFI, "msr": ROLE_MSR, "recovery": ROLE_RECOVERY}.get(role, "")


def format_name(volume: VolumeFacts) -> str:
    """Friendly file-system name; FORMAT_UNKNOWN when missing or unrecognised."""
    fstype = volume.fstype
    if fstype == "vfat":
        return _FAT_VERSIONS.get(volume.fsver, "FAT")
    if fstype == "bitlocker":
        return FORMAT_BITLOCKER
    if fstype == "crypto_luks":
        return FORMAT_LUKS
    return _FORMAT_NAMES.get(fstype, FORMAT_UNKNOWN)


def _volume_name(volume: VolumeFacts) -> str:
    if volume.label:
        return volume.label
    name = volume.partlabel
    generic = name.casefold() in _GENERIC_PARTLABELS or (
        name.casefold() == volume.parttypename.casefold()
    )
    return "" if generic else name


def _size_text(volume: VolumeFacts) -> str:
    from beamo_wipe.models import capacity_phrase

    # Same rule as Disk.size_phrase: a positive size never reads as 0 GB.
    if volume.size_bytes > 0 and (volume.size_gb_label or "").strip() == "0":
        return "under 1 GB"
    return capacity_phrase(volume.size_gb_label)


def _is_windows_candidate(volume: VolumeFacts) -> bool:
    return (
        volume.fstype in {"ntfs", "bitlocker"}
        and not _role(volume)
        and not _volume_name(volume)
    )


def _volume_item(device: ExcludedDevice, *, windows: bool = False) -> str:
    """One component as "Name (format) size"; "" without lsblk facts."""
    volume = device.volume
    if volume is None or volume.node_type in {"", "disk"}:
        return ""
    size = _size_text(volume)
    if volume.node_type != "part":
        # Opened encrypted, LVM or RAID volumes: the kind is the format,
        # with the file system inside when lsblk reported one.
        kind = kind_label_for_type(volume.node_type)
        inner = _FORMAT_NAMES.get(volume.fstype, "")
        desc = f"{kind}, {inner}" if inner else kind
        name = _volume_name(volume)
        if name:
            return ITEM_NAMED.format(name=name, format=desc, size=size)
        return f"{desc} {size}"
    role = _role_text(_role(volume))
    if role:
        return f"{role} {size}"
    fmt = format_name(volume)
    if windows:
        return f"{_ROLE_WINDOWS} ({fmt}) {size}"
    name = _volume_name(volume)
    if name:
        return ITEM_NAMED.format(name=name, format=fmt, size=size)
    return f"{fmt} {size}"


def contents_summary(children: Iterable[ExcludedDevice]) -> str:
    """Compact, recognisable contents line for a disk card. Display only.

    Largest first, two shown and "+N more" for the rest (all shown when only
    one more would be hidden). A component with a reason (mounted,
    protected) is never folded away. The single unnamed NTFS or BitLocker
    partition beside a Microsoft reserved or Windows recovery partition is
    named Windows, from the same partition-type evidence discovery uses.
    """
    items = tuple(children)
    if not items:
        return ""
    volumes = [child.volume for child in items]
    windows_marks = any(
        v is not None and v.node_type == "part" and _role(v) in {"msr", "recovery"}
        for v in volumes
    )
    candidates = [
        i for i, v in enumerate(volumes)
        if v is not None and v.node_type == "part" and _is_windows_candidate(v)
    ]
    windows_index = candidates[0] if windows_marks and len(candidates) == 1 else -1
    entries = []
    for index, child in enumerate(items):
        text = _volume_item(child, windows=index == windows_index) or nested_heading(child)
        reason = nested_reason_text(child)
        size = child.volume.size_bytes if child.volume is not None else 0
        entries.append((f"{text} ({reason})" if reason else text, bool(reason), size))
    order = sorted(range(len(items)), key=lambda i: (-entries[i][2], i))
    if len(order) > _SUMMARY_SHOWN + 1:
        shown = order[:_SUMMARY_SHOWN] + [
            i for i in order[_SUMMARY_SHOWN:] if entries[i][1]
        ]
    else:
        shown = order
    parts = [entries[i][0] for i in shown]
    hidden = len(items) - len(shown)
    if hidden:
        parts.append(MORE_COUNT.format(count=hidden))
    return " \u00b7 ".join(parts)


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line if line else line for line in text.split("\n"))


def full_text(devices: tuple[ExcludedDevice, ...]) -> str:
    blocks = [INTRO]
    for device in devices:
        blocks.append(explanation(device))
        nested = card_nesting_text(device.children)
        if nested:
            blocks.append(_indent(nested))
    return "\n\n".join(blocks)


def _path_aliases(path: str) -> set[str]:
    aliases = {path}
    try:
        aliases.add(os.path.realpath(path))
    except OSError:
        pass
    return aliases


def _raw_other_devices(discovery: DiscoveryResult) -> tuple[ExcludedDevice, ...]:
    from beamo_wipe.safety import selectable_disks

    assert discovery.boot is not None  # other_devices checks this before calling.
    boot_paths = _path_aliases(discovery.boot.path)
    if discovery.excluded:
        return tuple(
            device
            for device in discovery.excluded
            if not device.path or not (_path_aliases(device.path) & boot_paths)
        )
    eligible = {d.path for d in selectable_disks(discovery)}
    return tuple(
        excluded_device(d)
        for d in discovery.disks
        if d.path not in eligible and os.path.realpath(d.path) not in boot_paths
    )


def _known_parent_paths(
    raw: tuple[ExcludedDevice, ...], discovery: DiscoveryResult
) -> set[str]:
    from beamo_wipe.safety import selectable_disks

    known: set[str] = set()
    for disk in selectable_disks(discovery):
        known.update(_path_aliases(disk.path))
    if discovery.boot is not None:
        known.update(_path_aliases(discovery.boot.path))
    for device in raw:
        if device.path and not device.parent_path:
            known.update(_path_aliases(device.path))
    return known


def _group_other_devices(
    raw: tuple[ExcludedDevice, ...], discovery: DiscoveryResult
) -> tuple[ExcludedDevice, ...]:
    known = _known_parent_paths(raw, discovery)
    roots = []
    for device in raw:
        if device.parent_path and _path_aliases(device.parent_path) & known:
            continue
        roots.append(device)
    grouped = []
    for device in roots:
        kids = nested_under(device.path, raw) if device.path else ()
        grouped.append(replace(device, children=kids) if kids else device)
    return tuple(grouped)


def other_devices(discovery: DiscoveryResult) -> tuple[ExcludedDevice, ...]:
    """Display-only exclusions, with confirmed boot media presented separately.

    Children of a known physical parent are omitted here and shown on that
    parent instead. Orphans with missing parentage stay visible.
    """
    # Never display inventory when boot identity failed closed.
    if not discovery.boot_identified or discovery.error or discovery.boot is None:
        return ()
    return _group_other_devices(_raw_other_devices(discovery), discovery)


UNKNOWN_COUNT = (
    "Disk list could not be confirmed. No disk is available to erase."
)
USB_PROTECTED = "Beamo USB protected"
DISC_PROTECTED = "Beamo boot disc protected"
UNCERTAIN_NOTE = "Some devices could not be fully identified"
AVAILABLE_NONE = "No disks available to erase"
AVAILABLE_ONE = "1 disk available to erase"
AVAILABLE_MANY = "{count} disks available to erase"
UNAVAILABLE_ONE = "1 other device not available"
UNAVAILABLE_MANY = "{count} other devices not available"
_UNCERTAIN_REASONS = frozenset(
    {
        "capacity could not be confirmed",
        "eligibility could not be confirmed",
        "identity could not be confirmed",
    }
)


def _join_count(parts: tuple[str, ...], *, spoken: bool) -> str:
    if spoken:
        text = ". ".join(parts)
        return text if text.endswith(".") else text + "."
    return " · ".join(parts)


def _has_uncertain_reason(device: ExcludedDevice) -> bool:
    from beamo_wipe import lang

    # Discovery snapshots retain the language used when their reason strings
    # were created. Match every supported translation after a language switch.
    reasons = _UNCERTAIN_REASONS | {
        lang.translated(code, module, name)
        for code in lang.LANGUAGE_ORDER if code != "en"
        for module, name in (
            ("inventory", "REASON_CAPACITY_UNKNOWN"),
            ("inventory", "REASON_ELIGIBILITY"),
            ("discover", "IDENTITY_UNCONFIRMED"),
        )
    }
    if any(reason in reasons for reason in device.reasons):
        return True
    return any(_has_uncertain_reason(child) for child in device.children)


def count_summary(discovery: DiscoveryResult, *, spoken: bool = False) -> str:
    """Concise hardware inventory. Display only; never changes eligibility."""
    if not discovery.boot_identified or discovery.error or discovery.boot is None:
        return UNKNOWN_COUNT
    from beamo_wipe.safety import OPTICAL_RE, selectable_disks

    eligible = len(selectable_disks(discovery))
    if eligible == 0:
        available = AVAILABLE_NONE
    elif eligible == 1:
        available = AVAILABLE_ONE
    else:
        available = AVAILABLE_MANY.format(count=eligible)
    parts = [available]
    boot = discovery.boot
    # USB-SATA bridges can report ATA/SATA (or no TRAN). A /dev/sd* boot
    # medium is still the Beamo USB; only an optical kernel node is a disc.
    parts.append(
        DISC_PROTECTED
        if OPTICAL_RE.fullmatch(os.path.realpath(boot.path))
        else USB_PROTECTED
    )
    others = other_devices(discovery)
    if others:
        n = len(others)
        if n == 1:
            parts.append(UNAVAILABLE_ONE)
        else:
            parts.append(UNAVAILABLE_MANY.format(count=n))
        if any(_has_uncertain_reason(device) for device in others):
            parts.append(UNCERTAIN_NOTE)
    return _join_count(tuple(parts), spoken=spoken)


def _same_char(a: str, b: str) -> bool:
    # Per character, so the offsets stay offsets into the shown serial even
    # when casefold() would change a string's length. Case-only differences
    # cannot establish identity.
    return a.casefold() == b.casefold()


def _distinguishing(serial: str, other: str) -> set[int] | None:
    """Offsets in ``serial`` that tell it apart from ``other`` (#152).

    None when the two share nothing at either end: they do not look alike,
    so marking every character would not help. Otherwise strip the shared
    beginning and ending. If what remains has the same length on both
    sides, only the characters that differ are marked; if the lengths
    differ, every remaining character of ``serial`` is (none when ``serial``
    is the shorter one and is wholly contained at the ends of ``other``).
    """
    shortest = min(len(serial), len(other))
    prefix = 0
    while prefix < shortest and _same_char(serial[prefix], other[prefix]):
        prefix += 1
    suffix = 0
    while (suffix < shortest - prefix
           and _same_char(serial[-suffix - 1], other[-suffix - 1])):
        suffix += 1
    if prefix == 0 and suffix == 0:
        return None
    mine = serial[prefix:len(serial) - suffix]
    theirs = other[prefix:len(other) - suffix]
    if len(mine) == len(theirs):
        return {prefix + i for i, ch in enumerate(mine) if not _same_char(ch, theirs[i])}
    return set(range(prefix, len(serial) - suffix))


def _runs(offsets: set[int]) -> tuple[tuple[int, int], ...]:
    runs: list[list[int]] = []
    for offset in sorted(offsets):
        if runs and runs[-1][1] == offset:
            runs[-1][1] = offset + 1
        else:
            runs.append([offset, offset + 1])
    return tuple((a, b) for a, b in runs)


def _positions(runs: tuple[tuple[int, int], ...]) -> str:
    """One-based, spoken-friendly: "character 7", "characters 7 and 11"."""
    if len(runs) == 1:
        a, b = runs[0]
        return POSITION_ONE.format(n=a + 1) if b == a + 1 else POSITION_RANGE.format(a=a + 1, b=b)
    items = [str(a + 1) if b == a + 1 else POSITION_ITEM_RANGE.format(a=a + 1, b=b) for a, b in runs]
    listed = ", ".join(items[:-1]) + f" {POSITION_AND} " + items[-1]
    return POSITION_MANY.format(items=listed)


def serial_differences(
    disk: Disk, peers: tuple[Disk, ...]
) -> tuple[tuple[tuple[int, int], ...], str]:
    """Display-only marks (runs of Python offsets) and a spoken explanation.

    Compares the serial with every other disk of the same displayed
    capacity (the same-size warning's group), one pair at a time (#152):
    a disk's marks are the characters that tell it apart from each
    look-alike, for any number of similar disks and serials of different
    lengths. A same-size serial that shares nothing with it adds no mark.
    Missing serials prevent a complete comparison; duplicate serials never
    receive marks. Never changes identity, eligibility or the token.
    """
    serial = (disk.serial or "").strip()
    others = [d for d in peers if d.path != disk.path
              and d.size_gb_label == disk.size_gb_label]
    values = [serial, *((d.serial or "").strip() for d in others)]
    if (disk.is_boot or not others or not all(values)
            or any(serial.casefold() == (other.serial or "").strip().casefold()
                   for other in peers if other.path != disk.path)):
        return (), ""
    marks: set[int] = set()
    alike = 0
    contained = False
    for other in others:
        theirs = (other.serial or "").strip()
        found = _distinguishing(serial, theirs)
        if found is None:
            continue
        alike += 1
        if not found and len(theirs) > len(serial):
            contained = True
        marks |= found
    reminder = REMINDER_CHECK_ID
    if not marks:
        if contained:
            unit = UNIT_CHAR if len(serial) == 1 else UNIT_CHARS
            return (), SERIAL_LONGER.format(count=len(serial), unit=unit, reminder=reminder)
        return (), ""
    runs = _runs(marks)
    if len(others) == 1:
        template = COMPARE_SERIAL_OTHER
    elif alike == 1:
        template = COMPARE_SERIAL_SIMILAR_ONE
    else:
        template = COMPARE_SERIAL_SIMILAR_MANY
    # Positions only: the card shows the serial once with these characters
    # marked; the note must not print them again (#148).
    return runs, template.format(size=disk.size_phrase, position=_positions(runs), reminder=reminder)


REMINDER_CHECK_ID = "Check the full ID before choosing."
UNIT_CHAR = "character"
UNIT_CHARS = "characters"
SERIAL_LONGER = "Serial number has {count} {unit}; other serials are longer. {reminder}"
POSITION_ONE = "character {n}"
POSITION_RANGE = "characters {a} to {b}"
POSITION_MANY = "characters {items}"
POSITION_ITEM_RANGE = "{a} to {b}"
POSITION_AND = "and"
COMPARE_SERIAL_OTHER = "Differs from the other {size} disk at {position}. {reminder}"
COMPARE_SERIAL_SIMILAR_ONE = "Differs from the similar {size} disk at {position}. {reminder}"
COMPARE_SERIAL_SIMILAR_MANY = "Differs from the similar {size} disks at {position}. {reminder}"
ENTRY_DISK = "Disk {number}"
ENTRY_MODEL = "Model: {value}"
ENTRY_CAPACITY = "Capacity: {value}"
ENTRY_SERIAL = "Serial number: {value}"
ENTRY_CONNECTION = "Connection: {value}"


COMPARE_TITLE = "Compare disks"
COMPARE_INTRO = (
    "Read only. Compare model, capacity, serial number and connection before choosing. "
    "Your selection stays unchanged. If identity is uncertain, do not guess."
)


def comparison_entries(
    disks: Iterable[Disk], *, peers: Iterable[Disk] | None = None
) -> tuple[str, ...]:
    """Accept only the caller's eligible snapshot; never discover or select."""
    from beamo_wipe.identity import present_disk, SERIAL_LABEL, SERIAL_NOT_REPORTED

    candidates = tuple(disks)
    identity_peers = tuple(peers) if peers is not None else candidates
    entries = []
    from beamo_wipe.disk_order import pick_order

    # "Disk N" is the disk's place in the pick list (#151 order).
    numbered = enumerate(pick_order(candidates), 1)
    # Keep equal-capacity candidates adjacent while retaining picker numbers.
    ordered = sorted(
        numbered, key=lambda item: (item[1].size_bytes, (item[1].model or "").casefold(), item[0])
    )
    for number, disk in ordered:
        view = present_disk(disk, identity_peers)
        lines = [
            ENTRY_DISK.format(number=number),
            ENTRY_MODEL.format(value=view.title),
            ENTRY_CAPACITY.format(value=view.capacity),
            ENTRY_SERIAL.format(
                value=view.id_value if view.id_label == SERIAL_LABEL else SERIAL_NOT_REPORTED
            ),
            ENTRY_CONNECTION.format(value=view.connection),
        ]
        if view.id_label != SERIAL_LABEL:
            lines.append(f"{view.id_label}: {view.id_value}")
        lines.extend(view.notes)
        entries.append("\n".join(lines))
    return tuple(entries)


def comparison_text(disks: Iterable[Disk], *, peers: Iterable[Disk] | None = None) -> str:
    return COMPARE_INTRO + "\n\n" + "\n\n".join(comparison_entries(disks, peers=peers))
