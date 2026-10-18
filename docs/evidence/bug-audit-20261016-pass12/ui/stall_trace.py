"""Persisted fake-clock stall text across actual graphical polling frames."""

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


def children(widget):
    yield widget
    if isinstance(widget, Gtk.Widget):
        sequence = widget.get_children() if isinstance(widget, Gtk.Container) else ()
    else:
        sequence = widget.winfo_children()
    for child in sequence:
        yield from children(child)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    result = []
    for surface in ("tk", "gtk"):
        clock = [0.0]
        next_stage, release, finished = (threading.Event() for _ in range(3))
        run_ref = []
        real_run = startup_stages.StartupRun
        phases = []
        windows = []

        def fake_run(build, **_kwargs):
            run = real_run(build, clock=lambda: clock[0], stall_after_s=10)
            run_ref.append(run)
            return run

        def build(report):
            try:
                assert next_stage.wait(timeout=2)
                report(startup_stages.STAGE_BOOT_USB)
                assert release.wait(timeout=2)
                return object()
            finally:
                finished.set()

        def root():
            return windows[0] if surface == "tk" else next(window for window in Gtk.Window.list_toplevels() if window.get_title() == C.STARTING_TITLE and window.get_mapped())

        def inspect(name):
            strings = []
            for widget in children(root()):
                if isinstance(widget, Gtk.Label):
                    strings.append(widget.get_text())
                elif surface == "tk" and isinstance(widget, tk_wizard.tk.Label):
                    strings.append(widget.cget("text"))
            phases.append({"frame": name, "clock": clock[0], "stall_visible": C.STARTUP_STILL_WORKING in strings, "active_stage": run_ref[0].stages.active, "stalled_reported": run_ref[0].stages._stalled_reported})
            return False

        def transition():
            clock[0] = 12
            next_stage.set()
            return False

        def schedule(add):
            add(130, lambda: clock.__setitem__(0, 11))
            add(230, lambda: inspect("first-stall"))
            add(330, lambda: inspect("later-stall"))
            add(340, transition)
            add(430, lambda: inspect("new-stage-reset"))
            add(440, lambda: clock.__setitem__(0, 23))
            add(530, lambda: inspect("new-stage-first-stall"))
            add(630, lambda: inspect("new-stage-later-stall"))
            add(660, lambda: root().destroy())

        with ExitStack() as patches:
            patches.enter_context(patch.object(startup_stages, "StartupRun", fake_run))
            for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
                patches.enter_context(patch(target, forbidden))
            if surface == "tk":
                real_tk = tk_wizard.tk.Tk

                def factory():
                    window = real_tk()
                    windows.append(window)
                    schedule(window.after)
                    return window

                patches.enter_context(patch.object(tk_wizard.tk, "Tk", factory))
                patches.enter_context(patch.object(tk_wizard, "_ensure_tk_display", lambda: None))
                presenter = tk_wizard.run_tk_startup
            else:
                patches.enter_context(patch.object(accessible_wizard, "_ensure_gtk_display", lambda: None))
                schedule(lambda ms, callback: GLib.timeout_add(ms, callback))
                # A native destroy without Gtk.main_quit cannot retire Gtk.main.
                GLib.timeout_add(670, lambda: Gtk.main_quit())
                presenter = accessible_wizard.run_accessible_startup
            try:
                outcome = presenter(build)
            finally:
                next_stage.set()
                release.set()
                assert finished.wait(timeout=1)
        result.append({"surface": surface, "outcome": outcome[0], "phases": phases})
    label = os.environ.get("PASS12_TRACE_LABEL", "original")
    output = {"display": os.environ["DISPLAY"], "results": result, "owned_teardown": True}
    Path(f"/tmp/pass12-ui/{label}-stall-trace.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
