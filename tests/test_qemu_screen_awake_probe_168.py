# SPDX-License-Identifier: GPL-3.0-or-later
"""BW-168's opt-in QEMU screen-awake probe drives and judges correctly.

The probe (QEMU_SCREEN_AWAKE=1 in scripts/qemu-verify.sh) proves on a real X
server that #168 keeps the screen lit through a long erase and restores the
kiosk's 600 s blank timeout afterwards. These tests run its driver against a
fake guest and clock, and its frame checker against hand-built PNGs. A real
run needs a Linux KVM worker.
"""

import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

import pytest


ROOT = Path(__file__).resolve().parents[1]
QEMU = ROOT / "scripts/qemu-verify.sh"
CHECKER = ROOT / "scripts/qemu_frame_check.py"


def _checker():
    spec = importlib.util.spec_from_file_location("qemu_frame_check", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _png(rows, filter_type=0) -> bytes:
    """Encode RGB rows (lists of (r, g, b)) with one PNG row filter."""
    height, width = len(rows), len(rows[0])
    raw = bytearray()
    previous = bytes(width * 3)
    for row in rows:
        line = bytes(channel for pixel in row for channel in pixel)
        out = bytearray()
        for i, value in enumerate(line):
            left = line[i - 3] if i >= 3 else 0
            up = previous[i]
            upper_left = previous[i - 3] if i >= 3 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) >> 1
            else:
                estimate = left + up - upper_left
                pa, pb, pc = (
                    abs(estimate - left),
                    abs(estimate - up),
                    abs(estimate - upper_left),
                )
                predictor = (
                    left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                )
            out.append((value - predictor) & 0xFF)
        raw += bytes([filter_type]) + out
        previous = line

    def chunk(kind, body):
        return (
            struct.pack(">I", len(body))
            + kind
            + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )


BLANK = [[(0, 0, 0)] * 4 for _ in range(3)]


def _lit(shade: int):
    return [
        [(shade, 40, 200), (255, 255, 255), (0, 0, 0), (shade, shade, 0)]
        for _ in range(3)
    ]


@pytest.mark.parametrize("filter_type", [0, 1, 2, 3, 4])
def test_png_decoder_recovers_pixels_through_every_row_filter(filter_type):
    module = _checker()
    rows = [
        [(r * 40 + c, 255 - c * 30, (r * c * 17) & 0xFF) for c in range(5)]
        for r in range(4)
    ]
    width, height, channels, pixels = module.decode_png(_png(rows, filter_type))
    assert (width, height, channels) == (5, 4, 3)
    assert pixels == bytes(v for row in rows for pixel in row for v in pixel)


def test_blank_means_every_pixel_has_one_value(tmp_path):
    module = _checker()
    (tmp_path / "blank.png").write_bytes(_png(BLANK, 1))
    (tmp_path / "lit.png").write_bytes(_png(_lit(10), 4))
    assert module.summarize(tmp_path / "blank.png")["blank"] is True
    lit = module.summarize(tmp_path / "lit.png")
    assert lit["blank"] is False
    assert lit["distinct_values"] == 4


def test_non_png_or_unsupported_layout_is_refused():
    module = _checker()
    with pytest.raises(module.FrameError):
        module.decode_png(b"not a png")
    palette = _png(BLANK).replace(
        struct.pack(">IIBBBBB", 4, 3, 8, 2, 0, 0, 0),
        struct.pack(">IIBBBBB", 4, 3, 8, 3, 0, 0, 0),
    )
    with pytest.raises(module.FrameError):
        module.decode_png(palette)


def _frames(tmp_path, **overrides):
    frames = {
        "erase-030": _lit(10),
        "erase-570": _lit(20),
        "erase-645": _lit(30),
        "after-030": _lit(40),
        "after-645": BLANK,
        "wake": _lit(50),
    }
    frames.update(overrides)
    for name, rows in frames.items():
        if rows is not None:
            (tmp_path / f"screen-awake-{name}.png").write_bytes(_png(rows, 2))


def _judge(tmp_path, **observations):
    base = {
        "screen_markers_before_wake": 9,
        "screen_markers_after_wake": 9,
        "done_before_last_erase_frame": 0,
    }
    base.update(observations)
    return _checker().judge(tmp_path, base)


