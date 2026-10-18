"""Large-log assessment keeps normalized summary records in their original context."""

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest


_STAMP = "[2026/10/16 12:00:00] info: "
_NONE = _STAMP + "No hidden sectors on /dev/sda\n"
_HEADER = "******************************* Erasure Summary ********************************\n"
_CLOSE = "********************************************************************************\n"
_STATUS = (
    module.NWIPE_DRIVE_STATUS_HEADER + "\n"
    " sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)


class _Exited:
    returncode = 0

    def poll(self):
        return self.returncode


class _Stopped:
    returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def wait(self, timeout):
        return self.returncode


def _padding(size):
    lines, tail = divmod(size, 65536)
    return ("x" * 65535 + "\n") * lines + (
        "x" * (tail - 1) + "\n" if tail else ""
    )


def _assess(tmp_path, text, method, *, stop=False):
    logfile = tmp_path / "fake-summary.log"
    logfile.write_bytes(text.encode())
    runner = module.NwipeRunner()
    runner._proc = _Stopped() if stop else _Exited()
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))
    runner._active_request = request
    runner._last_logfile = str(logfile)
    if stop:
        runner.cancel()
        assert runner.result is not None and runner.result.reason == "cancelled"
    else:
        result = runner.poll(request)
        assert result is not None and result.ok
    assert runner._proc is None
    assert logfile.read_bytes() == text.encode()
    return runner._assessment_log_text


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize("prefix", ["", "info: ", _STAMP])
@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ("! sda | 1 | 2 | 50.00%\n", "warning"),
        ("! sda | invalid | 2 | 50.00%\n", "unavailable"),
        ("! sda | 2 | 2 | 100.00%\n", "pass"),
    ],
)
def test_summary_row_prefix_does_not_change_checks_at_large_log_boundary(
    tmp_path, method, large, prefix, row, expected
):
    text = (
        _NONE + _HEADER + prefix + row + _CLOSE
        + (_padding(module.NWIPE_COMPLETION_LOG_BYTES) if large else "")
        + _STATUS
    )
    full_checks = check_payloads(text, "/dev/sda")
    assert full_checks[0]["status"] == expected
    assessment = _assess(tmp_path, text, method)
    assert check_payloads(assessment, "/dev/sda") == full_checks


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize("prefix", ["info: ", _STAMP])
def test_prefixed_summary_close_keeps_later_rows_outside_table(
    tmp_path, method, large, prefix
):
    text = (
        _NONE + _HEADER + " sda | 2 | 2 | 100.00%\n"
        + prefix + _CLOSE + "! sda | 1 | 2 | 50.00%\n"
        + (_padding(module.NWIPE_COMPLETION_LOG_BYTES) if large else "")
        + _STATUS
    )
    full_checks = check_payloads(text, "/dev/sda")
    assert full_checks[0]["status"] == "pass"
    assessment = _assess(tmp_path, text, method)
    assert check_payloads(assessment, "/dev/sda") == full_checks


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize(
    "row", ["! sda | 1 | 2 | 50.00%\n", "! sda | invalid | 2 | 50.00%\n"]
)
def test_stop_keeps_prefixed_summary_warning_or_uncertainty(
    tmp_path, method, large, row
):
    text = (
        _NONE + _HEADER + _STAMP + row + _CLOSE
        + (_padding(module.NWIPE_COMPLETION_LOG_BYTES) if large else "")
    )
    full_checks = check_payloads(text, "/dev/sda")
    assert full_checks[0]["status"] in {"warning", "unavailable"}
    assessment = _assess(tmp_path, text, method, stop=True)
    assert check_payloads(assessment, "/dev/sda") == full_checks


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_summary_shortfall_stays_warning_at_exact_scan_boundary(tmp_path, delta):
    evidence = _NONE + _HEADER + _STAMP + "! sda | 1 | 2 | 50.00%\n" + _CLOSE
    text = evidence + _padding(
        module.NWIPE_COMPLETION_LOG_BYTES + delta - len(evidence) - len(_STATUS)
    ) + _STATUS
    assert len(text) == module.NWIPE_COMPLETION_LOG_BYTES + delta
    assessment = _assess(tmp_path, text, MethodId.EVERYDAY)
    assert check_payloads(assessment, "/dev/sda")[0]["status"] == "warning"
