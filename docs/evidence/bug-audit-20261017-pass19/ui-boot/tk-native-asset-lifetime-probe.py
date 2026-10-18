"""Root-run private-X11 proof of supported Tk close/asset ownership.

Preparation only. No runtime was executed by the author. Child runs are owned,
bounded Python fixtures; every application side effect is forbidden inside them.
"""

import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
import weakref

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import tk_wizard as ui


def _admit_private_x11():
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("An explicitly isolated X11 display is required")
    assert os.environ.get("DISPLAY") not in {None, "", ":1", ":99"}


def _forbid_application_effects(patch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("application side effect")
        raise AssertionError("An application side effect was attempted")

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


def _fake_wizard():
    wizard = make_demo_wizard()
    wizard.skip_splash()
    return wizard


def _font_refs(app):
    return {
        name: weakref.ref(value) for name, value in vars(app).items()
        if isinstance(value, ui.tkfont.Font)
    }


def _has_owner_closure(app):
    command = getattr(getattr(app, "_primary", None), "_command", None)
    return any(cell.cell_contents is app for cell in (getattr(command, "__closure__", None) or ()))


def _construct_and_close(*, retained, repeated):
    # This helper returns no strong UI/resource reference in the unretained
    # case. Peer observers are tested and retired before leaving its scope.
    app = ui.TkWizard(_fake_wizard())
    app.root.withdraw()
    errors = []
    app.root.report_callback_exception = lambda cls, error, _tb: errors.append((cls.__name__, str(error)))
    fonts = _font_refs(app)
    assert len(fonts) == 17
    before = dict(backlink=app.root._tk_wizard is app, primary_closure=_has_owner_closure(app))
    assert before == dict(backlink=True, primary_closure=True)
    variable = app._typing_var
    peers = []
    peer_token = variable.trace_add("write", lambda *_args: peers.append("peer"))
    try:
        variable.set("live input")
        assert app.w.typing_check == "live input"
        app._teardown()
        if repeated:
            app._teardown()
        variable.set("after teardown")
        assert app.w.typing_check == "live input"
        assert peers == ["peer", "peer"]
        assert [str(token) for _modes, token in variable.trace_info()] == [peer_token]
        assert not errors
        after = dict(backlink=getattr(app.root, "_tk_wizard", None) is app,
                     primary_closure=_has_owner_closure(app), dead=app._ui_dead)
        return (weakref.ref(app), weakref.ref(app.root), fonts,
                app if retained else None, dict(before=before, after=after, errors=errors, peer_calls=peers))
    finally:
        if any(str(token) == peer_token for _modes, token in variable.trace_info()):
            variable.trace_remove("write", peer_token)


@pytest.mark.parametrize("retained", [False, True])
@pytest.mark.parametrize("repeated", [False, True])
def test_teardown_structure_keeps_outer_owner_boundary_explicit(monkeypatch, request, retained, repeated):
    _admit_private_x11()
    effects = _forbid_application_effects(monkeypatch)
    was_enabled = gc.isenabled()
    gc.disable()
    owner = None
    try:
        app_ref, root_ref, fonts, owner, evidence = _construct_and_close(retained=retained, repeated=repeated)
        alive = sorted(name for name, reference in fonts.items() if reference() is not None)
        evidence.update(retained=retained, repeated=repeated, alive_fonts=alive,
                        app_alive=app_ref() is not None, root_alive=root_ref() is not None,
                        automatic_gc_enabled=gc.isenabled())
        request.node.user_properties.append(("native_asset_ownership", json.dumps(evidence)))
        assert not effects
        assert evidence["after"]["dead"]
        if retained:
            # Keeping the owner is a control, not a claim that native assets
            # must remain allocated after teardown in a future correction.
            assert owner is not None and app_ref() is owner
        else:
            # This is structural evidence, not the supported outer run_tk
            # boundary assertion tested in the separate child. Teardown is
            # still running with self and cannot collect its own live frame.
            assert evidence["app_alive"] and evidence["root_alive"]
            assert len(alive) == 17
    finally:
        owner = None
        # This cleanup runs on the UI thread after assertions/evidence. It is
        # deliberately outside the tested lifecycle and cannot make it pass.
        gc.collect()
        if was_enabled:
            gc.enable()


def _emit(event, **fields):
    print(json.dumps(dict(event=event, at=time.perf_counter(), **fields)), flush=True)


class ControlledInterfaceFailure(RuntimeError):
    pass


def _child(retained, route):
    _admit_private_x11()
    assert threading.current_thread() is threading.main_thread()
    was_enabled = gc.isenabled()
    gc.disable()
    owner = []
    fonts = {}
    original_class = ui.TkWizard
    original_del = ui.tkfont.Font.__del__

    def observed_font_del(font):
        _emit("font-finalizer-enter", font_id=id(font), name=getattr(font, "name", ""),
              thread=threading.get_ident(), thread_name=threading.current_thread().name)
        try:
            return original_del(font)
        finally:
            _emit("font-finalizer-return", font_id=id(font),
                  thread=threading.get_ident(), thread_name=threading.current_thread().name)

    def construct(*args, **kwargs):
        app = original_class(*args, **kwargs)
        fonts.update(_font_refs(app))
        _emit("actual-constructor", fonts={name: id(reference()) for name, reference in fonts.items()},
              owner_thread=threading.get_ident())
        if retained:
            owner.append(app)
        if route == "raise":
            original_mainloop = app.root.mainloop

            def run_and_raise():
                original_mainloop()
                raise ControlledInterfaceFailure("owned GUI failure after actual teardown")

            app.root.mainloop = run_and_raise
        # Exercise actual run_tk -> actual full constructor -> actual run()
        # and its ordinary supported teardown. Never replace its mainloop.
        app.root.after(50, app._teardown)
        return app

    with pytest.MonkeyPatch.context() as patch:
        effects = _forbid_application_effects(patch)
        patch.setattr(ui.tkfont.Font, "__del__", observed_font_del)
        patch.setattr(ui, "TkWizard", construct)
        def call_supported():
            try:
                code = ui.run_tk(_fake_wizard())
            except ControlledInterfaceFailure as error:
                # Retain only scalar traceback provenance, then leave the
                # except scope. Do not clear frames or suppress the error
                # while run_tk could still execute its finally boundary.
                frames = traceback.extract_tb(error.__traceback__)
                _emit("supported-run-exception", route=route,
                      frames=[dict(file=f.filename, line=f.lineno, function=f.name) for f in frames])
                assert route == "raise"
                return None
            assert route == "return"
            return code

        code = call_supported()
        _emit("supported-run-return", code=code, retained=retained, route=route,
              alive_fonts=sorted(name for name, ref in fonts.items() if ref() is not None))
        assert code == (0 if route == "return" else None) and len(fonts) == 17
        outcome = []

        def collect_later():
            _emit("worker-collect-enter", thread=threading.get_ident())
            outcome.append(gc.collect())
            _emit("worker-collect-return", thread=threading.get_ident())

        collector = threading.Thread(target=collect_later, name="owned-later-collector", daemon=True)
        collector.start()
        collector.join(timeout=2)
        if collector.is_alive():
            frame = sys._current_frames().get(collector.ident)
            stack = [dict(file=entry.filename, line=entry.lineno, function=entry.name)
                     for entry in traceback.extract_stack(frame)] if frame is not None else []
            del frame
            _emit("worker-collection-timeout", stack=stack)
            # End only this positively owned diagnostic child. Normal Python
            # shutdown could wait on the very finalizer being diagnosed.
            os._exit(91)
        _emit("worker-collected", retained=retained, route=route, collections=outcome,
              alive_fonts=sorted(name for name, ref in fonts.items() if ref() is not None))
        assert not effects
        owner.clear()
        gc.collect()  # owner-thread fixture cleanup, after the tested result
    if was_enabled:
        gc.enable()
    _emit("child-complete", retained=retained, route=route)


@pytest.mark.parametrize("retained", [False, True])
@pytest.mark.parametrize("route", ["return", "raise"])
def test_full_supported_run_releases_assets_before_later_worker_collection(request, retained, route):
    _admit_private_x11()
    assert not os.environ.get("PYTEST_PLUGINS")
    source = Path(__file__).resolve()
    command = [sys.executable, str(source), "--owned-child", "retained" if retained else "unretained", route]
    # This is the only child launch. The fixed script/arguments are local and
    # child-side guards reject every native application action, including a
    # second process. Private display ownership belongs to the root runner.
    env = dict(os.environ, PYTHONFAULTHANDLER="1")
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=8, check=False)
        evidence = dict(command=command, retained=retained, route=route, returncode=result.returncode,
                        stdout=result.stdout, stderr=result.stderr, timed_out=False)
    except subprocess.TimeoutExpired as error:
        evidence = dict(command=command, retained=retained, route=route, timed_out=True,
                        stdout=str(error.stdout), stderr=str(error.stderr))
    request.node.user_properties.append(("owned_native_collection_child", json.dumps(evidence)))
    assert not evidence["timed_out"], evidence
    assert evidence["returncode"] == 0, evidence
    assert '"event": "worker-collected"' in evidence["stdout"], evidence
    assert '"event": "child-complete"' in evidence["stdout"], evidence


if __name__ == "__main__":
    assert len(sys.argv) == 4 and sys.argv[1] == "--owned-child"
    assert sys.argv[2] in {"retained", "unretained"}
    assert sys.argv[3] in {"return", "raise"}
    _child(retained=sys.argv[2] == "retained", route=sys.argv[3])
