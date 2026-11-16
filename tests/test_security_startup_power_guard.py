"""Live startup failure must still prove external-engine absence before poweroff."""

import threading

import pytest

from beamo_wipe import app, nwipe_runner
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.nwipe_runner import DryRunRunner, NwipeRunner
from beamo_wipe.wizard import Wizard


def idle_wizard(runner):
    wizard = Wizard.__new__(Wizard)
    wizard.runner = runner
    wizard.dry_run = False
    wizard.preview = False
    wizard._lock = threading.Lock()
    wizard.wants_shutdown = True
    wizard.wants_new_session = False
    wizard._runner_is_active = lambda: False
    wizard._recovery_busy = lambda: False
    wizard._session_store = None
    wizard._finishing = False
    wizard._evidence_saving = False
    wizard._report_exporting = False
    wizard._diagnostic_busy = False
    return wizard


@pytest.mark.parametrize("runner_type", [DryRunRunner, NwipeRunner])
@pytest.mark.parametrize("engine_state", [False, True, None, "error"])
def test_live_power_request_checks_external_engine(monkeypatch, runner_type, engine_state):
    wizard = idle_wizard(runner_type())
    probes = []
    power = []

    def probe():
        probes.append(True)
        if engine_state == "error":
            raise OSError("fake process inspection failure")
        return engine_state

    monkeypatch.setattr(nwipe_runner, "pinned_nwipe_already_running", probe)
    monkeypatch.setattr(app, "_shutdown", lambda: power.append(True) or True)
    assert app._shutdown_if_still_safe(wizard) is (engine_state is False)
    assert probes == [True]
    assert power == ([True] if engine_state is False else [])


@pytest.mark.parametrize("flag", ["dry_run", "preview"])
def test_inert_modes_do_not_probe_live_processes(monkeypatch, flag):
    wizard = idle_wizard(DryRunRunner())
    setattr(wizard, flag, True)

    def forbidden():
        raise AssertionError("inert mode queried native process state")

    monkeypatch.setattr(nwipe_runner, "pinned_nwipe_already_running", forbidden)
    assert wizard._live_pinned_engine_busy() is False


def test_startup_fallback_remains_live_for_power_safety(monkeypatch):
    captured = []
    wizard = idle_wizard(DryRunRunner())

    def construct(discovery, runner, *, dry_run):
        assert isinstance(discovery, DiscoveryResult)
        assert isinstance(runner, DryRunRunner)
        captured.append(dry_run)
        wizard.runner = runner
        wizard.dry_run = dry_run
        return wizard

    monkeypatch.setattr(app, "Wizard", construct)
    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)
    monkeypatch.setattr(nwipe_runner, "pinned_nwipe_already_running", lambda: True)
    monkeypatch.setattr(
        app, "_shutdown", lambda: pytest.fail("startup failure requested real power")
    )
    assert app._blocked_wizard(OSError("fake startup failure")) is wizard
    assert captured == [False]
    assert app._shutdown_if_still_safe(wizard) is False
