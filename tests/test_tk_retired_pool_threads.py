"""Retired Tk records must never be retained by a foreign collector thread."""

import _thread
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import weakref

import pytest

from beamo_wipe.ui import tk_wizard as ui


@pytest.mark.parametrize("pool_kind", ["assets", "interpreters"])
@pytest.mark.parametrize("via_gc_callback", [False, True])
@pytest.mark.parametrize("worker_owns_resource", [False, True])
def test_foreign_drain_cannot_keep_last_record(
    monkeypatch, pool_kind, via_gc_callback, worker_owns_resource
):
    """Pause a foreign snapshot while the creator releases its own resource.

    Probe finalizers have no Tcl side effects, so a regression reports the
    wrong thread instead of aborting or hanging the test process.
    """
    creator = threading.current_thread()
    progress = threading.Event()
    release_snapshot = threading.Event()
    finalizers = []
    errors = []

    class Probe(ui.tk.Variable):
        def __init__(self, label):
            self.label = label

        def __del__(self):
            finalizers.append((self.label, threading.current_thread()))

    class SnapshotGate(dict):
        def items(self):
            snapshot = list(super().items())
            if threading.current_thread() is not creator:
                progress.set()
                if not release_snapshot.wait(5):
                    raise AssertionError("Creator did not release the diagnostic snapshot")
            return snapshot

    monkeypatch.setattr(ui, "_RETIRED_NATIVE_ASSETS", SnapshotGate() if pool_kind == "assets" else {})
    monkeypatch.setattr(ui, "_RETIRED_INTERPRETERS", SnapshotGate() if pool_kind == "interpreters" else {})

    def pin(resource):
        if pool_kind == "assets":
            ui._pin_retired_assets((resource,), threading.current_thread())
        else:
            # Only the native handle field is needed by the pin helper. This
            # root owns no actual Tcl interpreter and opens no display.
            root = ui.tk.Tk.__new__(ui.tk.Tk)
            root.tk = resource
            ui._pin_retired_interpreter(root)
            root.tk = None

    resource = Probe("creator")
    reference = weakref.ref(resource)
    pin(resource)
    del resource

    def foreign_drain():
        try:
            if worker_owns_resource:
                resource = Probe("worker")
                pin(resource)
                del resource
            if via_gc_callback:
                ui._drain_retired_native_after_gc("stop", {})
            else:
                ui._drain_retired_native()
        except BaseException as error:
            errors.append((type(error).__name__, str(error)))
        finally:
            progress.set()

    # Disable automatic collections only for this deterministic fixture. The
    # callback path above is still exercised explicitly on the worker.
    enabled = gc.isenabled()
    gc.disable()
    worker = threading.Thread(target=foreign_drain, name="foreign-retired-collector")
    try:
        worker.start()
        assert progress.wait(5), "Worker did not reach the snapshot or finish"
        ui._drain_retired_native()
    finally:
        release_snapshot.set()
        worker.join(5)
        if enabled:
            gc.enable()
    assert not worker.is_alive(), "Owned worker did not finish"
    assert not errors, errors
    assert reference() is None
    assert [(name, owner.name) for name, owner in finalizers if name == "creator"] == [
        ("creator", creator.name)
    ]
    if worker_owns_resource:
        assert [(name, owner.name) for name, owner in finalizers if name == "worker"] == [
            ("worker", worker.name)
        ]


@pytest.mark.parametrize("pool_kind", ["assets", "interpreters"])
def test_drain_preserves_external_reference_until_creator_releases_it(monkeypatch, pool_kind):
    creator = threading.current_thread()
    finalized = []

    class Probe(ui.tk.Variable):
        def __init__(self):
            pass

        def __del__(self):
            finalized.append(threading.current_thread())

    monkeypatch.setattr(ui, "_RETIRED_NATIVE_ASSETS", {})
    monkeypatch.setattr(ui, "_RETIRED_INTERPRETERS", {})
    resource = Probe()
    reference = weakref.ref(resource)
    if pool_kind == "assets":
        ui._pin_retired_assets((resource,), creator)
        ui._pin_retired_assets((resource,), creator)
    else:
        root = ui.tk.Tk.__new__(ui.tk.Tk)
        root.tk = resource
        ui._pin_retired_interpreter(root)
        ui._pin_retired_interpreter(root)
        root.tk = None
    ui._drain_retired_native_after_gc("start", {})
    ui._drain_retired_native()
    assert reference() is resource and not finalized
    del resource
    ui._drain_retired_native()
    assert reference() is None and finalized == [creator]
    ui._drain_retired_native()  # Repeated/empty drain must remain harmless.


