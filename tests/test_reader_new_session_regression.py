"""A newly selected accessible session speaks its startup stages."""

import sys
from types import ModuleType, SimpleNamespace

from beamo_wipe import app


def test_reader_starts_before_second_session_after_tk_switch(monkeypatch):
    events = []
    handle = object()
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")
    accessible.start_live_reader = lambda: events.append("start") or handle
    accessible.stop_live_reader = lambda reader: events.append(("stop", reader))
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)
    monkeypatch.setattr(app, "Wizard", SimpleNamespace)

    def run_one(_args, **kwargs):
        events.append(("build", kwargs["want_accessible"], kwargs["reader"]))
        if (
            len(
                [
                    event
                    for event in events
                    if isinstance(event, tuple) and event[0] == "build"
                ]
            )
            == 1
        ):
            return SimpleNamespace(
                keyboard_layout="us",
                language="en",
                text_size="normal",
                diagnostic_ui="accessible",
            )
        return 0

    monkeypatch.setattr(app, "_run_one_session", run_one)
    assert (
        app._run_session(
            SimpleNamespace(demo=False),
            session_store=None,
            use_console=False,
            want_accessible=False,
            fullscreen=True,
            reader=None,
        )
        == 0
    )
    assert events == [
        ("build", False, None),
        "start",
        ("build", True, handle),
        ("stop", handle),
    ]


def test_exited_reader_is_replaced_before_accessible_startup(monkeypatch):
    events = []
    replacement = object()
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")
    accessible.start_live_reader = lambda: events.append("start") or replacement
    accessible.stop_live_reader = lambda reader: events.append(("stop", reader))
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)

    class ExitedReader:
        def poll(self):
            return 1

    def run_one(_args, **kwargs):
        events.append(("build", kwargs["reader"]))
        return 0

    monkeypatch.setattr(app, "_run_one_session", run_one)
    assert (
        app._run_session(
            SimpleNamespace(demo=False),
            session_store=None,
            use_console=False,
            want_accessible=True,
            fullscreen=True,
            reader=ExitedReader(),
        )
        == 0
    )
    assert events == ["start", ("build", replacement), ("stop", replacement)]


def test_uninspectable_reader_is_replaced_before_accessible_startup(monkeypatch):
    events = []
    replacement = object()
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")
    accessible.start_live_reader = lambda: events.append("start") or replacement
    accessible.stop_live_reader = lambda reader: events.append(("stop", reader))
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)

    class UninspectableReader:
        def poll(self):
            raise OSError("process status unavailable")

    monkeypatch.setattr(
        app,
        "_run_one_session",
        lambda _args, **kwargs: events.append(("build", kwargs["reader"])) or 0,
    )
    assert (
        app._run_session(
            SimpleNamespace(demo=False),
            session_store=None,
            use_console=False,
            want_accessible=True,
            fullscreen=True,
            reader=UninspectableReader(),
        )
        == 0
    )
    assert events == ["start", ("build", replacement), ("stop", replacement)]
