"""Read fullscreen geometry on the live kiosk's bare private Xvfb."""

import json
import os
from pathlib import Path
import threading
import time
from contextlib import ExitStack
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import copy as C
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import accessible_wizard
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, GLib, Gtk


def forbidden(*args, **kwargs):
    raise AssertionError("External app effect forbidden")


def drain(seconds=0.05):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.002)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    result = []
    with ExitStack() as patches:
        for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown"):
            patches.enter_context(patch(target, forbidden))
        for fullscreen in (False, True):
            wizard = make_demo_wizard()
            wizard.skip_intro()
            app = AccessibleWizard(wizard, fullscreen=fullscreen)
            try:
                drain(0.15)
                monitor = app.window.get_display().get_primary_monitor() or app.window.get_display().get_monitor(0)
                geometry = monitor.get_geometry()
                allocation = app.window.get_allocation()
                result.append({"surface": "wizard", "fullscreen_requested": fullscreen, "size": list(app.window.get_size()), "allocation": [allocation.width, allocation.height], "monitor_geometry": [geometry.x, geometry.y, geometry.width, geometry.height], "native_fullscreen_state": bool(app.window.get_window().get_state() & Gdk.WindowState.FULLSCREEN), "mapped": app.window.get_mapped(), "xid": app.window.get_window().get_xid()})
            finally:
                app.close()
                drain()
        patches.enter_context(patch.object(accessible_wizard, "_ensure_gtk_display", lambda: None))
        for fullscreen in (False, True):
            release = threading.Event()
            finished = threading.Event()

            def build(_report):
                try:
                    assert release.wait(timeout=2)
                    return object()
                finally:
                    finished.set()

            def inspect():
                window = next(w for w in Gtk.Window.list_toplevels() if w.get_title() == C.STARTING_TITLE and w.get_mapped())
                monitor = window.get_display().get_primary_monitor() or window.get_display().get_monitor(0)
                geometry = monitor.get_geometry()
                allocation = window.get_allocation()
                result.append({"surface": "startup", "fullscreen_requested": fullscreen, "size": list(window.get_size()), "allocation": [allocation.width, allocation.height], "monitor_geometry": [geometry.x, geometry.y, geometry.width, geometry.height], "native_fullscreen_state": bool(window.get_window().get_state() & Gdk.WindowState.FULLSCREEN), "mapped": window.get_mapped(), "xid": window.get_window().get_xid()})
                window.emit("delete-event", None)
                return False

            GLib.timeout_add(150, inspect)
            assert accessible_wizard.run_accessible_startup(build, fullscreen=fullscreen) == ("abandoned", None)
            release.set()
            assert finished.wait(timeout=1)
            drain()
    output = {"display": os.environ["DISPLAY"], "states": result, "owned_teardown": True}
    Path("/tmp/pass11-ui/native-fullscreen-geometry-trace.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
