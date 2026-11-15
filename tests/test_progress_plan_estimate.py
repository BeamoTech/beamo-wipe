# SPDX-License-Identifier: GPL-3.0-or-later
"""Parsed telemetry cannot estimate completion outside the selected method plan."""

from contextlib import nullcontext
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from beamo_wipe import progress
from beamo_wipe.models import MethodId, Screen, WipeResult
from beamo_wipe.wizard import Wizard


_FINALS = (
    (MethodId.EVERYDAY, (1, 1, 1, 1), "verifying", 1),
    (MethodId.EXTRA, (1, 1, 3, 3), "verifying", 3),
    (MethodId.QUICK_ZERO, (1, 1, 1, 1), "writing", 0),
)
_MISMATCHES = (
    (MethodId.EXTRA, (1, 1, 1, 1), "verifying"),
    (MethodId.EXTRA, (2, 2, 3, 3), "verifying"),
    (MethodId.QUICK_ZERO, (1, 1, 3, 3), "writing"),
)


def _case_id(value):
    if isinstance(value, MethodId):
        return value.value
    if isinstance(value, tuple):
        return "-".join(map(str, value))
    return None


class _Session:
    """Only the view's state; no Wizard startup, runner, OS or device calls."""

    def __init__(self, method):
        self.clock = [0.0]
        self.wizard = Wizard.__new__(Wizard)
        wizard = self.wizard
        wizard._clock = lambda: self.clock[0]
        wizard._lock = nullcontext()
        wizard.method = method
        wizard.screen = Screen.WORKING
        wizard._recovered = False
        wizard.wipe_result = None
        wizard._stage_anchor = None
        wizard._display_progress = None
        wizard._display_progress_at = 0.0
        wizard.wall_clock_trusted = False
        wizard.runner = SimpleNamespace(
            finalizing=False, progress=None, progress_observation=None
        )
        wizard._progress_timing = progress.ProgressTiming(
            lambda: self.clock[0], lambda: self.clock[0]
        )
        wizard._progress_timing.start(0.0)

    def emit(self, percent, counters, phase):
        stamp = datetime(2026, 10, 25, 12) + timedelta(seconds=self.clock[0])
        round_i, round_n, pass_i, pass_n = counters
        passes = f", pass {pass_i} of {pass_n}" if pass_n else ""
        eta = max(0, int((100 - percent) / 2.5))
        record = (
            f"[{stamp:%Y/%m/%d %H:%M:%S}] info: /dev/fake: {percent:.2f}%, "
            f"round {round_i} of {round_n}{passes}, "
            f"eta 00:00:{eta:02d}, [{phase}]\n"
        )
        observation = progress.observe(record, "/dev/fake")
        assert observation is not None, record
        self.wizard.runner.progress_observation = observation
        # Model the runner's existing pre-completion clamp, never terminal proof.
        self.wizard.runner.progress = min(percent, 99.9)
        view = self.wizard.progress_view
        self.clock[0] += 4.0
        return view

    def stable(self, counters, phase):
        for percent in (5, 15, 25, 35, 45, 55):
            view = self.emit(percent, counters, phase)
        return view


