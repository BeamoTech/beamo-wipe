"""Independent real-classifier trace: read-time failure, then bad UTF-8."""
import builtins
import io

import pytest

from beamo_wipe import app, discover, safety, session_recovery
from beamo_wipe.nwipe_runner import NwipeRunner


@pytest.mark.parametrize("location", ["cmdline", "mountinfo"])
@pytest.mark.parametrize("first_read_failed", [True, False])
def test_late_decode_error_returns_blocked_status(monkeypatch, location, first_read_failed):
    counts = {"cmdline": 0, "mountinfo": 0}
    effects = []
    store_events = []
    original_open = builtins.open
    mounts = b"2 1 8:241 / /run/live/medium rw - iso9660 /dev/sdz1 rw\n"

    class FailedRead:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): raise OSError("Controlled read-time metadata failure")

    def fake_open(path, *args, **kwargs):
        kind = {"/proc/cmdline": "cmdline", discover.MOUNTINFO_PATH: "mountinfo"}.get(str(path))
        if kind is None:
            return original_open(path, *args, **kwargs)
        counts[kind] += 1
        if kind == location and counts[kind] == 1 and first_read_failed:
            return FailedRead()
        data = b"boot=live quiet" if kind == "cmdline" else mounts
        if kind == location and counts[kind] == 2:
            data += b" bad=\xff" if kind == "cmdline" else b"3 1 8:33 / /media/\xff rw - ext4 /dev/sdc1 rw\n"
        return io.TextIOWrapper(io.BytesIO(data), encoding="utf-8")

    def forbidden(*args, **kwargs):
        effects.append(True)
        raise AssertionError("Native action forbidden")

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(safety.sys, "platform", "linux")
    monkeypatch.setattr(app, "running_on_live_usb", safety.running_on_live_usb)
    for boundary in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
                     "beamo_wipe.discover.read_mount_sources", "beamo_wipe.discover._run_findmnt"):
        monkeypatch.setattr(boundary, forbidden)
    monkeypatch.setattr(NwipeRunner, "start", forbidden)
    monkeypatch.setattr(app, "_shutdown", forbidden)
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *a, **kw: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *a, **kw: None)

    class Store:
        def __init__(self): store_events.append("create")
        def open(self): store_events.append("open")
        def close(self): store_events.append("close")

    monkeypatch.setattr(session_recovery, "SessionStore", Store)
    escaped = None
    code = None
    try:
        code = app.main(["--demo", "--console"])
    except UnicodeError as error:
        escaped = type(error).__name__
    assert escaped is None, (counts, store_events, escaped)
    assert code == 3
    assert store_events == ([] if first_read_failed else ["create", "open", "close"])
    assert effects == []
