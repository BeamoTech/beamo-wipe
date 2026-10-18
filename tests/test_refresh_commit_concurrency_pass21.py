# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression: refresh acceptance under an actual waiting worker interleaving."""

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


def _admit(module, prefix):
    source = Path(module.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    default = Path(__file__).resolve().parents[1]/("src/beamo_wipe/ui/tk_wizard.py" if prefix=="TK" else "src/beamo_wipe/ui/accessible_wizard.py")
    expected = Path(os.environ.get(f"BEAMO_{prefix}_PROBE_SOURCE", str(default))).resolve()
    assert source == expected
    assert digest == os.environ.get(f"BEAMO_{prefix}_PROBE_SHA256", hashlib.sha256(expected.read_bytes()).hexdigest())
    return dict(source=str(source), sha256=digest)


def _accessible(patch):
    source = Path(os.environ.get("BEAMO_GTK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/accessible_wizard.py"))).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == os.environ.get("BEAMO_GTK_PROBE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    gi = types.ModuleType("gi")
    gi.require_version = lambda *_args: None
    repository = types.ModuleType("gi.repository")
    for name in ("Atk", "Gdk", "GLib", "Gtk", "Pango"):
        setattr(repository, name, types.SimpleNamespace())
    patch.setitem(sys.modules, "gi", gi)
    patch.setitem(sys.modules, "gi.repository", repository)
    spec = importlib.util.spec_from_file_location("beamo_wipe.ui.pass21_realrefresh_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ControlledLaunchInterruption(KeyboardInterrupt):
    pass


class FakeRoot:
    def __init__(self):
        self.callbacks = []

    def after(self, _ms, callback):
        self.callbacks.append(callback)
        return len(self.callbacks)


@pytest.mark.parametrize("surface", ("tk", "gtk"))
@pytest.mark.parametrize("fault", ("set-before", "set-after", "normal-control"))
def test_actual_woken_refresh_worker_observes_locked_acceptance(monkeypatch, request, surface, fault):
    module = tk_wizard if surface == "tk" else _accessible(monkeypatch)
    provenance = _admit(module, "TK" if surface == "tk" else "GTK")
    real_event = threading.Event
    real_thread = threading.Thread
    worker_passed = real_event()  # Created before the module Event factory is patched.
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
    effects, scans, completions, errors, threads, gates, waits = [], [], [], [], [], [], []
    event_calls = []
    phase = ["observed-launch"]
    original_error = ControlledLaunchInterruption(f"controlled actual-thread {surface} {fault}")
    original_finish = wizard.finish_refresh
    main_ident = threading.get_ident()

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
        monkeypatch.setattr(target, forbidden)

    def finish(seq, outcome):
        completions.append(dict(seq=seq, error_id=id(outcome) if isinstance(outcome, BaseException) else None,
                                thread=threading.get_ident()))
        return original_finish(seq, outcome)

    def fake_discovery():
        scans.append(dict(phase=phase[0], thread=threading.get_ident()))
        return discovery_for_scenario("happy")

    monkeypatch.setattr(wizard, "finish_refresh", finish)
    wizard._rediscover = fake_discovery

    class ControlledEvent:
        def __init__(self):
            self.inner = real_event()
            self.set_calls = 0

        def wait(self, timeout=None):
            result = self.inner.wait(timeout)
            waits.append(dict(signalled=result, thread=threading.get_ident()))
            if result:
                # This is deliberately before the production worker's lock
                # acquisition. UI set-after cannot raise until it reached here.
                worker_passed.set()
            return result

        def set(self):
            self.set_calls += 1
            first = self.set_calls == 1
            if first and fault == "set-before":
                raise original_error
            self.inner.set()
            if first:
                assert worker_passed.wait(1), "Owned actual worker did not pass the launch wait"
                if fault == "set-after":
                    raise original_error

        def clear(self):
            self.inner.clear()

        def is_set(self):
            return self.inner.is_set()

    def event_factory():
        event_calls.append(threading.get_ident())
        if len(event_calls) == 1:
            gate = ControlledEvent()
            gates.append(gate)
            return gate
        # Real Thread.__init__ calls threading.Event for its _started marker.
        # Returning the original Event here leaves actual thread mechanics intact.
        return real_event()

    def thread_factory(*args, **kwargs):
        worker = real_thread(*args, **kwargs)
        threads.append(worker)
        return worker

    def launch():
        if surface == "tk":
            return app._start_refresh_scan(lambda applied: None)
        return app._begin_refresh_scan()

    def apply_result():
        if surface == "tk":
            app._poll_refresh(wizard._refresh_seq, lambda applied: None)
        else:
            app._drain_refresh_result()

    first = None
    cleanup_alive = []
    with monkeypatch.context() as launches:
        launches.setattr(module.threading, "Event", event_factory)
        launches.setattr(module.threading, "Thread", thread_factory)
        try:
            try:
                result = launch()
            except BaseException as error:
                errors.append(dict(type=type(error).__name__, identity=id(error), original=error is original_error))
                result = None
            state_at_return = wizard.screen.name
            # No fixture release has happened. A pre-set interruption in the
            # original source leaves exactly this owned worker blocked.
            for worker in threads:
                worker.join(2)
            first = dict(result=result, state_at_return=state_at_return, state_after_join=wizard.screen.name,
                         scans=list(scans), errors=list(errors), completions=list(completions),
                         alive=[worker.is_alive() for worker in threads], registered=len(app._refresh_threads),
                         gate_signalled=gates[0].inner.is_set(), set_calls=gates[0].set_calls,
                         worker_passed=worker_passed.is_set(), waits=list(waits))
        finally:
            # Release/join only positively owned handles after the first
            # boundary snapshot. The inner original Event bypasses injection.
            phase[0] = "fixture-cleanup"
            for gate in gates:
                gate.inner.set()
            for worker in threads:
                worker.join(2)
                cleanup_alive.append(worker.is_alive())

    record = dict(surface=surface, fault=fault, provenance=provenance, original_error_id=id(original_error),
                  first=first, cleanup_alive=cleanup_alive, cleanup_scans=list(scans), effects=effects)
    request.node.user_properties.append(("actual_refresh_acceptance_trace", json.dumps(record)))
    assert not effects and not any(cleanup_alive), record
    assert len(threads) == 1, record
    assert len(gates) == 1 and len(event_calls) >= 2, "Actual Thread._started did not use the original Event"
    assert all(row["thread"] != main_ident for row in waits), record
    if fault == "normal-control":
        assert first["errors"] == [] and len(first["scans"]) == 1, record
        assert first["alive"] == [False], record
        apply_result()
        assert wizard.screen is Screen.OWNER and not wizard.owner_ok and wizard.selected is None
    else:
        assert first["state_at_return"] == first["state_after_join"] == "PICK_BLOCKED", record
        assert not first["scans"] and first["alive"] == [False], record
        assert not first["registered"] and not wizard.selectable and wizard.can_refresh, record
        assert first["completions"] and first["completions"][0]["error_id"] == id(original_error), record
        assert all(error["original"] for error in first["errors"]), "Original exception identity changed"
        # Retry uses ordinary Event/Thread APIs after the rejection, still with
        # fake rediscovery. Track only this new known worker, never peers.
        phase[0] = "retry"
        retry_threads = []

        def capture_retry(*args, **kwargs):
            worker = real_thread(*args, **kwargs)
            retry_threads.append(worker)
            return worker

        with monkeypatch.context() as retry_patch:
            retry_patch.setattr(module.threading, "Thread", capture_retry)
            retry_result = launch()
            for worker in retry_threads:
                worker.join(2)
            assert retry_result is not None and len(retry_threads) == 1
            assert not any(worker.is_alive() for worker in retry_threads)
            apply_result()
        assert wizard.screen is Screen.OWNER and not wizard.owner_ok and wizard.selected is None
        assert [scan["phase"] for scan in scans] == ["retry"], scans
        assert all(scan["thread"] != main_ident for scan in scans)
        record["retry"] = dict(state=wizard.screen.name, scans=list(scans), threads=1, alive=False)
        request.node.user_properties.append(("actual_refresh_retry_trace", json.dumps(record["retry"])))
