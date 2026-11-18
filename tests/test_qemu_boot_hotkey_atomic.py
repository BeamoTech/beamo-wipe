# SPDX-License-Identifier: GPL-3.0-or-later
"""The BIOS boot-menu hotkey and its Return reach the guest together.

Main run 44120735113 (attempt 2) and PR #113 run 44120852587 (attempt 1)
booted bios-troubleshoot-usb into the normal entry: T and Return were two
taps 0.4 s apart, T was dropped before the guest keyboard was ready and the
Return then booted isolinux's default. The driver also kept pressing T and
Return into the running wizard until its deadline. Now one QMP command
carries both keys, and a boot that reached the kiosk without the requested
entry's marker stops the keys and fails at once.
"""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading

import pytest


QEMU = Path(__file__).resolve().parents[1] / "scripts/qemu-verify.sh"


def _function(source: str, name: str) -> str:
    return f"{name}() {{" + source.split(f"{name}() {{", 1)[1].split("\n}", 1)[0] + "\n}"


# A guest model: keys sent before its keyboard is ready are dropped, and the
# keyboard becomes ready after the first delivery. In the isolinux menu, the
# hotkey selects its entry and Return boots whatever is selected (the normal
# default unless the hotkey arrived first). GRUB's hotkey boots directly.
MOCKS = r"""
state=firmware
SECONDS=0
BOOT_WAIT_SECONDS=120
log() { :; }
report_marker_summary() { printf 'summary\n'; }
sleep() { :; }
deliver() {
  local keys="$1"
  printf 'deliver=%s\n' "$keys"
  if [[ "$state" == firmware ]]; then state=menu; return; fi
  if [[ "$state" != menu ]]; then printf 'key-in-wizard=%s\n' "$keys"; return; fi
  case "$keys" in
    "$HOTKEY,ret") state="$TARGET" ;;
    "$HOTKEY") if [[ "$FIRMWARE" == uefi ]]; then state="$TARGET"; else state=menu-hotkey; fi ;;
    ret) state=normal ;;
  esac
}
qmp_request() {
  case "$2" in
    key-sequence) deliver "$3" ;;
    key-tap)
      if [[ "$state" == menu-hotkey && "$3" == ret ]]; then state="$TARGET"; return; fi
      deliver "$3" ;;
    *) printf 'unexpected=%s\n' "$2"; return 1 ;;
  esac
}
marker_count() {
  case "$2" in
    BEAMO_WIPE_KIOSK_READY) [[ "$state" == normal || "$state" == "$TARGET" ]] && echo 1 || echo 0 ;;
    "$MODE_MARKER") [[ "$state" == "$TARGET" ]] && echo 1 || echo 0 ;;
    *) echo 0 ;;
  esac
}
wait_for_marker() { [[ "$state" == "$TARGET" ]]; }
"""


def _drive(driver: str, label: str, hotkey: str, mode_marker: str, start: str = "firmware"):
    source = QEMU.read_text(encoding="utf-8")
    script = "\n".join((
        MOCKS,
        f"state={start}",
        _function(source, "send_key"),
        _function(source, "send_boot_hotkey"),
        _function(source, "booted_other_entry"),
        _function(source, driver),
        f"{driver} {label} /fake/qmp",
    ))
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ["PATH"],
            "HOTKEY": hotkey,
            "TARGET": "target",
            "MODE_MARKER": mode_marker,
            "FIRMWARE": "bios" if label.startswith("bios") else "uefi",
        },
    )


@pytest.mark.parametrize("driver,label,hotkey,marker", [
    ("drive_troubleshoot_boot", "bios-troubleshoot-usb", "t", "BEAMO_WIPE_SAFE_VIDEO=1"),
    ("drive_speech_boot", "bios-speech-usb", "s", "BEAMO_WIPE_UI_MODE=accessible"),
])
def test_bios_hotkey_and_return_arrive_together(driver, label, hotkey, marker):
    result = _drive(driver, label, hotkey, marker)
    assert result.returncode == 0, result.stdout + result.stderr
    # The first sequence is dropped whole; the next selects and boots the
    # requested entry. Return never reaches the menu on its own.
    assert result.stdout.splitlines() == [f"deliver={hotkey},ret"] * 2


def test_uefi_hotkey_is_sent_without_return():
    result = _drive(
        "drive_troubleshoot_boot", "uefi-troubleshoot-usb", "t", "BEAMO_WIPE_SAFE_VIDEO=1"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["deliver=t", "deliver=t"]


@pytest.mark.parametrize("driver,label,hotkey,marker", [
    ("drive_troubleshoot_boot", "bios-troubleshoot-usb", "t", "BEAMO_WIPE_SAFE_VIDEO=1"),
    ("drive_speech_boot", "uefi-speech-usb", "s", "BEAMO_WIPE_UI_MODE=accessible"),
])
def test_a_different_entry_stops_the_keys_and_fails(driver, label, hotkey, marker):
    result = _drive(driver, label, hotkey, marker, start="normal")
    assert result.returncode != 0
    assert "never selected the" in result.stderr
    assert "deliver=" not in result.stdout
    assert "key-in-wizard" not in result.stdout


def _qmp_program(source: str) -> str:
    body = source.split("qmp_request() {", 1)[1]
    return body.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="needs AF_UNIX sockets")
def test_key_sequence_is_one_ordered_input_event_command(tmp_path):
    path = str(tmp_path / "qmp.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(path)
    server.listen(1)
    commands = []

    def serve():
        connection, _ = server.accept()
        with connection:
            connection.sendall(b'{"QMP": {}}\r\n')
            reader = connection.makefile("rb")
            for line in reader:
                message = json.loads(line)
                commands.append(message)
                reply = {"return": {}, "id": message.get("id")}
                connection.sendall(json.dumps(reply).encode() + b"\r\n")

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            [sys.executable, "-", path, "key-sequence", "t,ret"],
            input=_qmp_program(QEMU.read_text(encoding="utf-8")),
            capture_output=True,
            text=True,
            timeout=30,
        )
    finally:
        server.close()
    assert result.returncode == 0, result.stderr
    thread.join(5)
    assert [c["execute"] for c in commands] == ["qmp_capabilities", "input-send-event"]
    events = commands[1]["arguments"]["events"]
    assert [(e["data"]["key"]["data"], e["data"]["down"]) for e in events] == [
        ("t", True), ("t", False), ("ret", True), ("ret", False),
    ]
    assert all(e["type"] == "key" and e["data"]["key"]["type"] == "qcode" for e in events)
