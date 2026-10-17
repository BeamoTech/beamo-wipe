"""Startup teardown retires only its pending native Tcl callbacks."""

import json
import os
import threading
import time
import tkinter as tk

import pytest

from beamo_wipe.startup_stages import StartupRun
from beamo_wipe.ui import tk_wizard


@pytest.fixture(autouse=True)
def isolated_fake_startup(monkeypatch):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native Tcl lifecycle requires a private X11 display")
    assert os.environ.get("DISPLAY") not in {":1", ":99"}
    monkeypatch.setattr(tk_wizard, "_ensure_tk_display", lambda: None)
    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
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
    yield
    assert not effects


@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("ending", ["close-early", "close-poll", "destroy-early", "destroy-poll",
                                    "start-failed", "loop-failed", "wizard", "failed"])
def test_startup_retires_callbacks_before_its_window_is_destroyed(monkeypatch, request, fullscreen, ending):
    real_tk = tk_wizard.tk.Tk
    real_start = StartupRun.start
    release = threading.Event()
    roots, runs, errors, snapshots = [], [], [], []

    def factory():
        root = real_tk()
        roots.append(root)
        # Tcl bgerror runs outside Tkinter.report_callback_exception. Keep the
        # observer in the Tcl interpreter so it also survives window destruction.
        root.tk.eval("set pass17_bgerrors {}; proc bgerror {message} {lappend ::pass17_bgerrors [list $message $::errorInfo]}")
        root.report_callback_exception = lambda kind, value, _tb: errors.append([kind.__name__, str(value)])
        real_destroy = root.destroy

        def destroy():
            pending = []
            for callback in root.tk.call("after", "info"):
                script, kind = root.tk.call("after", "info", callback)
                pending.append({"id": str(callback), "script": str(script), "kind": str(kind),
                                "exists": bool(root.tk.call("info", "commands", str(script)))})
            snapshots.append(pending)
            return real_destroy()

        root.destroy = destroy
        if ending.startswith("close-"):
            root.after(0 if ending.endswith("early") else 30,
                       lambda: root.tk.call(root.protocol("WM_DELETE_WINDOW")))
        elif ending.startswith("destroy-"):
            root.after(0 if ending.endswith("early") else 30, root.destroy)
        elif ending == "loop-failed":
            def fail_loop():
                raise RuntimeError("fake startup mainloop failure")
            root.mainloop = fail_loop
        return root

    def start(run):
        runs.append(run)
        if ending == "start-failed":
            raise RuntimeError("fake startup thread start failure")
        return real_start(run)

    def build(_report):
        if ending not in {"wizard", "failed"}:
            assert release.wait(3), "fixture startup worker was not released"
        if ending == "failed":
            raise OSError("fake discovery failure")
        return "fake wizard"

    monkeypatch.setattr(tk_wizard.tk, "Tk", factory)
    monkeypatch.setattr(StartupRun, "start", start)
    try:
        if ending in {"start-failed", "loop-failed"}:
            with pytest.raises(RuntimeError, match="fake startup"):
                tk_wizard.run_tk_startup(build, fullscreen=fullscreen)
        else:
            result = tk_wizard.run_tk_startup(build, fullscreen=fullscreen)
            expected = "wizard" if ending == "wizard" else "failed" if ending == "failed" else "abandoned"
            assert result[0] == expected
        release.set()
        for run in runs:
            if run.thread.ident is not None:
                run.thread.join(1)
                assert not run.thread.is_alive()
        root = roots[0]
        until = time.monotonic() + 0.15
        while time.monotonic() < until:
            root.tk.call("update")
            time.sleep(0.003)
        raw = root.tk.call("set", "pass17_bgerrors")
        native_errors = list(raw) if isinstance(raw, tuple) else root.tk.splitlist(raw)
        request.node.user_properties.append(("retirement_trace", json.dumps({
            "ending": ending, "fullscreen": fullscreen, "before_destroy": snapshots,
            "tcl_bgerrors": [str(item) for item in native_errors], "python_errors": errors,
        })))
        assert not errors
        assert not native_errors, native_errors
    finally:
        release.set()
        for run in runs:
            if run.thread.ident is not None:
                run.thread.join(1)
        for root in roots:
            for callback in root.tk.call("after", "info"):
                root.tk.call("after", "cancel", callback)
            try:
                root.destroy()
            except tk.TclError:
                pass
            # Do not leave a root -> closure -> root cycle for unrelated
            # worker-thread collection after this native lifecycle test.
            root.__dict__.pop("destroy", None)