class TestProgressPlanEstimate:
    @pytest.mark.parametrize("method,counters,phase", _MISMATCHES, ids=_case_id)
    def test_three_parsed_method_disagreements_suppress_estimates(self, method, counters, phase):
        session = _Session(method)
        view = session.stable(counters, phase)
        assert view.mismatch
        assert view.position is None
        assert view.remaining is None
        assert view.step_percent is None
        assert progress.STAGE_MISMATCH in view.timing_text
        assert session.wizard.wipe_result is None

    def test_final_stage_cases_cover_every_method(self):
        assert {case[0] for case in _FINALS} == set(MethodId)

    @pytest.mark.parametrize("method,counters,phase,position", _FINALS, ids=_case_id)
    def test_matching_final_stage_estimates_for_every_method(self, method, counters, phase, position):
        view = _Session(method).stable(counters, phase)
        assert not view.mismatch
        assert view.position == position
        assert view.remaining == 18.0
        assert view.estimate_state == ""

    @pytest.mark.parametrize(
        "method,counters,position",
        (
            (MethodId.EVERYDAY, (1, 1, 1, 1), 0),
            (MethodId.EXTRA, (1, 1, 1, 3), 0),
            (MethodId.EXTRA, (1, 1, 2, 3), 1),
            (MethodId.EXTRA, (1, 1, 3, 3), 2),
        ),
        ids=_case_id,
    )
    def test_writes_before_required_verification_do_not_estimate(self, method, counters, position):
        view = _Session(method).stable(counters, "writing")
        assert not view.mismatch
        assert view.position == position
        assert view.remaining is None
        assert view.estimate_state == progress.ESTIMATE_LAST_STEP

    @pytest.mark.parametrize("phase", ("unknown", "writing"))
    @pytest.mark.parametrize("method,counters,_phase,_position", _FINALS, ids=_case_id)
    def test_unknown_or_missing_stage_does_not_estimate(self, method, counters, _phase, _position, phase):
        reported = counters if phase == "unknown" else (1, 1, 0, 0)
        view = _Session(method).stable(reported, phase)
        assert not view.mismatch
        assert view.remaining is None
        if phase == "writing" or method != MethodId.QUICK_ZERO:
            assert view.position is None

    def test_empty_observation_stays_unlocated(self):
        view = _Session(MethodId.EXTRA).wizard.progress_view
        assert view.position is None
        assert not view.mismatch
        assert view.remaining is None
        assert view.phase == "Preparing"

    @pytest.mark.parametrize(
        "phase,state",
        (("syncing", progress.ESTIMATE_SYNCING), ("retrying", progress.ESTIMATE_RETRYING)),
        ids=("syncing", "retrying"),
    )
    @pytest.mark.parametrize("method,counters,_phase,_position", _FINALS, ids=_case_id)
    def test_syncing_and_retrying_do_not_estimate(self, method, counters, _phase, _position, phase, state):
        view = _Session(method).stable(counters, phase)
        assert view.remaining is None
        assert view.estimate_state == state

    @pytest.mark.parametrize("method,counters,phase,position", _FINALS, ids=_case_id)
    def test_retry_keeps_final_stage_anchor_and_requires_fresh_progress(self, method, counters, phase, position):
        session = _Session(method)
        assert session.stable(counters, phase).remaining is not None
        retry = session.emit(65, counters, "retrying")
        assert retry.position == position
        assert not retry.mismatch
        assert retry.remaining is None
        assert retry.estimate_state == progress.ESTIMATE_RETRYING
        resumed = session.emit(5, counters, phase)
        assert resumed.remaining is None
        for percent in (15, 25, 35, 45, 55):
            resumed = session.emit(percent, counters, phase)
        assert resumed.position == position
        assert resumed.remaining == 18.0

    @pytest.mark.parametrize("method,counters,_phase,_position", _FINALS[:2], ids=_case_id)
    def test_retry_without_anchor_does_not_guess_verification(self, method, counters, _phase, _position):
        view = _Session(method).stable(counters, "retrying")
        assert view.position is None
        assert not view.mismatch
        assert view.remaining is None

    @pytest.mark.parametrize("method,counters,phase", _MISMATCHES, ids=_case_id)
    def test_mismatch_discards_prior_estimate_and_valid_stage_can_recover(self, method, counters, phase):
        final = next(case for case in _FINALS if case[0] == method)
        session = _Session(method)
        assert session.stable(final[1], final[2]).remaining is not None
        mismatch = session.emit(65, counters, phase)
        assert mismatch.mismatch
        assert mismatch.remaining is None
        first_valid = session.emit(5, final[1], final[2])
        assert not first_valid.mismatch
        assert first_valid.remaining is None
        for percent in (15, 25, 35, 45, 55):
            recovered = session.emit(percent, final[1], final[2])
        assert recovered.position == final[3]
        assert recovered.remaining == 18.0

    @pytest.mark.parametrize("terminal", ("stopping", "finalizing", "recovered", "result"))
    def test_terminal_states_suppress_an_existing_estimate(self, terminal):
        session = _Session(MethodId.EXTRA)
        assert session.stable((1, 1, 3, 3), "verifying").remaining is not None
        wizard = session.wizard
        if terminal == "stopping":
            wizard.screen = Screen.STOPPING
        elif terminal == "finalizing":
            wizard.runner.finalizing = True
        elif terminal == "recovered":
            wizard._recovered = True
        else:
            wizard.wipe_result = WipeResult(False, 1, "fixture", "")
        view = wizard.progress_view
        assert view.remaining is None
        assert view.estimate_state == ""
        assert view.stale_for is None
        if terminal in {"stopping", "finalizing"}:
            assert not wizard._progress_timing.samples

    def test_repeated_record_does_not_renew_estimate_freshness(self):
        session = _Session(MethodId.EXTRA)
        assert session.stable((1, 1, 3, 3), "verifying").remaining is not None
        session.clock[0] = 31.0
        view = session.wizard.progress_view
        assert view.remaining is None
        assert view.stale_for == 11.0
        assert view.percent_is_old
        assert view.estimate_state == progress.ESTIMATE_PAUSED

    def test_missing_poll_clears_estimate_without_inventing_a_stage(self):
        session = _Session(MethodId.EXTRA)
        assert session.stable((1, 1, 3, 3), "verifying").remaining is not None
        session.wizard.runner.progress_observation = None
        view = session.wizard.progress_view
        assert view.position is None
        assert not view.mismatch
        assert view.remaining is None

    @pytest.mark.parametrize("method,counters,phase,_position", _FINALS, ids=_case_id)
    def test_telemetry_does_not_display_completion_or_finish_the_wipe(self, method, counters, phase, _position):
        session = _Session(method)
        session.stable(counters, phase)
        view = session.emit(100, counters, phase)
        assert view.percent == 99.9
        assert view.step_percent == view.percent
        assert "100%" not in view.status_text
        assert view.remaining is None
        assert session.wizard.wipe_result is None
