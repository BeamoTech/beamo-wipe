# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep active physical expectations consistent with the inspected boot chain.

These checks inspect documentation only; they never alter firmware or run nwipe.
Historical releases and execution logs deliberately remain outside this policy.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HUB = DOCS / "evidence/physical-acceptance-111"
ACTIVE = (
    "secure-boot-acceptance.md",
    "compatibility-matrix.md",
    "accessibility-lowres-matrix.md",
    "release-verification.md",
    "evidence-tiers.md",
    "runbook.md",
    "desktop-hardware-acceptance.md",
    "desktop-entry-design.md",
    "storage-and-controller-limits.md",
    "evidence/physical-acceptance-111/README.md",
    "evidence/physical-acceptance-111/results/firmware.md",
    "evidence/physical-acceptance-111/results/desktop-usb-launch.md",
)
OBSOLETE = (
    r"no (?:enrolled )?Beamo key[^\n]{0,180}(?:refus|reject)",
    r"no enrolled key[^\n]{0,180}(?:refus|reject)",
    r"unsigned image (?:rejects|refuses)",
    r"unsupported[^\n]{0,50}unless user disables",
    r"Disable Secure Boot, boot as",
    r"on lab hardware you may toggle it",
    r"on \*\*lab\*\* hardware only, USB boots",
)


@pytest.mark.parametrize("relative", ACTIVE)
def test_active_guidance_never_uses_enrollment_as_a_rejection_or_disables_security(relative):
    text = (DOCS / relative).read_text(encoding="utf-8")
    for pattern in OBSOLETE:
        assert not re.search(pattern, text, re.IGNORECASE), (relative, pattern)


def test_physical_cases_cover_known_acceptance_rejection_and_uninspectable_states():
    text = (DOCS / "secure-boot-acceptance.md").read_text(encoding="utf-8")
    rows = {
        cells[0]: cells
        for line in text.splitlines()
        if line.startswith("| SB-")
        for cells in [[cell.strip() for cell in line.strip("|").split("|")]]
    }
    expected = {
        "SB-ACCEPT": "ACCEPT",
        "SB-NO-ANCHOR": "REJECT",
        "SB-DBX": "REJECT",
        "SB-SHIM": "REJECT",
        "SB-UNKNOWN": "UNKNOWN",
        "SB-INSPECTION": "INSPECTION FAILED",
        "SB-ARCH": "UNSUPPORTED",
    }
    assert set(rows) == set(expected)
    for name, outcome in expected.items():
        cells = rows[name]
        assert len(cells) == 5
        assert "Q12" in cells[1], name
        assert all(cells), name
        assert outcome in cells[3], name
    for phrase in ("dbx", "SBAT", "SetupMode", "MokSBStateRT", "NOT TESTED"):
        assert phrase in text
    assert "missing USB entry alone" in text
    assert "Unknown is never Pass" in text
    assert "Do not enroll" in text
    assert "before and after" in text
    assert "Do not reset or roll back" in text


def test_every_secure_boot_physical_row_points_to_a_case_and_identity():
    firmware = (HUB / "results/firmware.md").read_text(encoding="utf-8")
    assert "Q12" in firmware
    for row_id, case in (
        ("PHY-FW-03", "SB-ACCEPT"),
        ("PHY-FW-11", "SB-DBX"),
        ("PHY-FW-13", "SB-NO-ANCHOR"),
        ("PHY-FW-14", "SB-SHIM"),
        ("PHY-FW-15", "SB-UNKNOWN"),
        ("PHY-FW-16", "SB-INSPECTION"),
        ("PHY-FW-17", "SB-ARCH"),
    ):
        row = next(line for line in firmware.splitlines() if line.startswith(f"| {row_id} |"))
        assert case in row
        assert "NOT TESTED" in row
    identity = (HUB / "BUILD-IDENTITY.md").read_text(encoding="utf-8")
    for field in ("db / dbx", "SBAT", "MokSBStateRT", "component", "case ID"):
        assert field in identity


def test_inspection_receipt_binds_the_chain_to_exact_published_bytes():
    receipt = json.loads((DOCS / "evidence/secure-boot-119/components.json").read_text())
    assert receipt["physical_status"] == "NOT TESTED"
    assert receipt["source_commit"] == "e986419379f512f8088f5982ee02a51dc91a9dae"
    assert receipt["iso_sha256"] == "73554d35aecafac7fc6dffe41d1f1efdb658b43c39da85a2f0bebfe8f1beb598"
    assert receipt["usb_sha256"] == "1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b"
    components = {item["path"]: item for item in receipt["components"]}
    for path, signer in (
        ("EFI/boot/bootx64.efi", "Microsoft Windows UEFI Driver Publisher"),
        ("EFI/boot/grubx64.efi", "Debian Secure Boot Signer 2022 - grub2"),
        ("live/vmlinuz-6.1.0-53-amd64", "Debian Secure Boot Signer 2022 - linux"),
    ):
        item = components[path]
        assert signer in item["signer"]
        assert item["verification"] == "cryptographic signature and PE digest verified"
        assert item["iso_usb_identical"] is True
        assert re.fullmatch("[a-f0-9]{64}", item["sha256"])
        assert re.fullmatch("[a-f0-9]{64}", item["authenticode_sha256"])
    assert components["EFI/boot/bootia32.efi"]["verification"] == "unsigned"
    assert components["live/initrd.img-6.1.0-53-amd64"]["verification"] == "outside PE signature chain"
    assert components["usr/lib/shim/shimx64.efi.signed"]["sha256"] == components["EFI/boot/bootx64.efi"]["sha256"]
    assert components["usr/lib/grub/x86_64-efi-signed/gcdx64.efi.signed"]["sha256"] == components["EFI/boot/grubx64.efi"]["sha256"]
    assert receipt["corruption_control"] == "rejected"


def test_canonical_secure_boot_links_resolve():
    for relative in ("secure-boot-acceptance.md", "evidence/secure-boot-119/README.md"):
        path = DOCS / relative
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            assert (path.parent / target).is_file(), (relative, target)
