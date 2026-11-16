"""Malformed telemetry cannot substantiate a 'nothing erased' assurance."""

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("record,reason", [
    ("/dev/sda is reported as IN USE", "occupied"),
    ("Unable to open device '/dev/sda'.", "open_failed"),
    ("No sane device geometry for /dev/sda", "geometry_unusable"),
])
@pytest.mark.parametrize("activity", ["none", "malformed", "round_only_then_malformed", "other_device"])
def test_full_and_projected_logs_preserve_activity(tmp_path, method, record, reason, activity):
    text = "[2026/10/25 00:00:00] error: " + record + "\n"
    if activity == "round_only_then_malformed":
        text += "/dev/sda: 010.00%, round 1 of 1\n"
    if activity in {"malformed", "round_only_then_malformed"}:
        text += "/dev/sda: 010.00%, round 1 of 1, pass 1 of\n"
    if activity == "other_device":
        text += "/dev/sdb: 010.00%, round 1 of 1, pass 1 of\n"
    text += "ordinary diagnostic message\n" * 100
    logfile = tmp_path / "engine.log"
    logfile.write_text(text)
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat()),
    )
    assert projected is not None
    expected = "indeterminate" if activity in {"malformed", "round_only_then_malformed"} else reason
    assert module.completion_for_method(0, text, "/dev/sda", method)[2] == expected
    assert module.completion_for_method(0, projected, "/dev/sda", method)[2] == expected
