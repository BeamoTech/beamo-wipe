# SPDX-License-Identifier: GPL-3.0-or-later
"""When a QEMU boot never reaches its screen, the evidence says why.

CI run 40820524524: the BIOS safe-video (troubleshoot) boot finished disk
discovery but never showed the Tk keyboard screen, and the serial log could
not tell a failed X start (the kiosk then falls back to keyboard text
screens, which send no markers) from a hung window. The kiosk now sends a
fixed BEAMO_WIPE_GRAPHICAL_FAILED marker before that fallback, and the gate
saves a guest screenshot when an expected marker never comes. Fake shells
and files only.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KIOSK = ROOT / "packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk"
QEMU = ROOT / "scripts/qemu-verify.sh"
X_MARKERS = {
    "BEAMO_WIPE_X_FB0=1", "BEAMO_WIPE_X_FB0=0", "BEAMO_WIPE_X_DRI=1", "BEAMO_WIPE_X_DRI=0",
    "BEAMO_WIPE_X_LOG_MISSING", "BEAMO_WIPE_X_NO_SCREENS", "BEAMO_WIPE_X_NO_DEVICES",
    "BEAMO_WIPE_X_MODESET_ERROR", "BEAMO_WIPE_X_FBDEV_ERROR", "BEAMO_WIPE_X_VESA_ERROR",
    "BEAMO_WIPE_X_FB_NOT_FOUND",
    "BEAMO_WIPE_X_FB_OPEN_FAILED",
    "BEAMO_WIPE_X_FB_GET_INFO_FAILED",
    "BEAMO_WIPE_X_FB_PUT_VAR_FAILED",
    "BEAMO_WIPE_X_FB_MODE_MODIFIED",
    "BEAMO_WIPE_X_FB_MODE_INIT_FAILED",
    "BEAMO_WIPE_X_FB_MMAP_FAILED",
    "BEAMO_WIPE_X_FB_DEPTH_UNSUPPORTED",
    "BEAMO_WIPE_X_FB_SHADOW_FAILED",
    "BEAMO_WIPE_X_FB_VISUAL_FAILED",
    "BEAMO_WIPE_X_FB_TYPE_UNSUPPORTED",
    "BEAMO_WIPE_X_SCREEN_INIT_FAILED",
    "BEAMO_WIPE_X_NO_USABLE_SCREEN",
    "BEAMO_WIPE_X_MODULE_MISSING", "BEAMO_WIPE_X_FATAL",
}


def _function(source: str, name: str) -> str:
    return name + "() {" + source.split(name + "() {", 1)[1].split("\n}\n", 1)[0] + "\n}\n"


def _run_ui(tmp_path, startx_rc: int) -> tuple[subprocess.CompletedProcess, list[str]]:
    source = KIOSK.read_text(encoding="utf-8")
    serial = tmp_path / "ttyS0"
    serial.write_text("")
    block = (_function(source, "run_console") + _function(source, "graphical_diagnostics")
             + _function(source, "qemu_x_details") + _function(source, "run_ui"))
    block = (
        block.replace("[ -c /dev/ttyS0 ]", f'[ -f "{serial}" ]')
        .replace(">/dev/ttyS0", f'>>"{serial}"')
        .replace("/usr/local/bin/beamo-wipe --console", "fake_console")
        # CI runners may themselves be QEMU guests; the harness is not one.
        .replace("/sys/class/dmi/id/sys_vendor", f"{tmp_path.as_posix()}/no-dmi")
    )
    script = (
        "set -u\n"
        f'XAUTHORITY="{tmp_path}/xauth"\nUI_MODE=standard\n'
        "graphical_rc=not-run\nconsole_rc=not-run\n"
        "say() { :; }\n"
        f"startx() {{ return {startx_rc}; }}\n"
        "fake_console() { echo CONSOLE_RAN; }\n"
        "safe_video_x_config() { :; }\n"
        "firmware_fb_for_x() { :; }\n"
        + block
        + "run_ui\n"
    )
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True, timeout=30)
    return result, serial.read_text().splitlines()


def test_failed_graphical_start_sends_a_fixed_marker_then_falls_back(tmp_path):
    result, markers = _run_ui(tmp_path, 1)
    assert result.returncode == 0, result.stderr
    assert markers[0] == "BEAMO_WIPE_GRAPHICAL_FAILED"
    # Then only fixed classifications: display devices present and known
    # X errors, never log text or hardware names.
    assert set(markers[1:]) <= X_MARKERS
    assert {m.split("=")[0] for m in markers if "=" in m} == {"BEAMO_WIPE_X_FB0", "BEAMO_WIPE_X_DRI"}
    assert "CONSOLE_RAN" in result.stdout


def test_working_graphical_start_sends_no_failure_marker(tmp_path):
    result, markers = _run_ui(tmp_path, 0)
    assert result.returncode == 0, result.stderr
    assert markers == []
    assert "CONSOLE_RAN" not in result.stdout


def test_gate_reports_the_marker_and_saves_a_screenshot_on_a_missed_marker():
    source = QEMU.read_text(encoding="utf-8")
    summary = _function(source, "report_marker_summary")
    assert "BEAMO_WIPE_GRAPHICAL_FAILED" in summary
    for marker in X_MARKERS:
        assert marker in summary, marker
    kiosk = KIOSK.read_text(encoding="utf-8")
    emitted = set(re.findall(r"echo (BEAMO_WIPE_X_[A-Z0-9_]+(?:=[01])?)", kiosk))
    emitted |= set(re.findall(r"\n\s+echo (BEAMO_WIPE_X_[A-Z0-9_]+)", kiosk))
    assert emitted == X_MARKERS
    waiting = _function(source, "wait_for_marker")
    timeout_branch = waiting.rsplit('report_marker_summary "$label"', 1)[1]
    assert 'capture_guest_screen "$label"' in timeout_branch
    capture = _function(source, "capture_guest_screen")
    assert 'qmp_request "$socket_path" screendump "$EVIDENCE_DIR/${label}-screen.png"' in capture
    assert "|| true" in capture  # diagnostics never change the outcome
    qmp = _function(source, "qmp_request")
    assert 'execute("screendump", {"filename": value, "format": "png"}, "screendump")' in qmp


def test_capture_is_skipped_without_a_live_qmp_socket(tmp_path):
    source = QEMU.read_text(encoding="utf-8")
    script = (
        "set -euo pipefail\n"
        f'RUN_ROOT="{tmp_path}"\nEVIDENCE_DIR="{tmp_path}"\n'
        "qmp_request() { echo CALLED; }\n"
        + _function(source, "capture_guest_screen")
        + "capture_guest_screen bios-troubleshoot-usb\necho DONE\n"
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["DONE"]


def _safe_video_args(tmp_path, cmdline: str, fb0: bool, dri: bool) -> list[str]:
    """The X server arguments run_ui passes after "--", from fake devices."""
    source = KIOSK.read_text(encoding="utf-8")
    dev = tmp_path / "dev"
    (dev / "dri").mkdir(parents=True)
    if fb0:
        (dev / "fb0").write_text("")
    if dri:
        (dev / "dri" / "card0").write_text("")
    (tmp_path / "cmdline").write_text(cmdline + "\n")
    block = _function(source, "boot_has_word") + _function(source, "safe_video_x_config")
    block = block.replace("/proc/cmdline", f'"{tmp_path.as_posix()}/cmdline"')
    block = block.replace("[ -e /dev/", f"[ -e {dev.as_posix()}/")
    startx = next(line for line in _function(source, "run_ui").splitlines()
                  if "startx /usr/local/bin/beamo-wipe --" in line and "--accessible" not in line)
    server = startx.split(" -- ", 1)[1].split(" || ", 1)[0]
    script = (
        "set -u\n" + 'SAFE_VIDEO_X_CONFIG=beamo-safe-video.conf\n' + block
        + 'x_config="$(safe_video_x_config)"\n'
        + "printf '%s\\n' " + server + "\n"
    )
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.split("\n")[:-1]


def test_uefi_safe_video_points_x_at_the_firmware_framebuffer(tmp_path):
    # CI run 41237147966: fb0 present, no DRM device, X tried only vesa.
    args = _safe_video_args(tmp_path, "boot=live nomodeset nosplash", fb0=True, dri=False)
    assert args == ["-nolisten", "tcp", "vt1", "-config", "beamo-safe-video.conf"]
    config = (ROOT / "packaging/live/config/includes.chroot/etc/X11/beamo-safe-video.conf").read_text(
        encoding="utf-8")
    assert 'Driver "fbdev"' in config and 'Option "fbdev" "/dev/fb0"' in config
    assert "BusID" not in config and 'Driver "vesa"' not in config


def test_other_sessions_leave_x_autodetection_alone(tmp_path):
    # BIOS safe video (no framebuffer: vesa works), KMS present, or a normal
    # boot: X gets no extra config file.
    plain = ["-nolisten", "tcp", "vt1"]
    assert _safe_video_args(tmp_path / "a", "boot=live nomodeset", fb0=False, dri=False) == plain
    assert _safe_video_args(tmp_path / "b", "boot=live nomodeset", fb0=True, dri=True) == plain
    assert _safe_video_args(tmp_path / "c", "boot=live quiet", fb0=True, dri=False) == plain


def test_safe_video_writes_nothing_under_the_read_only_etc():
    # CI run 41255192420: the kiosk service has ProtectSystem=full, so a
    # runtime write to /etc/X11/xorg.conf.d failed silently.
    unit = (ROOT / "packaging/live/config/includes.chroot/etc/systemd/system/"
            "beamo-wipe-kiosk.service").read_text(encoding="utf-8")
    assert "ProtectSystem=full" in unit
    source = KIOSK.read_text(encoding="utf-8")
    body = _function(source, "safe_video_x_config")
    assert ">" not in body.replace("2>/dev/null", "")
    assert "xorg.conf.d/20-beamo" not in source
    run_ui = _function(source, "run_ui")
    assert run_ui.index('x_config="$(safe_video_x_config)"') < run_ui.index("startx ")
    assert run_ui.count('${x_config:+-config "$x_config"}') == 2
    assert not (ROOT / "packaging/live/config/includes.chroot/etc/X11/xorg.conf.d/"
                "20-beamo-safe-video.conf").exists()


def _firmware_fb(tmp_path, *, fb0=True, dri=False, link="../../devices/pci0000:00/0000:00:02.0/"
                 "efi-framebuffer.0/graphics/fb0", bus="../../../../bus/platform"):
    """Run firmware_fb_for_x against a fake /dev and sysfs; mount and ln are
    recorded, never run."""
    source = KIOSK.read_text(encoding="utf-8")
    dev = tmp_path / "dev"
    (dev / "dri").mkdir(parents=True)
    if fb0:
        (dev / "fb0").write_text("")
    if dri:
        (dev / "dri" / "card0").write_text("")
    calls = tmp_path / "calls"
    block = _function(source, "firmware_fb_for_x")
    block = block.replace("[ -e /dev/", f"[ -e {dev.as_posix()}/")
    script = (
        "set -u\n"
        f'FIRMWARE_FB_LINK=x\n'
        f'readlink() {{ case "$1" in */device/subsystem) [ -n "{bus}" ] && echo "{bus}" ;; '
        f'*) [ -n "{link}" ] && echo "{link}" ;; esac; }}\n'
        f'mount() {{ echo "mount $*" >>"{calls.as_posix()}"; }}\n'
        f'ln() {{ echo "ln $*" >>"{calls.as_posix()}"; }}\n'
        + block + "firmware_fb_for_x\n"
    )
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return calls.read_text().splitlines() if calls.exists() else []


def test_firmware_framebuffer_under_pci_gets_a_link_x_accepts(tmp_path):
    # Linux 6.12 sysfb parent + Xorg 21.1.7 fbdevhw (CI run 41258566638:
    # -config used, fbdev tried, still no screens).
    calls = _firmware_fb(tmp_path)
    assert calls == [
        "mount -t tmpfs -o mode=0755,size=64k,nosuid,nodev,noexec beamo-graphics /sys/class/graphics",
        "ln -s x /sys/class/graphics/fb0",
    ]
    source = KIOSK.read_text(encoding="utf-8")
    assert "FIRMWARE_FB_LINK=../../devices/platform/" in source
    assert "devices/pci" not in source.split("FIRMWARE_FB_LINK=", 1)[1].split("\n", 1)[0]


def test_firmware_framebuffer_link_is_left_alone_otherwise(tmp_path):
    # DRM bound, no fb0, fb0 not under PCI (e.g. older kernels), a real PCI
    # GPU fbdev driver (bus pci), or an unreadable link: nothing is mounted.
    assert _firmware_fb(tmp_path / "a", dri=True) == []
    assert _firmware_fb(tmp_path / "b", fb0=False) == []
    assert _firmware_fb(tmp_path / "c", link="../../devices/platform/efi-framebuffer.0/graphics/fb0") == []
    assert _firmware_fb(tmp_path / "d", bus="../../../../bus/pci") == []
    assert _firmware_fb(tmp_path / "e", link="") == []
    assert _firmware_fb(tmp_path / "f", bus="") == []


def test_firmware_framebuffer_link_stays_in_the_private_namespace():
    unit = (ROOT / "packaging/live/config/includes.chroot/etc/systemd/system/"
            "beamo-wipe-kiosk.service").read_text(encoding="utf-8")
    assert "PrivateMounts=yes" in unit
    run_ui = _function(KIOSK.read_text(encoding="utf-8"), "run_ui")
    assert run_ui.index("firmware_fb_for_x") < run_ui.index("startx ")


def test_uefi_safe_video_runs_after_the_other_qemu_stages_with_its_own_target():
    source = QEMU.read_text(encoding="utf-8")
    probe = source.index("uefi_boot_probe uefi-troubleshoot-usb ovmf-troubleshoot-vars.fd")
    for earlier in ("boot_probe secureboot-usb no", "run_bus_journey bios-sata-usb sata 0004 vfat",
                    "run_bus_journey uefi-nvme-usb nvme 0005 exfat \\"):
        assert source.index(earlier) < probe, earlier
    assert probe < source.index("ABORT: USB image changed during QEMU verification")
    saved = source.index('troubleshoot_uefi_target="$TARGET"')
    # Saved after the UEFI probes and Secure Boot, before any bus journey.
    assert source.index("boot_probe secureboot-usb no") < saved < source.index("run_bus_journey() {")
    assert source.index('uefi_boot_probe uefi-speech-usb ovmf-speech-vars.fd') < saved
    restore = source[:probe].rsplit("\nfi\n", 1)[1]
    assert restore.split() == [
        'TARGET="$troubleshoot_uefi_target"',
        'QEMU_TARGET_SERIAL="$troubleshoot_uefi_serial"',
        'REPORT_RAW="$troubleshoot_uefi_report"',
    ]


def test_qemu_details_are_sent_only_inside_a_qemu_guest(tmp_path):
    source = KIOSK.read_text(encoding="utf-8")
    log = tmp_path / "Xorg.0.log"
    log.write_text(
        '[    12.3] (II) FBDEV(0): Modeline "current"x0.0   20.83  800 832 928 1024  600 604 608 624\n'
        "[    12.4] (EE) FBDEV(0): FBIOPUT_VSCREENINFO succeeded but modified mode\n"
        "[    12.5] (II) unrelated line\n"
    )
    vendor = tmp_path / "sys_vendor"
    block = _function(source, "qemu_x_details").replace(
        "/sys/class/dmi/id/sys_vendor", vendor.as_posix()
    ).replace("/sys/bus/platform/devices/*/graphics/fb0", f"{tmp_path.as_posix()}/none/*")

    def run():
        result = subprocess.run(["sh", "-c", "set -u\n" + block + f'qemu_x_details "{log.as_posix()}"\n'],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        return result.stdout.splitlines()

    vendor.write_text("LENOVO\n")
    assert run() == []
    vendor.write_text("QEMU\n")
    lines = run()
    log_lines = [line for line in lines if line.startswith("BEAMO_WIPE_QEMU_X_LOG ")]
    assert len(log_lines) == 2 and all(line.startswith("BEAMO_WIPE_QEMU_X_LOG [") for line in log_lines)
    assert "modified mode" in log_lines[1]
    # Then the kernel framebuffer var/fix, or a fixed marker when unreadable.
    rest = lines[2:]
    assert rest and all(line.startswith("BEAMO_WIPE_QEMU_FB_") for line in rest)
    # graphical_diagnostics calls it last, after the fixed classes.
    body = _function(source, "graphical_diagnostics")
    assert body.rstrip().splitlines()[-3].strip() == 'qemu_x_details "$x_log"'


def test_grub_hands_linux_a_32_bit_framebuffer_when_it_can():
    # CI run 41272451830: fb0 was 800x600 at 24 bpp packed (line 2400), set
    # by GRUB's bochs driver; X (no 24bpp pixmaps) asked fbdev for 32 bpp
    # and fbdevhw rejected the unchanged 24-bpp var. Firmware GOP modes are
    # almost always 32 bpp; the fallbacks keep the old choice elsewhere.
    config = (ROOT / "packaging/live/config/bootloaders/grub-pc/config.cfg").read_text(
        encoding="utf-8")
    lines = [line.strip() for line in config.splitlines()]
    assert "set gfxmode=800x600x32,800x600,auto" in lines
    assert "set gfxmode=800x600" not in lines
    assert lines.index("set gfxmode=800x600x32,800x600,auto") < lines.index("set gfxpayload=keep")
