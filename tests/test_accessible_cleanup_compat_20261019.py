# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional exception notes cannot replace errors on supported Python 3.10."""

import threading
from types import SimpleNamespace

import pytest

from test_accessible_close_cleanup_pass21 import _module


class ErrorWithoutNotes(RuntimeError):
    add_note = None  # Model the absent Python 3.10 exception capability.


@pytest.fixture(autouse=True)
def no_device_actions(monkeypatch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("A device or application action was reached")

    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    yield
    assert not effects


@pytest.mark.parametrize("error_type", [RuntimeError, ErrorWithoutNotes])
def test_close_keeps_primary_error_after_secondary_cleanup_failures(monkeypatch, error_type):
    module, _provenance = _module(monkeypatch)
    original = error_type("primary audio cancellation error")
    calls, caught = [], []

    def fail(name, error):
        calls.append(name)
        raise error

    module.GLib.source_remove = lambda source: calls.append(("remove-timer", source))
    module.Gtk.main_level = lambda: 1
    module.Gtk.main_quit = lambda: calls.append("quit-loop")
    app = module.AccessibleWizard.__new__(module.AccessibleWizard)
    app.w = SimpleNamespace(cancel_audio=lambda: fail("cancel-audio", original))
    app.closed = False
    app.timer = 19
    app._sound_dialog = SimpleNamespace(close=lambda: fail("close-dialog", OSError("secondary dialog error")))
    app.window = SimpleNamespace(destroy=lambda: fail("destroy-window", ValueError("secondary window error")))
    try:
        app.close()
    except BaseException as error:
        caught.append(error)
    assert calls == ["cancel-audio", "close-dialog", ("remove-timer", 19), "destroy-window", "quit-loop"]
    assert app.closed and app.timer == 0
    assert caught == [original]
    if error_type is RuntimeError and callable(getattr(original, "add_note", None)):
        assert len(original.__notes__) == 2


@pytest.mark.parametrize("error_type", [RuntimeError, ErrorWithoutNotes])
def test_refresh_launch_failure_finishes_claim_when_wake_also_fails(monkeypatch, error_type):
    module, _provenance = _module(monkeypatch)
    original = error_type("primary launch error")
    calls, caught = [], []

    def wake_failed():
        calls.append("wake")
        raise OSError("secondary wake error")

    def start_failed():
        calls.append("start")
        raise original

    app = module.AccessibleWizard.__new__(module.AccessibleWizard)
    app.w = SimpleNamespace(
        begin_refresh=lambda: 7,
        finish_refresh=lambda seq, error: calls.append(("finish", seq, error)),
    )
    app._refresh_lock = threading.Lock()
    monkeypatch.setattr(module.threading, "Event", lambda: SimpleNamespace(set=wake_failed))
    monkeypatch.setattr(module.threading, "Thread", lambda **_kwargs: SimpleNamespace(start=start_failed))
    returned = None
    try:
        returned = app._begin_refresh_scan()
    except BaseException as error:
        caught.append(error)
    assert not caught
    assert returned is True
    assert calls == ["start", "wake", ("finish", 7, original)]
    if error_type is RuntimeError and callable(getattr(original, "add_note", None)):
        assert len(original.__notes__) == 1
