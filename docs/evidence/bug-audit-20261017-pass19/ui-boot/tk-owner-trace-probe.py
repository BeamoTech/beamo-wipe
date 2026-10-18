"""Root-run, private-X11 proof for TkWizard-owned variable trace lifetime.

Preparation only: this evidence-local module has not been executed by its author.
It uses the actual full constructor, its actual variable callbacks and teardown.
"""

import gc
import json
import os
import sys
import tkinter as tk
import weakref

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard


@pytest.fixture(autouse=True)
def native_effects_forbidden(monkeypatch):
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Explicit isolated X11 display is required")
    assert os.environ.get("DISPLAY") not in {None, "", ":1", ":99"}
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("native application action")
        raise AssertionError("Native application action reached")

    for name in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(name, forbidden)
    monkeypatch.setattr("beamo_wipe.ui.tk_wizard.emit_serial_marker", lambda *_args: None)
    yield
    # Finish collection on the UI thread while the private display exists.
    gc.collect()
    assert not effects


def _app(kind):
    wizard = make_demo_wizard()
    if kind == "typing":
        wizard.skip_splash()
        assert wizard.screen is Screen.KEYBOARD
    else:
        wizard.skip_intro()
        wizard.set_owner(True)
        wizard.continue_owner()
        wizard.select_disk(wizard.selectable[0].path)
        wizard.continue_pick()
        assert wizard.screen is Screen.CONFIRM
    app = TkWizard(wizard)
    app.root.withdraw()
    errors = []
    app.root.report_callback_exception = lambda cls, error, _tb: errors.append((cls.__name__, str(error)))
    # Destroy will not drain unrelated queued callbacks; full product teardown
    # owns their retirement. The probe does not use root.update after destroy.
    return app, errors


def _tokens(variable):
    return {str(token) for _modes, token in variable.trace_info()}


def _cleanup(app, variables, peers=()):
    # Only exact tokens observed before the probe are retired during fixture
    # cleanup, after assertions/evidence. This also releases failing old-source
    # callbacks without sweeping any independently added observer.
    for variable, tokens in variables:
        for token in tokens:
            if token in _tokens(variable):
                variable.trace_remove("write", token)
    for variable, token in peers:
        if token in _tokens(variable):
            variable.trace_remove("write", token)
    try:
        app._teardown()
    except tk.TclError:
        pass


@pytest.mark.parametrize("kind", ["confirm", "typing"])
@pytest.mark.parametrize("repeated", [False, True])
def test_teardown_retires_owned_traces_preserves_peer_and_state(request, kind, repeated):
    app, errors = _app(kind)
    variables = [app._confirm_var, app._typing_var]
    owned = [(variable, _tokens(variable)) for variable in variables]
    assert all(len(tokens) == 1 for _variable, tokens in owned)
    peer_calls = [[], []]
    peers = []
    for index, variable in enumerate(variables):
        calls = peer_calls[index]
        token = variable.trace_add("write", lambda *_args, calls=calls: calls.append("observed"))
        peers.append((variable, token))
    before = (app.w.confirm_input, app.w.typing_check)
    try:
        app._teardown()
        if repeated:
            app._teardown()
        variables[0].set("post-teardown-confirm")
        variables[1].set("post-teardown-typing")
        after = (app.w.confirm_input, app.w.typing_check)
        remaining = [sorted(_tokens(variable)) for variable in variables]
        request.node.user_properties.append(("owner_trace_retirement", json.dumps({
            "kind": kind, "repeated": repeated,
            "owned_before": [sorted(tokens) for _variable, tokens in owned],
            "after": remaining, "peer_tokens": [token for _variable, token in peers],
            "state_before": before, "state_after": after,
            "errors": errors, "peer_calls": peer_calls,
        })))
        assert after == before
        assert not errors
        assert all(not tokens.intersection(_tokens(variable)) for variable, tokens in owned)
        assert remaining == [[token] for _variable, token in peers]
        assert peer_calls == [["observed"], ["observed"]]
    finally:
        _cleanup(app, owned, peers)


@pytest.mark.parametrize("kind", ["confirm", "typing"])
def test_live_owner_traces_still_apply_exact_input(kind):
    app, errors = _app(kind)
    owned = [(variable, _tokens(variable)) for variable in (app._confirm_var, app._typing_var)]
    try:
        if kind == "confirm":
            token = app.w.confirm.token
            app._confirm_var.set(token)
            assert app.w.confirm_input == token
            assert app.w.token_ok
        else:
            app._typing_var.set("Owner keyboard check")
            assert app.w.typing_check == "Owner keyboard check"
        assert all(len(_tokens(variable)) == 1 for variable, _tokens_before in owned)
        assert not errors
    finally:
        _cleanup(app, owned)


@pytest.mark.parametrize("kind", ["confirm", "typing"])
def test_destroyed_app_and_local_variables_can_be_collected(request, kind):
    def build_and_destroy():
        app, errors = _app(kind)
        variables = (app._confirm_var, app._typing_var)
        refs = (weakref.ref(app), weakref.ref(app.root), *(weakref.ref(variable) for variable in variables))
        tokens = [_tokens(variable) for variable in variables]
        app._teardown()
        return refs, tokens, errors

    refs, tokens, errors = build_and_destroy()
    try:
        gc.collect()
        alive = [reference() is not None for reference in refs]
        request.node.user_properties.append(("owner_trace_collection", json.dumps({
            "kind": kind, "app_root_confirm_typing_alive": alive,
            "owned_tokens": [sorted(value) for value in tokens], "errors": errors,
        })))
        assert alive == [False, False, False, False]
        assert not errors
    finally:
        app = refs[0]()
        if app is not None:
            _cleanup(app, [(variable, saved) for variable, saved in zip((app._confirm_var, app._typing_var), tokens)])
        del app
        gc.collect()
