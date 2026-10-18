"""Prefixed negative error evidence cannot be overruled by an Erased row."""

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest


_STAMP = "[2026/10/16 12:00:00] info: "
_PREFIXES = ("", "info: ", _STAMP)
_ERROR_HEADER = "******************************** Error Summary *********************************\n"
_CLOSE = "********************************************************************************\n"
_STATUS = (
    module.NWIPE_DRIVE_STATUS_HEADER + "\n"
    " sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)


def _padding(size):
    lines, tail = divmod(size, 65536)
    return ("x" * 65535 + "\n") * lines + (
        "x" * (tail - 1) + "\n" if tail else ""
    )


def _error_log(prefix, counts, *, name="sda"):
    return _ERROR_HEADER + prefix + f"! {name} | {counts}\n" + _CLOSE


def _assess(tmp_path, text, method, *, late_stop=False):
    logfile = tmp_path / "fake-prefixed-errors.log"
    logfile.write_bytes(text.encode())

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

        def terminate(self):
            pytest.fail("Late Stop must classify the already exited fake process")

    runner = module.NwipeRunner()
    runner._proc = Exited()
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))
    runner._active_request = request
    runner._last_logfile = str(logfile)
    if late_stop:
        runner.cancel()
        result = runner.result
    else:
        result = runner.poll(request)
    assert result is not None
    assert runner._proc is None
    assert logfile.read_bytes() == text.encode()
    return result, runner._assessment_log_text


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize(
    ("counts", "reason", "io_status"),
    [
        ("1 | 0 | 0", "engine_failed", "fail"),
        ("0 | 1 | 0", "engine_failed", "fail"),
        ("0 | 0 | 1", "engine_failed", "fail"),
        ("unknown | 0 | 0", "indeterminate", "unavailable"),
    ],
)
def test_prefixed_target_error_row_blocks_terminal_success(
    method, prefix, counts, reason, io_status
):
    text = _error_log(prefix, counts) + _STATUS
    assert check_payloads(text, "/dev/sda")[1]["status"] == io_status
    outcome = module.completion_for_method(0, text, "/dev/sda", method)
    assert not outcome[0]
    assert outcome[2] == reason


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize(("name", "counts"), [("sda", "0 | 0 | 0"), ("sdb", "1 | 0 | 0")])
def test_zero_or_foreign_error_row_keeps_genuine_completion(method, prefix, name, counts):
    text = _error_log(prefix, counts, name=name) + _STATUS
    assert module.completion_for_method(0, text, "/dev/sda", method)[0]


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("prefix", _PREFIXES[1:])
@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize("late_stop", [False, True])
def test_actual_poll_and_late_stop_keep_prefixed_errors_at_scan_boundary(
    tmp_path, method, prefix, large, late_stop
):
    text = (
        _error_log(prefix, "1 | 0 | 0")
        + (_padding(module.NWIPE_COMPLETION_LOG_BYTES) if large else "")
        + _STATUS
    )
    result, assessment = _assess(tmp_path, text, method, late_stop=late_stop)
    assert not result.ok
    assert result.reason == "engine_failed"
    assert check_payloads(assessment, "/dev/sda") == check_payloads(text, "/dev/sda")


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("prefix", _PREFIXES[1:])
def test_headerless_prefixed_error_is_uncertain_instead_of_success(method, prefix):
    text = prefix + "! sda | 1 | 0 | 0\n" + _CLOSE + _STATUS
    assert module.completion_for_method(0, text, "/dev/sda", method)[2] == "indeterminate"


@pytest.mark.parametrize("prefix", _PREFIXES[1:])
@pytest.mark.parametrize(
    "guard",
    [
        "/dev/sda is IN USE but --force is not set, not wiping it\n",
        "Unable to open device '/dev/sda'.\n",
        "No sane device geometry for '/dev/sda'.\n",
    ],
)
def test_prefixed_error_activity_prevents_no_erase_claim(prefix, guard):
    text = guard + _error_log(prefix, "1 | 0 | 0")
    assert module.evaluate_nwipe_outcome(0, text, "/dev/sda")[2] == "indeterminate"


@pytest.mark.parametrize("prefix", _PREFIXES[1:])
def test_shared_status_error_row_stays_unassignable(prefix):
    target = "/dev/sdabcdef"
    text = (
        "/dev/sdxsdabcdef: selected\n"
        + _ERROR_HEADER + prefix + "! sdabcdef | 1 | 0 | 0\n" + _CLOSE
        + target + ": 100.00%, round 1 of 1, pass 1 of 1, "
        "eta 00:00:00, [verifying]\n"
    )
    assert module.completion_for_method(0, text, target, MethodId.EVERYDAY)[2] == "indeterminate"


@pytest.mark.parametrize("prefix", _PREFIXES[1:])
def test_prefixed_closing_delimiter_ends_error_context(prefix):
    text = (
        _ERROR_HEADER + "! sda | 0 | 0 | 0\n"
        + prefix + _CLOSE + "! sda | unknown | 0 | 0\n" + _STATUS
    )
    assert module.evaluate_nwipe_outcome(0, text, "/dev/sda")[0]


@pytest.mark.parametrize("prefix", _PREFIXES[1:])
def test_model_phrase_does_not_start_error_context(prefix):
    text = prefix + "Model: Error Summary\n" + prefix + "! sda | unknown | 0 | 0\n" + _STATUS
    assert module.evaluate_nwipe_outcome(0, text, "/dev/sda")[0]


@pytest.mark.parametrize("large", [False, True])
def test_error_normalization_does_not_upgrade_cr_status_provenance(tmp_path, large):
    text = (
        _error_log(_STAMP, "0 | 0 | 0")
        + (_padding(module.NWIPE_COMPLETION_LOG_BYTES) if large else "")
        + _STATUS.replace(module.NWIPE_DRIVE_STATUS_HEADER + "\n", module.NWIPE_DRIVE_STATUS_HEADER + "\r\n")
    )
    result, _assessment = _assess(tmp_path, text, MethodId.EVERYDAY)
    assert not result.ok
    assert result.reason == "completion_missing"


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_prefixed_error_survives_exact_large_log_boundary(tmp_path, delta):
    evidence = _error_log(_STAMP, "1 | 0 | 0")
    text = evidence + _padding(
        module.NWIPE_COMPLETION_LOG_BYTES + delta - len(evidence) - len(_STATUS)
    ) + _STATUS
    assert len(text) == module.NWIPE_COMPLETION_LOG_BYTES + delta
    result, _assessment = _assess(tmp_path, text, MethodId.EVERYDAY)
    assert result.reason == "engine_failed"
