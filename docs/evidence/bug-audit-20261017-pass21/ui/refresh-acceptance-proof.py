"""Prepared root-run fake-only traces; no actual worker or display is created."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import types

import pytest

from beamo_wipe.demo import discovery_for_scenario, make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard


class ControlledLaunchInterruption(KeyboardInterrupt):
    pass


class WouldBlock(RuntimeError):
    pass


def _admit(module, prefix):
    source = Path(module.__file__).resolve()
    expected = Path(os.environ[f"BEAMO_{prefix}_PROBE_SOURCE"]).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source == expected
    assert digest == os.environ[f"BEAMO_{prefix}_PROBE_SHA256"]
    return dict(source=str(source), sha256=digest)


def _accessible(patch):
    source = Path(os.environ["BEAMO_GTK_PROBE_SOURCE"]).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == os.environ["BEAMO_GTK_PROBE_SHA256"]
    gi = types.ModuleType("gi")
    gi.require_version = lambda *_args: None
    repository = types.ModuleType("gi.repository")
    for name in ("Atk", "Gdk", "GLib", "Gtk", "Pango"):
        setattr(repository, name, types.SimpleNamespace())
    patch.setitem(sys.modules, "gi", gi)
    patch.setitem(sys.modules, "gi.repository", repository)
    spec = importlib.util.spec_from_file_location("beamo_wipe.ui.pass21_refresh_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRoot:
    def __init__(self):
        self.callbacks = []

    def after(self, _ms, callback):
        self.callbacks.append(callback)
        return len(self.callbacks)


@pytest.mark.parametrize("surface", ("tk", "gtk"))
@pytest.mark.parametrize("fault", ("event-constructor", "set-before", "set-after", "normal-control"))
def test_refresh_acceptance_failure_resolves_claim(monkeypatch, request, surface, fault):
    module = tk_wizard if surface == "tk" else _accessible(monkeypatch)
    provenance = _admit(module, "TK" if surface == "tk" else "GTK")
    wizard = make_demo_wizard()
    wizard.skip_intro()
    assert wizard.open_refresh_confirm()
    app_class = module.TkWizard if surface == "tk" else module.AccessibleWizard
    app = app_class.__new__(app_class)
    app.w = wizard
    app._refresh_lock = threading.Lock()
    app._refresh_results = {}
    app._refresh_threads = {}
    app._refresh_result = None
    app._ui_dead = False
    app.closed = False
    app.root = FakeRoot()
    app._draw = lambda: None
    effects = []
    scans = []
    completions = []
    errors = []
    threads = []
    events = []
    waits = []
    injected = []
    original_error = ControlledLaunchInterruption(f"controlled {surface} {fault}")
    original_finish = wizard.finish_refresh

    def forbidden(*_args, **_kwargs):
        effects.append("application side effect")
        raise AssertionError("Application side effect attempted")

    for name in (
        "subprocess.run", "subprocess.Popen", "os.system", "socket.create_connection",
        "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start",
        "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(name, forbidden)

    def finish(seq, outcome):
        completions.append(dict(seq=seq, exception_id=id(outcome) if isinstance(outcome, BaseException) else None))
        return original_finish(seq, outcome)

    monkeypatch.setattr(wizard, "finish_refresh", finish)
    wizard._rediscover = lambda: scans.append("fake scan") or discovery_for_scenario("happy")

    class FakeEvent:
        def __init__(self):
            if fault == "event-constructor" and not injected:
                injected.append("event-constructor")
                raise original_error
            self.flag = False
            self.number = len(events)
            events.append(self)

        def set(self):
            selected = self.number == 0 and fault in ("set-before", "set-after") and not injected
            if selected and fault == "set-before":
                injected.append("set-before")
                raise original_error
            self.flag = True
            if selected:
                injected.append("set-after")
                raise original_error

        def clear(self):
            self.flag = False

        def is_set(self):
            return self.flag

        def wait(self, timeout=None):
            waits.append(dict(event=self.number, signalled=self.flag))
            if not self.flag:
                raise WouldBlock("Actual worker would remain waiting for the unmade launch decision")
            return True

    class FakeThread:
        def __init__(self, target, **_kwargs):
            self.target = target
            self.started = False
            threads.append(self)

        def start(self):
            self.started = True

    monkeypatch.setattr(module.threading, "Event", FakeEvent)
    monkeypatch.setattr(module.threading, "Thread", FakeThread)
    try:
        if surface == "tk":
            result = app._start_refresh_scan(lambda applied: None)
        else:
            result = app._begin_refresh_scan()
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, identity=id(error), original=error is original_error))
        result = None
    for worker in threads:
        if worker.started:
            try:
                worker.target()
            except WouldBlock:
                pass  # Scalar concrete trace, no native thread actually exists.
    if fault == "normal-control":
        if surface == "tk":
            app._poll_refresh(wizard._refresh_seq, lambda applied: None)
        else:
            app._drain_refresh_result()
    record = dict(surface=surface, fault=fault, provenance=provenance, result=result,
                  state=wizard.screen.name, selectable=len(wizard.selectable), errors=errors,
                  original_exception_id=id(original_error), completions=completions,
                  scans=scans, waits=waits, registered=len(app._refresh_threads),
                  events=[dict(number=event.number, signalled=event.flag) for event in events],
                  started=sum(worker.started for worker in threads), effects=effects)
    request.node.user_properties.append(("refresh_acceptance_trace", json.dumps(record)))
    assert not effects
    if fault == "normal-control":
        assert not errors and scans == ["fake scan"]
        assert wizard.screen is Screen.OWNER
    else:
        assert injected == [fault]
        assert wizard.screen is Screen.PICK_BLOCKED, record
        assert not wizard.selectable and wizard.can_refresh, record
        assert not scans, "Rejected refresh worker entered discovery"
        assert not app._refresh_threads, record
        assert completions and completions[0]["exception_id"] == id(original_error), record
        assert not errors or all(row["original"] for row in errors), "Original launch exception identity changed"
