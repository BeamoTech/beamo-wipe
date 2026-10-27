"""Stopping retains the observed process status through persisted evidence."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from beamo_wipe.models import Screen, WipeResult
from test_refresh_disks import authorized


@pytest.mark.parametrize("code,expected_signal", [(-15, 15), (-9, 9), (143, None), (130, None), (0, None), (None, None)])
@pytest.mark.parametrize("origin", ["user", "system"])
@pytest.mark.parametrize("summary", ["cancelled", "interrupted"])
def test_stop_preserves_observed_status_in_terminal_evidence(
    tmp_path, monkeypatch, code, expected_signal, origin, summary
):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    wizard = authorized()
    wizard.confirm_erase()
    assert wizard.screen == Screen.WORKING
    observed = WipeResult(False, code, summary, wizard._wipe_request.logfile)
    wizard.runner = SimpleNamespace(
        result=observed, poll=lambda _request: None, cancel=lambda: None,
    )
    wizard.cancel_wipe(origin=origin)
    assert wizard.screen == Screen.DONE
    assert wizard.wipe_result.ok is False
    assert wizard.wipe_result.exit_code == code
    assert wizard.wipe_result.summary == "interrupted"
    assert wizard.evidence_path and not wizard.evidence_error
    evidence = json.loads(Path(wizard.evidence_path).read_text(encoding="utf-8"))
    assert evidence["exit_evidence"]["exit_code"] == code
    assert evidence["exit_evidence"]["signal"] == expected_signal
    assert evidence["interruption"]["interrupted"] is True
    assert evidence["interruption"]["cancelled"] is (origin == "user")
