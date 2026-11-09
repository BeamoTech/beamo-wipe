# SPDX-License-Identifier: GPL-3.0-or-later
"""Canonical, offline storage guidance shared by renderers and evidence.

#181: the screens use short, plain sentences (OVERWRITE_LIMITS, notice()).
Saved reports keep the wording they have always had (REPORT_OVERWRITE_LIMITS,
report_notice()): result.json warnings, the coverage check and RESULT.txt
are persisted evidence text. Both say the same thing.
"""

from beamo_wipe.models import DiskKind

TITLE = "Supported storage limits"
BUTTON = "Storage limits (L)"
OVERWRITE_LIMITS = (
    "Overwriting reaches only storage the device exposes. It cannot guarantee "
    "to reach flash areas that cannot be accessed. The same goes for remapped, "
    "spare and controller-managed areas. Additional overwrite passes do not fix "
    "these limitations."
)
# The same limits as saved in every report (evidence warnings, the coverage
# check, RESULT.txt). Persisted wording: not rewritten with the screens.
REPORT_OVERWRITE_LIMITS = (
    "Overwriting reaches only storage the device exposes. It cannot guarantee "
    "coverage of inaccessible, remapped, over-provisioned (spare), or "
    "controller-managed flash areas. Additional overwrite passes do not fix these limitations."
)
VERIFICATION_SCOPE = (
    "Read-back verification checks exposed storage against the final overwrite. "
    "It does not prove that hidden copies were erased."
)


NOTICE_SSD_LEAD = "SSD limits: "
NOTICE_HDD_LEAD = "Hard disk selected. Hidden or remapped sectors may remain. Flash limits: "
NOTICE_UNKNOWN_LEAD = "Device type is unknown; do not assume it is a hard disk or SSD. Flash limits: "


def _lead(kind: DiskKind) -> str:
    if kind in (DiskKind.SSD, DiskKind.NVME):
        return NOTICE_SSD_LEAD
    if kind == DiskKind.HDD:
        return NOTICE_HDD_LEAD
    return NOTICE_UNKNOWN_LEAD


def notice(kind: DiskKind) -> str:
    """The storage limits notice the screens show (Method's Show more)."""
    return _lead(kind) + OVERWRITE_LIMITS


def report_notice(kind: DiskKind) -> str:
    """The same notice in the wording saved in reports (persisted evidence)."""
    return _lead(kind) + REPORT_OVERWRITE_LIMITS


# #158: the Method screen's one-line summary, between the selected disk and
# the method cards; Show more opens notice() for the same kind, unchanged.
# Hard disk and unknown lines are the first sentences of their notice.
LINE_SSD = "On SSDs, overwriting may not reach every hidden area."
LINE_HDD = "Hard disk selected. Hidden or remapped sectors may remain."
LINE_UNKNOWN = "Device type is unknown; do not assume it is a hard disk or SSD."


def line(kind: DiskKind) -> str:
    if kind in (DiskKind.SSD, DiskKind.NVME):
        return LINE_SSD
    if kind == DiskKind.HDD:
        return LINE_HDD
    return LINE_UNKNOWN


SECTION_SUPPORTS_TITLE = "What this tool supports"
SECTION_SUPPORTS_BODY = (
    "Beamo Wipe uses pinned nwipe v0.42 to overwrite a whole disk that you "
    "select. The disk must be exposed to the operating system. It does not issue controller secure-erase "
    "or sanitize commands. It does not support Apple Silicon Macs, Chromebooks, "
    "or erasing the running Windows disk."
)
SECTION_SSD_TITLE = "SSD and flash storage"
SECTION_VERIFY_TITLE = "Read-back verification"
SECTION_HDD_TITLE = "Hard disks, hidden areas, and damaged media"
SECTION_HDD_BODY = (
    "The overwrite does not reach hidden HPA/DCO areas. Nor does it reach "
    "remapped or unreadable sectors, or NVMe namespaces that are not exposed. "
    "A disk can report completion while hidden data remains. Do not treat read "
    "or write errors as success. The same goes for an interruption, or for "
    "completion evidence that is missing."
)
SECTION_UNKNOWN_TITLE = "Unknown devices and controllers"
SECTION_UNKNOWN_BODY = (
    "A missing device type stays unknown. A USB bridge or RAID controller "
    "may hide the media type or capacity. It may also hide physical members or "
    "caches. An exposed virtual disk does not show that every physical member "
    "is covered. "
    "Do not use a displayed SSD or HDD label as proof that hidden areas are absent."
)
SECTION_ENCRYPTION_TITLE = "Encryption and locked devices"
SECTION_ENCRYPTION_BODY = (
    "Beamo Wipe does not unlock BitLocker, OPAL, ATA security or other locked "
    "devices. It does not extract keys, reset passwords or bypass Secure Boot. "
    "Overwriting an exposed encrypted device does not prove that its keys were "
    "destroyed. It also does not prove that hidden encrypted copies were covered. "
    "Mapped volumes and partitions are not whole-disk targets."
)
SECTION_ALTERNATIVE_TITLE = "When to use a different process"
SECTION_ALTERNATIVE_BODY = (
    "Do you need coverage beyond exposed storage? Then see the disk maker's "
    "guidance for the exact model and firmware. Vendor secure erase support "
    "and validation vary. This USB does not perform or certify that process. "
    "Need assurance that cannot be established? Then use a qualified "
    "destruction service. Beamo reports are not a formal certificate."
)
SECTION_OWNERSHIP_TITLE = "Ownership and safety"
SECTION_OWNERSHIP_BODY = (
    "Erase only disks you own or have written permission to erase. Confirm "
    "the device identity and keep backups. The erase warnings and the Beamo USB "
    "exclusion still apply. So do the confirmation token and the five-second "
    "delay. If you are unsure of the device identity, stop. Do not bypass the "
    "safety gates."
)


def _build_sections():
    return (
        (SECTION_SUPPORTS_TITLE, SECTION_SUPPORTS_BODY),
        (SECTION_SSD_TITLE, OVERWRITE_LIMITS),
        (SECTION_VERIFY_TITLE, VERIFICATION_SCOPE),
        (SECTION_HDD_TITLE, SECTION_HDD_BODY),
        (SECTION_UNKNOWN_TITLE, SECTION_UNKNOWN_BODY),
        (SECTION_ENCRYPTION_TITLE, SECTION_ENCRYPTION_BODY),
        (SECTION_ALTERNATIVE_TITLE, SECTION_ALTERNATIVE_BODY),
        (SECTION_OWNERSHIP_TITLE, SECTION_OWNERSHIP_BODY),
    )


SECTIONS = _build_sections()


def _apply_language() -> None:
    global SECTIONS
    SECTIONS = _build_sections()


def full_text() -> str:
    return "\n\n".join(f"{title}\n{body}" for title, body in SECTIONS)
