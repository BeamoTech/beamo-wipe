"""Observe labels after exact startup-poll frames using a controlled clock."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import copy as C, startup_stages
from beamo_wipe.ui import accessible_wizard, tk_wizard
from beamo_wipe.ui.accessible_wizard import GLib, Gtk


def forbidden(*_args, **_kwargs):
    raise AssertionError("Native application effects forbidden")


def widgets(widget):
    yield widget
    children = (widget.get_children() if isinstance(widget, Gtk.Container) else ()) if isinstance(widget, Gtk.Widget) else widget.winfo_children()
    for child in children:
        yield from widgets(child)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    results = []
    for surface in ("tk", "gtk"):
        clock = [0.0]
        release, finished = threading.Event(), threading.Event()
        phases, windows = [], []
        real_run = startup_stages.StartupRun
        frame = [0]
        rescue_fired = []

        def root():
            return windows[0] if surface == "tk" else next(window for window in Gtk.Window.list_toplevels() if window.get_title() == C.STARTING_TITLE and window.get_mapped())

        def close():
            if surface == "tk":
                root().destroy()
            else:
                root().emit("delete-event", None)
            return False

        def after(callback):
            return root().after_idle(callback) if surface == "tk" else GLib.idle_add(callback)

        def fake_run(build, **_kwargs):
            run = real_run(build, clock=lambda: clock[0], stall_after_s=10)
            original = run.stalled_note

            def note(**kwargs):
                index = frame[0]
                frame[0] += 1
                if index == 1:
                    clock[0] = 11
                value = original(**kwargs)

                def inspect():
                    texts = [widget.get_text() if isinstance(widget, Gtk.Label) else widget.cget("text") for widget in widgets(root()) if isinstance(widget, (Gtk.Label, tk_wizard.tk.Label))]
                    phases.append({"frame": index, "stall_visible": C.STARTUP_STILL_WORKING in texts, "model_note": value, "active_stage": run.stages.active, "clock": clock[0]})
                    if index == 2:
                        clock[0] = 12
                        run.report(startup_stages.STAGE_BOOT_USB)
                    elif index == 3:
                        clock[0] = 23
                    elif index == 5:
                        after(close)
                    return False

                after(inspect)
                return value

            run.stalled_note = note
            return run

        def build(_report):
            try:
                assert release.wait(timeout=3)
                return object()
            finally:
                finished.set()

        with ExitStack() as patches:
            patches.enter_context(patch.object(startup_stages, "StartupRun", fake_run))
            for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
                patches.enter_context(patch(target, forbidden))
            if surface == "tk":
                real_tk = tk_wizard.tk.Tk

                def factory():
                    window = real_tk()
                    windows.append(window)
                    window.after(2000, lambda: rescue_fired.append(True) or close())
                    return window

                patches.enter_context(patch.object(tk_wizard.tk, "Tk", factory))
                patches.enter_context(patch.object(tk_wizard, "_ensure_tk_display", lambda: None))
                presenter = tk_wizard.run_tk_startup
            else:
                patches.enter_context(patch.object(accessible_wizard, "_ensure_gtk_display", lambda: None))
                rescue = GLib.timeout_add(2000, lambda: rescue_fired.append(True) or close())
                presenter = accessible_wizard.run_accessible_startup
            try:
                outcome = presenter(build)
                assert not rescue_fired
                if surface == "gtk":
                    GLib.source_remove(rescue)
            finally:
                release.set()
                assert finished.wait(timeout=1)
        assert len(phases) == 6
        results.append({"surface": surface, "outcome": outcome[0], "phases": phases})
    label = os.environ.get("PASS12_TRACE_LABEL", "original")
    output = {"display": os.environ["DISPLAY"], "results": results, "owned_teardown": True}
    Path(f"/tmp/pass12-ui/{label}-stall-frames-trace.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
