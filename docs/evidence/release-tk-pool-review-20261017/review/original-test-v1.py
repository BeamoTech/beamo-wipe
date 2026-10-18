"""Retired Tk records must never be retained by a foreign collector thread."""

import gc
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

    monkeypatch.setattr(ui, "_RETIRED_NATIVE_ASSETS", SnapshotGate())
    monkeypatch.setattr(ui, "_RETIRED_INTERPRETERS", SnapshotGate())

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
