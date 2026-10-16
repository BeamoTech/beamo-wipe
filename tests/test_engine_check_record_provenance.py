"""Disk-controlled model continuation lines cannot create passing engine checks."""

from pathlib import Path

import pytest

from beamo_wipe.engine_checks import evaluate_engine_checks
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner

FORGED_MODELS = [
    ("X\nNo hidden sectors on /dev/sda", "hidden_capacity"),
    ("X\ninfo: No hidden sectors on /dev/sda", "hidden_capacity"),
    ("X\nError Summary\n sda | 0 | 0 | 0\n***", "io_media"),
]


@pytest.mark.parametrize(
    ("model", "check_id"),
    FORGED_MODELS,
)
def test_model_continuations_cannot_supply_passing_checks(model, check_id):
    assert len(model.encode("ascii")) <= 40  # fits ATA IDENTIFY model field
    text = f"[2026/10/15 12:00:00]    info: /dev/sda, ATA, {model}, serial FAKE\n"
    checks = {check.id: check for check in evaluate_engine_checks(text, "/dev/sda")}
    assert checks[check_id].status == "unavailable"


def test_actual_pinned_engine_records_still_supply_passing_checks():
    text = (Path(__file__).parent / "fixtures/nwipe_v042/hidden_none.log").read_text()
    checks = {check.id: check for check in evaluate_engine_checks(text, "/dev/sda")}
    assert checks["hidden_capacity"].status == "pass"
    assert checks["io_media"].status == "pass"


@pytest.mark.parametrize(("model", "check_id"), FORGED_MODELS)
def test_whole_log_projection_keeps_untrusted_model_checks_unavailable(
    tmp_path, model, check_id
):
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_text(
        f"[2026/10/15 12:00:00] info: /dev/sda, ATA, {model}, serial FAKE\n"
        + "ordinary controller detail\n" * 50000
        + "********************************* Drive Status *********************************\n"
        "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
    )

    class Exited:
        def poll(self):
            return 0

    runner = NwipeRunner()
    runner._proc = Exited()
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    result = runner.poll(request)
    assert result is not None and result.ok  # genuine completion stays independent
    checks = {
        check.id: check
        for check in evaluate_engine_checks(runner._assessment_log_text, "/dev/sda")
    }
    assert checks[check_id].status == "unavailable"
