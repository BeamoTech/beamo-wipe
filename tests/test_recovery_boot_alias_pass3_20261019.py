# SPDX-License-Identifier: GPL-3.0-or-later
"""Recovery must preserve protected aliases without blocking an unrelated target."""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from beamo_wipe.models import MethodId, Screen, WipeRequest
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import assert_boot_excluded
from beamo_wipe.wizard import Wizard
from test_discovery_observation_fallback_pass16 import (
    _boot,
    _disk,
    fake_machine,  # noqa: F401 - guarded fake-machine pytest fixture
)
from test_session_recovery import (
    finish,
    recover,
    session,  # noqa: F401 - ordinary-file recovery-store pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
PROTECTION = ("wwn", "serial", "system-mount")


def _discovery(scan, route, protection):
    boot = _boot()
    protected = _disk("sdc", tran="usb")
    if protection == "wwn":
        protected["wwn"] = boot["wwn"]
    elif protection == "serial":
        boot["wwn"] = protected["wwn"] = ""
        protected["serial"] = boot["serial"]
    elif protection == "system-mount":
        protected["mountpoints"] = ["/home/owner"]
    else:
        assert protection == "distinct-wwn"
        protected["serial"] = boot["serial"]
    return scan({"blockdevices": [boot, _disk("sda"), protected]}, route)


def _request(discovery, store, method=MethodId.QUICK_ZERO):
    return WipeRequest(
        "/dev/sda", method, discovery.boot.path,
        str(store.directory / "nwipe-fake.log"),
    )


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("protection", PROTECTION)
@pytest.mark.parametrize("method", list(MethodId))
def test_protected_peers_survive_arm_reopen_terminal_and_ui_recovery(
    fake_machine, session, monkeypatch, route, protection, method,  # noqa: F811
):
    discovery = _discovery(fake_machine, route, protection)
    assert_boot_excluded(discovery)
    assert [d.path for d in discovery.selectable] == ["/dev/sda"]
    assert {d.path for d in discovery.disks if d.is_boot} == {"/dev/sdz", "/dev/sdc"}
    first = session()
    request = _request(discovery, first, method)
    first.arm(discovery, request)
    assert first.record["phase"] == "armed"
    path = finish(first, discovery, request)
    first.close()

    reopened = session()
    assert not reopened.invalid and reopened.record["phase"] == "terminal"
    _, recovered_discovery, target = reopened.context()
    assert target.path == "/dev/sda" and not target.is_boot
    assert {d.path for d in recovered_discovery.disks if d.is_boot} == {"/dev/sdz", "/dev/sdc"}
    spawn = Mock(side_effect=AssertionError("Recovery must not spawn a process"))
    start = Mock(side_effect=AssertionError("Recovery must not start an erase"))
    monkeypatch.setattr("beamo_wipe.nwipe_runner.subprocess.Popen", spawn)
    monkeypatch.setattr("beamo_wipe.nwipe_runner.DryRunRunner.start", start)
    wizard = recover(reopened)
    assert wizard.screen == Screen.DONE and wizard.done_ok and wizard.can_save_report
    assert wizard.evidence_path == str(path)
    assert wizard._wipe_request is None and not wizard.owner_ok and not wizard.confirm_input
    spawn.assert_not_called()
    start.assert_not_called()


@pytest.mark.parametrize("route", ROUTES)
def test_distinct_wwns_still_disambiguate_reused_boot_serial(
    fake_machine, session, route,  # noqa: F811
):
    discovery = _discovery(fake_machine, route, "distinct-wwn")
    assert_boot_excluded(discovery)
    assert {d.path for d in discovery.disks if d.is_boot} == {"/dev/sdz"}
    store = session()
    store.arm(discovery, _request(discovery, store))
    assert store.record["phase"] == "armed"


@pytest.mark.parametrize("protection", PROTECTION)
def test_armed_restart_preserves_protection_without_resuming(
    fake_machine, session, monkeypatch, protection,  # noqa: F811
):
    discovery = _discovery(fake_machine, "direct", protection)
    first = session()
    first.arm(discovery, _request(discovery, first))
    first.close()
    reopened = session()
    assert not reopened.invalid and reopened.record["phase"] == "armed"
    _, historical, target = reopened.context()
    assert target.path == "/dev/sda" and not target.is_boot
    assert {d.path for d in historical.disks if d.is_boot} == {"/dev/sdz", "/dev/sdc"}
    start = Mock(side_effect=AssertionError("Recovery must not resume an erase"))
    monkeypatch.setattr("beamo_wipe.nwipe_runner.DryRunRunner.start", start)
    wizard = recover(reopened)
    assert wizard.screen == Screen.DONE and not wizard.done_ok
    assert wizard.result_view.code == "indeterminate"
    assert not wizard.owner_ok and wizard._wipe_request is None
    start.assert_not_called()


@pytest.mark.parametrize("protection", PROTECTION)
def test_fake_kiosk_confirmation_can_arm_only_unrelated_target(
    fake_machine, session, monkeypatch, protection,  # noqa: F811
):
    discovery = _discovery(fake_machine, "production-metadata-stub", protection)
    store = session()
    # Native identity acquisition is fake; the ordinary controller/journal and
    # confirmation flow run unchanged, with no engine or physical device.
    monkeypatch.setattr("beamo_wipe.safety.assert_not_boot", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.nwipe_runner.assert_not_boot", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.safety.assert_existing_is_block_device", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.safety.block_rdev", lambda path: 8 if path == "/dev/sda" else 16)
    runner = DryRunRunner()
    wizard = Wizard(discovery, runner, dry_run=False, rediscover=lambda: discovery)
    wizard.enable_session_recovery(store)
    wizard.skip_intro()
    wizard.accept_what()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk("/dev/sda")
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.set_method(MethodId.QUICK_ZERO)
    wizard.continue_method()
    assert wizard.screen == Screen.LAST_CHANCE
    wizard._erase_until = 0
    wizard.confirm_erase()
    assert wizard.screen == Screen.WORKING and runner._started is not None
    assert store.record["phase"] == "armed"
    assert store.record["context"]["target"] == "/dev/sda"
    assert {d["path"] for d in store.record["context"]["disks"] if d["is_boot"]} == {"/dev/sdz", "/dev/sdc"}


@pytest.mark.parametrize("protection", PROTECTION)
@pytest.mark.parametrize("corruption", ("target-protected", "boot-unprotected", "duplicate", "missing-boot"))
def test_protected_peer_support_preserves_context_refusals(
    fake_machine, session, protection, corruption,  # noqa: F811
):
    discovery = _discovery(fake_machine, "direct", protection)
    store = session()
    request = _request(discovery, store)
    if corruption == "target-protected":
        request = replace(request, device="/dev/sdc")
    elif corruption == "boot-unprotected":
        discovery = replace(discovery, disks=tuple(
            replace(disk, is_boot=False) if disk.path == request.boot_device else disk
            for disk in discovery.disks
        ))
    elif corruption == "duplicate":
        discovery = replace(discovery, disks=(*discovery.disks, discovery.selectable[0]))
    else:
        request = replace(request, boot_device="/dev/sdy")
    with pytest.raises(ValueError, match="Contradictory disk identities"):
        store.arm(discovery, request)
    assert store.record["phase"] == "preflight"
