"""Destroyed checkbox rows release only their own Tk variable traces."""

import gc
import json
import os
import sys
import tkinter as tk
from tkinter import font as tkfont
import weakref

import pytest

from beamo_wipe.ui.tk_wizard import TkWizard, _CheckRow


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Trace lifetime checks require an explicitly isolated X11 display")
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
    yield
    assert not effects


@pytest.fixture
def native_root():
    root = tk.Tk()
    root.withdraw()
    root.tk.call("tk", "scaling", 1.0)
    errors = []
    root.report_callback_exception = lambda kind, error, _tb: errors.append((kind.__name__, str(error)))
    root.tk.eval("set pass18_trace_bgerrors {}; proc bgerror {message} {lappend ::pass18_trace_bgerrors $message}")
    font = tkfont.Font(root=root, family="DejaVu Sans", size=-14)
    yield root, font, errors
    # This fixture owns the complete private interpreter. Retire its timers
    # before widgets, independently of the product's row trace handling.
    for callback in root.tk.call("after", "info"):
        root.tk.call("after", "cancel", callback)
    try:
        root.destroy()
    except tk.TclError:
        pass


def _variable(root, kind):
    return tk.BooleanVar(master=root, value=False) if kind == "boolean" else tk.IntVar(master=root, value=0)


def _retire_fixture_callbacks(owner):
    pending = [owner]
    commands = {}
    while pending:
        widget = pending.pop()
        commands.update((name, widget) for name in (getattr(widget, "_tclCommands", None) or ()))
        pending.extend(widget.winfo_children())
    for callback in owner.tk.call("after", "info"):
        script, _kind = owner.tk.call("after", "info", callback)
        widget = commands.get(str(script))
        if widget is not None:
            widget.after_cancel(callback)


def _retire_row(root, parent, row, lifecycle):
    # The probe isolates variable traces from the known widget-after issue:
    # cancel pending _flow_label work while its command still exists.
    _retire_fixture_callbacks(row)
    if lifecycle == "row":
        row.destroy()
    elif lifecycle == "parent":
        parent.destroy()
    else:
        controller = TkWizard.__new__(TkWizard)
        controller.root = root
        controller._clear(parent)


@pytest.mark.parametrize("kind", ["boolean", "integer"])
@pytest.mark.parametrize("lifecycle", ["row", "parent", "redraw-clear"])
def test_retained_variable_does_not_call_a_destroyed_row(native_root, request, kind, lifecycle):
    root, font, errors = native_root
    parent = tk.Frame(root, bg="white")
    parent.pack()
    variable = _variable(root, kind)
    peer_trace_calls = []
    peer_token = variable.trace_add("write", lambda *_args: peer_trace_calls.append(variable.get()))
    try:
        row = _CheckRow(parent, text="Report preference", variable=variable, command=lambda: None, font=font)
        row.pack()
        before = [str(token) for _modes, token in variable.trace_info()]
        row_tokens = set(before) - {peer_token}
        assert len(row_tokens) == 1
        root_jobs = []
        root.after_idle(lambda: root_jobs.append("live root"))
        _retire_row(root, parent, row, lifecycle)
        variable.set(1)
        root.update()
        after = [str(token) for _modes, token in variable.trace_info()]
        native_errors = list(root.tk.call("set", "pass18_trace_bgerrors"))
        request.node.user_properties.append(("trace_retirement", json.dumps({
            "kind": kind, "lifecycle": lifecycle, "before": before, "after": after,
            "python_errors": errors, "tcl_errors": native_errors, "root_jobs": root_jobs,
            "peer_calls": peer_trace_calls,
        })))
        assert not errors
        assert not native_errors
        assert not row_tokens.intersection(after)
        assert after == [peer_token]
        assert peer_trace_calls == [variable.get()]
        assert root_jobs == ["live root"]
    finally:
        if any(str(token) == peer_token for _modes, token in variable.trace_info()):
            variable.trace_remove("write", peer_token)


@pytest.mark.parametrize("kind", ["boolean", "integer"])
@pytest.mark.parametrize("lifecycle", ["row", "parent", "redraw-clear"])
def test_destroyed_local_row_and_variable_are_collectable(native_root, request, kind, lifecycle):
    root, font, errors = native_root
    parent = tk.Frame(root, bg="white")
    parent.pack()
    variable = _variable(root, kind)
    row = _CheckRow(parent, text="Compare disks", variable=variable, command=lambda: None, font=font)
    row.pack()
    row_ref, variable_ref = weakref.ref(row), weakref.ref(variable)
    _retire_row(root, parent, row, lifecycle)
    del row, variable
    gc.collect()
    request.node.user_properties.append(("local_trace_release", json.dumps({
        "kind": kind, "lifecycle": lifecycle,
        "row_alive": row_ref() is not None, "variable_alive": variable_ref() is not None,
    })))
    assert row_ref() is None
    assert variable_ref() is None
    assert not errors


@pytest.mark.parametrize("kind", ["boolean", "integer"])
@pytest.mark.parametrize("initial", [0, 1])
@pytest.mark.parametrize("retire_first", [False, True])
def test_live_and_peer_rows_keep_their_variable_callbacks(native_root, kind, initial, retire_first):
    root, font, errors = native_root
    variable = _variable(root, kind)
    variable.set(initial)
    actions = []
    first = _CheckRow(root, text="First", variable=variable, command=lambda: actions.append("first"), font=font)
    peer = _CheckRow(root, text="Peer", variable=variable, command=lambda: actions.append("peer"), font=font)
    first.pack()
    peer.pack()
    assert len(variable.trace_info()) == 2
    first.invoke()
    root.update()
    assert variable.get() == (not initial)
    assert actions == ["first"]
    assert not errors
    if not retire_first:
        peer.invoke()
        root.update()
        assert variable.get() == bool(initial)
        assert actions == ["first", "peer"]
        assert len(variable.trace_info()) == 2
        assert not errors
        return
    _retire_fixture_callbacks(first)
    first.destroy()
    _retire_fixture_callbacks(peer)
    peer.invoke()
    root.update()
    assert variable.get() == bool(initial)
    assert actions == ["first", "peer"]
    assert len(variable.trace_info()) == 1
    assert not errors
