# SPDX-License-Identifier: GPL-3.0-or-later
"""Live-image boot hardening from shipped source files and fake shells only.

- The troubleshoot entry is safe video (nomodeset), without legacy failsafe
  flags that can hang or stall modern UEFI PCs.
- GRUB has a superuser and no published password, so every entry and
  submenu must stay --unrestricted or it becomes an unusable login prompt.
- Ctrl+Alt+Del and Magic SysRq cannot reboot past the running-erase guard.
- The QEMU gate boots the troubleshoot entry and checks the built image.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "packaging/live"
CHROOT = LIVE / "config/includes.chroot"
HOOK = LIVE / "config/hooks/normal/0500-build-nwipe.hook.chroot"
GRUB = LIVE / "config/bootloaders/grub-pc/grub.cfg"
GRUB_CONFIG = LIVE / "config/bootloaders/grub-pc/config.cfg"
KIOSK = CHROOT / "usr/local/sbin/beamo-wipe-kiosk"
SYSTEM_CONF = CHROOT / "etc/systemd/system.conf.d/beamo-kiosk.conf"
SYSCTL = CHROOT / "etc/sysctl.d/90-beamo-kiosk.conf"
QEMU = ROOT / "scripts/qemu-verify.sh"
PUBLISHER = ROOT / "scripts/publish_release_gcs.py"


def _bootappend(name: str) -> list[str]:
    text = (LIVE / "inside-docker.sh").read_text(encoding="utf-8")
    marker = f'--{name} "'
    (line,) = [ln for ln in text.splitlines() if marker in ln]
    return line.split(marker, 1)[1].rsplit('"', 1)[0].split()


def test_troubleshoot_entry_is_safe_video_not_legacy_failsafe():
    normal = _bootappend("bootappend-live")
    failsafe = _bootappend("bootappend-live-failsafe")
    # Every safety flag of the normal entry is retained.
    assert set(normal) <= set(failsafe)
    assert {"nomodeset", "nosplash", "vga=788"} <= set(failsafe)
    for flag in ("memtest", "noapic", "nolapic", "nosmp", "nomce", "nodma", "noapm"):
        assert flag not in failsafe
    assert "nomodeset" not in normal


def test_qemu_requires_safe_video_and_rejects_legacy_flags_on_built_iso():
    source = QEMU.read_text(encoding="utf-8")
    required = re.search(r"for required in (boot=live .*?); do", source, re.S)
    assert required
    flags = required.group(1).replace("\\\n", " ").split()
    assert "nomodeset" in flags and "noapic" not in flags and "memtest" not in flags
    assert "for forbidden in memtest noapic nolapic nosmp; do" in source


def _grub_lines():
    return GRUB.read_text(encoding="utf-8").splitlines()


def test_grub_superuser_has_no_password_so_every_entry_is_unrestricted():
    config = GRUB_CONFIG.read_text(encoding="utf-8")
    assert 'set superusers="beamo"' in config
    assert "password" not in config.lower().replace("no published password", "")
    entries = [
        line.strip() for line in _grub_lines()
        if re.match(r"\s*(menuentry|submenu)\b", line)
    ]
    assert any(line.startswith("submenu 'Utilities...'") for line in entries)
    # The installer submenu is disabled (--debian-installer none) and
    # never generated; every reachable entry must boot without a login.
    reachable = [line for line in entries if "Advanced install options" not in line]
    assert reachable
    for line in reachable:
        assert "--unrestricted" in line, line


def test_ctrl_alt_del_cannot_reboot_the_live_session():
    hook = HOOK.read_text(encoding="utf-8")
    assert "ln -sfn /dev/null /etc/systemd/system/ctrl-alt-del.target" in hook
    assert "systemctl mask ctrl-alt-del.target" in hook
    text = SYSTEM_CONF.read_text(encoding="utf-8")
    assert re.search(r"^\[Manager\]$", text, re.M)
    assert re.search(r"^CtrlAltDelBurstAction=none$", text, re.M)
    # Wizard Shut down still uses systemctl poweroff; nothing masks it.
    assert "poweroff.target" not in hook and "reboot.target" not in hook


def test_magic_sysrq_is_disabled():
    text = SYSCTL.read_text(encoding="utf-8")
    settings = [line for line in text.splitlines() if line and not line.startswith("#")]
    assert settings == ["kernel.sysrq = 0"]


def test_new_policy_files_are_required_root_owned_and_world_readable():
    hook = HOOK.read_text(encoding="utf-8")
    for path in ("/etc/systemd/system.conf.d/beamo-kiosk.conf", "/etc/sysctl.d/90-beamo-kiosk.conf"):
        # Listed in the missing-policy check, chown and chmod 0644 blocks.
        assert hook.count(path) == 3, path


def test_qemu_inspects_the_built_squashfs_for_reboot_key_policy():
    source = QEMU.read_text(encoding="utf-8")
    assert '"$SQUASH_MOUNT/etc/systemd/system/ctrl-alt-del.target"' in source
    assert "^CtrlAltDelBurstAction=none$" in source
    assert "kernel\\.sysrq" in source


def _kiosk_markers(cmdline: str, tmp_path: Path) -> list[str]:
    """Run only the kiosk's marker block with fake /proc/cmdline and serial."""
    source = KIOSK.read_text(encoding="utf-8")
    start = source.index("boot_ui_mode() {")
    end = source.index("# These fixed status values")
    block = source[start:end]
    serial = tmp_path / "ttyS0"
    serial.write_text("")
    fake_cmdline = tmp_path / "cmdline"
    fake_cmdline.write_text(cmdline + "\n")
    block = (
        block.replace("/proc/cmdline", str(fake_cmdline))
        .replace("[ -c /dev/ttyS0 ]", f"[ -f {serial} ]")
        .replace(">/dev/ttyS0", f">>{serial}")
    )
    script = "set -eu\nsay() { :; }\n" + block
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return serial.read_text().splitlines()