def test_lit_erase_restored_blanking_and_clean_wake_pass(tmp_path):
    _frames(tmp_path)
    status, receipt = _judge(tmp_path)
    assert (status, receipt["verdict"]) == (0, "PASS"), receipt["reasons"]
    assert receipt["checks"]["erase_645_vs_030_differing_pixels"] == 6
    assert set(receipt["frames"]) == {
        "erase-030",
        "erase-570",
        "erase-645",
        "after-030",
        "after-645",
        "wake",
    }
    assert all(len(frame["sha256"]) == 64 for frame in receipt["frames"].values())


@pytest.mark.parametrize(
    ("overrides", "observations", "reason"),
    [
        ({"erase-645": BLANK}, {}, "PASS-1: a frame during the erase was blank"),
        ({"erase-645": _lit(10)}, {}, "PASS-1: the 10 min 45 s frame did not change"),
        (
            {"after-645": _lit(60)},
            {},
            "PASS-2: the screen was still lit 10 min 45 s after the erase",
        ),
        (
            {"after-030": BLANK},
            {},
            "PASS-2: the screen was already blank 30 s after the erase",
        ),
        ({"wake": BLANK}, {}, "PASS-3: the screen stayed blank after the wake key"),
        (
            {},
            {"screen_markers_after_wake": 10},
            "PASS-3: the wake key changed the app's screen",
        ),
        ({}, {"blanking_change_failed": 1}, "power/display_blanking_change_failed"),
    ],
)
def test_each_broken_condition_fails(tmp_path, overrides, observations, reason):
    _frames(tmp_path, **overrides)
    status, receipt = _judge(tmp_path, **observations)
    assert (status, receipt["verdict"]) == (1, "FAIL")
    assert any(
        item.startswith(reason) or reason in item for item in receipt["reasons"]
    ), receipt["reasons"]


def test_erase_that_ends_too_early_is_inconclusive_never_a_pass(tmp_path):
    _frames(tmp_path, **{"after-030": None, "after-645": None, "wake": None})
    status, receipt = _judge(tmp_path, done_before_last_erase_frame=1)
    assert (status, receipt["verdict"]) == (3, "INCONCLUSIVE")


def test_missing_frame_is_inconclusive(tmp_path):
    _frames(tmp_path, wake=None)
    status, receipt = _judge(tmp_path)
    assert (status, receipt["verdict"]) == (3, "INCONCLUSIVE")
    assert "wake" in receipt["reasons"][0]


