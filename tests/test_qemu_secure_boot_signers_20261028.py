# SPDX-License-Identifier: GPL-3.0-or-later
"""The QEMU gate records the exact image's Secure Boot signers and SBAT.

docs/secure-boot-acceptance.md needs the signer list and SBAT entries of the
next image's shim, GRUB and kernel before release (BW-FIN-SB-Q12). The gate
records them as evidence and requires only the publishers every Debian
signed chain has. Fake PE files and a fake sbverify only.
"""

from __future__ import annotations

from pathlib import Path
import struct
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
QEMU = ROOT / "scripts/qemu-verify.sh"

SHIM_SBAT = "sbat,1,SBAT Version,sbat,1,https://github.com/rhboot/shim/blob/main/SBAT.md\nshim,4,UEFI shim,shim,1,https://github.com/rhboot/shim\n"
GRUB_SBAT = "sbat,1,SBAT Version,sbat,1,https://github.com/rhboot/shim/blob/main/SBAT.md\ngrub,5,Free Software Foundation,grub,2.06,https://www.gnu.org/software/grub/\n"


def _pe(sbat: str | None) -> bytes:
    """A minimal PE image with an optional .sbat section."""
    sections = [(b".text", b"\x90" * 16)]
    if sbat is not None:
        sections.append((b".sbat", sbat.encode() + b"\0" * 7))
    header = bytearray(0x80)
    header[:2] = b"MZ"
    struct.pack_into("<I", header, 0x3C, 0x80)
    optional = 0xF0
    coff = b"PE\0\0" + struct.pack("<HHIIIHH", 0x8664, len(sections), 0, 0, 0, optional, 0x22)
    table = b""
    data = b""
    base = 0x80 + len(coff) + optional + 40 * len(sections)
    for name, body in sections:
        table += name.ljust(8, b"\0") + struct.pack(
            "<IIIIIIHHI", len(body), 0x1000, len(body), base + len(data), 0, 0, 0, 0, 0
        )
        data += body
    return bytes(header) + coff + b"\0" * optional + table + data


def _block() -> str:
    source = QEMU.read_text(encoding="utf-8")
    start = source.index("# Secure Boot chain of this exact image for the human Q12 inspection")
    end = source.index("# Boot menus carry Beamo Wipe identity")
    return source[start:end]


SIGNERS = {
    "bootx64.efi": "image signature issuers:\n - /C=US/O=Microsoft Corporation/CN=Microsoft Corporation UEFI CA 2011\n",
    "grubx64.efi": "image signature issuers:\n - /CN=Debian Secure Boot CA\nsubject: Debian Secure Boot Signer 2022 - grub2\n",
    "vmlinuz-6.12.113+deb12-amd64": "image signature issuers:\n - /CN=Debian Secure Boot CA\n",
}


def _run(tmp_path, signers=SIGNERS, kernel_sbat=None):
    iso = tmp_path / "iso"
    (iso / "EFI/boot").mkdir(parents=True)
    (iso / "live").mkdir()
    (iso / "EFI/boot/bootx64.efi").write_bytes(_pe(SHIM_SBAT))
    (iso / "EFI/boot/grubx64.efi").write_bytes(_pe(GRUB_SBAT))
    (iso / "live/vmlinuz-6.12.113+deb12-amd64").write_bytes(_pe(kernel_sbat))
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    fake = "\n".join(
        f'  *{name}) printf %s {repr(text)} ;;' for name, text in signers.items()
    )
    script = (
        "set -euo pipefail\n"
        f'ISO_MOUNT="{iso}"\nEVIDENCE_DIR="{evidence}"\n'
        'sbverify() {\n  [[ "$1" == --list ]] || return 2\n  case "$2" in\n'
        + fake + "\n  *) echo 'No signature table present'; return 1 ;;\n  esac\n}\n"
        + _block()
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    return result, (evidence / "secure-boot-signers.txt")


def test_signers_and_sbat_of_shim_grub_and_kernel_are_recorded(tmp_path):
    result, evidence = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    text = evidence.read_text()
    for name in ("EFI/boot/bootx64.efi", "EFI/boot/grubx64.efi", "live/vmlinuz-6.12.113+deb12-amd64"):
        assert f"== {name}\n" in text
        assert f"-- sbat {name}\n" in text
    assert "Microsoft Corporation UEFI CA 2011" in text
    assert "shim,4,UEFI shim" in text and "grub,5,Free Software Foundation" in text


@pytest.mark.parametrize("broken", ["bootx64.efi", "grubx64.efi", "vmlinuz-6.12.113+deb12-amd64"])
def test_a_missing_expected_publisher_fails_the_gate(tmp_path, broken):
    signers = dict(SIGNERS)
    signers[broken] = "image signature issuers:\n - /CN=Someone Else\n"
    result, _ = _run(tmp_path, signers)
    assert result.returncode != 0


def test_an_unsigned_component_fails_the_gate(tmp_path):
    signers = {key: value for key, value in SIGNERS.items() if key != "grubx64.efi"}
    result, _ = _run(tmp_path, signers)
    assert result.returncode != 0
    assert "could not list" in result.stderr


def test_worker_installs_sbverify():
    hosted = (ROOT / "scripts/ci-hosted.sh").read_text(encoding="utf-8")
    assert " sbsigntool " in hosted
