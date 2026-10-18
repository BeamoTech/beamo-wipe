"""Streaming assessment preserves progress order around incomplete summary tables."""

import pytest

from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import NwipeRunner, _log_signature, completion_for_method


@pytest.mark.parametrize("counts", ["0 | 0 | 0", "1 | 0 | 0", "0 | 1 | 0", "0 | 0 | 1"])
@pytest.mark.parametrize("closed", [False, True])
def test_projected_progress_does_not_move_inside_later_error_summary(tmp_path, counts, closed):
    progress = "/dev/sda: 50.00%, round 1 of 1, pass 1 of 1, eta 00:01:00, [writing]\n"
    text = (
        progress
        + "******************************** Error Summary *********************************\n"
        + f" sda | {counts}\n"
        + ("********************************************************************************\n" if closed else "")
    )
    logfile = tmp_path / "fake.log"
    logfile.write_text(text)
    projected = NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", _log_signature(logfile.stat())
    )
    assert projected is not None
    assert check_payloads(projected, "/dev/sda") == check_payloads(text, "/dev/sda")
    for method in MethodId:
        assert completion_for_method(0, projected, "/dev/sda", method) == completion_for_method(
            0, text, "/dev/sda", method
        )


@pytest.mark.parametrize("closed", [False, True])
def test_last_duplicate_counter_progress_keeps_original_table_position(tmp_path, closed):
    first = "/dev/sda: 25.00%, round 1 of 1, pass 1 of 1, eta 00:01:00, [writing]\n"
    last = "/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n"
    text = (
        first + last
        + "******************************** Error Summary *********************************\n"
        + " sda | 1 | 0 | 0\n"
        + ("********************************************************************************\n" if closed else "")
    )
    logfile = tmp_path / "fake.log"
    logfile.write_text(text)
    projected = NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", _log_signature(logfile.stat())
    )
    assert projected is not None
    assert check_payloads(projected, "/dev/sda") == check_payloads(text, "/dev/sda")
    assert not completion_for_method(0, projected, "/dev/sda", MethodId.EVERYDAY)[0]
