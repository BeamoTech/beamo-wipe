"""Incomplete nwipe records cannot supply passing report checks."""

import pytest

from beamo_wipe.engine_checks import evaluate_engine_checks


@pytest.mark.parametrize(
    ("text", "check_id"),
    [
        ("No hidden sectors on /dev/sda", "hidden_capacity"),
        ("Error Summary\n  sda | 0 | 0 | 0", "io_media"),
    ],
)
def test_unterminated_positive_record_is_unavailable(text, check_id):
    checks = {check.id: check for check in evaluate_engine_checks(text, "/dev/sda")}
    assert checks[check_id].status == "unavailable"
    assert "not a pass" in checks[check_id].summary


@pytest.mark.parametrize(
    ("text", "check_id"),
    [
        ("No hidden sectors on /dev/sda\n", "hidden_capacity"),
        ("Error Summary\n  sda | 0 | 0 | 0\n", "io_media"),
    ],
)
def test_complete_positive_record_still_passes(text, check_id):
    checks = {check.id: check for check in evaluate_engine_checks(text, "/dev/sda")}
    assert checks[check_id].status == "pass"


def test_incomplete_log_preserves_explicit_disk_failure():
    text = "/dev/sda: >>> FAILURE! <<<\nError Summary\n  sda | 0 | 0 | 0"
    checks = {check.id: check for check in evaluate_engine_checks(text, "/dev/sda")}
    assert checks["io_media"].status == "fail"
