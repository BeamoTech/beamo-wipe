"""Exercise actual fixture bodies under forced failure and native Tk teardown."""
import ast
import gc
import threading
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import font as tkfont
import weakref

import pytest


@pytest.fixture(autouse=True)
def reject_native_effects(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Native application effect reached fixture probe")
    for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
                   "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
                   "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
                   "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
        monkeypatch.setattr(target, forbidden)


@pytest.mark.parametrize("failure", ["slow-click", "click-exception"])
def test_audio_fixture_releases_its_controlled_worker_on_first_failure(monkeypatch, failure):
    from beamo_wipe import sound

    source = Path("tests/test_accessible_runtime.py").read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)
                and n.name == "test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog")
    namespace = dict(C=SimpleNamespace(SOUND_CHECK_BUTTON="sound"),
                     _canned_sound=lambda *_: object(),
                     time=SimpleNamespace(perf_counter=iter((0.0, 0.075)).__next__))
    exec(compile(ast.Module(body=[node], type_ignores=[]), "actual_fixture_body", "exec"), namespace)
    original_event = threading.Event
    barriers = []
    threads = []

    def event_factory():
        event = original_event()
        if len(barriers) < 2:
            barriers.append(event)
        return event

    monkeypatch.setattr(threading, "Event", event_factory)

    def clicked():
        thread = threading.Thread(target=sound.list_outputs)
        threads.append(thread)
        thread.start()
        assert barriers[0].wait(timeout=1)
        if failure == "click-exception":
            raise RuntimeError("injected click failure")

    app = SimpleNamespace(actions={"sound": SimpleNamespace(clicked=clicked)})
    expected = RuntimeError if failure == "click-exception" else AssertionError
    try:
        with pytest.raises(expected):
            namespace[node.name](lambda: app, monkeypatch)
        # Original first-assertion failure must not strand the controlled job.
        assert len(barriers) == 2
        assert barriers[1].is_set(), "fixture returned with its release barrier unset"
    finally:
        # Probe-owned cleanup also runs against the deliberately broken body.
        if len(barriers) == 2:
            barriers[1].set()
        for thread in threads:
            thread.join(timeout=1)
            assert not thread.is_alive()


@pytest.mark.parametrize("kind", ["boolean", "integer"])
@pytest.mark.parametrize("lifecycle", ["row", "parent", "redraw-clear"])
def test_native_trace_fixture_releases_its_independent_peer(monkeypatch, kind, lifecycle):
    import test_checkrow_trace_lifetime_pass18 as case

    root = tk.Tk()
    root.withdraw()
    root.tk.call("tk", "scaling", 1.0)
    errors = []
    root.report_callback_exception = lambda kind, error, _tb: errors.append((kind.__name__, str(error)))
    root.tk.eval("set pass18_trace_bgerrors {}; proc bgerror {message} {lappend ::pass18_trace_bgerrors $message}")
    font = tkfont.Font(root=root, family="DejaVu Sans", size=-14)
    captured = []
    original_trace = tk.Variable.trace_add

    def trace_add(variable, mode, callback):
        token = original_trace(variable, mode, callback)
        if getattr(callback, "__name__", None) == "<lambda>":
            captured.append((weakref.ref(variable), token))
        return token

    monkeypatch.setattr(tk.Variable, "trace_add", trace_add)
    request = SimpleNamespace(node=SimpleNamespace(user_properties=[]))
    try:
        case.test_retained_variable_does_not_call_a_destroyed_row((root, font, errors), request, kind, lifecycle)
        assert len(captured) == 1
        for callback in root.tk.call("after", "info"):
            root.tk.call("after", "cancel", callback)
        root.destroy()
        gc.collect()
        assert captured[0][0]() is None, "fixture peer trace retained its captured Variable"
    finally:
        for reference, token in captured:
            variable = reference()
            if variable is not None:
                if any(str(current) == token for _modes, current in variable.trace_info()):
                    variable.trace_remove("write", token)
            del variable
        try:
            root.destroy()
        except tk.TclError:
            pass
        gc.collect()
