# SPDX-License-Identifier: GPL-3.0-or-later
"""Best-effort block of OS sleep while an erase is running.

Does not wrap nwipe, does not block shutdown, and never prevents a wipe
from starting. Firmware lid and held power-button behavior are outside
this helper.

#168: while the erase runs it also turns off X screen blanking (the kiosk's
10-minute screensaver) so progress stays visible, and restores the kiosk
policy afterwards. Only the X screensaver changes: DPMS stays as the
launcher set it (never powers the panel down), and lid, suspend and power
handling are untouched. The console fallbacks cannot be controlled this way
and keep their "screen may go dark" note.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from beamo_wipe.safety import CLEAN_SUBPROCESS_ENV

INHIBIT_BIN = "/usr/bin/systemd-inhibit"
SLEEP_BIN = "/bin/sleep"
WHAT = "sleep:idle"
WHO = "Beamo Wipe"
WHY = "An erase is running"
MODE = "block"
XSET_BIN = "/usr/bin/xset"
# The kiosk policy the launcher sets (usr/local/bin/beamo-wipe); restore it.
SCREEN_BLANK_SECONDS = 600


def display_awake_argv() -> list[str]:
    return [XSET_BIN, "s", "off"]


def display_restore_argv() -> list[str]:
    return [XSET_BIN, "s", str(SCREEN_BLANK_SECONDS), "s", "blank", "s", "on"]


def inhibit_argv() -> list[str]:
    return [
        INHIBIT_BIN,
        f"--what={WHAT}",
        f"--who={WHO}",
        f"--why={WHY}",
        f"--mode={MODE}",
        SLEEP_BIN,
        "infinity",
    ]


class SleepInhibit:
    """Hold a logind sleep/idle inhibit for the life of one erase."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._display_held = False

    @property
    def active(self) -> bool:
        proc = self._proc
        if proc is None:
            return False
        try:
            return proc.poll() is None
        except (OSError, AttributeError):
            # Status could not be confirmed; retain the handle for another stop.
            return True

    def start(self) -> None:
        self.stop()
        if self._proc is not None:
            # The previous inhibitor may still be alive. Do not lose its handle
            # by replacing it with a second process.
            return
        if os.environ.get("BEAMO_WIPE_LIVE") != "1":
            return
        if os.environ.get("BEAMO_WIPE_DRY_RUN") == "1":
            return
        self._keep_display_on()
        argv = inhibit_argv()
        if "--what=shutdown" in argv or "shutdown" in WHAT.split(":"):
            raise RuntimeError("sleep inhibit must not block shutdown")
        try:
            self._proc = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                close_fds=True,
                cwd="/",
                env=dict(CLEAN_SUBPROCESS_ENV),
                start_new_session=True,
            )
        except (OSError, ValueError):
            self._proc = None
            try:
                from beamo_wipe.diagnostics import log_diag

                log_diag("power", "sleep_inhibit_unavailable", INHIBIT_BIN)
            except BaseException:
                # Optional logging must not interrupt erase ownership cleanup.
                pass

    def _xset(self, argv: list[str]) -> bool:
        """Run xset against the kiosk display. Never raises; False on failure."""
        display = os.environ.get("DISPLAY", "")
        if not display or not os.path.isfile(XSET_BIN):
            return False
        env = dict(CLEAN_SUBPROCESS_ENV)
        env["DISPLAY"] = display
        if os.environ.get("XAUTHORITY"):
            env["XAUTHORITY"] = os.environ["XAUTHORITY"]
        try:
            done = subprocess.run(
                argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, shell=False, close_fds=True, cwd="/",
                env=env, timeout=5, check=False,
            )
            ok = done.returncode == 0
        except (OSError, ValueError, subprocess.SubprocessError):
            ok = False
        if not ok:
            try:
                from beamo_wipe.diagnostics import log_diag

                log_diag("power", "display_blanking_change_failed", " ".join(argv[1:]))
            except BaseException:
                pass
        return ok

    def _keep_display_on(self) -> None:
        if self._display_held:
            return
        self._display_held = self._xset(display_awake_argv())

    def _restore_display(self) -> None:
        if not self._display_held:
            return
        self._display_held = False
        self._xset(display_restore_argv())

    def stop(self) -> None:
        # Restore the screensaver whether or not the sleep inhibitor started.
        self._restore_display()
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except (OSError, AttributeError):
                    proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1)
            self._proc = None
        except (OSError, subprocess.TimeoutExpired, AttributeError):
            # A failed terminate/kill leaves liveness uncertain. A successful
            # poll can still prove that the process exited in the meantime.
            try:
                if proc.poll() is not None:
                    self._proc = None
            except (OSError, AttributeError):
                pass
            try:
                from beamo_wipe.diagnostics import log_diag

                log_diag("power", "sleep_inhibit_stop_failed", "terminate")
            except BaseException:
                # Retain helper ownership without interrupting engine retirement.
                pass
