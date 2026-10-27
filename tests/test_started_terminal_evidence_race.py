# SPDX-License-Identifier: GPL-3.0-or-later
"""STARTED evidence must never supersede a terminal observation.

Use the existing fake-runner start helper and synchronous reentrant callbacks:
no real runner, threads, sleeps, device writes, or UI are needed.
"""

import copy
import errno
from pathlib import Path

import pytest

from beamo_wipe import evidence
from beamo_wipe.models import Screen
from beamo_wipe.wizard import Wizard
from test_evidence_retry import start


def _fail_on_next_tick(wizard):
    wizard.runner.fail = True
    wizard.runner._clock.add(1)
    wizard.tick()


def _terminal_snapshot(wizard):
    return {
        "screen": wizard.screen,
        "result": wizard.wipe_result,
        "path": wizard.evidence_path,
        "evidence": copy.deepcopy(wizard.evidence),
        "pending": copy.deepcopy(wizard._pending_evidence),
        "error_code": wizard.evidence_error_code,
    }


def _assert_saved_failure(wizard, terminal):
    assert terminal["screen"] == Screen.DONE
    assert terminal["result"] is not None
    assert not terminal["result"].ok
    assert wizard.screen == Screen.DONE
    assert wizard.wipe_result == terminal["result"]
    assert wizard.evidence_path == terminal["path"]
    assert wizard.evidence == terminal["evidence"]
    assert wizard.evidence_status == "saved"
    assert wizard.evidence_error is None
    assert wizard.evidence["outcome"] == evidence.OUTCOME_FAILED
    assert wizard.evidence["exit_evidence"]["exit_code"] == wizard.wipe_result.exit_code
    assert evidence.verify_evidence_checksum(Path(wizard.evidence_path))
    assert wizard.can_save_report
    assert wizard.report_view.can_save
    assert not wizard.result_view.success


@pytest.mark.parametrize("terminal_save_fails", [False, True])
def test_delayed_started_write_preserves_terminal_save_or_retry(
    tmp_path, monkeypatch, terminal_save_fails
):
    """Finish inside arming, before _perform_start writes initial evidence."""
    original_arm = Wizard._arm_running_wipe
    original_writer = evidence.write_evidence_atomic
    terminal = {}

    def arm_then_finish(wizard, request):
        original_arm(wizard, request)
        _fail_on_next_tick(wizard)
        terminal.update(_terminal_snapshot(wizard))

    def writer(record, **kwargs):
        if terminal_save_fails and record["outcome"] == evidence.OUTCOME_FAILED:
            raise OSError(errno.ENOSPC, "injected terminal evidence failure")
        return original_writer(record, **kwargs)

    monkeypatch.setattr(Wizard, "_arm_running_wipe", arm_then_finish)
    monkeypatch.setattr(evidence, "write_evidence_atomic", writer)
    wizard, _clock = start(tmp_path, monkeypatch)

    assert terminal["screen"] == Screen.DONE
    assert terminal["result"] is not None and not terminal["result"].ok
    assert wizard.screen == Screen.DONE
    assert wizard.wipe_result == terminal["result"]
    if not terminal_save_fails:
        _assert_saved_failure(wizard, terminal)
        return

    assert terminal["error_code"] == "storage_full"
    assert wizard.evidence_error_code == "storage_full"
    assert wizard.evidence_status == "failed"
    assert wizard.evidence_path == terminal["path"]
    assert wizard.evidence == terminal["evidence"]
    assert wizard._pending_evidence == terminal["pending"]
    assert wizard._pending_evidence[2] == wizard.wipe_result
    assert wizard.can_retry_evidence
    assert not wizard.can_save_report
    assert not wizard.result_view.success

    monkeypatch.setattr(evidence, "write_evidence_atomic", original_writer)

    def forbidden_runner_call(*_args, **_kwargs):
        pytest.fail("saving terminal evidence must not call the wipe runner")

    for name in ("start", "poll", "cancel"):
        monkeypatch.setattr(wizard.runner, name, forbidden_runner_call)
    assert wizard.retry_evidence_save()
    assert wizard.wipe_result == terminal["result"]
    assert wizard.evidence["outcome"] == evidence.OUTCOME_FAILED
    assert wizard.evidence["exit_evidence"]["exit_code"] == terminal["result"].exit_code
    assert wizard.evidence_error is None
    assert wizard.evidence_status == "saved"
    assert wizard.can_save_report
    assert evidence.verify_evidence_checksum(Path(wizard.evidence_path))
    assert not wizard.retry_evidence_save()


def test_started_evidence_is_saved_while_fake_runner_is_working(tmp_path, monkeypatch):
    wizard, clock = start(tmp_path, monkeypatch)

    assert wizard.screen == Screen.WORKING
    assert wizard.wipe_result is None
    assert wizard.evidence["outcome"] == evidence.OUTCOME_STARTED
    assert wizard.evidence_status == "saved"
    assert wizard.evidence_error is None
    assert evidence.verify_evidence_checksum(Path(wizard.evidence_path))
    assert not wizard.can_save_report
    assert not wizard.can_retry_evidence

    wizard.runner.fail = True
    clock.add(1)
    wizard.tick()
    _assert_saved_failure(wizard, _terminal_snapshot(wizard))


@pytest.mark.parametrize("stale_write_fails", [False, True])
def test_in_flight_started_write_cannot_publish_over_terminal_evidence(
    tmp_path, monkeypatch, stale_write_fails
):
    """The older save returns (or fails) after a newer terminal save finishes."""
    original_arm = Wizard._arm_running_wipe
    original_writer = evidence.write_evidence_atomic
    active = {}
    terminal = {}

    def remember_running_wizard(wizard, request):
        original_arm(wizard, request)
        active["wizard"] = wizard

    def writer(record, **kwargs):
        if record["outcome"] != evidence.OUTCOME_STARTED:
            return original_writer(record, **kwargs)
        # The initial persistence call is already in flight. Let tick finish
        # the fake engine before that older call can publish its observation.
        wizard = active["wizard"]
        _fail_on_next_tick(wizard)
        terminal.update(_terminal_snapshot(wizard))
        if stale_write_fails:
            raise OSError(errno.EIO, "injected obsolete STARTED write failure")
        return original_writer(record, **kwargs)

    monkeypatch.setattr(Wizard, "_arm_running_wipe", remember_running_wizard)
    monkeypatch.setattr(evidence, "write_evidence_atomic", writer)
    wizard, _clock = start(tmp_path, monkeypatch)

    _assert_saved_failure(wizard, terminal)
    assert not wizard.can_retry_evidence
