"""A closing Tk interpreter retires native timers without deleting Tcl commands."""

import threading
import time

import pytest

from beamo_wipe.ui import tk_wizard as ui
from test_accessible_sound_review_pass15_ui import _review
from test_tk_native_constructor_pass20 import _admit, _guard


@pytest.mark.parametrize("route", ["wizard", "startup"])
@pytest.mark.parametrize("kind", ["idle", "timer"])
def test_closed_root_retires_native_tcl_work_and_preserves_peer(monkeypatch, route, kind):
    _admit()
    effects = _guard(monkeypatch)
    app = None
    if route == "wizard":
        wizard, _clock = _review()
        app = ui.TkWizard(wizard)
        root = app.root
    else:
        root = ui.tk.Tk()
    root.withdraw()
    peer = ui.tk.Tk()
    peer.withdraw()
    root.tk.eval('set closed_errors {}; proc bgerror {message} {lappend ::closed_errors $message}')
    root.tk.eval('proc beamo_native_timer {} {event generate . <<BeamoTest>>}')
    peer.tk.eval('set peer_calls 0; proc beamo_native_timer {} {incr ::peer_calls}')
    delay = "idle" if kind == "idle" else 0
    own_timer = root.tk.call("after", delay, "beamo_native_timer")
    peer_timer = peer.tk.call("after", delay, "beamo_native_timer")
    try:
        assert own_timer in root.tk.call("after", "info")
        assert peer_timer in peer.tk.call("after", "info")
        if app is not None:
            app._teardown()
        else:
            ui._close_owned_startup_root(root, threading.current_thread())
        pending = root.tk.call("after", "info")
        assert not pending, pending
        # Tcl procedures have their own ownership. Cancelling a native timer
        # must not delete its command as Tkinter.after_cancel would do.
        assert root.tk.call("info", "commands", "beamo_native_timer")
        assert peer_timer in peer.tk.call("after", "info")
        until = time.monotonic() + 0.1
        while time.monotonic() < until:
            peer.tk.call("update")
            time.sleep(0.003)
        assert peer.tk.call("set", "peer_calls") == 1
        assert not root.tk.call("set", "closed_errors")
        assert not effects
        if app is not None:
            assert not app.w.runner.started and not app.w.runner.cancelled
    finally:
        # Fixture-only cleanup follows the tested observations, including the
        # original failing assertion. Touch only these two owned interpreters.
        for owned in (root, peer):
            for callback in owned.tk.call("after", "info"):
                owned.tk.call("after", "cancel", callback)
            try:
                owned.destroy()
            except ui.tk.TclError:
                pass
        if app is not None:
            app._teardown()
        ui._collect_retired_interpreters()


def test_native_theme_remains_live_after_destroy_failure_and_retires_on_retry(monkeypatch):
    _admit()
    effects = _guard(monkeypatch)
    root = ui.tk.Tk()
    root.withdraw()
    root.tk.eval('set theme_calls 0; ttk::button .probe; bind .probe <<ThemeChanged>> {incr ::theme_calls}')
    original = root.destroy

    def fail_destroy():
        raise RuntimeError("controlled destroy interruption")

    root.destroy = fail_destroy
    try:
        with pytest.raises(RuntimeError, match="controlled destroy interruption"):
            ui._close_owned_startup_root(root, threading.current_thread())
        # An interrupted teardown must preserve the actual live notification.
        before = root.tk.call("set", "theme_calls")
        root.tk.call("ttk::ThemeChanged")
        assert root.tk.call("set", "theme_calls") > before
        root.__dict__.pop("destroy")
        ui._close_owned_startup_root(root, threading.current_thread())
        # The retained interpreter can safely receive the obsolete C callback.
        root.tk.call("ttk::ThemeChanged")
        with pytest.raises(ui.tk.TclError, match="deliberate Tcl error"):
            root.tk.call("error", "deliberate Tcl error")
        assert not effects
    finally:
        root.__dict__.pop("destroy", None)
        try:
            original()
        except ui.tk.TclError:
            pass
        ui._collect_retired_interpreters()
