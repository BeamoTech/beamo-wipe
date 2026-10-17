"""Prepared, NOT RUN by author: root-owned private-X native lifetime proof.

Every subprocess is this fixed script in an explicitly isolated display. The
child rejects application side effects. Destructors are observed, never skipped
or made inert. GC changes below are diagnostic fixture state, not a product fix.
"""

import gc
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


ROUTES = ("return", "raise", "quit", "raw-destroy", "constructor-raise", "redraw")


class ControlledBoundaryFailure(RuntimeError):
    pass


def _admit():
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Explicit isolated X11 display required")
    assert os.environ.get("DISPLAY") not in (None, "", ":1", ":99")
    assert not os.environ.get("PYTEST_PLUGINS")


def _emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


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


def _child(route, retain_owner, peer):
    _admit()
    assert threading.current_thread() is threading.main_thread()
    ui_thread = threading.get_ident()
    old_gc_enabled = gc.isenabled()
    gc.disable()
    resources = []
    finalizers = []
    owners = []
    retained_errors = []
    peer_owner = []
    peer_calls = []
    callback_errors = []
    app_refs = []
    root_refs = []
    redraw_retired = []
    constructor_returned = []
    expected_typing = []
    original_class = ui.TkWizard
    original_apply_fonts = original_class._apply_fonts

    def resource_observers(patch, kind, cls):
        original_init = cls.__init__
        original_del = cls.__del__

        def observed_init(resource, *args, **kwargs):
            original_init(resource, *args, **kwargs)
            resources.append(dict(kind=kind, identity=id(resource), reference=weakref.ref(resource)))
            _emit("resource-created", kind=kind, identity=id(resource), thread=threading.get_ident())

        def observed_del(resource):
            row = dict(kind=kind, identity=id(resource), thread=threading.get_ident(), returned=False)
            finalizers.append(row)
            _emit("resource-finalizer-enter", **row)
            try:
                return original_del(resource)
            finally:
                row["returned"] = True
                _emit("resource-finalizer-return", **row)

        patch.setattr(cls, "__init__", observed_init)
        patch.setattr(cls, "__del__", observed_del)

    def apply_fonts(app):
        original_apply_fonts(app)
        if route == "constructor-raise":
            app_refs.append(weakref.ref(app))
            root_refs.append(weakref.ref(app.root))
            # Preserve this exact exception and its original constructor frame.
            raise ControlledBoundaryFailure("controlled after native font allocation")

    def construct(*args, **kwargs):
        app = original_class(*args, **kwargs)
        constructor_returned.append(True)
        app_refs.append(weakref.ref(app))
        root_refs.append(weakref.ref(app.root))
        app.root.withdraw()
        app.root.report_callback_exception = (
            lambda kind, error, _tb: callback_errors.append((kind.__name__, str(error)))
        )
        if retain_owner:
            owners.append(app)
        if peer:
            variable = app._typing_var
            token = variable.trace_add("write", lambda *_args: peer_calls.append("peer"))
            peer_owner.append((variable, token))
            before_typing = app.w.typing_check
            variable.set("live typing")
            assert app.w.typing_check == (before_typing if route == "redraw" else "live typing")
            expected_typing.append(app.w.typing_check)
        assert sum(row["kind"] == "font" for row in resources) == 17

        if route == "raise":
            original_mainloop = app.root.mainloop

            def mainloop_and_raise():
                original_mainloop()
                raise ControlledBoundaryFailure("controlled after actual mainloop")

            app.root.mainloop = mainloop_and_raise

        def leave():
            try:
                if route == "quit":
                    app.root.quit()
                elif route == "raw-destroy":
                    app.root.destroy()
                elif route == "redraw":
                    old_variables = [
                        row for row in resources if row["kind"] == "variable"
                        and row["reference"]() is not None
                        and row["reference"]() not in (app._confirm_var, app._typing_var, app._owner_var)
                    ]
                    assert old_variables, "Comparison view did not create its local variable"
                    app.w.select_disk(app.w.selectable[0].path)
                    app.w.continue_pick()
                    assert app.w.screen is Screen.CONFIRM
                    app._draw()
                    redraw_retired.extend(
                        dict(identity=row["identity"], alive=row["reference"]() is not None)
                        for row in old_variables
                    )
                    assert not any(row["alive"] for row in redraw_retired)
                    app._teardown()
                else:
                    app._teardown()
            except BaseException as error:
                callback_errors.append((type(error).__name__, str(error)))
                # Stop only this owned GUI. Preserve the original callback
                # traceback in retained_errors until all lifetime assertions.
                retained_errors.append(error)
                app.root.quit()

        app.root.after(30, leave)
        return app

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        resource_observers(patch, "font", ui.tkfont.Font)
        resource_observers(patch, "variable", ui.tk.Variable)
        resource_observers(patch, "image", ui.tk.PhotoImage)
        patch.setattr(original_class, "_apply_fonts", apply_fonts)
        patch.setattr(ui, "TkWizard", construct)
        try:
            wizard = make_demo_wizard()
            if route == "redraw":
                wizard.skip_intro()
                wizard.set_owner(True)
                wizard.continue_owner()
                assert wizard.screen is Screen.PICK
            else:
                wizard.skip_splash()
            code = None
            try:
                code = ui.run_tk(wizard)
            except ControlledBoundaryFailure as error:
                retained_errors.append(error)
                assert route in ("raise", "constructor-raise")
            assert code == (None if route in ("raise", "constructor-raise") else 0)
            assert bool(constructor_returned) == (route != "constructor-raise")
            assert not callback_errors, callback_errors
            assert not effects
            assert bool(retained_errors) == (route in ("raise", "constructor-raise"))
            # The exception is still strongly retained here. Its traceback is
            # described without clearing, replacing, or editing any frame.
            _emit("boundary", route=route, retained_owner=retain_owner, peer=peer,
                  retained_tracebacks=[
                      [dict(file=f.filename, line=f.lineno, function=f.name)
                       for f in traceback.extract_tb(error.__traceback__)]
                      for error in retained_errors
                  ], roots_alive=[ref() is not None for ref in root_refs],
                  redraw_retired=redraw_retired)
            excluded = {id(variable) for variable, _token in peer_owner}
            alive = [dict(kind=row["kind"], identity=row["identity"])
                     for row in resources if row["identity"] not in excluded
                     and row["reference"]() is not None]
            _emit("owned-native-at-boundary", alive=alive, finalizers=finalizers)
            assert not alive, "Product-owned native wrappers survived the supported boundary"
            assert all(row["thread"] == ui_thread and row["returned"] for row in finalizers)
            if owners:
                assert owners[0] is app_refs[0](), "Retained UI control was lost"
            for variable, token in peer_owner:
                variable.set("after boundary")
                assert [str(name) for _modes, name in variable.trace_info()] == [token]
                assert wizard.typing_check == expected_typing[0]
            if peer_owner:
                assert peer_calls == ["peer", "peer"]
            collected = []

            def collect_later():
                collected.append(gc.collect())

            worker = threading.Thread(target=collect_later, daemon=True, name="owned-later-collector")
            worker.start()
            worker.join(2)
            if worker.is_alive():
                frame = sys._current_frames().get(worker.ident)
                _emit("worker-timeout", stack=[
                    dict(file=f.filename, line=f.lineno, function=f.name)
                    for f in traceback.extract_stack(frame)
                ] if frame is not None else [])
                del frame
                os._exit(91)  # This positively owned isolated child only.
            assert collected and all(row["thread"] == ui_thread for row in finalizers)
            _emit("child-complete", route=route, finalizers=finalizers, effects=effects)
        finally:
            for variable, token in peer_owner:
                if any(str(name) == token for _modes, name in variable.trace_info()):
                    variable.trace_remove("write", token)
            peer_owner.clear()
            owners.clear()
            retained_errors.clear()
            # Cleanup only after the tested boundary. It cannot satisfy the
            # earlier weakref assertions. Never dispatch disposal to a worker.
            for reference in app_refs:
                app = reference()
                if app is not None:
                    try:
                        app._teardown()
                    except ui.tk.TclError:
                        pass
            app = None
            gc.collect()
            if old_gc_enabled:
                gc.enable()


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("retain_owner", (False, True))
@pytest.mark.parametrize("peer", (False, True))
def test_supported_boundary_releases_owned_native_wrappers(request, route, retain_owner, peer):
    _admit()
    command = [sys.executable, str(Path(__file__).resolve()), "--owned-child", route,
               "retained" if retain_owner else "unretained", "peer" if peer else "no-peer"]
    try:
        result = subprocess.run(command, env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                                capture_output=True, text=True, timeout=8, check=False)
        row = dict(command=command, returncode=result.returncode, stdout=result.stdout,
                   stderr=result.stderr, timed_out=False)
    except subprocess.TimeoutExpired as error:
        row = dict(command=command, timed_out=True, stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("native_owned_boundary", json.dumps(row)))
    assert not row["timed_out"], row
    assert row["returncode"] == 0, row
    assert '"event": "child-complete"' in row["stdout"], row


if __name__ == "__main__":
    assert len(sys.argv) == 5 and sys.argv[1] == "--owned-child"
    assert sys.argv[2] in ROUTES and sys.argv[3] in ("retained", "unretained")
    assert sys.argv[4] in ("peer", "no-peer")
    _child(sys.argv[2], sys.argv[3] == "retained", sys.argv[4] == "peer")
