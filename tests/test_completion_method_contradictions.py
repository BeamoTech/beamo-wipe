"""Explicit completion cannot override counters contradicting the launched method."""

import pytest

from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe import nwipe_runner as module
from beamo_wipe.nwipe_runner import completion_for_method

STATUS = (
    "********************************* Drive Status *********************************\n"
    "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("wrong_counter", ["passes", "rounds"])
def test_erased_row_cannot_hide_method_counter_contradiction(method, wrong_counter):
    spec = METHODS[method]
    passes = spec.overwrite_passes + (1 if wrong_counter == "passes" else 0)
    rounds = spec.rounds + (1 if wrong_counter == "rounds" else 0)
    phase = "writing" if spec.verify == "off" else "verifying"
    text = (
        f"/dev/sda: 100.00%, round {rounds} of {rounds}, pass {passes} of {passes}, "
        f"eta 00:00:00, [{phase}]\n" + STATUS
    )
    ok, _summary, reason = completion_for_method(0, text, "/dev/sda", method)
    assert not ok
    assert reason == "indeterminate"


@pytest.mark.parametrize("phase", ["syncing", "retrying", "blanking"])
@pytest.mark.parametrize("method", list(MethodId))
def test_other_complete_engine_phases_cannot_hide_counter_contradictions(phase, method):
    spec = METHODS[method]
    wrong_passes = spec.overwrite_passes + 1
    text = (
        f"/dev/sda: 010.00%, round 1 of 1, pass 1 of {wrong_passes}, "
        f"eta 00:00:10, [{phase}]\n" + STATUS
    )
    assert completion_for_method(0, text, "/dev/sda", method)[0] is False


@pytest.mark.parametrize("method", list(MethodId))
def test_matching_or_absent_progress_counters_keep_erased_completion(method):
    spec = METHODS[method]
    phase = "writing" if spec.verify == "off" else "verifying"
    matching = (
        f"/dev/sda: 099.87%, round {spec.rounds} of {spec.rounds}, "
        f"pass {spec.overwrite_passes} of {spec.overwrite_passes}, "
        f"eta 00:00:01, [{phase}]\n"
    )
    foreign = (
        "/dev/sdb: 100.00%, round 999 of 999, pass 999 of 999, "
        "eta 00:00:00, [verifying]\n"
    )
    for text in (STATUS, matching + STATUS, foreign + STATUS):
        assert completion_for_method(0, text, "/dev/sda", method)[0]


@pytest.mark.parametrize("method", list(MethodId))
def test_final_progress_cannot_claim_an_unrequested_round(method):
    spec = METHODS[method]
    phase = "writing" if spec.verify == "off" else "verifying"
    text = (
        f"/dev/sda: 100.00%, round 2 of 2, pass {spec.overwrite_passes} "
        f"of {spec.overwrite_passes}, eta 00:00:00, [{phase}]\n"
    )
    assert completion_for_method(0, text, "/dev/sda", method)[0] is False


@pytest.mark.parametrize("large_log", [False, True])
def test_later_matching_progress_cannot_hide_earlier_method_conflict(
    tmp_path, large_log
):
    early = (
        "/dev/sda: 010.00%, round 1 of 1, pass 1 of 1, "
        "eta 00:10:00, [writing]\n"
    )
    late = (
        "/dev/sda: 100.00%, round 1 of 1, pass 3 of 3, "
        "eta 00:00:00, [verifying]\n"
    )
    padding = "ordinary message\n" * 70000 if large_log else ""
    logfile = tmp_path / "nwipe.log"
    logfile.write_text(early + padding + late + STATUS)
    runner = module.NwipeRunner()

    class Exited:
        def poll(self):
            return 0

    runner._proc = Exited()
    request = WipeRequest("/dev/sda", MethodId.EXTRA, "/dev/sr0", str(logfile))
    result = runner.poll(request)
    assert result is not None and not result.ok
    assert result.reason == "indeterminate"


@pytest.mark.parametrize(
    "bad_sample",
    [
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta",  # cut ETA
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1",  # cut phase
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta 00:00:00, [writing] junk",
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta 00:00:00, [writing]\0",
        "/dev/sda: 100.00%, round 0 of 2, pass 1 of 1, eta 00:00:00, [writing]",
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta 00:00:00, [unknown]",
        "/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta 00:00:00, ",
    ],
)
def test_malformed_samples_cannot_establish_method_counter_conflicts(bad_sample):
    assert completion_for_method(0, bad_sample + "\n" + STATUS, "/dev/sda", MethodId.EXTRA)[0]


def test_counter_projection_refuses_when_distinct_totals_exceed_evidence_cap(
    tmp_path, monkeypatch
):
    logfile = tmp_path / "nwipe.log"
    samples = "".join(
        f"/dev/sda: 010.00%, round 1 of 1, pass 1 of {total}, "
        "eta 00:10:00, [writing]\n" for total in range(1, 5)
    )
    logfile.write_text(samples + STATUS)
    monkeypatch.setattr(module, "NWIPE_COMPLETION_EVIDENCE_BYTES", 250)
    projection = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat())
    )
    assert projection is None
