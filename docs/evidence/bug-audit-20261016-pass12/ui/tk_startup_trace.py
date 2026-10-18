"""First Tk startup Escape uses real XTest input on private bare X11 only."""

import ctypes
from contextlib import ExitStack
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe.ui import tk_wizard


def forbidden(*_args, **_kwargs):
    raise AssertionError("External native operation forbidden")


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
    x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert connection
    results = []
    try:
        for fullscreen in (False, True):
            for requested_pointer_inside in (False, True):
                release, finished = threading.Event(), threading.Event()
                phases = []
                x11.XSetInputFocus(connection, 1, 0, 0)
                assert xtst.XTestFakeMotionEvent(connection, -1, 1550, 950, 0)
                x11.XSync(connection, False)
                real_tk = tk_wizard.tk.Tk

                def root_factory():
                    root = real_tk()

                    def position_pointer():
                        x, y = root.winfo_rootx(), root.winfo_rooty()
                        width, height = root.winfo_width(), root.winfo_height()
                        if requested_pointer_inside:
                            point = (x + width // 2, y + height // 2)
                        else:
                            point = (0, 0)
                        assert xtst.XTestFakeMotionEvent(connection, -1, *point, 0)
                        x11.XSync(connection, False)
                        phases.append({"phase": "position-pointer", "window_rect": [x, y, width, height], "pointer": point, "pointer_is_inside": x <= point[0] < x + width and y <= point[1] < y + height})

                    def key():
                        focus = ctypes.c_ulong()
                        revert = ctypes.c_int()
                        x11.XGetInputFocus(connection, ctypes.byref(focus), ctypes.byref(revert))
                        phases.append({"phase": "before-key", "native_focus": focus.value, "window_xid": root.winfo_id(), "gtk_focus": str(root.focus_get()), "mapped": bool(root.winfo_ismapped())})
                        code = x11.XKeysymToKeycode(connection, 0xFF1B)
                        assert xtst.XTestFakeKeyEvent(connection, code, 1, 0)
                        assert xtst.XTestFakeKeyEvent(connection, code, 0, 0)
                        x11.XSync(connection, False)

                    def rescue():
                        phases.append({"phase": "native-escape-had-no-effect"})
                        root.destroy()

                    root.after(100, position_pointer)
                    root.after(180, key)
                    root.after(400, rescue)
                    return root

                def build(_report):
                    try:
                        assert release.wait(timeout=2)
                        return object()
                    finally:
                        finished.set()

                try:
                    with ExitStack() as patches:
                        patches.enter_context(patch.object(tk_wizard, "_ensure_tk_display", lambda: None))
                        patches.enter_context(patch.object(tk_wizard.tk, "Tk", root_factory))
                        for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
                            patches.enter_context(patch(target, forbidden))
                        outcome = tk_wizard.run_tk_startup(build, fullscreen=fullscreen)
                        release.set()
                        assert finished.wait(timeout=1)
                        results.append({"fullscreen": fullscreen, "requested_pointer_inside": requested_pointer_inside, "outcome": outcome[0], "phases": phases, "native_escape_effective": all(phase["phase"] != "native-escape-had-no-effect" for phase in phases)})
                finally:
                    release.set()
    finally:
        x11.XCloseDisplay(connection)
    label = os.environ.get("PASS12_TRACE_LABEL", "original")
    result = {"display": os.environ["DISPLAY"], "results": results, "owned_teardown": True}
    Path(f"/tmp/pass12-ui/{label}-tk-startup-trace.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
