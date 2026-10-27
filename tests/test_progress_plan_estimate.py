# SPDX-License-Identifier: GPL-3.0-or-later
"""Parsed telemetry cannot estimate completion outside the selected method plan."""

from contextlib import nullcontext
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import TestCase

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


class TestProgressPlanEstimate(TestCase):
    def test_three_parsed_method_disagreements_suppress_estimates(self):
        for method, counters, phase in _MISMATCHES:
            with self.subTest(method=method, counters=counters):
                session = _Session(method)
                view = session.stable(counters, phase)
                self.assertTrue(view.mismatch)
                self.assertIsNone(view.position)
                self.assertIsNone(view.remaining)
                self.assertIsNone(view.step_percent)
                self.assertIn(progress.STAGE_MISMATCH, view.timing_text)
                self.assertIsNone(session.wizard.wipe_result)

    def test_matching_final_stage_estimates_for_every_method(self):
        self.assertEqual({case[0] for case in _FINALS}, set(MethodId))
        for method, counters, phase, position in _FINALS:
            with self.subTest(method=method):
                view = _Session(method).stable(counters, phase)
                self.assertFalse(view.mismatch)
                self.assertEqual(view.position, position)
                self.assertEqual(view.remaining, 18.0)
                self.assertEqual(view.estimate_state, "")

    def test_writes_before_required_verification_do_not_estimate(self):
        cases = (
            (MethodId.EVERYDAY, (1, 1, 1, 1), 0),
            (MethodId.EXTRA, (1, 1, 1, 3), 0),
            (MethodId.EXTRA, (1, 1, 2, 3), 1),
            (MethodId.EXTRA, (1, 1, 3, 3), 2),
        )
        for method, counters, position in cases:
            with self.subTest(method=method, counters=counters):
                view = _Session(method).stable(counters, "writing")
                self.assertFalse(view.mismatch)
                self.assertEqual(view.position, position)
                self.assertIsNone(view.remaining)
                self.assertEqual(view.estimate_state, progress.ESTIMATE_LAST_STEP)

    def test_unknown_or_missing_stage_does_not_estimate(self):
        for method, counters, _phase, _position in _FINALS:
            for phase, reported in (("unknown", counters), ("writing", (1, 1, 0, 0))):
                with self.subTest(method=method, phase=phase):
                    view = _Session(method).stable(reported, phase)
                    self.assertFalse(view.mismatch)
                    self.assertIsNone(view.remaining)
                    if phase == "writing" or method != MethodId.QUICK_ZERO:
                        self.assertIsNone(view.position)

    def test_empty_observation_stays_unlocated(self):
        view = _Session(MethodId.EXTRA).wizard.progress_view
        self.assertIsNone(view.position)
        self.assertFalse(view.mismatch)
        self.assertIsNone(view.remaining)
        self.assertEqual(view.phase, "Preparing")

    def test_syncing_and_retrying_do_not_estimate(self):
        for method, counters, _phase, _position in _FINALS:
            for phase, state in (
                ("syncing", progress.ESTIMATE_SYNCING),
                ("retrying", progress.ESTIMATE_RETRYING),
            ):
                with self.subTest(method=method, phase=phase):
                    view = _Session(method).stable(counters, phase)
                    self.assertIsNone(view.remaining)
                    self.assertEqual(view.estimate_state, state)

    def test_retry_keeps_final_stage_anchor_and_requires_fresh_progress(self):
        for method, counters, phase, position in _FINALS:
            with self.subTest(method=method):
                session = _Session(method)
                self.assertIsNotNone(session.stable(counters, phase).remaining)
                retry = session.emit(65, counters, "retrying")
                self.assertEqual(retry.position, position)
                self.assertFalse(retry.mismatch)
                self.assertIsNone(retry.remaining)
                self.assertEqual(retry.estimate_state, progress.ESTIMATE_RETRYING)
                resumed = session.emit(5, counters, phase)
                self.assertIsNone(resumed.remaining)
                for percent in (15, 25, 35, 45, 55):
                    resumed = session.emit(percent, counters, phase)
                self.assertEqual(resumed.position, position)
                self.assertEqual(resumed.remaining, 18.0)

    def test_retry_without_anchor_does_not_guess_verification(self):
        for method, counters, _phase, _position in _FINALS[:2]:
            with self.subTest(method=method):
                view = _Session(method).stable(counters, "retrying")
                self.assertIsNone(view.position)
                self.assertFalse(view.mismatch)
                self.assertIsNone(view.remaining)

    def test_mismatch_discards_prior_estimate_and_valid_stage_can_recover(self):
        for method, counters, phase in _MISMATCHES:
            with self.subTest(method=method, counters=counters):
                final = next(case for case in _FINALS if case[0] == method)
                session = _Session(method)
                self.assertIsNotNone(session.stable(final[1], final[2]).remaining)
                mismatch = session.emit(65, counters, phase)
                self.assertTrue(mismatch.mismatch)
                self.assertIsNone(mismatch.remaining)
                first_valid = session.emit(5, final[1], final[2])
                self.assertFalse(first_valid.mismatch)
                self.assertIsNone(first_valid.remaining)
                for percent in (15, 25, 35, 45, 55):
                    recovered = session.emit(percent, final[1], final[2])
                self.assertEqual(recovered.position, final[3])
                self.assertEqual(recovered.remaining, 18.0)

    def test_terminal_states_suppress_an_existing_estimate(self):
        for terminal in ("stopping", "finalizing", "recovered", "result"):
            with self.subTest(terminal=terminal):
                session = _Session(MethodId.EXTRA)
                self.assertIsNotNone(session.stable((1, 1, 3, 3), "verifying").remaining)
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
                self.assertIsNone(view.remaining)
                self.assertEqual(view.estimate_state, "")
                self.assertIsNone(view.stale_for)
                if terminal in {"stopping", "finalizing"}:
                    self.assertFalse(wizard._progress_timing.samples)

    def test_repeated_record_does_not_renew_estimate_freshness(self):
        session = _Session(MethodId.EXTRA)
        self.assertIsNotNone(session.stable((1, 1, 3, 3), "verifying").remaining)
        session.clock[0] = 31.0
        view = session.wizard.progress_view
        self.assertIsNone(view.remaining)
        self.assertEqual(view.stale_for, 11.0)
        self.assertTrue(view.percent_is_old)
        self.assertEqual(view.estimate_state, progress.ESTIMATE_PAUSED)

    def test_missing_poll_clears_estimate_without_inventing_a_stage(self):
        session = _Session(MethodId.EXTRA)
        self.assertIsNotNone(session.stable((1, 1, 3, 3), "verifying").remaining)
        session.wizard.runner.progress_observation = None
        view = session.wizard.progress_view
        self.assertIsNone(view.position)
        self.assertFalse(view.mismatch)
        self.assertIsNone(view.remaining)

    def test_telemetry_does_not_display_completion_or_finish_the_wipe(self):
        for method, counters, phase, _position in _FINALS:
            with self.subTest(method=method):
                session = _Session(method)
                session.stable(counters, phase)
                view = session.emit(100, counters, phase)
                self.assertEqual(view.percent, 99.9)
                self.assertEqual(view.step_percent, view.percent)
                self.assertNotIn("100%", view.status_text)
                self.assertIsNone(view.remaining)
                self.assertIsNone(session.wizard.wipe_result)
