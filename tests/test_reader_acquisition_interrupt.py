"""Inert ownership checks on the exact session function, without GTK/services."""

import ast
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


@pytest.mark.parametrize("acquisition", [1, 2])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, None])
@pytest.mark.parametrize("previous_status", ["unknown", "exited"])
def test_session_reader_acquisition_is_owned_before_next_line(
    monkeypatch, acquisition, error_type, previous_status,
):
    source = Path(__file__).resolve().parents[1] / "src/beamo_wipe/app.py"
    function_node = next(
        node for node in ast.parse(source.read_bytes()).body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_session"
    )
    acquired, stopped = [], []

    class Wizard:
        keyboard_layout = "us"
        language = "en"
        text_size = "normal"
        diagnostic_ui = "accessible"

    def poll():
        if previous_status == "unknown":
            raise OSError("fake reader status unavailable")
        return 1

    def start():
        handle = SimpleNamespace(poll=poll)
        acquired.append(handle)
        return handle

    reader_module = ModuleType("beamo_wipe.ui.accessible_wizard")
    reader_module.start_live_reader = start
    reader_module.stop_live_reader = stopped.append
    monkeypatch.setitem(sys.modules, reader_module.__name__, reader_module)
    namespace = dict(
        Wizard=Wizard, running_on_live_usb=lambda: True,
        _run_one_session=lambda *_a, **_kw: Wizard() if len(acquired) < acquisition else 0,
    )
    exec(  # noqa: S102 - exact checked-in function, without platform imports
        compile(ast.Module(body=[function_node], type_ignores=[]), str(source), "exec"), namespace,
    )
    function = namespace["_run_session"]
    primary = error_type("fake interruption after acquisition") if error_type else None
    previous_trace = sys.gettrace()
    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if (primary is not None and not fired and event == "line"
                and frame.f_code is function.__code__ and len(acquired) == acquisition
                and frame.f_locals.get("owned_reader") is acquired[-1]):
            fired = True
            raise primary
        return interrupt

    def call():
        return function(
            SimpleNamespace(demo=False), session_store=None, use_console=False,
            want_accessible=True, fullscreen=True, reader=None,
        )

    try:
        sys.settrace(interrupt)
        if primary is None:
            assert call() == 0
        else:
            with pytest.raises(error_type) as caught:
                call()
            assert caught.value is primary
    finally:
        sys.settrace(previous_trace)
    assert fired is (primary is not None)
    assert len(acquired) == acquisition
    assert len(stopped) == len(acquired)
    assert all(sum(handle is stopped_handle for stopped_handle in stopped) == 1
               for handle in acquired)
