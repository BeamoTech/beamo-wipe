"""BW-QEMU-FLAKES part a: fixed X input warning markers, QEMU gate only."""

import os
import sys
from pathlib import Path

import pytest

from beamo_wipe import diagnostics


@pytest.fixture
def emitted(monkeypatch):
    seen = []
    monkeypatch.setattr(diagnostics, "emit_serial_marker", lambda m: seen.append(m) or True)
    return seen


def _vendor(tmp_path, text):
    path = tmp_path / "sys_vendor"
    path.write_text(text, encoding="ascii")
    return str(path)


def test_customer_pc_never_reads_or_reports_the_x_log(tmp_path, emitted):
    log = tmp_path / "Xorg.0.log"
    log.write_text("event processing lagging behind by 30ms\n", encoding="ascii")
    for vendor in ("Dell Inc.\n", "QEMUX\n", ""):
        assert diagnostics.emit_x_input_markers((str(log),), _vendor(tmp_path, vendor)) == []
    assert diagnostics.emit_x_input_markers((str(log),), str(tmp_path / "absent")) == []
    assert emitted == []


def test_qemu_names_each_warning_class_without_log_text(tmp_path, emitted):
    log = tmp_path / "Xorg.0.log"
    log.write_text(
        "[    12.3] (II) event2  - AT Translated Set 2 keyboard: is tagged by udev as: Keyboard\n"
        "[   812.0] (EE) event2  - AT Translated Set 2 keyboard: client bug: event processing "
        "lagging behind by 41ms, your system is too slow\n"
        "[   813.0] (EE) event5  - QEMU USB Tablet: SYN_DROPPED event - some input events have "
        "been lost.\n",
        encoding="ascii",
    )
    result = diagnostics.emit_x_input_markers(
        (str(tmp_path / "missing.log"), str(log)), _vendor(tmp_path, "QEMU\n")
    )
    assert result == emitted == [
        "BEAMO_WIPE_XINPUT_LOG_SCANNED",
        "BEAMO_WIPE_XINPUT_LAGGING",
        "BEAMO_WIPE_XINPUT_SYN_DROPPED",
        "BEAMO_WIPE_XINPUT_CLIENT_BUG",
    ]
    assert all(diagnostics.SERIAL_MARKER_RE.fullmatch(m) for m in result)


def test_qemu_reports_a_clean_or_missing_log(tmp_path, emitted):
    vendor = _vendor(tmp_path, "QEMU\n")
    clean = tmp_path / "clean.log"
    clean.write_text("(II) nothing to see\n", encoding="ascii")
    assert diagnostics.emit_x_input_markers((str(clean),), vendor) == [
        "BEAMO_WIPE_XINPUT_LOG_SCANNED"
    ]
    assert diagnostics.emit_x_input_markers((str(tmp_path / "none.log"),), vendor) == [
        "BEAMO_WIPE_XINPUT_LOG_MISSING"
    ]
    # A directory is not a log.
    assert diagnostics.emit_x_input_markers((str(tmp_path),), vendor) == [
        "BEAMO_WIPE_XINPUT_LOG_MISSING"
    ]


def test_only_the_bounded_tail_is_read(tmp_path, emitted, monkeypatch):
    monkeypatch.setattr(diagnostics, "X_LOG_TAIL_BYTES", 64)
    log = tmp_path / "Xorg.0.log"
    log.write_text("SYN_DROPPED early\n" + "x" * 200 + "\n(II) tail\n", encoding="ascii")
    assert diagnostics.emit_x_input_markers((str(log),), _vendor(tmp_path, "QEMU")) == [
        "BEAMO_WIPE_XINPUT_LOG_SCANNED"
    ]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlink semantics")
def test_a_linked_log_is_not_followed(tmp_path, emitted):
    target = tmp_path / "target.log"
    target.write_text("SYN_DROPPED\n", encoding="ascii")
    link = tmp_path / "Xorg.0.log"
    os.symlink(target, link)
    assert diagnostics.emit_x_input_markers((str(link),), _vendor(tmp_path, "QEMU")) == [
        "BEAMO_WIPE_XINPUT_LOG_MISSING"
    ]


def test_qemu_summary_lists_every_new_marker():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "qemu-verify.sh").read_text(
        encoding="utf-8"
    )
    summary = source.split("report_marker_summary() {", 1)[1].split("\n}", 1)[0]
    markers = {"BEAMO_WIPE_XINPUT_LOG_SCANNED", "BEAMO_WIPE_XINPUT_LOG_MISSING"}
    markers |= {marker for _needle, marker in diagnostics.X_INPUT_WARNINGS}
    markers |= {
        "BEAMO_WIPE_APP_FOCUS_LOST",
        "BEAMO_WIPE_APP_FOCUS_LOST_RETURN_HELD",
        "BEAMO_WIPE_APP_FOCUS_REGAINED",
    }
    markers |= set(diagnostics.SERIAL_DROP_MARKERS.values())
    for marker in markers:
        assert f"    {marker} \\\n" in summary, marker


def test_the_vendor_is_read_from_its_start_and_the_log_from_its_end(tmp_path):
    # sysfs reports st_size 4096 for the short sys_vendor attribute, so a
    # tail read would see nothing there. Only the growing X log is tailed.
    padded = tmp_path / "padded"
    padded.write_bytes(b"QEMU\n" + b" " * 5000)
    assert diagnostics._read_bounded(str(padded), 64).startswith(b"QEMU\n")
    assert diagnostics._read_bounded(str(padded), 64, tail=True) == b" " * 64
