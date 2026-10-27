"""Evidence fallback reads have one descriptor owner across interruptions."""

import stat
import sys
import threading
from types import SimpleNamespace

import pytest

from beamo_wipe import wizard as module
from beamo_wipe import nwipe_runner
from beamo_wipe import diagnostics


@pytest.mark.parametrize("boundary", ["open", "wrapped", "normal"])
@pytest.mark.parametrize("close_error", [False, True])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_evidence_fallback_has_one_descriptor_owner(monkeypatch, boundary, close_error, error_type):
    handles, closes, failures, saves = {}, [], [], []
    wrapped = False

    def opened(*_args):
        handles[17] = "log"
        return 17

    def closed(fd):
        closes.append(handles.pop(fd, "already-closed"))
        if close_error:
            raise OSError(5, "fake close failure")

    class Stream:
        def __init__(self, closefd):
            self.closefd = closefd

        def __enter__(self):
            nonlocal wrapped
            wrapped = True
            return self

        def __exit__(self, *_args):
            if self.closefd:
                closed(17)
                handles[17] = "unrelated"

        def seek(self, *_args):
            pass

        def tell(self):
            return 4

        def read(self, _count):
            return b"data"

    fake_os = SimpleNamespace(
        open=opened, close=closed, O_RDONLY=1, O_NOFOLLOW=2, O_NONBLOCK=4,
        fstat=lambda _fd: SimpleNamespace(st_mode=stat.S_IFREG, st_uid=0), getuid=lambda: 0,
        fdopen=lambda _fd, _mode, closefd=True: Stream(closefd),
    )
    monkeypatch.setattr(module, "os", fake_os)
    monkeypatch.setattr(nwipe_runner, "os", fake_os)
    monkeypatch.setattr(nwipe_runner, "_try_log_diag", lambda *_args: None)
    monkeypatch.setattr(diagnostics, "log_diag", lambda *_args: None)
    owner = SimpleNamespace(
        _wipe_request=SimpleNamespace(logfile="/inert/log"), runner=SimpleNamespace(),
        _lock=threading.RLock(), wipe_result=None, _evidence_written_for=None,
        _evidence_flag_hint={}, _evidence_write_seq=0, _touch_report_locked=lambda: None,
        _evidence_start_wall="", _evidence_start_mono=None,
        _evidence_wall_provenance="injected", _evidence_argv=[],
        _capture_wall=lambda: ("", "injected"), now=0, selected=None, discovery=None,
        method="everyday", language="en", keyboard_layout="us", _evidence_context=lambda: (),
        _persist_evidence=lambda seq: saves.append(seq),
        _evidence_failed=lambda exc, *_args: failures.append(exc),
    )
    function = module.Wizard._write_evidence
    primary = error_type("fake interruption")
    previous = sys.gettrace()
    fired = False

    def trace(frame, event, _arg):
        nonlocal fired
        if (boundary != "normal" and not fired and event == "line"
                and frame.f_code is function.__code__ and frame.f_locals.get("fd") == 17
                and ((boundary == "open" and not wrapped) or (boundary == "wrapped" and wrapped))):
            fired = True
            raise primary
        return trace

    try:
        sys.settrace(trace)
        function(owner, result=None, cancelled=False, interrupted=False)
    finally:
        sys.settrace(previous)
    assert closes == ["log"]
    assert handles == {}
    assert fired is (boundary != "normal")
    if boundary == "normal":
        assert not failures and saves == [1]
        assert owner._pending_evidence[0]["log_text"] == "data"
    else:
        assert failures == [primary] and not saves
