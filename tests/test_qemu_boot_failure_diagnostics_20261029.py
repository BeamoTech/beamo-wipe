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
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KIOSK = ROOT / "packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk"
QEMU = ROOT / "scripts/qemu-verify.sh"


def _function(source: str, name: str) -> str:
    return name + "() {" + source.split(name + "() {", 1)[1].split("\n}\n", 1)[0] + "\n}\n"


def _run_ui(tmp_path, startx_rc: int) -> tuple[subprocess.CompletedProcess, list[str]]:
    source = KIOSK.read_text(encoding="utf-8")
    serial = tmp_path / "ttyS0"
    serial.write_text("")
    block = (_function(source, "run_console") + _function(source, "run_ui"))
    block = (
        block.replace("[ -c /dev/ttyS0 ]", f'[ -f "{serial}" ]')
        .replace(">/dev/ttyS0", f'>>"{serial}"')
        .replace("/usr/local/bin/beamo-wipe --console", "fake_console")
    )
    script = (
        "set -u\n"
        f'XAUTHORITY="{tmp_path}/xauth"\nUI_MODE=standard\n'
        "graphical_rc=not-run\nconsole_rc=not-run\n"
        "say() { :; }\n"
        f"startx() {{ return {startx_rc}; }}\n"
        "fake_console() { echo CONSOLE_RAN; }\n"
        + block
        + "run_ui\n"
    )
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True, timeout=30)
    return result, serial.read_text().splitlines()


def test_failed_graphical_start_sends_a_fixed_marker_then_falls_back(tmp_path):
    result, markers = _run_ui(tmp_path, 1)
    assert result.returncode == 0, result.stderr
    assert markers == ["BEAMO_WIPE_GRAPHICAL_FAILED"]
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
