"""Queued confirmation focus work must retire with its screen and widgets."""

import os
import sys
import time
import tkinter as tk

import pytest

from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard
from test_accessible_sound_review_pass15_ui import _review


def _children(widget):
    for child in widget.winfo_children():
        yield child
        yield from _children(child)


def _authority(wizard):
    return (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
            wizard.method, wizard._erase_until, wizard._authorized_operation,
            wizard._wipe_request, wizard.wants_shutdown, wizard.wants_new_session)


def _pump(root, seconds=0.12):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        root.tk.call("update")
        time.sleep(0.003)
    root.tk.call("update")


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Callback lifetime checks require an explicitly isolated X11 display")
    assert os.environ.get("DISPLAY") not in {":1", ":99"}
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("native application effect")
        raise AssertionError("Native application effect reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    monkeypatch.setattr("beamo_wipe.ui.tk_wizard.emit_serial_marker", lambda *_args: None)
    yield
    assert not effects


@pytest.fixture
def ui():
    apps = []

    def build(text_size):
        wizard, clock = _review()
        wizard.set_language("en")
        wizard.back()
        wizard.back()
        wizard.set_text_size(text_size)
        assert wizard.screen is Screen.CONFIRM
        app = TkWizard(wizard)
        errors = []
        original_report = app.root.report_callback_exception

        def callback_error(kind, error, trace):
            errors.append((kind.__name__, str(error)))
            original_report(kind, error, trace)

        app.root.report_callback_exception = callback_error
        # Background Tcl timer errors do not reach report_callback_exception.
        # Capture them explicitly so a silent stderr warning fails the test.
        app.root.createcommand("pass16_lifetime_bgerror", lambda message: errors.append(("Tcl bgerror", message)))
        app.root.tk.eval("proc bgerror {message} {pass16_lifetime_bgerror $message}")
        apps.append((app, errors))
        return app, clock, errors

    yield build
    for app, errors in reversed(apps):
        reported = len(errors)
        # Fixture teardown owns only these private interpreters. Cancel Tcl
        # timers while Python callback commands still exist, then destroy.
        for callback in app.root.tk.call("after", "info"):
            app.root.tk.call("after", "cancel", callback)
        app._teardown()
        # Earlier errors fail the test's explicit assertion. Only additional
        # teardown errors belong to fixture teardown, avoiding double-reporting.
        assert not errors[reported:]


def _entry(app):
    return next(child for child in _children(app.root)
                if isinstance(child, tk.Entry)
                and child.cget("textvariable") == str(app._confirm_var))


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("pending", ["idle", "retry"])
@pytest.mark.parametrize("lifecycle", ["redraw", "navigate", "destroy"])
def test_obsolete_confirmation_callbacks_do_not_outlive_their_owner(
    ui, monkeypatch, text_size, pending, lifecycle
):
    app, _clock, errors = ui(text_size)
    old_entry = _entry(app)
    before = _authority(app.w)
    attempts = []
    if pending == "retry":
        original = app._ensure_confirm_focus

        def observe(entry, *args, **kwargs):
            attempts.append((entry, app.root.focus_get() is entry))
            return original(entry, *args, **kwargs)

        monkeypatch.setattr(app, "_ensure_confirm_focus", observe)
        app.root.withdraw()
        app.root.update_idletasks()
        assert any(entry is old_entry and not focused for entry, focused in attempts)
        assert not errors

    if lifecycle == "navigate":
        app.w.back()
        before = _authority(app.w)
        assert app.w.screen is Screen.PICK
        app._draw()
    elif lifecycle == "redraw":
        app._draw()
    else:
        app._teardown()

    assert not app.root.tk.call("info", "commands", str(old_entry))
    if lifecycle == "destroy":
        _pump(app.root)
    else:
        app.root.geometry("800x600+0+0")
        app.root.deiconify()
        app.root.update()
        app.root.focus_force()
        _pump(app.root)
        focus = app.root.focus_get()
        assert focus is not old_entry
        if lifecycle == "redraw":
            current = _entry(app)
            assert focus is current
            assert current.get() == app.w.confirm_input
        else:
            assert app.w.screen is Screen.PICK
            assert focus is app._primary
    assert not errors
    assert _authority(app.w) == before
    assert not app.w.erase_enabled and app.w._wipe_request is None
    assert not app.w.runner.started and not app.w.runner.cancelled


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("pending", ["idle", "retry"])
def test_current_confirmation_focus_work_keeps_input_and_authority(ui, text_size, pending):
    app, _clock, errors = ui(text_size)
    if pending == "retry":
        app.root.withdraw()
        app.root.update_idletasks()
    before = _authority(app.w)
    app.root.geometry("800x600+0+0")
    app.root.deiconify()
    app.root.update()
    app.root.focus_force()
    _pump(app.root)
    current = _entry(app)
    assert app.root.focus_get() is current
    assert current.get() == app.w.confirm_input
    assert _authority(app.w) == before
    assert not errors
    assert not app.w.erase_enabled and app.w._wipe_request is None
    assert not app.w.runner.started and not app.w.runner.cancelled


def _close_peer(peer):
    for callback in peer.tk.call("after", "info"):
        peer.tk.call("after", "cancel", callback)
    peer.destroy()


def test_redraw_retires_child_work_but_preserves_container_and_peer_work(ui):
    app, _clock, errors = ui("standard")
    peer = tk.Tk()
    peer.withdraw()
    peer_errors = []
    peer.report_callback_exception = lambda kind, error, _trace: peer_errors.append((kind.__name__, str(error)))
    peer.createcommand("pass16_peer_bgerror", lambda message: peer_errors.append(("Tcl bgerror", message)))
    peer.tk.eval("proc bgerror {message} {pass16_peer_bgerror $message}")
    retired, live_container, other_interpreter = [], [], []
    before = _authority(app.w)
    try:
        _entry(app).after(0, lambda: retired.append("retired child"))
        app._body.after(0, lambda: live_container.append("live container"))
        peer.after(0, lambda: other_interpreter.append("peer"))
        app._draw()
        _pump(app.root)
        assert retired == []
        assert live_container == ["live container"]
        assert other_interpreter == ["peer"]
        assert not errors and not peer_errors
        assert _authority(app.w) == before
        assert not app.w.runner.started and not app.w.runner.cancelled
    finally:
        _close_peer(peer)


def test_teardown_retires_root_and_descendant_work_but_keeps_peer_work(ui):
    app, _clock, errors = ui("standard")
    peer = tk.Tk()
    peer.withdraw()
    peer_errors = []
    peer.report_callback_exception = lambda kind, error, _trace: peer_errors.append((kind.__name__, str(error)))
    peer.createcommand("pass16_peer_bgerror", lambda message: peer_errors.append(("Tcl bgerror", message)))
    peer.tk.eval("proc bgerror {message} {pass16_peer_bgerror $message}")
    retired_root, retired_child, other_interpreter = [], [], []
    before = _authority(app.w)
    try:
        app.root.after(0, lambda: retired_root.append("retired root"))
        _entry(app).after(0, lambda: retired_child.append("retired child"))
        peer.after(0, lambda: other_interpreter.append("peer"))
        app._teardown()
        _pump(peer)
        assert retired_root == [] and retired_child == []
        assert other_interpreter == ["peer"]
        assert not errors and not peer_errors
        assert _authority(app.w) == before
        assert not app.w.runner.started and not app.w.runner.cancelled
    finally:
        _close_peer(peer)
