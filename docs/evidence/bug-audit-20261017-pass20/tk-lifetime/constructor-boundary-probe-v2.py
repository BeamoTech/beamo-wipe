"""Prepared source-only: eleven construction/cleanup fault routes and two live controls.

NOT RUN by this author. Root owns private-X11 admission and serialized runtime.
Requires BEAMO_TK_PROBE_SOURCE and BEAMO_TK_PROBE_SHA256 to authenticate the
actual imported product file in both parent and each fixed diagnostic child.
"""

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


CASES = (
    "tk-load-before", "tk-load-after", "row-label", "row-sync", "row-trace",
    "cleanup-error", "tk-init-before", "font-after-init", "variable-after-init",
    "local-variable-after-init", "image-after-init", "root-control", "row-control",
)


class ControlledConstructorFailure(RuntimeError):
    pass


class ControlledNativeConstructorFailure(ValueError):
    pass


class CleanupFailure(RuntimeError):
    pass


def _emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


def _admit():
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Explicit isolated private X11 required")
    assert os.environ.get("DISPLAY") not in (None, "", ":1", ":99")
    assert not os.environ.get("PYTEST_PLUGINS")
    expected_path = os.environ.get("BEAMO_TK_PROBE_SOURCE")
    expected_hash = os.environ.get("BEAMO_TK_PROBE_SHA256")
    actual_path = Path(ui.__file__).resolve()
    actual_hash = hashlib.sha256(actual_path.read_bytes()).hexdigest()
    assert expected_path and expected_hash, "Root must explicitly pin the imported candidate"
    assert actual_path == Path(expected_path).resolve(), (str(actual_path), expected_path)
    assert actual_hash == expected_hash, (actual_hash, expected_hash)
    return dict(source=str(actual_path), sha256=actual_hash)


