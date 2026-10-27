"""Session-owned reader handles survive replacement and startup failures."""
import sys
from types import ModuleType, SimpleNamespace

import pytest

from beamo_wipe import app


@pytest.mark.parametrize("replacement", ["new", "missing", "raises"])
@pytest.mark.parametrize("previous_status", ["unknown", "exited"])
def test_replaced_owned_reader_is_still_cleaned(monkeypatch, replacement, previous_status):
    stopped = []
    started = []

    class Reader:
        def poll(self):
            if previous_status == "unknown":
                raise OSError("fixture status unavailable")
            return 1

    first, second = Reader(), object()
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")

    def start():
        started.append(True)
        if len(started) == 1:
            return first
        if replacement == "raises":
            raise OSError("fixture reader startup failed")
        return second if replacement == "new" else None

    accessible.start_live_reader = start
    accessible.stop_live_reader = stopped.append
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)
    monkeypatch.setattr(app, "Wizard", SimpleNamespace)
    seen = []

    def run_one(_args, **kwargs):
        seen.append(kwargs["reader"])
        if len(seen) == 1:
            return SimpleNamespace(keyboard_layout="us", language="en", text_size="normal",
                                   diagnostic_ui="accessible")
        return 0

    monkeypatch.setattr(app, "_run_one_session", run_one)
    def call():
        return app._run_session(
            SimpleNamespace(demo=False), session_store=None, use_console=False,
            want_accessible=True, fullscreen=True, reader=None,
        )
    if replacement == "raises":
        with pytest.raises(OSError, match="fixture reader startup failed"):
            call()
    else:
        assert call() == 0
        assert seen == [first, second if replacement == "new" else None]
    assert first in stopped
    assert len(stopped) == (2 if replacement == "new" else 1)
    if replacement == "new":
        assert second in stopped


def test_live_owned_reader_is_reused_and_cleaned_once(monkeypatch):
    stopped = []
    handle = SimpleNamespace(poll=lambda: None)
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")
    starts = []
    accessible.start_live_reader = lambda: starts.append(True) or handle
    accessible.stop_live_reader = stopped.append
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)
    monkeypatch.setattr(app, "Wizard", SimpleNamespace)
    sessions = iter([SimpleNamespace(keyboard_layout="us", language="en", text_size="normal",
                                     diagnostic_ui="accessible"), 0])
    monkeypatch.setattr(app, "_run_one_session", lambda *_args, **_kwargs: next(sessions))
    assert app._run_session(SimpleNamespace(demo=False), session_store=None, use_console=False,
                            want_accessible=True, fullscreen=True, reader=None) == 0
    assert starts == [True]
    assert stopped == [handle]
