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
