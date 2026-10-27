"""Exercise exact Orca-test child ownership without importing GTK or services."""

import ast
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("boundary", ["audio", "reader", "audio-start", "reader-start"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_orca_child_acquisition_is_protected(monkeypatch, tmp_path, boundary, error_type):
    source = Path(__file__).with_name("test_accessible_runtime.py")
    node = next(item for item in ast.parse(source.read_bytes()).body
                if isinstance(item, ast.FunctionDef) and item.name == "test_orca_announces_every_result")
    acquired, calls = [], []
    primary = error_type("fake child acquisition interruption")

    class Child:
        def __init__(self, name):
            self.name = name

        def poll(self):
            calls.append((self.name, "poll"))
            return None

        def terminate(self):
            calls.append((self.name, "terminate"))

        def wait(self, timeout):
            calls.append((self.name, "wait", timeout))
            return 0

    def popen(argv, **kwargs):
        assert kwargs == {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        name = "audio" if argv[0] == "pulseaudio" else "reader"
        if boundary == name + "-start":
            raise primary
        handle = Child(name)
        acquired.append(handle)
        return handle

    monkeypatch.setattr("shutil.which", lambda _name: "/fake/orca")
    namespace = dict(
        os=SimpleNamespace(environ={"BEAMO_TEST_ORCA_CHILD": "1", "DBUS_SESSION_BUS_ADDRESS": "fake"}),
        sys=sys, Path=Path, time=time,
        subprocess=SimpleNamespace(Popen=popen, DEVNULL=subprocess.DEVNULL),
    )
    exec(  # noqa: S102 - exact checked-in test function, without GTK/services
        compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace,
    )
    function = namespace[node.name]
    previous_trace = sys.gettrace()
    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if (not fired and boundary in {"audio", "reader"} and event == "line"
                and frame.f_code is function.__code__
                and frame.f_locals.get(boundary) is not None
                and any(frame.f_locals[boundary] is handle for handle in acquired)):
            fired = True
            raise primary
        return interrupt

    try:
        sys.settrace(interrupt)
        with pytest.raises(error_type) as caught:
            function(tmp_path, SimpleNamespace(getfixturevalue=lambda _name: None))
        assert caught.value is primary
    finally:
        sys.settrace(previous_trace)
    assert fired is (boundary in {"audio", "reader"})
    assert len(acquired) == {"audio": 1, "reader": 2, "audio-start": 0, "reader-start": 1}[boundary]
    for handle in acquired:
        assert calls.count((handle.name, "terminate")) == 1
        assert calls.count((handle.name, "wait", 5 if handle.name == "audio" else 10)) == 1