@pytest.mark.parametrize("cmdline,expected", [
    ("boot=live nox11autologin nomodeset nosplash vga=788", True),
    ("boot=live nox11autologin", False),
    ("boot=live xnomodeset nomodesetx", False),
    ("boot=live beamo.ui=accessible", False),
])
def test_kiosk_reports_safe_video_only_for_the_exact_kernel_word(tmp_path, cmdline, expected):
    markers = _kiosk_markers(cmdline, tmp_path)
    assert markers[0] == "BEAMO_WIPE_KIOSK_READY"
    assert ("BEAMO_WIPE_SAFE_VIDEO=1" in markers) is expected
    assert ("BEAMO_WIPE_UI_MODE=accessible" in markers) is ("beamo.ui=accessible" in cmdline)


def _helper(name: str) -> str:
    source = QEMU.read_text(encoding="utf-8")
    match = re.search(rf"{name}\(\) \{{\n.*?\n\}}\n", source, re.S)
    assert match, name
    return match.group(0)


@pytest.mark.parametrize("label,keys", [
    ("bios-troubleshoot-usb", ["key=t", "key=ret"]),
    ("uefi-troubleshoot-usb", ["key=t"]),
])
def test_troubleshoot_probe_uses_hotkey_until_safe_video_marker(label, keys):
    harness = '''
set -euo pipefail
BOOT_WAIT_SECONDS=120
presses=0
marker_count() { [[ "$2" == BEAMO_WIPE_SAFE_VIDEO=1 && $presses -ge 2 ]] && echo 1 || echo 0; }
send_key() { printf 'key=%s\\n' "$2"; [[ "$2" == t ]] && presses=$((presses + 1)); return 0; }
sleep() { :; }
report_marker_summary() { :; }
log() { printf 'log=%s\\n' "$*"; }
'''
    result = subprocess.run(
        ["bash", "-c", harness + _helper("drive_troubleshoot_boot") + f"\ndrive_troubleshoot_boot {label} /fake/qmp"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[:-1] == keys * 2
    assert lines[-1].startswith(f"log={label} troubleshoot entry booted")


def test_troubleshoot_probe_times_out_with_fixed_summary_only():
    harness = '''
BOOT_WAIT_SECONDS=0
marker_count() { echo 0; }
report_marker_summary() { printf 'safe summary for %s\\n' "$1" >&2; }
'''
    result = subprocess.run(
        ["bash", "-c", harness + _helper("drive_troubleshoot_boot") + "\ndrive_troubleshoot_boot uefi-troubleshoot-usb /fake/qmp"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "safe summary for uefi-troubleshoot-usb" in result.stderr
    assert "never selected the troubleshoot boot entry" in result.stderr


def test_qemu_gate_boots_troubleshoot_entry_on_both_firmware_and_records_it():
    source = QEMU.read_text(encoding="utf-8")
    assert re.search(r"^boot_probe bios-troubleshoot-usb no$", source, re.M)
    assert re.search(r"^uefi_boot_probe uefi-troubleshoot-usb ovmf-troubleshoot-vars\.fd$", source, re.M)
    assert 'if [[ "$label" == *-troubleshoot-usb ]]; then' in source
    assert "troubleshoot_bios_usb=pass" in source and "troubleshoot_uefi_usb=pass" in source
    summary = source.split("report_marker_summary() {", 1)[1].split("\n}", 1)[0]
    assert "BEAMO_WIPE_SAFE_VIDEO=1" in summary
    publisher = PUBLISHER.read_text(encoding="utf-8")
    assert '"bios-troubleshoot-usb",' in publisher and '"uefi-troubleshoot-usb",' in publisher


def test_changed_shell_scripts_parse():
    for path in (QEMU, KIOSK, HOOK, LIVE / "inside-docker.sh"):
        shell = "sh" if path == KIOSK else "bash"
        result = subprocess.run([shell, "-n", str(path)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, (path, result.stderr)


def test_shellcheck_accepts_kiosk_when_available():
    import shutil

    if not shutil.which("shellcheck"):
        pytest.skip("shellcheck not installed")
    result = subprocess.run(
        ["shellcheck", "-s", "sh", str(KIOSK)], capture_output=True, text=True, timeout=60,
        env=dict(os.environ),
    )
    assert result.returncode == 0, result.stdout + result.stderr
