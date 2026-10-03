"""Owned, bounded private Xvfb lifecycle for Linux accessibility tests."""

import logging
import os
from pathlib import Path
import shutil
import subprocess
import time


def stop_private_xvfb(proc) -> None:
    """Signal only this child, then reap it; no pipes or shared X server."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    else:
        proc.wait(timeout=5)


def start_private_xvfb():
    """Use a real X11 connection to detect readiness, including WSL sockets.

    A private server at 72 DPI avoids the parent's AT-SPI root-window state.
    Unlike nested xvfb-run, this preserves the existing hosted display. WSL
    may expose a read-only /tmp/.X11-unix: Xvfb can still serve an abstract
    socket, so the filesystem socket alone cannot establish readiness.
    """
    for command in ("Xvfb", "xdpyinfo"):
        assert shutil.which(command), (
            f"The Linux accessibility tests require {command} "
            "(install xvfb and x11-utils)"
        )
    Path("/tmp/.X11-unix").mkdir(mode=0o1777, exist_ok=True)
    for n in range(110, 141):
        if os.path.exists(f"/tmp/.X{n}-lock") or os.path.exists(f"/tmp/.X11-unix/X{n}"):
            continue
        display = f":{n}"
        proc = subprocess.Popen(
            ["Xvfb", display, "-screen", "0", "1600x1000x24", "-dpi", "72",
             "-nolisten", "tcp", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 5
            while proc.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    probe = subprocess.run(
                        ["xdpyinfo", "-display", display],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=min(remaining, 1),
                    )
                except subprocess.TimeoutExpired:
                    continue
                if probe.returncode == 0 and proc.poll() is None:
                    return proc, display
                time.sleep(min(0.05, remaining))
        except BaseException as exc:
            try:
                stop_private_xvfb(proc)
            except BaseException as cleanup_error:
                detail = f"Private Xvfb cleanup failed: {cleanup_error!r}"
                if hasattr(exc, "add_note"):
                    exc.add_note(detail)
                else:
                    logging.getLogger(__name__).error(detail)
            raise
        stop_private_xvfb(proc)
    raise RuntimeError("could not start a private Xvfb for Orca")
