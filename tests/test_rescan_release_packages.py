# SPDX-License-Identifier: GPL-3.0-or-later
"""Published-release rescan for fixed Debian vulnerabilities (fixture data only)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from beamo_wipe.verification_evidence import build_package_inventory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("beamo_rescan", SCRIPTS / "rescan_release_packages.py")
rescan = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(rescan)


@pytest.mark.parametrize("a,b,expected", [
    ("1.0", "1.0", 0),
    ("1.0-1", "1.0-2", -1),
    ("1.0~rc1", "1.0", -1),
    ("1.0", "1.0+deb12u1", -1),
    ("2.36-9+deb12u10", "2.36-9+deb12u9", 1),
    ("1:2.66-4", "2.70-1", 1),
    ("6.1.0-53", "6.1.0-6", 1),
    ("3.0.17-1~deb12u2", "3.0.17-1~deb12u3", -1),
    ("1.2a", "1.2", 1),
    ("252.38-1~deb12u1", "252.39-1~deb12u1", -1),
    ("0.9", "0.10", -1),
])
def test_debian_version_ordering_matches_dpkg(a, b, expected):
    assert rescan.compare_versions(a, b) == expected
    assert rescan.compare_versions(b, a) == -expected


def _manifest(packages):
    inventory = build_package_inventory(
        packages=packages, collected_from="squashfs var/lib/dpkg/status",
        apt_sources=["https://deb.debian.org/debian/"], source_commit="a" * 40,
        generated_at="2026-10-18T00:00:00Z",
    )
    return {"beamo_wipe_version": "0.2.13", "installed_packages": inventory}


PACKAGES = [
    {"name": "libssl3", "version": "3.0.17-1~deb12u2", "arch": "amd64", "source": "openssl"},
    {"name": "libc6", "version": "2.36-9+deb12u10", "arch": "amd64", "source": "glibc"},
    {"name": "bash", "version": "5.2.15-2+b8", "arch": "amd64", "source": "bash (5.2.15-2)"},
]
TRACKER = {
    "openssl": {
        "CVE-2026-0001": {"releases": {"bookworm": {"status": "resolved", "fixed_version": "3.0.17-1~deb12u3", "urgency": "high"}}},
        "CVE-2025-9999": {"releases": {"bookworm": {"status": "resolved", "fixed_version": "3.0.17-1~deb12u2"}}},
        "CVE-2026-0002": {"releases": {"bookworm": {"status": "open", "urgency": "low"}}},
    },
    "glibc": {"CVE-2026-0003": {"releases": {"bookworm": {"status": "resolved", "fixed_version": "0"}}}},
    "bash": {"CVE-2026-0004": {"releases": {"trixie": {"status": "resolved", "fixed_version": "5.3-1"}}}},
}


def test_rescan_lists_only_fixed_issues_newer_than_the_installed_source():
    findings = rescan.rescan(_manifest(PACKAGES), TRACKER, "bookworm")
    assert findings == [{
        "source": "openssl", "installed": "3.0.17-1~deb12u2", "fixed": "3.0.17-1~deb12u3",
        "issue": "CVE-2026-0001", "urgency": "high", "suite": "bookworm",
    }]


def test_rescan_refuses_unmeasured_or_tampered_inventory():
    manifest = _manifest(PACKAGES)
    manifest["installed_packages"]["measured"] = False
    with pytest.raises(RuntimeError, match="measured"):
        rescan.rescan(manifest, TRACKER, "bookworm")
    manifest = _manifest(PACKAGES)
    manifest["installed_packages"]["packages"][0]["version"] = "9.9"
    with pytest.raises(RuntimeError):
        rescan.rescan(manifest, TRACKER, "bookworm")


def test_cli_exit_codes(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    tracker = tmp_path / "tracker.json"
    manifest.write_text(json.dumps(_manifest(PACKAGES)))
    tracker.write_text(json.dumps(TRACKER))
    assert rescan.main([str(manifest), "--tracker", str(tracker)]) == 1
    assert "1 fixed issues missing across 1 source packages" in capsys.readouterr().out
    tracker.write_text(json.dumps({}))
    assert rescan.main([str(manifest), "--tracker", str(tracker)]) == 0
    assert rescan.main([str(tmp_path / "missing.json"), "--tracker", str(tracker)]) == 2


# Debian 12 image with the bookworm-backports kernel: records as dpkg
# reports them (signed wrappers name their own source and version).
BOOT_PACKAGES = [
    {"name": "linux-image-6.12.95+deb12-amd64", "version": "6.12.95-1~bpo12+1", "arch": "amd64",
     "source": "linux-signed-amd64 (6.12.95+1~bpo12+1)"},
    {"name": "grub-efi-amd64-signed", "version": "1+2.06+13+deb12u1", "arch": "amd64",
     "source": ""},
    {"name": "shim-signed", "version": "1.51~1+deb12u1+16.1-2~deb12u1", "arch": "amd64",
     "source": "shim-signed (1.51~1+deb12u1)"},
]
BOOT_TRACKER = {
    "linux": {
        # Fixed in trixie after the backport was built: missing.
        "CVE-2026-1001": {"releases": {
            "bookworm": {"status": "resolved", "fixed_version": "6.1.170-1"},
            "trixie": {"status": "resolved", "fixed_version": "6.12.113-1", "urgency": "high"},
        }},
        # Fixed in exactly the trixie version the backport was built from.
        "CVE-2026-1002": {"releases": {
            "trixie": {"status": "resolved", "fixed_version": "6.12.95-1"},
        }},
    },
    "grub2": {"CVE-2026-1003": {"releases": {
        "bookworm": {"status": "resolved", "fixed_version": "2.06-13+deb12u2"},
    }}},
    "shim": {"CVE-2026-1004": {"releases": {
        "bookworm": {"status": "resolved", "fixed_version": "16.1-2~deb12u1"},
    }}},
}


def test_signed_boot_packages_and_backports_are_checked_as_their_real_sources():
    findings = rescan.rescan(_manifest(BOOT_PACKAGES), BOOT_TRACKER, "bookworm")
    assert [(f["source"], f["installed"], f["fixed"], f["issue"], f["suite"]) for f in findings] == [
        ("grub2", "2.06-13+deb12u1", "2.06-13+deb12u2", "CVE-2026-1003", "bookworm"),
        ("linux", "6.12.95-1~bpo12+1", "6.12.113-1", "CVE-2026-1001", "trixie"),
    ]


# The shipped route: Debian 12 LTS's linux-6.12 from bookworm-security. The
# tracker files its fixes under the versioned source for bookworm.
LTS_KERNEL = [
    {"name": "linux-image-6.12.113+deb12-amd64", "version": "6.12.113-1~deb12u1", "arch": "amd64",
     "source": "linux-signed-6.12-amd64 (6.12.113+1~deb12u1)"},
    {"name": "linux-image-6.12-amd64", "version": "6.12.113-1~deb12u1", "arch": "amd64",
     "source": "linux-signed-6.12-amd64 (6.12.113+1~deb12u1)"},
]
LTS_TRACKER = {
    "linux-6.12": {
        "CVE-2026-2001": {"releases": {
            "bookworm": {"status": "resolved", "fixed_version": "6.12.113-1~deb12u1"},
        }},
        "CVE-2026-2002": {"releases": {
            "bookworm": {"status": "resolved", "fixed_version": "6.12.117-1~deb12u1", "urgency": "high"},
        }},
    },
    # The 6.1 kernel's issues never apply to the 6.12 source.
    "linux": {"CVE-2026-2003": {"releases": {
        "bookworm": {"status": "resolved", "fixed_version": "6.1.199-1"},
    }}},
}


def test_lts_kernel_is_checked_as_bookworm_linux_6_12():
    findings = rescan.rescan(_manifest(LTS_KERNEL), LTS_TRACKER, "bookworm")
    assert [(f["source"], f["installed"], f["fixed"], f["issue"], f["suite"]) for f in findings] == [
        ("linux-6.12", "6.12.113-1~deb12u1", "6.12.117-1~deb12u1", "CVE-2026-2002", "bookworm"),
    ]


def test_cli_marks_findings_from_another_release(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    tracker = tmp_path / "tracker.json"
    manifest.write_text(json.dumps(_manifest(BOOT_PACKAGES)))
    tracker.write_text(json.dumps(BOOT_TRACKER))
    assert rescan.main([str(manifest), "--tracker", str(tracker)]) == 1
    out = capsys.readouterr().out
    assert "linux 6.12.95-1~bpo12+1 < 6.12.113-1 [trixie]  CVE-2026-1001 high" in out
    assert "grub2 2.06-13+deb12u1 < 2.06-13+deb12u2  CVE-2026-1003" in out
