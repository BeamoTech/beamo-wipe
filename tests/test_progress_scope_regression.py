"""nwipe's SIGUSR1 percentage covers the job, not the current pass."""

import pytest

from beamo_wipe import lang
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import NwipeRunner
from test_operation_sequence import _working
from test_progress_timing import line, sample


@pytest.mark.parametrize(
    "language,label", [("en", "40% overall"), ("fr", "40% au total"), ("de", "40% insgesamt")]
)
def test_job_percentage_is_never_described_as_within_step(language, label):
    wiz, _ = _working(MethodId.EXTRA)
    wiz.runner.progress_observation = sample(40, counters="round 1 of 1, pass 2 of 3")
    lang.set_language(language)
    text = wiz.progress_view.status_text
    assert label in text
    assert "of this step" not in text
    assert "de cette étape" not in text
    assert "dieses Schritts" not in text


def test_job_percentage_cannot_show_100_before_completion():
    wiz, _ = _working(MethodId.EXTRA)
    wiz.runner.progress = 99.9
    wiz.runner.progress_observation = sample(
        100, phase="verifying", counters="round 1 of 1, pass 3 of 3"
    )
    assert "100%" not in wiz.progress_view.status_text
    assert wiz.wipe_result is None


@pytest.mark.parametrize("next_percent,elapsed,expected", [(45, 1, 40), (35, 6, 40)])
def test_step_overall_percentage_shares_throttled_monotonic_headline(
    monkeypatch, next_percent, elapsed, expected
):
    wiz, clock = _working(MethodId.EXTRA)
    runner = NwipeRunner()
    runner._proc = object()  # A running sentinel; no process or disk is opened.
    wiz.runner = runner
    wiz._display_progress = None

    def refresh(percent):
        record = line(percent, counters="round 1 of 1, pass 2 of 3")
        monkeypatch.setattr(runner, "_read_log_tail", lambda *_: record)
        runner._refresh_progress("/unused-fake-log", "/dev/fake")

    refresh(40)
    assert wiz.progress_view.percent == 40
    clock.advance(elapsed)
    refresh(next_percent)
    assert runner.progress == max(40, next_percent)
    view = wiz.progress_view
    assert view.percent == expected
    assert f"({expected}% overall)" in view.status_text
    assert view.step_percent == view.percent
