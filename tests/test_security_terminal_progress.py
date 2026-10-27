"""Damaged target updates cannot preserve stale erase-completion evidence."""

import os

import pytest

from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import (
    NWIPE_COMPLETION_EVIDENCE_BYTES,
    NWIPE_DRIVE_STATUS_HEADER,
    NwipeRunner,
    _log_signature,
    completion_for_method,
    evaluate_nwipe_outcome,
)


def final_sample(method, device="/dev/sda"):
    spec = METHODS[method]
    phase = "writing" if spec.verify == "off" else "verifying"
    passes = spec.overwrite_passes
    return (
        f"{device}: 100.00%, round 1 of 1, pass {passes} of {passes}, "
        f"eta 00:00:00, [{phase}]\n"
    )


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize(
    "damaged",
    [
        "/dev/sda: 010.00%, round 1 of 1, pass 1 of\n",
        "/dev/sda: 101.00%, round 1 of 1, pass 1 of 1\n",
        "/dev/sda: 100.00%, round 0 of 1, pass 1 of 1\n",
        "/dev/sda: damaged round pass eta\n",
    ],
)
def test_damaged_target_update_clears_prior_completion(method, damaged):
    ok, _, reason = completion_for_method(
        0, final_sample(method) + damaged, "/dev/sda", method
    )
    assert not ok
    assert reason == "completion_missing"


@pytest.mark.parametrize("method", list(MethodId))
def test_exact_decimal_above_one_hundred_is_not_completion(method):
    sample = final_sample(method).replace("100.00%", "100.00000000000000001%")
    assert completion_for_method(0, sample, "/dev/sda", method)[0] is False
    assert completion_for_method(
        0, final_sample(method) + sample, "/dev/sda", method
    )[0] is False


@pytest.mark.parametrize("method", list(MethodId))
def test_other_device_update_does_not_clear_target_completion(method):
    log = final_sample(method) + "/dev/sdb: damaged round pass eta\n"
    assert completion_for_method(0, log, "/dev/sda", method)[0] is True


@pytest.mark.parametrize("method", list(MethodId))
def test_independent_erased_table_remains_completion_proof(method):
    log = (
        final_sample(method)
        + "/dev/sda: damaged round pass eta\n"
        + NWIPE_DRIVE_STATUS_HEADER
        + "\n     sda | Erased | 100 MB/s | 00:01:00 | fixture\n"
    )
    assert completion_for_method(0, log, "/dev/sda", method)[0] is True


@pytest.mark.parametrize(
    "skip",
    [
        "/dev/sda is reported as IN USE\n",
        "Unable to open device '/dev/sda'.\n",
        "/dev/sda: No sane device geometry\n",
    ],
)
def test_damaged_progress_cannot_support_nothing_erased(skip):
    log = skip + "/dev/sda: 010.00%, round 1 of 1, pass 1 of\n"
    assert evaluate_nwipe_outcome(0, log, "/dev/sda")[2] == "indeterminate"


def scan_fixture(tmp_path, raw):
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_bytes(raw)
    os.chmod(logfile, 0o600)
    return NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", _log_signature(logfile.stat())
    )


@pytest.mark.parametrize("method", list(MethodId))
def test_large_log_projection_preserves_damaged_latest_record(tmp_path, method):
    raw = (
        final_sample(method)
        + "/dev/sda: 010.00%, round 1 of 1, pass 1 of\n"
        + ("diagnostic " + "." * 100 + "\n") * 10000
    ).encode()
    projection = scan_fixture(tmp_path, raw)
    assert projection is not None
    assert completion_for_method(0, projection, "/dev/sda", method)[0] is False


@pytest.mark.parametrize("fill,accepted", [(b"x", True), (b"\xff", False)])
def test_scanner_budget_counts_normalized_utf8(tmp_path, fill, accepted):
    raw = (b"***" + fill * 65532 + b"\n") * 16 + b"diagnostic\n"
    projection = scan_fixture(tmp_path, raw)
    if accepted:
        assert projection is not None
        assert len(projection.encode("utf-8")) == NWIPE_COMPLETION_EVIDENCE_BYTES
    else:
        assert projection is None


def test_scanner_budget_includes_deferred_progress(tmp_path):
    raw = (b"***" + b"x" * 65532 + b"\n") * 16
    raw += final_sample(MethodId.EVERYDAY).encode()
    assert scan_fixture(tmp_path, raw) is None
