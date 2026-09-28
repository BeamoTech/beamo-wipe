# SPDX-License-Identifier: GPL-3.0-or-later
"""One bounded worker for optional audio I/O; UI threads poll tickets.

Only the latest waiting request is retained. A cancelled running request is
cooperatively stopped by sound._run. A stuck third-party call can occupy the
single daemon, but cannot create more workers or hold the interface hostage.
"""

from __future__ import annotations

import atexit
import threading
import time
from typing import Callable


OPERATION_SECONDS = 30.0


class AudioTicket:
    def __init__(self, seconds: float = OPERATION_SECONDS):
        self.cancelled = threading.Event()
        self.deadline = time.monotonic() + seconds
        self._lock = threading.Lock()
        self._done = False
        self._value = None
        self._completed_at: float | None = None
        self._expired = False

    def cancel(self) -> None:
        self.cancelled.set()

    def _finish(self, value) -> None:
        with self._lock:
            self._value = value
            self._completed_at = time.monotonic()
            self._done = True

    def poll(self):
        """(ready, value). Cancelled tickets are deliberately never applied."""
        if self.cancelled.is_set():
            return True, TimeoutError("Audio operation timed out") if self._expired else None
        with self._lock:
            if self._done and self._completed_at is not None and self._completed_at <= self.deadline:
                return True, self._value
            late = self._done
        if late or time.monotonic() >= self.deadline:
            self._expired = True
            self.cancel()
            return True, TimeoutError("Audio operation timed out")
        return False, None


class AudioWorker:
    def __init__(self):
        self._condition = threading.Condition()
        self._pending: tuple[AudioTicket, Callable] | None = None
        self._active: AudioTicket | None = None
        self._closed = False
        self._thread: threading.Thread | None = None

    def submit(self, action: Callable, seconds: float = OPERATION_SECONDS) -> AudioTicket:
        ticket = AudioTicket(seconds)
        with self._condition:
            if self._closed:
                ticket._finish(RuntimeError("Audio worker closed"))
                return ticket
            if self._active is not None:
                self._active.cancel()
            if self._pending is not None:
                self._pending[0].cancel()
            self._pending = (ticket, action)
            if self._thread is None:
                self._thread = threading.Thread(
                    target=self._run, name="beamo-audio", daemon=True
                )
                try:
                    self._thread.start()
                except RuntimeError as exc:
                    self._pending = None
                    self._thread = None
                    ticket._finish(exc)
                    return ticket
            self._condition.notify()
        return ticket

    def _run(self) -> None:
        from beamo_wipe import sound

        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    if not self._condition.wait(timeout=1.0):
                        self._thread = None
                        return
                if self._closed:
                    return
                if self._pending is None:
                    continue
                ticket, action = self._pending
                self._pending = None
                self._active = ticket
            try:
                if ticket.cancelled.is_set():
                    value = None
                else:
                    sound._audio_context.ticket = ticket
                    try:
                        value = action()
                    finally:
                        del sound._audio_context.ticket
            except BaseException as exc:
                value = exc
            ticket._finish(value)
            with self._condition:
                if self._active is ticket:
                    self._active = None

    def close(self) -> None:
        with self._condition:
            self._closed = True
            if self._active is not None:
                self._active.cancel()
            if self._pending is not None:
                self._pending[0].cancel()
                self._pending = None
            self._condition.notify_all()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=0.6)


worker = AudioWorker()
atexit.register(worker.close)
