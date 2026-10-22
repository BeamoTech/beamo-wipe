"""Optional diagnostics cannot strand a failed inventory refresh claim."""

import json

import pytest

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import DiscoveryResult, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard


@pytest.fixture
def fake_refresh(monkeypatch, tmp_path):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native inventory, engine or power action forbidden")

    for boundary in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(boundary, forbidden)

    def failed_scan():
        raise OSError("Fake scan failure")

    wizard = Wizard(discovery_for_scenario("happy"), DryRunRunner(),
                    rediscover=failed_scan, dry_run=True)
    wizard.skip_intro()
    yield wizard
    assert not effects
    assert not wizard.runner.started


def _diagnostics(monkeypatch, error_kind):
    calls = []

    def log_diag(*args):
        calls.append(args[:2])
        if error_kind is not None:
            raise error_kind("Fake optional logging failure")

    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", log_diag)
    return calls


def _blocked_then_fresh_retry(wizard):
    assert wizard.screen is Screen.PICK_BLOCKED
    assert wizard.discovery.error_code == "refresh_failed"
    assert wizard.selectable == ()
    assert wizard.can_refresh
    wizard._rediscover = lambda: discovery_for_scenario("happy")
    assert wizard.refresh_disks()
    assert wizard.screen is Screen.OWNER
    assert not wizard.owner_ok
    assert wizard.selected is None
    assert wizard.confirm_input == ""
    assert not wizard.erase_enabled


@pytest.mark.parametrize("entry", ["sync", "confirmed", "completion"])
@pytest.mark.parametrize("diagnostic_error", [None, OSError, KeyboardInterrupt, SystemExit])
def test_failed_refresh_retires_despite_optional_logging(
    fake_refresh, monkeypatch, request, entry, diagnostic_error,
):
    wizard = fake_refresh
    calls = _diagnostics(monkeypatch, diagnostic_error)
    escaped = None
    try:
        if entry == "confirmed":
            assert wizard.open_refresh_confirm()
            assert wizard.confirm_refresh()
        elif entry == "completion":
            sequence = wizard.begin_refresh()
            assert sequence is not None
            assert wizard.finish_refresh(sequence, OSError("Fake scan failure"))
        else:
            assert wizard.refresh_disks()
    except BaseException as error:
        escaped = type(error).__name__
    request.node.user_properties.append(("refresh_trace", json.dumps({
        "entry": entry,
        "diagnostic_error": diagnostic_error.__name__ if diagnostic_error else None,
        "escaped": escaped,
        "screen": wizard.screen.name,
        "can_refresh": wizard.can_refresh,
        "diagnostic_calls": calls,
    })))
    assert wizard.screen is Screen.PICK_BLOCKED
    assert escaped is None
    assert calls == [("discover", "refresh_failed")]
    _blocked_then_fresh_retry(wizard)


@pytest.mark.parametrize("diagnostic_error", [KeyboardInterrupt, SystemExit])
def test_stale_refresh_failure_cannot_log_or_replace_a_new_claim(
    fake_refresh, monkeypatch, diagnostic_error,
):
    wizard = fake_refresh
    calls = _diagnostics(monkeypatch, diagnostic_error)
    first = wizard.begin_refresh()
    assert wizard.finish_refresh(first, discovery_for_scenario("happy"))
    second = wizard.begin_refresh()
    assert second != first
    assert not wizard.finish_refresh(first, OSError("Stale failed scan"))
    assert wizard.screen is Screen.REFRESHING
    assert wizard.finish_refresh(second, discovery_for_scenario("happy"))
    assert not wizard.finish_refresh(second, OSError("Duplicate failed scan"))
    assert wizard.screen is Screen.OWNER
    assert calls == []


@pytest.mark.parametrize("outcome", ["invalid-type", "unidentified-boot"])
@pytest.mark.parametrize("diagnostic_error", [None, KeyboardInterrupt])
def test_malformed_refresh_retires_and_preserves_fresh_retry(
    fake_refresh, monkeypatch, outcome, diagnostic_error,
):
    wizard = fake_refresh
    _diagnostics(monkeypatch, diagnostic_error)
    sequence = wizard.begin_refresh()
    inventory = object() if outcome == "invalid-type" else DiscoveryResult(boot_identified=False)
    escaped = None
    try:
        wizard.finish_refresh(sequence, inventory)
    except BaseException as error:
        escaped = type(error).__name__
    assert wizard.screen is Screen.PICK_BLOCKED
    assert escaped is None
    _blocked_then_fresh_retry(wizard)
