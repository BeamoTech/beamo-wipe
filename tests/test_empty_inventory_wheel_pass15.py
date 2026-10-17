"""Empty-screen prose must preserve each nested reader's own wheel scrolling."""

import ctypes
from dataclasses import replace
import os
import sys
import time
import tkinter as tk

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import ExcludedDevice, Screen
from beamo_wipe.ui.tk_wizard import TkWizard, _Scrollbar


WHEELS = (
    pytest.param("<Button-5>", None, 1, id="button-down"),
    pytest.param("<Button-4>", None, -1, id="button-up"),
    pytest.param("<MouseWheel>", -120, 1, id="wheel-down"),
    pytest.param("<MouseWheel>", 120, -1, id="wheel-up"),
)
PROFILES = (
    pytest.param((800, 600), "standard", id="small-standard"),
    pytest.param((800, 600), "extra", id="small-extra"),
    pytest.param((1280, 720), "large", id="wide-large"),
)


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native wheel input requires an explicitly isolated X11 display")
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
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setenv("BEAMO_WIPE_DEMO", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    yield
    assert not effects


@pytest.fixture
def wheel_input():
    x11 = ctypes.CDLL("libX11.so.6")
    xtst = ctypes.CDLL("libXtst.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeMotionEvent.restype = ctypes.c_int
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.restype = ctypes.c_int
    connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert connection

    def dispatch(app, target, sequence, delta):
        x, y = _hit_point(app, target)
        if delta is None:
            button = 5 if sequence == "<Button-5>" else 4
            assert xtst.XTestFakeMotionEvent(connection, -1, x, y, 0)
            assert xtst.XTestFakeButtonEvent(connection, button, 1, 0)
            assert xtst.XTestFakeButtonEvent(connection, button, 0, 0)
            x11.XSync(connection, False)
        else:
            target.event_generate(sequence, delta=delta)
        app.root.update()

    try:
        yield dispatch
    finally:
        x11.XSync(connection, False)
        x11.XCloseDisplay(connection)


def _descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from _descendants(child)


def _state(wizard):
    return (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
            wizard.method, wizard._authorized_operation, wizard._wipe_request,
            wizard.wants_shutdown, wizard.wants_new_session)


def _settle(app):
    # Allow the owned picker's final geometry/restore timer to finish before
    # placing the wheel fixture. Later wheel input retains normal ownership.
    until = time.monotonic() + 0.21
    while time.monotonic() < until:
        app.root.update()
        time.sleep(0.005)
    app.root.update()


@pytest.fixture
def ui():
    apps = []

    def build(scenario="empty", size=(800, 600), text_size="standard", redraw=False):
        wizard = make_demo_wizard(scenario=scenario)
        wizard.preview = False
        wizard.set_text_size(text_size)
        wizard.discovery = replace(wizard.discovery, excluded=tuple(
            ExcludedDevice(f"Fake component {i}", ("read-only",), path=f"/dev/fake{i}")
            for i in range(16)
        ))
        wizard.skip_intro()
        wizard.set_owner(True)
        wizard.continue_owner()
        assert wizard.screen is (Screen.PICK_EMPTY if scenario == "empty" else Screen.PICK)
        app = TkWizard(wizard)
        errors = []
        original = app.root.report_callback_exception

        def callback_error(kind, error, trace):
            errors.append((kind.__name__, str(error)))
            original(kind, error, trace)

        app.root.report_callback_exception = callback_error
        apps.append((app, errors))
        # Polling is unrelated to wheel routing; no timer can advance a stage.
        if app._after_id is not None:
            app.root.after_cancel(app._after_id)
            app._after_id = None
        app.root.geometry(f"{size[0]}x{size[1]}+0+0")
        app.root.update()
        app.root.focus_force()
        app._draw()
        _settle(app)
        if redraw:
            app._draw()
            _settle(app)
        assert (app.root.winfo_width(), app.root.winfo_height()) == size
        assert not errors
        return app

    yield build
    for app, errors in reversed(apps):
        # Cancel owned Tcl timers while their Python command bindings still
        # exist. Python after_cancel here can remove bindings used by teardown.
        for callback in app.root.tk.call("after", "info"):
            app.root.tk.call("after", "cancel", callback)
        app._teardown()
        assert not errors


def _inventory(app):
    reader = next(widget for widget in _descendants(app.root)
                  if isinstance(widget, tk.Text) and getattr(widget, "_beamo_inventory", False))
    parent = reader.master
    while parent is not None and not isinstance(parent, tk.Canvas):
        parent = parent.master
    assert parent is not None
    return reader, parent


def _reveal(app, target, parent):
    target.focus_set()
    app.root.update()
    bounds = parent.bbox("all")
    assert bounds
    top = target.winfo_rooty() - parent.winfo_rooty()
    offset = parent.canvasy(0) + top - max(0, (parent.winfo_height()-target.winfo_height())/2)
    parent.yview_moveto(offset / max(1, bounds[3]))
    app.root.update()
    _hit_point(app, target)


def _hit_point(app, target):
    x = target.winfo_rootx() + max(1, min(20, target.winfo_width()//2))
    y = target.winfo_rooty() + max(1, min(12, target.winfo_height()//2))
    assert app.root.winfo_containing(x, y) is target
    return x, y


@pytest.mark.parametrize("size,text_size", PROFILES)
@pytest.mark.parametrize("scenario", ["empty", "happy"])
@pytest.mark.parametrize("redraw", [False, True])
@pytest.mark.parametrize("sequence,delta,direction", WHEELS)
def test_inventory_wheel_scrolls_only_its_reader(
    ui, wheel_input, size, text_size, scenario, redraw, sequence, delta, direction
):
    app = ui(scenario, size, text_size, redraw)
    reader, parent = _inventory(app)
    _reveal(app, reader, parent)
    reader.yview_moveto(0.3)
    app.root.update()
    before, outer_before = reader.yview(), parent.yview()
    text_before = reader.get("1.0", "end-1c")
    state = _state(app.w)
    assert reader.cget("state") == "disabled"
    wheel_input(app, reader, sequence, delta)
    assert direction * (reader.yview()[0] - before[0]) > 0
    assert parent.yview() == outer_before
    assert reader.get("1.0", "end-1c") == text_before
    assert reader.cget("state") == "disabled"
    assert app.root.focus_get() is reader
    assert _state(app.w) == state
    assert not app.w.runner.started and not app.w.erase_enabled


@pytest.mark.parametrize("redraw", [False, True])
@pytest.mark.parametrize("sequence,delta,direction", WHEELS)
def test_empty_prose_wheel_still_scrolls_the_outer_canvas(
    ui, wheel_input, redraw, sequence, delta, direction
):
    app = ui(redraw=redraw)
    _, parent = _inventory(app)
    parent.yview_moveto(0.2)
    app.root.update()
    top, bottom = parent.winfo_rooty(), parent.winfo_rooty()+parent.winfo_height()
    label = next(widget for widget in _descendants(parent)
                 if isinstance(widget, tk.Label) and widget.winfo_ismapped()
                 and top <= widget.winfo_rooty() and widget.winfo_rooty()+12 < bottom
                 and app.root.winfo_containing(widget.winfo_rootx()+min(20,widget.winfo_width()//2),
                                               widget.winfo_rooty()+min(12,widget.winfo_height()//2)) is widget)
    app.root.focus_set()
    app.root.update()
    before = parent.yview()
    focus, state = app.root.focus_get(), _state(app.w)
    wheel_input(app, label, sequence, delta)
    after = parent.yview()
    assert direction * (after[0]-before[0]) > 0
    parent.yview_moveto(before[0])
    parent.yview_scroll(direction, "units")
    assert after == parent.yview()
    assert app.root.focus_get() is focus
    assert _state(app.w) == state
    assert not app.w.runner.started


@pytest.mark.parametrize("redraw", [False, True])
@pytest.mark.parametrize("sequence,delta,direction", WHEELS)
def test_empty_inventory_scrollbar_keeps_its_own_wheel_command(
    ui, wheel_input, redraw, sequence, delta, direction
):
    app = ui(redraw=redraw)
    reader, parent = _inventory(app)
    scrollbar = next(widget for widget in reader.master.winfo_children()
                     if isinstance(widget, _Scrollbar))
    _reveal(app, scrollbar, parent)
    reader.yview_moveto(0.3)
    app.root.update()
    before, outer_before = reader.yview(), parent.yview()
    text_before = reader.get("1.0", "end-1c")
    state = _state(app.w)
    wheel_input(app, scrollbar, sequence, delta)
    assert direction * (reader.yview()[0]-before[0]) > 0
    assert parent.yview() == outer_before
    assert reader.get("1.0", "end-1c") == text_before
    assert reader.cget("state") == "disabled"
    assert app.root.focus_get() is scrollbar
    assert _state(app.w) == state
    assert not app.w.runner.started and not app.w.erase_enabled
