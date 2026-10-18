"""Large-log assessment preserves exact status-banner record contents."""

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


class _Exited:
    returncode = 0

    def poll(self):
        return self.returncode


class _ExitsAtStop:
    """A fake process finishing naturally as Stop is sent."""

    def __init__(self):
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 0

    def wait(self, timeout):
        return self.returncode


def _terminal_text(banner_ending, model):
    return (
        module.NWIPE_DRIVE_STATUS_HEADER
        + banner_ending
        + f" sda | Erased | 120MB/s | 00:01:00 | {model}\n"
    )


def _padding(large):
    # Exercise the actual size boundary without a long-line refusal. Each
    # ordinary line stays below the independent completion-scan line cap.
    return ("ordinary detail " + "x" * 65500 + "\n") * 17 if large else ""


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("banner_ending", ["\n", "\r\n", "\r\r\n"])
@pytest.mark.parametrize("large", [False, True])
def test_terminal_status_banner_is_not_normalized_by_log_size(
    tmp_path, method, banner_ending, large
):
    text = _padding(large) + _terminal_text(banner_ending, "FAKE/DISK")
    logfile = tmp_path / "fake-terminal.log"
    logfile.write_bytes(text.encode())
    runner = module.NwipeRunner()
    runner._proc = _Exited()
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))

    result = runner.poll(request)

    assert result is not None
    assert (result.ok, result.summary, result.reason) == module.completion_for_method(
        0, text, request.device, method
    )
    assert result.ok is (banner_ending == "\n")
    assert logfile.read_bytes() == text.encode()


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("banner_ending", ["\n", "\r\n", "\r\r\n"])
@pytest.mark.parametrize("large", [False, True])
def test_stop_race_uses_the_same_exact_status_banner_at_every_log_size(
    tmp_path, method, banner_ending, large
):
    text = _padding(large) + _terminal_text(banner_ending, "FAKE/DISK")
    logfile = tmp_path / "fake-stop.log"
    logfile.write_bytes(text.encode())
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner()
    runner._proc = _ExitsAtStop()
    runner._active_request = request
    runner._last_logfile = str(logfile)

    runner.cancel()

    assert runner.result is not None
    assert runner.result.ok is (banner_ending == "\n")
    assert runner.result.reason == (
        "completed" if banner_ending == "\n" else "cancelled"
    )
    assert runner._proc is None
    assert logfile.read_bytes() == text.encode()


@pytest.mark.parametrize("model", ["FAKE\rDISK", "FAKE\r", "FAKE\r\r"])
@pytest.mark.parametrize("large", [False, True])
def test_carriage_returns_in_model_do_not_change_a_genuine_banner(
    tmp_path, model, large
):
    text = _padding(large) + _terminal_text("\n", model)
    logfile = tmp_path / "fake-model.log"
    logfile.write_bytes(text.encode())
    runner = module.NwipeRunner()
    runner._proc = _Exited()
    request = WipeRequest(
        "/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile)
    )

    result = runner.poll(request)

    assert result is not None and result.ok
    assert result.reason == "completed"
    assert logfile.read_bytes() == text.encode()


@pytest.mark.parametrize("size_delta", [-1, 0, 1])
def test_malformed_banner_stays_unproven_at_the_completion_scan_boundary(
    tmp_path, size_delta
):
    terminal = _terminal_text("\r\n", "FAKE/DISK")
    desired = module.NWIPE_COMPLETION_LOG_BYTES + size_delta
    padding_size = desired - len(terminal)
    full_lines, tail_size = divmod(padding_size, 65536)
    padding = ("x" * 65535 + "\n") * full_lines
    if tail_size:
        padding += "x" * (tail_size - 1) + "\n"
    text = padding + terminal
    assert len(text) == desired
    logfile = tmp_path / "fake-boundary.log"
    logfile.write_bytes(text.encode())
    runner = module.NwipeRunner()
    runner._proc = _Exited()
    request = WipeRequest(
        "/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile)
    )

    result = runner.poll(request)

    assert result is not None and not result.ok
    assert result.reason == "completion_missing"
    assert runner.progress != 100.0
