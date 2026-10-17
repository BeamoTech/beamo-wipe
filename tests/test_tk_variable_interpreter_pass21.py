# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression: tk variable interpreter."""

import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import weakref

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as ui


CASES = ("ordinary-control", "peer-persistent", "peer-comparison", "no-default-persistent", "no-default-comparison", "ordinary-confirm", "peer-confirm")


def _admit():
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Explicit isolated private X11 required")
    assert os.environ.get("DISPLAY") not in (None, "", ":1", ":99")
    assert not os.environ.get("PYTEST_PLUGINS")
    expected = Path(os.environ.get("BEAMO_TK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/tk_wizard.py"))).resolve()
    actual = Path(ui.__file__).resolve()
    digest = hashlib.sha256(actual.read_bytes()).hexdigest()
    assert actual == expected
    assert digest == os.environ.get("BEAMO_TK_PROBE_SHA256", hashlib.sha256(Path(os.environ.get("BEAMO_TK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/tk_wizard.py"))).read_bytes()).hexdigest())
    return dict(source=str(actual), sha256=digest)


def _emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


def _guard(patch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("application side effect")
        raise AssertionError("Application side effect attempted")

    for name in (
        "subprocess.run", "subprocess.Popen", "os.system", "socket.create_connection",
        "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start",
        "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        patch.setattr(name, forbidden)
    patch.setattr(ui, "emit_serial_marker", lambda *_args: None)
    return effects


def _child(case):
    provenance = _admit()
    _emit("admission", case=case, provenance=provenance)
    assert threading.current_thread() is threading.main_thread()
    owner = threading.get_ident()
    app = peer = peer_var = None
    native_refs = []
    finalizers = []
    unraisables = []
    caught = []
    bindings = []
    peer_checks = []
    input_checks = []

    def watch(patch, label, cls):
        original_init = cls.__init__
        original_del = cls.__del__

        def initialize(resource, *args, **kwargs):
            original_init(resource, *args, **kwargs)
            native_refs.append((label, id(resource), weakref.ref(resource)))

        def finalize(resource):
            row = dict(kind=label, identity=id(resource), thread=threading.get_ident(), returned=False)
            finalizers.append(row)
            result = original_del(resource)
            row["returned"] = True
            return result

        patch.setattr(cls, "__init__", initialize)
        patch.setattr(cls, "__del__", finalize)

    def unraisable(error):
        unraisables.append(dict(type=error.exc_type.__name__, message=str(error.exc_value)))

    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        patch.setattr(sys, "unraisablehook", unraisable)
        watch(patch, "font", ui.tkfont.Font)
        watch(patch, "variable", ui.tk.Variable)
        watch(patch, "image", ui.tk.PhotoImage)
        try:
            if case.startswith("peer-"):
                peer = ui.tk.Tk()
                peer.withdraw()
                peer_var = ui.tk.StringVar(master=peer, value="peer-before")
                peer_events = []
                peer_token = peer_var.trace_add("write", lambda *_: peer_events.append("write"))
                assert ui.tk._default_root is peer
            elif case.startswith("no-default-"):
                ui.tk.NoDefaultRoot()  # This owned process only; never the parent.
            wizard = make_demo_wizard()
            if case.endswith(("comparison", "confirm")):
                wizard.skip_intro()
                wizard.set_owner(True)
                wizard.continue_owner()
                assert wizard.screen is Screen.PICK
                if case.endswith("confirm"):
                    wizard.select_disk(wizard.selectable[0].path)
                    wizard.continue_pick()
                    assert wizard.screen is Screen.CONFIRM
            else:
                wizard.skip_splash()
            try:
                app = ui.TkWizard(wizard)
            except BaseException as error:
                caught.append(dict(type=type(error).__name__, message=str(error), identity=id(error)))
            if app is not None:
                for name in ("_confirm_var", "_typing_var", "_owner_var"):
                    variable = getattr(app, name)
                    bindings.append(dict(name=name, own=variable._tk is app.root.tk,
                                         peer=peer is not None and variable._tk is peer.tk))
                variable = None
                local_rows = [row for row in descendants(app.root) if isinstance(row, ui._CheckRow)]
                if case.endswith("comparison"):
                    assert local_rows, "Comparison fixture never created its actual CheckRow"
                    for row in local_rows:
                        bindings.append(dict(name="comparison", own=row._variable._tk is app.root.tk,
                                             peer=peer is not None and row._variable._tk is peer.tk))
                    row = None
                local_rows.clear()
                if wizard.screen in (Screen.KEYBOARD, Screen.CONFIRM):
                    entries = [widget for widget in descendants(app.root) if isinstance(widget, ui.tk.Entry)]
                    assert len(entries) == 1, "Expected actual keyboard/confirmation entry"
                    entry = entries[0]
                    desired = wizard.confirm.token if wizard.screen is Screen.CONFIRM else "owned input 123"
                    entry.delete(0, ui.tk.END)
                    entry.insert(0, desired)
                    input_checks.append(dict(screen=wizard.screen.name, wanted=desired, displayed=entry.get(),
                                             model=wizard.confirm_input if wizard.screen is Screen.CONFIRM else wizard.typing_check,
                                             token_ok=wizard.token_ok if wizard.screen is Screen.CONFIRM else None))
                    entry = None
                    entries.clear()
                app._teardown()
                app = None
            if peer is not None:
                peer_checks.append(bool(peer.winfo_exists()))
                peer_var.set("peer-after")
                peer_checks.extend((peer_var.get() == "peer-after", peer_events == ["write"],
                                    any(token == peer_token and "write" in modes
                                        for modes, token in peer_var.trace_info())))
                peer_var.trace_remove("write", peer_token)
                peer_var = None
                peer.destroy()
                peer = None
            gc.collect()
            ui._collect_retired_interpreters()
            remaining = [dict(kind=kind, identity=identity) for kind, identity, ref in native_refs if ref() is not None]
            _emit("observed", case=case, bindings=bindings, errors=caught, peer_checks=peer_checks, input_checks=input_checks,
                  finalizers=finalizers, remaining=remaining, effects=effects, unraisables=unraisables)
            assert not effects and not unraisables
            assert all(row["thread"] == owner and row["returned"] for row in finalizers)
            assert not remaining
            assert all(peer_checks)
            assert not caught, "Explicit owned root must work independently of Tk default-root policy"
            assert all(row["wanted"] == row["displayed"] == row["model"] for row in input_checks), "Displayed Entry input never reached the wizard state"
            assert all(row["token_ok"] is not False for row in input_checks), "Exact displayed confirmation token did not enable the confirmation gate"
            assert bindings and all(row["own"] for row in bindings), "Wizard Variable belongs to a different interpreter"
            _emit("child-complete", case=case, provenance=provenance)
        finally:
            if app is not None:
                app._teardown()
            app = None
            if peer is not None:
                peer_var = None
                peer.destroy()
            peer = None
            gc.collect()
            ui._collect_retired_interpreters()


@pytest.mark.parametrize("case", CASES)
def test_native_variables_use_the_owned_root(request, case):
    provenance = _admit()
    command = [sys.executable, str(Path(__file__).resolve()), "--owned-child", case]
    try:
        result = subprocess.run(command, env=dict(os.environ, PYTHONFAULTHANDLER="1", BEAMO_TK_PROBE_SOURCE=provenance["source"], BEAMO_TK_PROBE_SHA256=provenance["sha256"]),
                                capture_output=True, text=True, timeout=8, check=False)
        record = dict(case=case, command=command, provenance=provenance, returncode=result.returncode,
                      stdout=result.stdout, stderr=result.stderr, timed_out=False)
    except subprocess.TimeoutExpired as error:
        record = dict(case=case, command=command, provenance=provenance, timed_out=True,
                      stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("variable_root_child", json.dumps(record)))
    assert not record["timed_out"], record
    assert record["returncode"] == 0, record
    assert not record["stderr"], record
    assert '"event": "child-complete"' in record["stdout"], record


if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--owned-child" and sys.argv[2] in CASES
    _child(sys.argv[2])
