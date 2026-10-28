# SPDX-License-Identifier: GPL-3.0-or-later
"""Hardware support in the live image: kernel, firmware, microcode, keymaps.

Source-level contract only. The hosted QEMU gate inspects the built squashfs
(installed packages, firmware files, keymaps); real hardware stays NOT TESTED.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "packaging/live"
PACKAGES = LIVE / "config/package-lists/beamo.list.chroot"
PREF = LIVE / "config/archives/backports.pref.chroot"
INSIDE = LIVE / "inside-docker.sh"
QEMU = ROOT / "scripts/qemu-verify.sh"

FIRMWARE = (
    "firmware-amd-graphics", "firmware-intel-graphics", "firmware-nvidia-graphics",
    "firmware-misc-nonfree", "firmware-intel-misc", "firmware-sof-signed",
    "firmware-intel-sound", "firmware-cirrus", "intel-microcode", "amd64-microcode",
)
RADIO = ("firmware-iwlwifi", "firmware-atheros", "firmware-brcm80211", "firmware-realtek",
         "firmware-mediatek", "firmware-libertas", "firmware-linux-nonfree", "firmware-linux")


def _packages() -> set[str]:
    return {
        line.strip() for line in PACKAGES.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _lb_option(name: str) -> str:
    text = INSIDE.read_text(encoding="utf-8")
    (line,) = [ln for ln in text.splitlines() if ln.strip().startswith(f"--{name} ")]
    return line.split(f"--{name} ", 1)[1].rstrip(" \\").strip('"')


def test_display_audio_usb_firmware_microcode_and_keymaps_are_listed():
    packages = _packages()
    for name in (*FIRMWARE, "console-data", "linux-image-amd64", "kbd", "console-setup"):
        assert name in packages, name


def test_no_radio_or_catch_all_firmware():
    packages = _packages()
    for name in RADIO:
        assert name not in packages, name
    # live-build's automatic firmware selection would pull every blob, Wi-Fi included.
    assert _lb_option("firmware-chroot") == "false"
    assert _lb_option("firmware-binary") == "false"


def test_archive_areas_enable_only_main_and_non_free_firmware():
    for option in ("archive-areas", "parent-archive-areas"):
        assert _lb_option(option).split() == ["main", "non-free-firmware"]
    assert _lb_option("backports") == "true"
    assert _lb_option("distribution") == "bookworm"


def test_backports_pin_covers_only_kernel_and_firmware():
    stanzas = [s for s in PREF.read_text(encoding="utf-8").split("\n\n") if "Package:" in s]
    assert len(stanzas) == 1
    fields = dict(
        line.split(":", 1) for line in stanzas[0].splitlines()
        if line and not line.startswith("#")
    )
    assert fields["Pin"].strip() == "release n=bookworm-backports"
    assert int(fields["Pin-Priority"]) > 500
    patterns = fields["Package"].split()
    assert set(patterns) == {"linux-image-*", "linux-kbuild-*", "linux-base", "firmware-*"}
    # Userland, boot chain and engine dependencies never come from backports.
    for name in ("shim-signed", "grub-efi-amd64-signed", "live-boot", "python3",
                 "systemd", "xserver-xorg-core", "libparted2", "initramfs-tools"):
        assert not any(re.fullmatch(p.replace("*", ".*"), name) for p in patterns), name


def test_normal_boot_is_quiet_and_troubleshoot_stays_verbose():
    normal = _lb_option("bootappend-live").split()
    failsafe = _lb_option("bootappend-live-failsafe").split()
    assert {"quiet", "loglevel=3"} <= set(normal)
    assert "quiet" not in failsafe
    for flag in ("boot=live", "nopersistence", "noswap", "ip=frommedia", "nox11autologin"):
        assert flag in normal and flag in failsafe


def test_usb_and_nvme_stay_awake_on_every_entry():
    for option in ("bootappend-live", "bootappend-live-failsafe"):
        flags = _lb_option(option).split()
        assert "usbcore.autosuspend=-1" in flags, option
        assert "nvme_core.default_ps_max_latency_us=0" in flags, option


def test_qemu_gate_inspects_kernel_firmware_and_every_offered_keymap():
    source = QEMU.read_text(encoding="utf-8")
    for name in (*FIRMWARE, "console-data"):
        assert name in source, name
    assert 'dpkg --compare-versions "$kernel_version" ge 6.12' in source
    # First Debian 12 shim-signed dual-signed by the Microsoft UEFI CA 2011 and 2023.
    assert "-W -f='${Version}' shim-signed)" in source
    assert "dpkg --compare-versions \"$shim_version\" ge '1.51~1+deb12u1'" in source
    for directory in ("amdgpu", "i915", "nvidia", "intel/sof", "intel-ucode", "amd-ucode"):
        assert directory in source, directory
    assert "for layout in keyboard.LAYOUTS.values():" in source
    assert '"$SQUASH_MOUNT/usr/share/X11/xkb/symbols/$xkb_layout"' in source
    assert '-name "${console_map}.kmap.gz"' in source
    for name in RADIO[:6]:
        assert name in source, name


def test_amd_early_microcode_does_not_depend_on_the_build_cpu():
    # amd64-microcode's default "auto" adds AMD early microcode only when the
    # build worker's own CPU is AMD; the image must carry it for every PC.
    default = LIVE / "config/includes.chroot/etc/default/amd64-microcode"
    settings = [
        line.strip() for line in default.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert settings == ["AMD64UCODE_INITRAMFS=early"]
    gate = QEMU.read_text(encoding="utf-8")
    for vendor in ("AuthenticAMD", "GenuineIntel"):
        assert f"kernel/x86/microcode/{vendor}.bin" in gate


def _newc(*names: str) -> bytes:
    """An uncompressed newc cpio archive of empty regular files."""
    out = b""
    for name in (*names, "TRAILER!!!"):
        encoded = name.encode() + b"\0"
        fields = [0, 0o100644, 0, 0, 1, 0, 0, 0, 0, 0, 0, len(encoded), 0]
        entry = b"070701" + b"".join(b"%08x" % value for value in fields) + encoded
        out += entry + b"\0" * (-len(entry) % 4)
    return out + b"\0" * (-len(out) % 512)


def _run_microcode_gate(tmp_path, *initrds: bytes):
    import subprocess
    import sys

    gate = QEMU.read_text(encoding="utf-8")
    start = gate.index('python3 - "$ISO_MOUNT/live" <<\'PY\' || exit 2\n')
    body = gate[gate.index("\n", start) + 1:]
    body = body[:body.index("\nPY\n")]
    live = tmp_path / "live"
    live.mkdir()
    for index, data in enumerate(initrds):
        (live / ("initrd.img" if index == 0 else f"initrd.img-6.12.{index}")).write_bytes(data)
    return subprocess.run(  # noqa: S603 - fixed interpreter and gate text
        [sys.executable, "-c", body, str(live)], capture_output=True, text=True, check=False,
    )


def test_microcode_gate_reads_every_early_archive(tmp_path):
    amd = _newc("kernel", "kernel/x86", "kernel/x86/microcode",
                "kernel/x86/microcode/AuthenticAMD.bin")
    intel = _newc("./kernel/x86/microcode/GenuineIntel.bin")
    main = b"\x1f\x8b compressed main archive"
    passed = _run_microcode_gate(tmp_path, amd + intel + main, intel + amd + main)
    assert passed.returncode == 0, passed.stderr


def test_microcode_gate_fails_without_amd_or_without_any_initrd(tmp_path):
    intel_only = _newc("kernel/x86/microcode/GenuineIntel.bin") + b"\x1f\x8b"
    failed = _run_microcode_gate(tmp_path, intel_only)
    assert failed.returncode != 0 and "AuthenticAMD.bin" in failed.stderr
    empty = tmp_path / "none"
    empty.mkdir()
    assert _run_microcode_gate(empty).returncode != 0
