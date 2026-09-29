# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep active physical expectations consistent with the inspected boot chain.

These checks inspect documentation only; they never alter firmware or run nwipe.
Historical releases and execution logs deliberately remain outside this policy.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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


def _check_operator_identity(text, receipt):
    rows = {
        cells[0]: cells[1]
        for line in text.splitlines()
        if line.startswith("| ")
        for cells in [[cell.strip() for cell in line.strip("|").split("|")]]
        if len(cells) == 2
    }
    assert re.findall(r"[a-f0-9]{40}", rows["Source"]) == [receipt["source_commit"]]
    assert f'`{receipt["tag"]}`' in rows["Source"]
    assert rows["Build"] == f'`{receipt["build_id"]}`, Blacksmith'
    version = receipt["tag"].removeprefix("v")
    for row, prefix, extension in (
        ("ISO", "iso", "iso"),
        ("Compressed USB download", "usb_gzip", "img.gz"),
        ("Decompressed USB", "usb", "img"),
    ):
        assert rows[row] == (
            f'`beamo-wipe-{version}-amd64.{extension}`, '
            f'{receipt[prefix + "_size_bytes"]} bytes, '
            f'SHA-256 `{receipt[prefix + "_sha256"]}`'
        )
    assert re.findall(r"[a-f0-9]{64}", rows["Signed manifest"]) == [receipt["manifest_sha256"]]


def test_operator_identity_matches_pinned_receipt():
    receipt = json.loads((DOCS / "evidence/secure-boot-119/components.json").read_text())
    assert receipt["iso_size_bytes"] == 564133888
    assert receipt["usb_size_bytes"] == 2147483648
    assert receipt["usb_gzip_size_bytes"] == 601441384
    assert receipt["usb_gzip_sha256"] == "a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972"
    _check_operator_identity((DOCS / "secure-boot-acceptance.md").read_text(), receipt)


@pytest.mark.parametrize("field", ["iso_sha256", "usb_sha256", "usb_gzip_sha256", "manifest_sha256"])
def test_operator_identity_rejects_a_changed_displayed_hash(field):
    receipt = json.loads((DOCS / "evidence/secure-boot-119/components.json").read_text())
    text = (DOCS / "secure-boot-acceptance.md").read_text()
    changed = text.replace(receipt[field], "0" * 64)
    assert changed != text
    with pytest.raises(AssertionError):
        _check_operator_identity(changed, receipt)


@pytest.mark.parametrize("case", ["match", "larger", "corrupt", "short", "missing", "zero", "invalid", "unset", "missing_reference", "wrong_size"])
def test_documented_readback_with_disposable_regular_files(tmp_path, case):
    if os.name != "posix":
        pytest.skip("documented readback command requires a POSIX shell")
    text = (HUB / "README.md").read_text()
    match = re.search(r"<!-- media-readback-command -->\n```sh\n(.*?)\n```", text, re.S)
    assert match, "physical procedure must provide the post-flash comparison"
    reference = tmp_path / "verified image.img"
    media = tmp_path / "fake media.img"
    payload = bytes(range(256)) * 8193  # Cross two read boundaries and a partial final chunk.
    reference.write_bytes(payload)
    media.write_bytes(payload)
    if case == "larger":
        media.write_bytes(payload + b"unused capacity")
    elif case == "corrupt":
        media.write_bytes(payload[:-1] + b"x")
    elif case == "short":
        media.write_bytes(payload[:-1])
    elif case == "missing":
        media.unlink()
    elif case == "missing_reference":
        reference.unlink()
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    env = {
        **os.environ,
        "VERIFIED_IMAGE": str(reference),
        "LAB_USB_DEVICE": str(media),
        "IMAGE_BYTES": str(len(payload)),
    }
    if case in ("zero", "invalid"):
        env["IMAGE_BYTES"] = "0" if case == "zero" else "invalid"
    elif case == "unset":
        del env["LAB_USB_DEVICE"]
    elif case == "wrong_size":
        env["IMAGE_BYTES"] = str(len(payload) - 1)
    result = subprocess.run(
        ["/bin/sh", "-c", match[1]], env=env, capture_output=True, text=True, timeout=5,
    )
    if case in ("match", "larger"):
        assert result.returncode == 0, result.stderr
        assert f"READBACK MATCH: {len(payload)} bytes" in result.stdout
    else:
        assert result.returncode != 0
        assert "READBACK MATCH" not in result.stdout
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_physical_readback_is_required_and_recorded():
    canonical = (DOCS / "secure-boot-acceptance.md").read_text()
    assert "#post-flash-readback" in canonical
    assert "SB-INSPECTION" in canonical
    procedure = (HUB / "README.md").read_text()
    assert "Complete the post-flash readback" in procedure
    assert "Re-run readback after any subsequent write" in procedure
    assert "never Pass" in procedure
    identity = (HUB / "BUILD-IDENTITY.md").read_text()
    assert "Post-flash readback" in identity
    assert "Readback byte count" in identity