def _guard(patch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("application side effect")
        raise AssertionError("Application side effect attempted")

    for target in (
        "subprocess.run", "subprocess.Popen", "os.system", "socket.create_connection",
        "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start",
        "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        patch.setattr(target, forbidden)
    patch.setattr(ui, "emit_serial_marker", lambda *_args: None)
    return effects


def _child(case):
    provenance = _admit()
    _emit("admission", case=case, provenance=provenance)
    assert threading.current_thread() is threading.main_thread()
    owner_thread = threading.get_ident()
    was_enabled = gc.isenabled()
    gc.disable()
    roots = []
    rows = []
    resources = []
    finalizers = []
    retained_errors = []
    injected = []
    original_error_ids = []
    partial_apps = []
    cleanup_calls = []
    app = None

    def inject(where, error_class=ControlledConstructorFailure):
        injected.append(where)
        error = error_class(where)
        original_error_ids.append(id(error))
        # Only scalar identity is retained outside the original traceback.
        _emit("fault-injected", where=where, exception_id=id(error))
        raise error

    original_root_init = ui.tk.Tk.__init__
    original_loadtk = ui.tk.Tk._loadtk
    original_row_init = ui._CheckRow.__init__
    original_label_init = ui.tk.Label.__init__
    original_sync = ui._CheckRow._sync
    original_trace = ui.tk.Variable.trace_add
    original_apply_fonts = ui.TkWizard._apply_fonts

    def observed_apply_fonts(owner):
        original_apply_fonts(owner)
        if case == "cleanup-error":
            partial_apps.append(weakref.ref(owner))
            inject("app constructor after native fonts, before controlled cleanup failure")

    def observed_root_init(root, *args, **kwargs):
        if case == "tk-init-before":
            inject("before native Tk.__init__, no interpreter allocated")
        return original_root_init(root, *args, **kwargs)

    def observed_loadtk(root):
        roots.append(dict(reference=weakref.ref(root), interpreter_id=id(root.tk)))
        if case == "tk-load-before":
            inject("before original Tk._loadtk, after native interpreter creation")
        original_loadtk(root)
        if case == "tk-load-after":
            inject("after original Tk._loadtk, before Tk.__init__ returned")

    def observed_row_init(row, *args, **kwargs):
        rows.append(dict(reference=weakref.ref(row),
                         original_command_id=id(kwargs.get("command"))))
        return original_row_init(row, *args, **kwargs)

    def observed_label_init(label, master=None, *args, **kwargs):
        if case == "row-label" and isinstance(master, ui._CheckRow):
            inject("CheckRow Label allocation before Destroy binding")
        return original_label_init(label, master, *args, **kwargs)

    def observed_sync(row):
        if case == "row-sync":
            inject("CheckRow first _sync before variable trace and Destroy binding")
        return original_sync(row)

    def observed_trace(variable, mode, callback):
        if case == "row-trace" and getattr(callback, "__name__", None) == "_on_variable":
            target = getattr(callback, "__self__", None)
            if isinstance(target, ui._CheckRow):
                inject("CheckRow trace_add before token assignment and Destroy binding")
        return original_trace(variable, mode, callback)

    def observe_resource(patch, kind, cls):
        original_init = cls.__init__
        original_del = cls.__del__

        def initialize(resource, *args, **kwargs):
            original_init(resource, *args, **kwargs)
            resources.append(dict(kind=kind, identity=id(resource), reference=weakref.ref(resource)))
            selected = (
                (case == "font-after-init" and kind == "font")
                or (case == "variable-after-init" and kind == "variable")
                or (case == "local-variable-after-init" and kind == "variable"
                    and isinstance(resource, ui.tk.BooleanVar))
                or (case == "image-after-init" and kind == "image")
            )
            if selected and not injected:
                inject(f"{kind} after native initialization, before owned field assignment",
                       ControlledNativeConstructorFailure)

        def finalize(resource):
            row = dict(kind=kind, identity=id(resource), thread=threading.get_ident(), returned=False)
            finalizers.append(row)
            _emit("native-finalizer-enter", **row)
            try:
                return original_del(resource)
            finally:
                row["returned"] = True
                _emit("native-finalizer-return", **row)

        patch.setattr(cls, "__init__", initialize)
        patch.setattr(cls, "__del__", finalize)

    def root_state():
        # The helper releases its temporary native wrapper on the UI thread.
        # No returned state holds a native object, bound method, or traceback.
        state = []
        for entry in roots:
            root = entry["reference"]()
            alive = False
            if root is not None:
                try:
                    alive = bool(root.winfo_exists())
                except ui.tk.TclError:
                    pass  # Correct destruction makes the command unavailable.
            state.append(dict(interpreter_id=entry["interpreter_id"],
                              wrapper_alive=root is not None, window_alive=alive))
            root = None
        return state

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        patch.setattr(ui.tk.Tk, "__init__", observed_root_init)
        patch.setattr(ui.tk.Tk, "_loadtk", observed_loadtk)
        patch.setattr(ui._CheckRow, "__init__", observed_row_init)
        patch.setattr(ui.tk.Label, "__init__", observed_label_init)
        patch.setattr(ui._CheckRow, "_sync", observed_sync)
        patch.setattr(ui.tk.Variable, "trace_add", observed_trace)
        patch.setattr(ui.TkWizard, "_apply_fonts", observed_apply_fonts)
        observe_resource(patch, "font", ui.tkfont.Font)
        observe_resource(patch, "variable", ui.tk.Variable)
        observe_resource(patch, "image", ui.tk.PhotoImage)
        try:
            wizard = make_demo_wizard()
            if case.startswith("row-") or case == "local-variable-after-init":
                wizard.skip_intro()
                wizard.set_owner(True)
                wizard.continue_owner()
                assert wizard.screen is Screen.PICK
            else:
                wizard.skip_splash()
                assert wizard.screen is Screen.KEYBOARD
            if case == "cleanup-error":
                original_cancel_audio = wizard.cancel_audio

                def fail_first_cleanup():
                    cleanup_calls.append("cancel_audio")
                    if len(cleanup_calls) == 1:
                        raise CleanupFailure("distinct controlled first cleanup failure")
                    return original_cancel_audio()

                patch.setattr(wizard, "cancel_audio", fail_first_cleanup)
            try:
                app = ui.TkWizard(wizard)
            except BaseException as error:
                retained_errors.append(error)
            fault = case not in ("root-control", "row-control")
            assert len(injected) == int(fault), injected
            assert len(retained_errors) == int(fault), retained_errors
            if case == "tk-init-before":
                assert not roots and not resources, "No-native control unexpectedly allocated a native object"
            else:
                assert roots, "No actual native root creation was observed"
            if case == "cleanup-error":
                owner = partial_apps[0]()
                assert owner is not None
                before_retry = dict(retiring=getattr(owner, "_retiring", False),
                                    native_retired=getattr(owner, "_native_retired", False),
                                    roots=root_state())
                retry_error = None
                try:
                    owner._teardown()
                except BaseException as error:
                    retry_error = dict(type=type(error).__name__, message=str(error))
                after_retry = dict(retiring=getattr(owner, "_retiring", False),
                                   native_retired=getattr(owner, "_native_retired", False),
                                   roots=root_state())
                owner = None
                violations = []
                if not (isinstance(retained_errors[0], ControlledConstructorFailure)
                        and id(retained_errors[0]) == original_error_ids[0]):
                    violations.append("original constructor exception was replaced")
                if before_retry["retiring"]:
                    violations.append("retiring flag stayed set after cleanup failed")
                if retry_error or after_retry["retiring"] or not after_retry["native_retired"]:
                    violations.append("cleanup retry did not reach retired state")
                if any(row["window_alive"] for row in after_retry["roots"]):
                    violations.append("cleanup retry left owned native window open")
                _emit("cleanup-error-boundary", before_retry=before_retry, after_retry=after_retry,
                      original_exception_ids=original_error_ids,
                      propagated_exception_ids=[id(error) for error in retained_errors],
                      propagated_exception_types=[type(error).__name__ for error in retained_errors],
                      cleanup_calls=cleanup_calls, retry_error=retry_error, violations=violations)
                assert not violations, violations
            else:
                assert all(isinstance(error, (ControlledConstructorFailure, ControlledNativeConstructorFailure))
                           for error in retained_errors)
                assert [id(error) for error in retained_errors] == original_error_ids
            if not fault:
                assert app is not None
                assert sum(row["kind"] == "font" for row in resources) == 17
                assert root_state()[0]["window_alive"], "Live constructor control unexpectedly closed"
                if case == "root-control":
                    app._typing_var.set("live keyboard control")
                    assert wizard.typing_check == "live keyboard control"
                else:
                    assert rows, "Live PICK control did not construct a comparison row"
                    live_row = rows[0]["reference"]()
                    assert live_row is not None and live_row._variable_trace is not None
                    live_row = None
                app._teardown()
            assert not effects
            state = root_state()
            alive = [dict(kind=row["kind"], identity=row["identity"])
                     for row in resources if row["reference"]() is not None]
            tracebacks = [
                [dict(file=f.filename, line=f.lineno, function=f.name)
                 for f in traceback.extract_tb(error.__traceback__)]
                for error in retained_errors
            ]
            row_state = []
            for entry in rows:
                row = entry["reference"]()
                row_state.append(dict(
                    wrapper_alive=row is not None,
                    retained_fields=[name for name in ("_font", "_variable", "_label", "_icon")
                                     if row is not None and getattr(row, name, None) is not None],
                    original_command_retained=(row is not None and
                                              id(getattr(row, "_command", None)) == entry["original_command_id"]),
                    own_trace_retained=(row is not None and getattr(row, "_variable_trace", None) is not None),
                ))
                row = None
            _emit("constructor-boundary", case=case, provenance=provenance,
                  root_state=state, native_alive=alive, finalizers=finalizers,
                  row_state=row_state,
                  retained_exception_ids=[id(error) for error in retained_errors],
                  retained_original_tracebacks=tracebacks)
            # These are behavioral assertions, not checks for a named product
            # pool/helper. The original exception/traceback is still retained.
            assert not any(row["window_alive"] for row in state), "Failed native root remained open"
            assert all(not row["retained_fields"] and not row["original_command_retained"]
                       and not row["own_trace_retained"] for row in row_state), row_state
            if not fault:
                assert not alive, "Normal close retained native wrappers without an external owner"
            # Failed CheckRow frames directly retain their original Font,
            # Variable, and command arguments. Their survival is legitimate;
            # only the product-owned row fields must be retired at this point.
            # The worker-release/owner-sweep check below verifies safe eventual
            # original finalization without clearing those traceback frames.
            assert all(row["thread"] == owner_thread and row["returned"] for row in finalizers)
            app = None
            outcome = []

            def release_and_collect():
                # Release only this fixture's exception owner. Do not edit its
                # traceback/frame objects or neutralize any native destructor.
                retained_errors.clear()
                outcome.append(gc.collect())

            collector = threading.Thread(target=release_and_collect, daemon=True,
                                         name="owned-constructor-release")
            collector.start()
            collector.join(2)
            if collector.is_alive():
                frame = sys._current_frames().get(collector.ident)
                _emit("worker-timeout", stack=[
                    dict(file=f.filename, line=f.lineno, function=f.name)
                    for f in traceback.extract_stack(frame)
                ] if frame is not None else [])
                del frame
                os._exit(91)  # This exact owned fixture child only.
            assert outcome and all(row["thread"] == owner_thread for row in finalizers)
            sweep = getattr(ui, "_collect_retired_interpreters", None)
            if sweep is not None:
                sweep()  # Owner-thread settlement after later external release.
            gc.collect()  # Same owner thread, after product's retirement sweep.
            remaining = [dict(kind=row["kind"], identity=row["identity"])
                         for row in resources if row["reference"]() is not None]
            assert not remaining, "Owner-thread sweep did not settle released native wrappers"
            assert all(row["thread"] == owner_thread and row["returned"] for row in finalizers)
            _emit("child-complete", case=case, provenance=provenance,
                  finalizers=finalizers, root_state=root_state(), effects=effects)
        finally:
            # This cleanup is after all tested boundary observations. It cannot
            # make an original-source boundary failure pass. Only owned roots
            # identified by weak references above can be destroyed here.
            if app is not None:
                try:
                    app._teardown()
                except ui.tk.TclError:
                    pass
            app = None
            retained_errors.clear()
            for entry in roots:
                root = entry["reference"]()
                if root is not None:
                    try:
                        root.destroy()
                    except ui.tk.TclError:
                        pass
                root = None
            gc.collect()
            if was_enabled:
                gc.enable()


@pytest.mark.parametrize("case", CASES)
def test_partial_native_and_row_constructor_releases_ownership(request, case):
    provenance = _admit()
    command = [sys.executable, str(Path(__file__).resolve()), "--owned-child", case]
    try:
        result = subprocess.run(command, env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                                capture_output=True, text=True, timeout=8, check=False)
        row = dict(command=command, case=case, provenance=provenance,
                   returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                   timed_out=False)
    except subprocess.TimeoutExpired as error:
        row = dict(command=command, case=case, provenance=provenance, timed_out=True,
                   stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("constructor_native_boundary", json.dumps(row)))
    assert not row["timed_out"], row
    assert row["returncode"] == 0, row
    assert '"event": "child-complete"' in row["stdout"], row


if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--owned-child" and sys.argv[2] in CASES
    _child(sys.argv[2])
