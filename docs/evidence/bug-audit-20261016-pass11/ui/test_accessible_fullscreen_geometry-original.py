"""The bare-X11 live GTK path must fill the requested monitor geometry."""

from types import SimpleNamespace
import threading
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.ui import accessible_wizard  # noqa: E402
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, GLib, Gtk  # noqa: E402
from test_accessible_runtime import drain  # noqa: E402


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    display = Gdk.Display.get_default()
    if display is None or display.__gtype__.name != "GdkX11Display":
        pytest.skip("Native geometry requires an X11 display")
    if __import__("os").environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Geometry tests require an explicitly isolated X11 display")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("A native application effect was reached")

    for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
        monkeypatch.setattr(target, forbidden)


def _state(window):
    Gdk.Display.get_default().sync()
    allocation = window.get_allocation()
    return {
        "size": tuple(window.get_size()),
        "allocation": (allocation.width, allocation.height),
        "origin": tuple(window.get_window().get_origin())[-2:],
        "fullscreen": bool(window.get_window().get_state() & Gdk.WindowState.FULLSCREEN),
        "mapped": window.get_mapped(),
        "xid": window.get_window().get_xid(),
    }


@pytest.mark.parametrize("surface", ["wizard", "startup"])
@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("monitor_origin", [False, True])
def test_gtk_uses_full_monitor_geometry_only_when_fullscreen(
    monkeypatch, surface, fullscreen, monitor_origin
):
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    actual = monitor.get_geometry()
    if monitor_origin:
        geometry = SimpleNamespace(x=100, y=50, width=actual.width - 150, height=actual.height - 100)
        workarea = SimpleNamespace(x=100, y=80, width=geometry.width - 20, height=geometry.height - 50)
        reported = SimpleNamespace(get_geometry=lambda: geometry, get_workarea=lambda: workarea)
        monkeypatch.setattr(Gdk.Display, "get_primary_monitor", lambda _self: reported)
    else:
        geometry, workarea = actual, monitor.get_workarea()
    expected_size = (
        (geometry.width, geometry.height) if fullscreen else
        (min(900, workarea.width), min(700, workarea.height)) if surface == "wizard" else
        (640, 420)
    )
    states = []
    if surface == "wizard":
        wizard = make_demo_wizard()
        wizard.skip_intro()
        app = AccessibleWizard(wizard, fullscreen=fullscreen)
        try:
            deadline = time.monotonic() + 0.25
            while time.monotonic() < deadline:
                drain()
                time.sleep(0.005)
            states.append(_state(app.window))
        finally:
            app.close()
            drain()
    else:
        monkeypatch.setattr(accessible_wizard, "_ensure_gtk_display", lambda: None)
        release = threading.Event()
        retired = threading.Event()

        def build(_report):
            try:
                assert release.wait(timeout=2)
                return object()
            finally:
                retired.set()

        def inspect():
            window = next(w for w in Gtk.Window.list_toplevels() if w.get_mapped() and w.get_title() == C.STARTING_TITLE)
            states.append(_state(window))
            window.emit("delete-event", None)
            return False

        GLib.timeout_add(150, inspect)
        try:
            assert accessible_wizard.run_accessible_startup(build, fullscreen=fullscreen) == ("abandoned", None)
        finally:
            release.set()
            assert retired.wait(timeout=1)
            drain()
    assert len(states) == 1
    state = states[0]
    assert state["mapped"]
    assert state["size"] == state["allocation"] == expected_size, state
    assert state["fullscreen"] is fullscreen, state
    if fullscreen:
        assert state["origin"] == (geometry.x, geometry.y), state
