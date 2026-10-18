"""Floating-point rounding cannot supply a missing exact 100% completion marker."""

import pytest

from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import _iter_target_progress, completion_for_method


@pytest.mark.parametrize("percent", ["99.99999999999999999999", "100.00000000000000000001"])
@pytest.mark.parametrize("method", list(MethodId))
def test_inexact_percent_cannot_round_into_completion(percent, method):
    passes = 3 if method == MethodId.EXTRA else 1
    phase = "writing" if method == MethodId.QUICK_ZERO else "verifying"
    text = (
        f"/dev/sda: {percent}%, round 1 of 1, pass {passes} of {passes}, "
        f"eta 00:00:00, [{phase}]\n"
    )
    assert completion_for_method(0, text, "/dev/sda", method)[0] is False


@pytest.mark.parametrize("percent", ["100", "100.0", "100.00", "100.00000000000000000000"])
@pytest.mark.parametrize("method", list(MethodId))
def test_exact_hundred_percent_still_proves_final_progress(percent, method):
    passes = 3 if method == MethodId.EXTRA else 1
    phase = "writing" if method == MethodId.QUICK_ZERO else "verifying"
    text = (
        f"/dev/sda: {percent}%, round 1 of 1, pass {passes} of {passes}, "
        f"eta 00:00:00, [{phase}]\n"
    )
    assert completion_for_method(0, text, "/dev/sda", method)[0] is True


def test_true_excess_above_hundred_is_not_a_progress_observation():
    text = (
        "/dev/sda: 100.00000000000000000001%, round 1 of 1, pass 1 of 1, "
        "eta 00:00:00, [verifying]\n"
    )
    assert list(_iter_target_progress(text, "/dev/sda")) == []
