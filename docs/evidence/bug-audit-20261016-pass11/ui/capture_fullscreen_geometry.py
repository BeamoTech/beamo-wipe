"""Save unedited private-Xvfb full-root GTK screenshots on fake boundaries."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from contextlib import ExitStack
from unittest.mock import patch

from PIL import ImageGrab

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import copy as C
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import accessible_wizard
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, GLib, Gtk


def forbidden(*args, **kwargs):
    raise AssertionError("External app effect forbidden")


def dpi_and_size():
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    for name in ("XDisplayWidth", "XDisplayHeight", "XDisplayWidthMM", "XDisplayHeightMM"):
        getattr(x11, name).argtypes = [ctypes.c_void_p, ctypes.c_int]
        getattr(x11, name).restype = ctypes.c_int
    connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert connection
    try:
        screen = x11.XDefaultScreen(connection)
        width, height, width_mm, height_mm = (getattr(x11, name)(connection, screen) for name in ("XDisplayWidth", "XDisplayHeight", "XDisplayWidthMM", "XDisplayHeightMM"))
        return (width, height), (width * 25.4 / width_mm, height * 25.4 / height_mm)
    finally:
        x11.XCloseDisplay(connection)


def drain(seconds=0.1):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.002)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    root_size, dpi = dpi_and_size()
    assert all(71 < value < 73 for value in dpi), dpi
    results = []

    def capture(window, name):
        Gdk.Display.get_default().sync()
        allocation = window.get_allocation()
        assert tuple(window.get_size()) == (allocation.width, allocation.height) == root_size
        assert tuple(window.get_window().get_origin())[-2:] == (0, 0)
        assert window.get_window().get_state() & Gdk.WindowState.FULLSCREEN
        captured = ImageGrab.grab(xdisplay=os.environ["DISPLAY"])
        assert captured.size == root_size
        assert any(low != high for low, high in captured.getextrema())
        path = Path(f"/tmp/pass11-ui/{name}-{root_size[0]}x{root_size[1]}-72dpi.png")
        captured.save(path, format="PNG")
        results.append({"surface": name, "image": str(path), "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "root_size": root_size, "native_allocation": (allocation.width, allocation.height), "native_origin": tuple(window.get_window().get_origin())[-2:], "native_xid": window.get_window().get_xid(), "native_fullscreen": True, "gtk_child_focused": window.get_focus() is not None, "xserver_dpi": dpi, "capture": "Pillow full private-Xvfb root; unedited"})

    with ExitStack() as patches:
        for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
            patches.enter_context(patch(target, forbidden))
        wizard = make_demo_wizard()
        wizard.skip_intro()
        app = AccessibleWizard(wizard, fullscreen=True)
        try:
            drain(0.2)
            capture(app.window, "wizard-fullscreen")
        finally:
            app.close()
            drain()
        patches.enter_context(patch.object(accessible_wizard, "_ensure_gtk_display", lambda: None))
        release = threading.Event()
        retired = threading.Event()
        errors = []

        def build(_report):
            try:
                assert release.wait(timeout=2)
                return object()
            finally:
                retired.set()

        def inspect():
            window = next(w for w in Gtk.Window.list_toplevels() if w.get_title() == C.STARTING_TITLE and w.get_mapped())
            try:
                capture(window, "startup-fullscreen")
            except BaseException as error:
                errors.append(error)
            window.emit("delete-event", None)
            return False

        GLib.timeout_add(200, inspect)
        try:
            assert accessible_wizard.run_accessible_startup(build, fullscreen=True) == ("abandoned", None)
            assert not errors, errors
        finally:
            release.set()
            assert retired.wait(timeout=1)
            drain()
    output = {"display": os.environ["DISPLAY"], "states": results, "owned_teardown": True}
    Path(f"/tmp/pass11-ui/fullscreen-capture-{root_size[0]}x{root_size[1]}.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
