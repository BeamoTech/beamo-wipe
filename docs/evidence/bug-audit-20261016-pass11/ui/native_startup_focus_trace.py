"""Check first GTK startup focus/Escape using private-Xvfb native input."""

import ctypes
import json
import os
from contextlib import ExitStack
from pathlib import Path
import threading
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import copy as C
from beamo_wipe.ui import accessible_wizard
from beamo_wipe.ui.accessible_wizard import Gdk, GLib, Gtk


def forbidden(*args, **kwargs):
    raise AssertionError("External app effect forbidden")


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    x11 = ctypes.CDLL("libX11.so.6")
    xtst = ctypes.CDLL("libXtst.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XKeysymToKeycode.restype = ctypes.c_uint
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int)]
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    native = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert native
    assert xtst.XTestFakeMotionEvent(native, -1, 1550, 950, 0)
    x11.XSync(native, False)
    release = threading.Event()
    complete = threading.Event()
    phases = []

    def inspect(name):
        window = next(w for w in Gtk.Window.list_toplevels() if w.get_title() == C.STARTING_TITLE and w.get_mapped())
        Gdk.Display.get_default().sync()
        focus = ctypes.c_ulong()
        revert = ctypes.c_int()
        x11.XGetInputFocus(native, ctypes.byref(focus), ctypes.byref(revert))
        phases.append({"phase": name, "focused_xid": focus.value, "window_xid": window.get_window().get_xid(), "mapped": window.get_mapped(), "gtk_child_focus": window.get_focus() is not None})
        return window

    def key():
        inspect("before-native-escape")
        code = x11.XKeysymToKeycode(native, Gdk.KEY_Escape)
        assert xtst.XTestFakeKeyEvent(native, code, True, 0)
        assert xtst.XTestFakeKeyEvent(native, code, False, 0)
        x11.XSync(native, False)
        return False

    def recover():
        windows = [w for w in Gtk.Window.list_toplevels() if w.get_title() == C.STARTING_TITLE and w.get_mapped()]
        if windows:
            window = inspect("native-escape-had-no-effect")
            window.emit("delete-event", None)
        else:
            phases.append({"phase": "native-escape-closed-window"})
        release.set()
        return False

    def build(report):
        try:
            assert release.wait(timeout=2)
            return object()
        finally:
            complete.set()

    try:
        with ExitStack() as patches:
            patches.enter_context(patch.object(accessible_wizard, "_ensure_gtk_display", lambda: None))
            for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown"):
                patches.enter_context(patch(target, forbidden))
            key_id = GLib.timeout_add(100, key)
            recover_id = GLib.timeout_add(300, recover)
            outcome = accessible_wizard.run_accessible_startup(build, fullscreen=False)
            release.set()
            assert complete.wait(timeout=1)
            phases.append({"phase": "result", "outcome": outcome[0]})
            # Retire pending owned timers if native Escape caused an early return.
            if len(phases) < 3 or phases[-2]["phase"] != "native-escape-had-no-effect":
                GLib.source_remove(recover_id)
    finally:
        release.set()
        x11.XCloseDisplay(native)
        result = {"display": os.environ["DISPLAY"], "pointer": [1550, 950], "phases": phases, "owned_teardown": complete.is_set()}
        Path("/tmp/pass11-ui/native-startup-focus-trace.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
