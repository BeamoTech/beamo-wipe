"""Cancellation outcome must retain the observed fake child's exit evidence."""

import json
from pathlib import Path

import pytest

from beamo_wipe.models import Screen, WipeResult
from test_wizard_flow import _wiz


@pytest.mark.parametrize("exit_code", [-9, -15, 0, 1, 143])
@pytest.mark.parametrize("origin", ["user", "terminal"])
def test_cancel_preserves_observed_exit_and_persisted_signal(
    monkeypatch, tmp_path, exit_code, origin
):
    monkeypatch.setattr("beamo_wipe.safety.DEFAULT_LOG_DIR", tmp_path)
    wizard, clock = _wiz()
    wizard.skip_intro()
    wizard.accept_what()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.continue_method()
    clock.add(5)
    wizard.confirm_erase()
    assert wizard.screen == Screen.WORKING
    request = wizard._wipe_request
    assert request is not None

    def cancel():
        wizard.runner.result = WipeResult(
            False, exit_code, "cancelled", request.logfile
        )

    monkeypatch.setattr(wizard.runner, "poll", lambda _request: None)
    monkeypatch.setattr(wizard.runner, "cancel", cancel)
    wizard.cancel_wipe(origin=origin)

    assert wizard.screen == Screen.DONE
    assert wizard.wipe_result is not None
    assert not wizard.wipe_result.ok
    assert wizard.wipe_result.summary == "interrupted"
    assert wizard.wipe_result.exit_code == exit_code
    assert wizard.evidence_path
    evidence = json.loads(Path(wizard.evidence_path).read_text(encoding="utf-8"))
    assert evidence["exit_evidence"]["exit_code"] == exit_code
    assert evidence["exit_evidence"]["signal"] == (
        -exit_code if exit_code < 0 else None
    )
    assert evidence["outcome"] == "interrupted"
    assert evidence["interruption"]["cancelled"] is (origin == "user")