@pytest.mark.parametrize("via_gc_callback", [False, True])
def test_unregistered_thread_drain_does_not_construct_dummy_thread(monkeypatch, via_gc_callback):
    """GC on an unrelated native thread must not create threading wrappers."""
    monkeypatch.setattr(ui, "_RETIRED_NATIVE_ASSETS", {})
    monkeypatch.setattr(ui, "_RETIRED_INTERPRETERS", {})

    class Probe(ui.tk.Variable):
        def __init__(self):
            pass

        def __del__(self):
            pass  # This probe allocates no Tcl resource.

    resource = Probe()
    ui._pin_retired_assets((resource,), threading.current_thread())
    del resource
    ui._drain_retired_native()  # Leave a legitimate empty creator bucket.
    done = threading.Event()
    errors = []
    attempted = []
    original = threading.Thread.__init__

    def initialize(thread, *args, **kwargs):
        if "target" not in kwargs:
            attempted.append("dummy thread constructor")
            raise KeyError("target")
        return original(thread, *args, **kwargs)

    def collect():
        try:
            if via_gc_callback:
                ui._drain_retired_native_after_gc("stop", {})
            else:
                ui._drain_retired_native()
        except BaseException as error:
            errors.append((type(error).__name__, str(error)))
        finally:
            done.set()

    enabled = gc.isenabled()
    gc.disable()
    try:
        monkeypatch.setattr(threading.Thread, "__init__", initialize)
        _thread.start_new_thread(collect, ())
        assert done.wait(5), "Owned raw-thread fixture did not finish"
    finally:
        monkeypatch.setattr(threading.Thread, "__init__", original)
        if enabled:
            gc.enable()
    assert not errors and not attempted, (errors, attempted)


def _native_child():
    from test_tk_native_constructor_pass20 import _admit, _guard

    provenance = _admit()
    owner = threading.current_thread()
    progress = threading.Event()
    release_snapshot = threading.Event()
    finalizers = []
    unraisables = []
    errors = []
    enabled = gc.isenabled()
    gc.disable()

    class SnapshotGate(dict):
        def items(self):
            snapshot = list(super().items())
            if threading.current_thread() is not owner:
                progress.set()
                if not release_snapshot.wait(5):
                    raise AssertionError("Native snapshot was not released")
            return snapshot

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        patch.setattr(ui, "_RETIRED_NATIVE_ASSETS", SnapshotGate())
        patch.setattr(ui, "_RETIRED_INTERPRETERS", SnapshotGate())
        patch.setattr(sys, "unraisablehook", lambda event: unraisables.append(
            (event.exc_type.__name__, str(event.exc_value))))

        def observe(cls):
            original = cls.__del__

            def finalize(resource):
                row = {"identity": id(resource), "thread": threading.get_ident(), "returned": False}
                finalizers.append(row)
                original(resource)
                row["returned"] = True

            patch.setattr(cls, "__del__", finalize)

        for cls in (ui.tkfont.Font, ui.tk.Variable, ui.tk.PhotoImage):
            observe(cls)
        root = ui.tk.Tk()
        root.withdraw()
        assets = [ui.tkfont.Font(root=root), ui.tk.StringVar(master=root),
                  ui.tk.PhotoImage(master=root, width=1, height=1)]
        identities = {id(asset) for asset in assets}
        references = [weakref.ref(asset) for asset in assets]
        ui._pin_retired_assets(assets, owner)
        ui._pin_retired_interpreter(root, owner)
        root.destroy()
        root = None
        assets.clear()

        def collect():
            try:
                gc.collect()  # Invoke the actual registered callback on the worker.
            except BaseException as error:
                errors.append((type(error).__name__, str(error)))
            finally:
                progress.set()

        worker = threading.Thread(target=collect, name="native-foreign-collector", daemon=True)
        try:
            worker.start()
            assert progress.wait(5)
            ui._drain_retired_native()
        finally:
            release_snapshot.set()
            worker.join(5)
        assert not worker.is_alive()
        assert not errors and not effects and not unraisables
        assert all(reference() is None for reference in references)
        assert {row["identity"] for row in finalizers} == identities
        assert all(row["thread"] == threading.get_ident() and row["returned"] for row in finalizers)
        # Empty per-thread metadata buckets deliberately remain; native records do not.
        assert not any(ui._RETIRED_NATIVE_ASSETS.values())
        assert not any(ui._RETIRED_INTERPRETERS.values())
        print(json.dumps({"event": "child-complete", "provenance": provenance,
                          "finalizers": finalizers, "unraisables": unraisables}), flush=True)
    if enabled:
        gc.enable()


def test_native_finalizers_stay_on_creator_during_foreign_gc(request):
    from test_tk_native_constructor_pass20 import _admit

    provenance = _admit()
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--native-child"],
                            env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                            capture_output=True, text=True, timeout=8, check=False)
    evidence = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                    timed_out=False, provenance=provenance)
    request.node.user_properties.append(("owned_native_pool_child", json.dumps(evidence)))
    assert result.returncode == 0, evidence
    assert not result.stderr, evidence
    complete = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(complete) == 1 and complete[0]["event"] == "child-complete"
    assert complete[0]["provenance"] == provenance
    assert provenance["sha256"] == hashlib.sha256(Path(ui.__file__).read_bytes()).hexdigest()


if __name__ == "__main__":
    assert sys.argv[1:] == ["--native-child"]
    _native_child()