def test_cli_writes_the_receipt_and_exit_status(tmp_path):
    _frames(tmp_path)
    receipt_path = tmp_path / "verdict.json"
    status = _checker().main(
        [
            str(tmp_path),
            str(receipt_path),
            "--observation",
            "screen_markers_before_wake=3",
            "--observation",
            "screen_markers_after_wake=3",
            "--observation",
            "t1_epoch=none",
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert status == 0 and receipt["verdict"] == "PASS"
    assert receipt["observations"]["t1_epoch"] == "none"


# --- the bash driver, against a fake guest and clock ------------------------


def _function(source: str, name: str) -> str:
    return (
        f"{name}() {{" + source.split(f"{name}() {{", 1)[1].split("\n}", 1)[0] + "\n}"
    )


DRIVER_MOCKS = r"""
# The fake clock is a shell variable: Git Bash forks are slow, and sleep and
# wait_for_new_marker run in the driver's own shell, so they can advance it.
MOCK_NOW="$MOCK_T0"
now() { printf '%s\n' "$MOCK_NOW"; }
date() { now; }
sleep() { local whole="${1%.*}"; MOCK_NOW=$(( MOCK_NOW + ${whole:-0} )); }
ev() { printf '%s\n' "$*" >> "$MOCK_EVENTS"; }
guest_pid() { printf '%s\n' "$$"; }
send_key_for_marker() { ev "key $3"; }
wait_for_marker() { :; }
type_token_for_marker() { ev "type $3"; }
send_key() { ev "key $2"; sleep 0.4; }
start_erase_with_return() { ev "start-erase"; }
report_marker_summary() { :; }
qmp_request() { ev "$2 ${3##*/} at+$(( MOCK_NOW - MOCK_T0 ))"; }
marker_count() {
  if [[ "$2" == BEAMO_WIPE_SCREEN_DONE && "$MOCK_NOW" -ge "$MOCK_DONE_AT" ]]; then echo 1; else echo 0; fi
}
wait_for_new_marker() {
  ev "await-new $2"
  if [[ "$MOCK_NOW" -lt "$MOCK_DONE_AT" ]]; then MOCK_NOW="$MOCK_DONE_AT"; fi
}
python3() { ev "judge $*"; return "$MOCK_VERDICT"; }
"""


def _drive(tmp_path, done_after: int, verdict: int = 0):
    source = QEMU.read_text(encoding="utf-8")
    events = tmp_path / "events"
    events.touch()
    t0 = 1_000_000
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "bios-screen-awake-serial.txt").write_text(
        "BEAMO_WIPE_SCREEN_OWNER\nBEAMO_WIPE_SCREEN_DONE\n"
    )
    script = "\n".join(
        [DRIVER_MOCKS]
        + [
            _function(source, name)
            for name in (
                "screen_awake_capture",
                "screen_awake_wait_until",
                "screen_marker_total",
                "drive_screen_awake",
            )
        ]
        + ["drive_screen_awake bios-screen-awake /tmp/qmp 3 1234 2648"]
    )
    result = subprocess.run(
        ["bash", "-ceu", script],
        env=dict(
            os.environ,
            MOCK_EVENTS=str(events),
            MOCK_T0=str(t0),
            MOCK_DONE_AT=str(t0 + done_after),
            MOCK_VERDICT=str(verdict),
            EVIDENCE_DIR=str(evidence),
            ROOT=str(ROOT),
            QEMU_TARGET_BYTES="4294967296",
            QEMU_TARGET_WRITE_BPS="4194304",
        ),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result, events.read_text().splitlines()


def test_driver_sends_no_input_between_working_and_the_single_wake_key(tmp_path):
    result, events = _drive(tmp_path, done_after=900)
    assert result.returncode == 0, result.stderr
    start = events.index("start-erase")
    after_start = events[start + 1 :]
    keys = [e for e in after_start if e.startswith(("key ", "type ", "key-"))]
    assert keys == ["key shift"]
    captures = [e for e in after_start if e.startswith("screendump")]
    # Times are from the fake clock's start. Working (T0) comes 6 s later,
    # after the Last chance countdown wait, so the erase frames sit at
    # T0 + 30, 570 and 645 s. Done arrives at +900 (T1), so the after frames
    # sit at T1 + 30 and 645 s and the wake frame 2 s after the wake key.
    assert captures == [
        "screendump screen-awake-erase-030.png at+36",
        "screendump screen-awake-erase-570.png at+576",
        "screendump screen-awake-erase-645.png at+651",
        "screendump screen-awake-after-030.png at+930",
        "screendump screen-awake-after-645.png at+1545",
        "screendump screen-awake-wake.png at+1547",
    ]
    assert after_start.index("key shift") < after_start.index(
        "screendump screen-awake-wake.png at+1547"
    )
    judge = next(e for e in events if e.startswith("judge "))
    assert "done_before_last_erase_frame=0" in judge
    assert "target_bytes=4294967296" in judge and "target_write_bps=4194304" in judge
    assert (
        "screen_markers_before_wake=2" in judge
        and "screen_markers_after_wake=2" in judge
    )


def test_driver_reaches_working_only_through_the_release_safe_start(tmp_path):
    result, events = _drive(tmp_path, done_after=900)
    assert result.returncode == 0, result.stderr
    before = events[: events.index("start-erase")]
    assert before == [
        "key spc",
        "key ret",
        "key down",
        "key ret",
        "type 1234",
        "key ret",
        "key 3",
        "key ret",
        "key tab",
    ]


def test_erase_done_before_the_last_frame_skips_the_idle_phase_and_fails(tmp_path):
    result, events = _drive(tmp_path, done_after=600, verdict=3)
    assert result.returncode == 1
    assert "INCONCLUSIVE (never a pass)" in result.stderr
    assert not any(
        e.startswith("screendump screen-awake-after-")
        or e.startswith("screendump screen-awake-wake")
        or e == "key shift"
        for e in events
    )
    assert "done_before_last_erase_frame=1" in next(
        e for e in events if e.startswith("judge ")
    )


def test_failed_verdict_fails_the_journey(tmp_path):
    result, _events = _drive(tmp_path, done_after=900, verdict=1)
    assert result.returncode == 1
    assert "screen-awake probe FAILED" in result.stderr


# --- wiring and the default gate --------------------------------------------


def test_probe_is_opt_in_and_the_gate_workflows_never_enable_it():
    source = QEMU.read_text(encoding="utf-8")
    assert 'case "${QEMU_SCREEN_AWAKE:-0}" in' in source
    assert "1) run_screen_awake_journey; SCREEN_AWAKE_RAN=1 ;;" in source
    manual = "screen-awake.yml"
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        if workflow.name == manual:
            continue
        assert "QEMU_SCREEN_AWAKE" not in workflow.read_text(encoding="utf-8"), (
            workflow.name
        )
    # Only the manual workflow enables it, on its QEMU step, and it has no
    # automatic trigger, no write permission and no secrets.
    text = (ROOT / ".github/workflows" / manual).read_text(encoding="utf-8")
    on_block = text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert on_block.strip() == "workflow_dispatch:"
    assert "permissions:\n  contents: read\n" in text
    assert "secrets." not in text and "write" not in text.split("jobs:", 1)[0]
    assert text.count("QEMU_SCREEN_AWAKE") == 1
    qemu_step = text.split("- name: QEMU journeys plus the screen-awake probe", 1)[1]
    qemu_step = qemu_step.split("- name:", 1)[0]
    assert 'QEMU_SCREEN_AWAKE: "1"' in qemu_step
    assert "run: bash scripts/ci-blacksmith.sh qemu" in qemu_step
    # The container receives the flag only when the host step sets it.
    blacksmith = (ROOT / "scripts/ci-blacksmith.sh").read_text(encoding="utf-8")
    assert "    -e QEMU_SCREEN_AWAKE \\\n" in blacksmith


def test_default_boot_keeps_the_unthrottled_target_chain():
    probe = _function(QEMU.read_text(encoding="utf-8"), "boot_probe")
    guard = 'if [[ -n "${QEMU_TARGET_WRITE_BPS:-}" ]]; then'
    assert (
        "local target_format_node=beamo-target target_throttle_group=() target_throttle_node=()"
        in probe
    )
    throttle = probe.split(guard, 1)[1].split("\n  fi\n", 1)[0]
    assert "target_format_node=beamo-target-qcow2" in throttle
    assert "throttle-group" in throttle
    assert (
        '-blockdev "driver=qcow2,node-name=$target_format_node,file=beamo-target-file"'
        in probe
    )
    assert (
        'confirmation_token="$(guest_confirmation_token "$boot_media" "$HOST_METHOD_BYTES" "$token")"'
        in probe
    )


RUNNER_MOCKS = r"""
qemu-img() { printf 'qemu-img %s\n' "$*" >> "$MOCK_EVENTS"; }
boot_probe() { printf 'boot_probe %s bytes=%s bps=%s\n' "$*" "$QEMU_TARGET_BYTES" "$QEMU_TARGET_WRITE_BPS" >> "$MOCK_EVENTS"; }
rm() { :; }
"""


@pytest.mark.parametrize(
    ("bytes_", "bps", "ok"),
    [
        (None, None, True),
        ("2147483648", "4194304", False),
        ("4294967296", "0", False),
        ("4294967296", "x", False),
    ],
)
def test_runner_sizes_the_erase_past_the_blank_timeout(tmp_path, bytes_, bps, ok):
    events = tmp_path / "events"
    events.touch()
    env = dict(
        os.environ, MOCK_EVENTS=str(events), RUN_ROOT="/run", EVIDENCE_DIR=str(tmp_path)
    )
    if bytes_:
        env["QEMU_SCREEN_AWAKE_TARGET_BYTES"] = bytes_
    if bps:
        env["QEMU_SCREEN_AWAKE_WRITE_BPS"] = bps
    script = (
        RUNNER_MOCKS
        + _function(QEMU.read_text(encoding="utf-8"), "run_screen_awake_journey")
        + "\nrun_screen_awake_journey\n"
    )
    result = subprocess.run(
        ["bash", "-ceu", script], env=env, capture_output=True, text=True, timeout=30
    )
    lines = events.read_text().splitlines()
    if ok:
        assert result.returncode == 0, result.stderr
        assert lines == [
            "qemu-img create -f qcow2 /run/target-screen-awake.qcow2 4294967296",
            "boot_probe bios-screen-awake screen-awake 3 7008 /run/target-screen-awake.qcow2 2648 bytes=4294967296 bps=4194304",
        ]
    else:
        assert result.returncode == 1
        assert lines == []
        assert "ABORT" in result.stderr


def test_screen_awake_serial_is_unique_among_guest_targets():
    source = QEMU.read_text(encoding="utf-8")
    assert source.count("serial=7008") == 1
    assert "|7008\n" not in source
