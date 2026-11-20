# SPDX-License-Identifier: GPL-3.0-or-later
"""BW-QEMU-FLAKES part c: a serial marker lost after the port opened is reported."""

from __future__ import annotations

import errno
import stat
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostics

EAGAIN_MARKER = "BEAMO_WIPE_SERIAL_MARKER_DROPPED_EAGAIN"
OTHER_MARKER = "BEAMO_WIPE_SERIAL_MARKER_DROPPED_OTHER"


@pytest.fixture
def serial(monkeypatch):
    """A fake character device whose next writes can be made to fail."""
    state = SimpleNamespace(written=bytearray(), closed=[], failures=[], mode=stat.S_IFCHR)

    def fake_write(_fd, data):
        if state.failures:
            raise state.failures.pop(0)
        state.written.extend(bytes(data))
        return len(data)

    monkeypatch.setattr(diagnostics.os, "open", lambda *_args, **_kwargs: 41)
    monkeypatch.setattr(diagnostics.os, "fstat", lambda _fd: SimpleNamespace(st_mode=state.mode))
    monkeypatch.setattr(diagnostics.os, "write", fake_write)
    monkeypatch.setattr(diagnostics.os, "close", state.closed.append)
    return state


def test_marker_lost_to_a_full_port_is_reported_before_the_next_one(serial):
    serial.failures.append(BlockingIOError(errno.EAGAIN, "full"))
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    assert serial.written == b""

    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_WORKING") is True
    assert serial.written == (EAGAIN_MARKER + "\nBEAMO_WIPE_SCREEN_WORKING\n").encode()

    # Reported once: the next marker is plain again.
    serial.written.clear()
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_DONE") is True
    assert serial.written == b"BEAMO_WIPE_SCREEN_DONE\n"
    assert serial.closed == [41, 41, 41]


def test_other_write_errors_are_reported_separately(serial):
    serial.failures.append(OSError(errno.EIO, "io"))
    serial.failures.append(BlockingIOError(errno.EAGAIN, "full"))
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_RETURN_RESULT_CHECKING") is False

    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_WORKING") is True
    assert serial.written == (
        EAGAIN_MARKER + "\n" + OTHER_MARKER + "\nBEAMO_WIPE_SCREEN_WORKING\n"
    ).encode()


def test_a_failed_report_keeps_the_drop_for_a_later_marker(serial):
    serial.failures.append(BlockingIOError(errno.EAGAIN, "full"))
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    # The write carrying the report fails too: neither drop may be forgotten.
    serial.failures.append(OSError(errno.EIO, "io"))
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_WORKING") is False

    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_DONE") is True
    assert serial.written == (
        EAGAIN_MARKER + "\n" + OTHER_MARKER + "\nBEAMO_WIPE_SCREEN_DONE\n"
    ).encode()


def test_a_short_write_counts_as_a_drop(serial, monkeypatch):
    monkeypatch.setattr(diagnostics.os, "write", lambda _fd, _data: 0)
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    assert diagnostics._take_serial_drops() == {"eagain": 0, "other": 1}


def test_no_serial_port_is_not_a_dropped_marker(serial, monkeypatch):
    def no_port(*_args, **_kwargs):
        raise FileNotFoundError(errno.ENOENT, "missing")

    monkeypatch.setattr(diagnostics.os, "open", no_port)
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    serial.mode = stat.S_IFREG
    monkeypatch.setattr(diagnostics.os, "open", lambda *_args, **_kwargs: 41)
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    assert diagnostics._take_serial_drops() == {"eagain": 0, "other": 0}


def test_invalid_marker_never_reports_or_consumes_drops(serial):
    serial.failures.append(BlockingIOError(errno.EAGAIN, "full"))
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_CHECKING") is False
    assert diagnostics.emit_serial_marker("BEAMO_WIPE_SCREEN_/dev/sda") is False
    assert serial.written == b""
    assert diagnostics._take_serial_drops() == {"eagain": 1, "other": 0}
