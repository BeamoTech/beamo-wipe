# SPDX-License-Identifier: GPL-3.0-or-later
"""BW-QEMU-FLAKES part c: concurrent marker writers must not drop each other.

Linux takes a per-tty write lock with a trylock when the writer opened the
port O_NONBLOCK, so a second writer that arrives while another write is in
progress gets EAGAIN even though the port has room. The fake port below
behaves the same way, and the stand-ins only replace behaviour for the fake
descriptor so pytest's own file handling keeps the real calls.
"""

from __future__ import annotations

import errno
import os
import stat
import threading
import time
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostics

FAKE_FD = 41
MARKERS = ("BEAMO_WIPE_EXPORT_SCAN_TWO", "BEAMO_WIPE_KEY_SPACE_RELEASE_RECEIVED")


@pytest.fixture
def tty(monkeypatch):
    """A fake tty whose write fails with EAGAIN while another write is in progress."""
    state = SimpleNamespace(
        written=[],
        busy=False,
        first_entered=threading.Event(),
        second_attempted=threading.Event(),
        guard=threading.Lock(),
        locked_during=[],
        hold=0.0,
    )
    real_fstat, real_write, real_close = os.fstat, os.write, os.close

    def fake_open(path, *_args, **_kwargs):
        assert path == diagnostics.SERIAL_DEVICE
        state.locked_during.append(("open", diagnostics._serial_write_lock.locked()))
        return FAKE_FD

    def fake_fstat(fd, *args, **kwargs):
        if fd != FAKE_FD:
            return real_fstat(fd, *args, **kwargs)
        return os.stat_result((stat.S_IFCHR | 0o620, 0, 0, 1, 0, 0, 0, 0, 0, 0))

    def fake_write(fd, data):
        if fd != FAKE_FD:
            return real_write(fd, data)
        with state.guard:
            if state.busy:
                state.second_attempted.set()
                raise BlockingIOError(errno.EAGAIN, "tty write lock held")
            state.busy = True
            first = not state.first_entered.is_set()
        try:
            if first:
                state.first_entered.set()
                # Hold the "kernel" lock until the other writer tries, or
                # give up waiting when it is (correctly) kept out.
                state.second_attempted.wait(timeout=0.5)
            elif state.hold:
                time.sleep(state.hold)
            state.written.append(bytes(data))
            return len(data)
        finally:
            with state.guard:
                state.busy = False

    def fake_close(fd):
        if fd != FAKE_FD:
            return real_close(fd)
        state.locked_during.append(("close", diagnostics._serial_write_lock.locked()))

    monkeypatch.setattr(diagnostics.os, "open", fake_open)
    monkeypatch.setattr(diagnostics.os, "fstat", fake_fstat)
    monkeypatch.setattr(diagnostics.os, "write", fake_write)
    monkeypatch.setattr(diagnostics.os, "close", fake_close)
    assert diagnostics._take_serial_drops() == {"eagain": 0, "other": 0}
    yield state
    diagnostics._take_serial_drops()


def test_a_second_writer_waits_its_turn_instead_of_dropping(tty):
    results = {}

    def emit(marker):
        results[marker] = diagnostics.emit_serial_marker(marker)

    first = threading.Thread(target=emit, args=(MARKERS[0],))
    first.start()
    assert tty.first_entered.wait(timeout=5)
    second = threading.Thread(target=emit, args=(MARKERS[1],))
    second.start()
    first.join(timeout=5)
    second.join(timeout=5)
    assert not first.is_alive() and not second.is_alive()

    assert results == {MARKERS[0]: True, MARKERS[1]: True}
    assert not tty.second_attempted.is_set()
    assert tty.written == [(marker + "\n").encode() for marker in MARKERS]
    assert diagnostics._take_serial_drops() == {"eagain": 0, "other": 0}


def test_open_and_close_stay_outside_the_write_lock(tty):
    # Closing a tty can wait for the port to drain; another writer must not
    # wait on that.
    assert diagnostics.emit_serial_marker(MARKERS[0]) is True
    assert tty.locked_during == [("open", False), ("close", False)]


def test_many_concurrent_writers_lose_nothing(tty):
    tty.second_attempted.set()  # no first-writer handshake: plain contention
    tty.hold = 0.0005
    markers = [f"BEAMO_WIPE_STRESS_{n}" for n in range(400)]
    results = []

    def emit_all(chunk):
        results.extend(diagnostics.emit_serial_marker(m) for m in chunk)

    threads = [threading.Thread(target=emit_all, args=(markers[i::4],)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert results.count(True) == len(markers)
    assert sorted(tty.written) == sorted((m + "\n").encode() for m in markers)
    assert diagnostics._take_serial_drops() == {"eagain": 0, "other": 0}
