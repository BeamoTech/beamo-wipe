"""Prepared actual-native interrupted trace registration, root-run only."""

import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import traceback
import weakref

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as ui


CASES = ("row-after", "typing-after", "confirm-after", "row-control")


def _admit():
    assert sys.platform.startswith("linux")
    assert os.environ.get("BEAMO_ISOLATED_X11_TEST") == "1"
    assert os.environ.get("DISPLAY") not in (None, "", ":1", ":99")
    assert not os.environ.get("PYTEST_PLUGINS")
    source = Path(ui.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source == Path(os.environ["BEAMO_TK_PROBE_SOURCE"]).resolve()
    assert digest == os.environ["BEAMO_TK_PROBE_SHA256"]
    return dict(source=str(source), sha256=digest)


def _emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


class ControlledRegistrationFailure(KeyboardInterrupt):
    pass


def _child(case):
    provenance = _admit()
    _emit("admission", case=case, provenance=provenance)
    assert threading.current_thread() is threading.main_thread()
    owner_thread = threading.get_ident()
    app = None
    held = []
    errors = []
    callbacks = []
    peers = []
    finalizers = []
    unraisables = []
    resources = []
    own_tokens = []
    peer_tokens = []
    injected_ids = []
    original_trace = ui.tk.Variable.trace_add
    callback_name = {"row-after": "_on_variable", "row-control": "_on_variable",
                     "typing-after": "_typing_var_written", "confirm-after": "_confirm_var_written"}[case]

    def observe_native(patch, kind, cls):
        original_init, original_del = cls.__init__, cls.__del__

        def initialize(resource, *args, **kwargs):
            original_init(resource, *args, **kwargs)
            resources.append((kind, id(resource), weakref.ref(resource)))

        def finalize(resource):
            row = dict(kind=kind, identity=id(resource), thread=threading.get_ident(), returned=False)
            finalizers.append(row)
            result = original_del(resource)
            row["returned"] = True
            return result

        patch.setattr(cls, "__init__", initialize)
        patch.setattr(cls, "__del__", finalize)

    def traced(variable, mode, callback):
        token = original_trace(variable, mode, callback)
        if not held and getattr(callback, "__name__", None) == callback_name:
            held.append(variable)
            own_tokens.append(token)
            peer_tokens.append(original_trace(variable, "write", lambda *_: peers.append("peer-write")))
            if case != "row-control":
                error = ControlledRegistrationFailure("original trace registration succeeded before controlled interruption")
                injected_ids.append(id(error))
                raise error
        return token

    def callback_error(kind, error, _trace):
        callbacks.append(dict(type=kind.__name__, message=str(error)))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Application side effect attempted")

    with pytest.MonkeyPatch.context() as patch:
        for target in (
            "subprocess.run", "subprocess.Popen", "os.system", "socket.create_connection",
            "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
            "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start",
            "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown",
            "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
        ):
            patch.setattr(target, forbidden)
        patch.setattr(ui, "emit_serial_marker", lambda *_args: None)
        patch.setattr(ui.tk.Tk, "report_callback_exception", lambda _root, *args: callback_error(*args))
        patch.setattr(sys, "unraisablehook", lambda error: unraisables.append(
            dict(type=error.exc_type.__name__, message=str(error.exc_value))))
        observe_native(patch, "font", ui.tkfont.Font)
        observe_native(patch, "variable", ui.tk.Variable)
        observe_native(patch, "image", ui.tk.PhotoImage)
        patch.setattr(ui.tk.Variable, "trace_add", traced)
        try:
            wizard = make_demo_wizard()
            if case.startswith("row-") or case.startswith("confirm-"):
                wizard.skip_intro()
                wizard.set_owner(True)
                wizard.continue_owner()
                assert wizard.screen is Screen.PICK
                if case.startswith("confirm-"):
                    wizard.select_disk(wizard.selectable[0].path)
                    wizard.continue_pick()
                    assert wizard.screen is Screen.CONFIRM
            else:
                wizard.skip_splash()
            try:
                app = ui.TkWizard(wizard)
            except BaseException as error:
                errors.append(error)
            assert len(held) == len(own_tokens) == len(peer_tokens) == 1
            assert len(errors) == int(case != "row-control")
            assert [id(error) for error in errors] == injected_ids
            before_frames = [[(entry.filename, entry.lineno, entry.name)
                              for entry in traceback.extract_tb(error.__traceback__)] for error in errors]
            if app is not None:
                app._teardown()
                app = None
            trace_tokens = [token for _modes, token in held[0].trace_info()]
            own_survived = own_tokens[0] in trace_tokens
            peer_survived = peer_tokens[0] in trace_tokens
            held[0].set(True if case.startswith("row-") else "trace-boundary-observation")
            after_frames = [[(entry.filename, entry.lineno, entry.name)
                             for entry in traceback.extract_tb(error.__traceback__)] for error in errors]
            observation = dict(case=case, own_trace_survived=own_survived, peer_trace_survived=peer_survived,
                               peer_calls=peers, callbacks=callbacks, exception_ids=[id(error) for error in errors],
                               original_exception_ids=injected_ids, exception_frames_unchanged=before_frames == after_frames)
            _emit("observed", **observation)
            # Cleanup only this owned fixture's surviving token AFTER the
            # boundary observation. It cannot alter the recorded result.
            for token in (own_tokens[0], peer_tokens[0]):
                if token in [name for _modes, name in held[0].trace_info()]:
                    held[0].trace_remove("write", token)
            held.clear()
            errors.clear()
            gc.collect()
            ui._collect_retired_interpreters()
            remaining = [(kind, identity) for kind, identity, reference in resources if reference() is not None]
            _emit("native-settled", finalizers=finalizers, remaining=remaining, unraisables=unraisables)
            assert not unraisables and not remaining
            assert all(row["thread"] == owner_thread and row["returned"] for row in finalizers)
            assert before_frames == after_frames, "Original exception traceback was changed"
            assert peer_survived and peers == ["peer-write"], "Independent peer trace was disturbed"
            assert not own_survived, "Interrupted trace token was not adopted and retired"
            assert not callbacks, "Closed UI callback ran on a later independent variable write"
            _emit("child-complete", case=case, provenance=provenance)
        finally:
            if app is not None:
                app._teardown()
            app = None
            for variable in held:
                for token in (*own_tokens, *peer_tokens):
                    if token in [name for _modes, name in variable.trace_info()]:
                        variable.trace_remove("write", token)
            variable = None
            held.clear()
            errors.clear()
            gc.collect()
            ui._collect_retired_interpreters()


@pytest.mark.parametrize("case", CASES)
def test_interrupted_owned_trace_is_retired(request, case):
    provenance = _admit()
    command = [sys.executable, str(Path(__file__).resolve()), "--owned-child", case]
    try:
        result = subprocess.run(command, env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                                capture_output=True, text=True, timeout=8, check=False)
        record = dict(case=case, command=command, provenance=provenance, returncode=result.returncode,
                      stdout=result.stdout, stderr=result.stderr, timed_out=False)
    except subprocess.TimeoutExpired as error:
        record = dict(case=case, command=command, provenance=provenance, timed_out=True,
                      stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("trace_adoption_child", json.dumps(record)))
    assert not record["timed_out"], record
    assert record["returncode"] == 0, record
    assert not record["stderr"], record
    assert '"event": "child-complete"' in record["stdout"], record


if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--owned-child" and sys.argv[2] in CASES
    _child(sys.argv[2])
