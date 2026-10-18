"""Prepared only: owned PhotoImage initializer/destructor boundary proof.

No runtime by the author. Root owns serialized private-X execution. Each child
authenticates its actual imported candidate and rejects application effects.
Original Image.__del__ is invoked unchanged; unraisables are scalar evidence.
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


CASES = ("before-init", "after-init", "live-control")


class ControlledImageInitializationFailure(ValueError):
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
    assert expected_path and expected_hash, "Root must pin the actual imported source"
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
    images = []
    roots = []
    finalizers = []
    unraisables = []
    retained_errors = []
    injected_ids = []
    app = None
    original_photo_init = ui.tk.PhotoImage.__init__
    original_image_del = ui.tk.Image.__del__
    original_loadtk = ui.tk.Tk._loadtk

    def inject(where):
        error = ControlledImageInitializationFailure(where)
        injected_ids.append(id(error))
        _emit("image-fault-injected", where=where, exception_id=id(error))
        raise error

    def photo_init(image, *args, **kwargs):
        # Only weak identity observations survive this constructor call.
        record = dict(reference=weakref.ref(image), identity=id(image), initialized=False)
        images.append(record)
        if case == "before-init" and not injected_ids:
            inject("PhotoImage initializer before original first statement")
        original_photo_init(image, *args, **kwargs)
        record["initialized"] = True
        if case == "after-init" and not injected_ids:
            inject("PhotoImage after actual native allocation, before app field assignment")

    def observed_photo_del(image):
        row = dict(identity=id(image), thread=threading.get_ident(), returned=False)
        finalizers.append(row)
        _emit("image-finalizer-enter", **row)
        try:
            result = original_image_del(image)
        except BaseException as error:
            row["exception_type"] = type(error).__name__
            row["exception_message"] = str(error)
            raise
        else:
            row["returned"] = True
            return result
        finally:
            _emit("image-finalizer-exit", **row)

    def loadtk(root):
        roots.append(weakref.ref(root))
        return original_loadtk(root)

    def unraisable_hook(argument):
        # Do not retain argument, exception, object, or traceback/frame objects.
        # Python's unraisable function identity is copied as plain text only.
        row = dict(
            exception_type=type(argument.exc_value).__name__,
            exception_message=str(argument.exc_value),
            function=str(getattr(argument.object, "__qualname__", type(argument.object).__name__)),
            message=str(argument.err_msg) if argument.err_msg is not None else None,
        )
        unraisables.append(row)
        _emit("unraisable", **row)

    def root_state():
        state = []
        for reference in roots:
            root = reference()
            window_alive = False
            if root is not None:
                try:
                    window_alive = bool(root.winfo_exists())
                except ui.tk.TclError:
                    pass
            state.append(dict(wrapper_alive=root is not None, window_alive=window_alive))
            root = None
        return state

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        patch.setattr(ui.tk.PhotoImage, "__init__", photo_init)
        patch.setattr(ui.tk.PhotoImage, "__del__", observed_photo_del)
        patch.setattr(ui.tk.Tk, "_loadtk", loadtk)
        patch.setattr(sys, "unraisablehook", unraisable_hook)
        try:
            wizard = make_demo_wizard()
            wizard.skip_splash()
            assert wizard.screen is Screen.KEYBOARD
            try:
                app = ui.TkWizard(wizard)
            except BaseException as error:
                retained_errors.append(error)
            fault = case != "live-control"
            assert len(injected_ids) == int(fault)
            assert [id(error) for error in retained_errors] == injected_ids
            assert all(isinstance(error, ControlledImageInitializationFailure) for error in retained_errors)
            assert images and roots
            if fault:
                assert app is None and len(images) == 1
                assert images[0]["initialized"] == (case == "after-init")
            else:
                assert app is not None and len(images) == 2
                assert all(row["initialized"] for row in images)
                assert app._logo_header is images[0]["reference"]()
                assert app._logo_splash is images[1]["reference"]()
                assert root_state()[0]["window_alive"]
                app._teardown()
            state = root_state()
            _emit("image-constructor-boundary", case=case, provenance=provenance,
                  root_state=state,
                  images=[dict(identity=row["identity"], initialized=row["initialized"],
                               alive=row["reference"]() is not None) for row in images],
                  retained_original_exception_ids=[id(error) for error in retained_errors],
                  retained_original_tracebacks=[
                      [dict(file=f.filename, line=f.lineno, function=f.name)
                       for f in traceback.extract_tb(error.__traceback__)]
                      for error in retained_errors
                  ], finalizers=finalizers, unraisables=unraisables, effects=effects)
            assert not any(row["window_alive"] for row in state)
            assert not effects
            app = None
            collected = []

            def release_and_collect():
                retained_errors.clear()
                collected.append(gc.collect())

            collector = threading.Thread(target=release_and_collect, daemon=True,
                                         name="owned-image-exception-release")
            collector.start()
            collector.join(2)
            if collector.is_alive():
                frame = sys._current_frames().get(collector.ident)
                _emit("worker-timeout", stack=[
                    dict(file=f.filename, line=f.lineno, function=f.name)
                    for f in traceback.extract_stack(frame)
                ] if frame is not None else [])
                del frame
                os._exit(91)  # Only this exact owned diagnostic child.
            assert collected
            sweep = getattr(ui, "_collect_retired_interpreters", None)
            if sweep is not None:
                sweep()
            gc.collect()
            alive = [row["identity"] for row in images if row["reference"]() is not None]
            _emit("image-owner-settled", case=case, finalizers=finalizers,
                  unraisables=unraisables, alive_images=alive)
            assert not alive
            assert {row["identity"] for row in finalizers} == {row["identity"] for row in images}
            assert all(row["thread"] == owner_thread for row in finalizers)
            assert not unraisables, "Original native Image finalizer emitted an unraisable"
            assert all(row["returned"] for row in finalizers)
            _emit("child-complete", case=case, provenance=provenance,
                  finalizers=finalizers, unraisables=unraisables, effects=effects)
        finally:
            # Owner-thread cleanup is after the boundary evidence/assertions.
            # No exception/traceback/native-handle or destructor is edited.
            if app is not None:
                try:
                    app._teardown()
                except ui.tk.TclError:
                    pass
            app = None
            retained_errors.clear()
            for reference in roots:
                root = reference()
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
def test_owned_image_initializer_preserves_safe_original_finalization(request, case):
    provenance = _admit()
    command = [sys.executable, str(Path(__file__).resolve()), "--owned-child", case]
    try:
        result = subprocess.run(command, env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                                capture_output=True, text=True, timeout=8, check=False)
        row = dict(command=command, case=case, provenance=provenance, returncode=result.returncode,
                   stdout=result.stdout, stderr=result.stderr, timed_out=False)
    except subprocess.TimeoutExpired as error:
        row = dict(command=command, case=case, provenance=provenance, timed_out=True,
                   stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("image_preinit_native_boundary", json.dumps(row)))
    assert not row["timed_out"], row
    assert row["returncode"] == 0, row
    assert '"event": "child-complete"' in row["stdout"], row


if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--owned-child" and sys.argv[2] in CASES
    _child(sys.argv[2])
