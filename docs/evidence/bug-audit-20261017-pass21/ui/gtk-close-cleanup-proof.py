"""Prepared fake-only GTK close-boundary proof; no application or GUI runs."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types

import pytest


def _module(patch):
    source = Path(os.environ["BEAMO_GTK_PROBE_SOURCE"]).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == os.environ["BEAMO_GTK_PROBE_SHA256"]
    gi = types.ModuleType("gi")
    gi.require_version = lambda *_args: None
    repository = types.ModuleType("gi.repository")
    for name in ("Atk", "Gdk", "GLib", "Gtk", "Pango"):
        setattr(repository, name, types.SimpleNamespace())
    patch.setitem(sys.modules, "gi", gi)
    patch.setitem(sys.modules, "gi.repository", repository)
    spec = importlib.util.spec_from_file_location("beamo_wipe.ui.pass21_close_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == source
    return module, dict(source=str(source), sha256=digest)


@pytest.mark.parametrize("fault", ("normal-control", "audio-runtimeerror", "audio-interruption"))
def test_gtk_close_completes_independent_cleanup_after_audio_failure(monkeypatch, request, fault):
    module, provenance = _module(monkeypatch)
    calls = []
    caught = []
    original = (KeyboardInterrupt("controlled audio cancellation interruption")
                if fault == "audio-interruption" else RuntimeError("controlled audio cancellation failure"))
    effects = []

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

    def cancel_audio():
        calls.append("cancel-audio")
        if fault != "normal-control":
            raise original

    module.GLib.source_remove = lambda source: calls.append(("remove-timer", source))
    module.Gtk.main_level = lambda: 1
    module.Gtk.main_quit = lambda: calls.append("quit-loop")
    app = module.AccessibleWizard.__new__(module.AccessibleWizard)
    app.w = types.SimpleNamespace(cancel_audio=cancel_audio)
    app.closed = False
    app.timer = 19
    app._sound_dialog = types.SimpleNamespace(close=lambda: calls.append("close-dialog"))
    app.window = types.SimpleNamespace(destroy=lambda: calls.append("destroy-window"))
    try:
        app.close()
    except BaseException as error:
        caught.append(error)
    app.close()  # Existing idempotency must not permanently prevent unfinished cleanup.
    record = dict(fault=fault, provenance=provenance, calls=calls, closed=app.closed,
                  timer=app.timer, error_ids=[id(error) for error in caught],
                  original_error_id=id(original), effects=effects)
    request.node.user_properties.append(("gtk_cleanup_trace", json.dumps(record)))
    assert not effects
    assert calls == ["cancel-audio", "close-dialog", ("remove-timer", 19), "destroy-window", "quit-loop"], record
    assert app.closed and app.timer == 0, record
    assert caught == ([] if fault == "normal-control" else [original]), record
