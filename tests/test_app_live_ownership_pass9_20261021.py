"""A recovered live classification cannot bypass interface ownership."""

import builtins
import io
import json
import os
import sys
from types import ModuleType, SimpleNamespace

import pytest

from beamo_wipe import app, discover, report_intent, safety, session_recovery
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult
from beamo_wipe.nwipe_runner import NwipeRunner
from beamo_wipe.wizard import Wizard


ROUTES = ("console", "plain-console", "graphical", "accessible")


@pytest.fixture
def machine(monkeypatch):
    calls, observations, effects = [], [], []
    reads = {"cmdline": 0, "mountinfo": 0}
    mode = {"location": None, "failures": 0, "live": True}
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_DEMO", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_UI", raising=False)
    monkeypatch.setattr(safety.sys, "platform", "linux")
    # Restore the actual classifier over the suite's ordinary desktop stub.
    monkeypatch.setattr(app, "running_on_live_usb", safety.running_on_live_usb)
    original_open = builtins.open

    def proc_file(path, *args, **kwargs):
        location = {
            "/proc/cmdline": "cmdline",
            discover.MOUNTINFO_PATH: "mountinfo",
        }.get(str(path))
        if location is not None:
            reads[location] += 1
            if mode["location"] == location and reads[location] <= mode["failures"]:
                calls.append(location + "-OSError")
                raise OSError("Injected transient proc-file read failure")
            if location == "cmdline":
                return io.StringIO("boot=live quiet" if mode["live"] else "quiet")
            return io.StringIO(
                "1 0 0:1 / / rw - overlay overlay rw\n"
                "2 1 8:241 / /run/live/medium rw - iso9660 /dev/sdz1 rw\n"
            )
        if str(path).startswith(("/dev/", "/proc/", "/sys/")):
            effects.append(str(path))
            raise AssertionError("Native path forbidden")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", proc_file)
    original_realpath = os.path.realpath
    monkeypatch.setattr(
        os.path,
        "realpath",
        lambda path, *args, **kwargs: str(path)
        if str(path).startswith("/dev/")
        else original_realpath(path, *args, **kwargs),
    )

    def forbidden(*_args, **_kwargs):
        effects.append("native callback")
        raise AssertionError("Native inventory, process, engine or power action forbidden")

    for boundary in (
        "subprocess.run",
        "subprocess.Popen",
        "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover._run_findmnt",
        "beamo_wipe.discover.read_mount_sources",
    ):
        monkeypatch.setattr(boundary, forbidden)
    monkeypatch.setattr(NwipeRunner, "start", forbidden)
    monkeypatch.setattr(app, "_shutdown", forbidden)
    monkeypatch.setattr(app.signal, "signal", lambda *_args: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None)
    boot = Disk(
        "/dev/sdz", "sdz", "Fake boot", "BOOT", 16_000_000_000, "16",
        DiskKind.SSD, "USB", "", is_boot=True,
        mountpoints=("/run/live/medium",),
    )
    target = Disk(
        "/dev/sda", "sda", "Fake target", "TARGET", 128_000_000_000, "128",
        DiskKind.SSD, "SATA", "",
    )
    inventory = DiscoveryResult(
        disks=(boot, target), selectable=(target,), boot=boot, boot_identified=True,
    )

    def fake_discover(**_kwargs):
        calls.append("fake-discovery")
        return inventory

    monkeypatch.setattr(app, "discover", fake_discover)
    # Exercise the real builder and controller without toolkit/worker timing.
    monkeypatch.setattr(app, "_build_wizard_with_console_stages", app._build_wizard)
    monkeypatch.setattr(
        app, "_build_wizard_with_tk_stages",
        lambda args, _fullscreen: app._build_wizard(args),
    )
    monkeypatch.setattr(
        app, "_build_wizard_with_accessible_stages",
        lambda args, _fullscreen: app._build_wizard(args),
    )

    class Store:
        previous = False
        invalid = False

        def __init__(self):
            calls.append("store-created")

        def open(self):
            calls.append("store-open")

        def close(self):
            calls.append("store-close")

    monkeypatch.setattr(session_recovery, "SessionStore", Store)
    monkeypatch.setattr(report_intent, "ReportIntentStore", lambda: object())
    monkeypatch.setattr(
        Wizard, "enable_report_intent_recovery",
        lambda _wizard, _store: calls.append("report-intent"),
    )

    def ui(wizard, **_kwargs):
        observations.append({
            "dry_run": wizard.dry_run,
            "runner": type(wizard.runner).__name__,
            "has_session_store": wizard._session_store is not None,
        })
        return 23

    monkeypatch.setattr("beamo_wipe.ui.console_wizard.run_console", ui)
    monkeypatch.setattr("beamo_wipe.ui.console_wizard._plain_loop", ui)
    tk = ModuleType("beamo_wipe.ui.tk_wizard")
    tk.run_tk = ui
    accessible = ModuleType("beamo_wipe.ui.accessible_wizard")
    accessible.run_accessible = ui
    accessible.start_live_reader = lambda: calls.append("reader-start") or object()
    accessible.stop_live_reader = lambda _reader: calls.append("reader-stop")
    monkeypatch.setitem(sys.modules, tk.__name__, tk)
    monkeypatch.setitem(sys.modules, accessible.__name__, accessible)
    fixture = SimpleNamespace(
        mode=mode, calls=calls, observations=observations, reads=reads, effects=effects,
    )
    yield fixture
    assert effects == []


def argv_for(route, preview):
    flags = [] if route == "graphical" else ["--" + route]
    return [*flags, preview]


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("preview", ["--demo", "--dry-run"])
@pytest.mark.parametrize("failures", [1, 2, 3])
@pytest.mark.parametrize("location", ["cmdline", "mountinfo"])
def test_transient_classification_never_exposes_unowned_live_controls(
    machine, request, route, preview, failures, location,
):
    machine.mode.update(location=location, failures=failures)
    code = app.main(argv_for(route, preview))
    request.node.user_properties.append(("ownership_trace", json.dumps({
        "location": location, "failures": failures, "route": route,
        "preview": preview, "code": code, "calls": machine.calls,
        "reads": machine.reads, "ui": machine.observations,
        "native_callbacks": len(machine.effects),
    })))
    assert code == 3
    assert machine.observations == []
    if failures == 1:
        assert "fake-discovery" not in machine.calls
    assert "store-created" not in machine.calls


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("preview", ["--demo", "--dry-run"])
def test_stable_live_metadata_preserves_owned_real_wizard(machine, route, preview):
    assert app.main(argv_for(route, preview)) == 23
    assert machine.observations == [{
        "dry_run": False, "runner": "NwipeRunner", "has_session_store": True,
    }]
    assert machine.calls.index("store-open") < machine.calls.index("fake-discovery")
    assert "store-close" in machine.calls


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("preview", ["--demo", "--dry-run"])
def test_desktop_preview_preserves_unowned_fake_wizard(machine, route, preview):
    machine.mode["live"] = False
    assert app.main(argv_for(route, preview)) == 23
    assert machine.observations == [{
        "dry_run": True, "runner": "DryRunRunner", "has_session_store": False,
    }]
    assert "store-created" not in machine.calls
