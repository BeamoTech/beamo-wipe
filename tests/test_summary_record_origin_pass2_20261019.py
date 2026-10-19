"""A model's short error table is uncertain; native tables retain precedence."""

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.engine_checks import evaluate_engine_checks
from beamo_wipe.models import MethodId, WipeRequest


STAMP = "[2026/10/19 04:00:00] info: "
ERRORS = "******************************** Error Summary *********************************\n"
STATUS = runner_module.NWIPE_DRIVE_STATUS_HEADER + "\n"
ERASED = "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
PADDING = ("p" * 65535 + "\n") * 18


@pytest.fixture(autouse=True)
def only_fake_processes(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("fake-log regression attempted a native action")

    monkeypatch.setattr(runner_module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(runner_module.subprocess, "run", forbidden)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)


def model_table(row):
    model = "X\nError Summary\n " + row + "\n***"
    assert len(model.encode("ascii")) <= 40
    return STAMP + "/dev/sda, ATA, " + model + ", serial FAKE\n"


def media_status(log):
    return {check.id: check.status for check in evaluate_engine_checks(log, "/dev/sda")}["io_media"]


def assess(tmp_path, log, method, large):
    if not large:
        ok, _summary, reason = runner_module.completion_for_method(0, log, "/dev/sda", method)
        return ok, reason, media_status(log)
    log = log.replace(STATUS, PADDING + STATUS, 1)
    path = tmp_path / "fake.log"
    path.write_text(log, encoding="ascii")
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(path))

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    runner._active_request = request
    result = runner.poll(request)
    assert result is not None
    assert runner._assessment_ready and runner._assessment_log_text is not None
    assert len(log.encode()) > runner_module.NWIPE_COMPLETION_LOG_BYTES
    assert path.read_text(encoding="ascii") == log
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
    return result.ok, result.reason, media_status(runner._assessment_log_text)


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("large", (False, True))
@pytest.mark.parametrize("row", ("sda|1|0|0", "sda|0|1|0", "sda|0|0|1", "sda|unknown|0|0"))
def test_model_error_summary_is_ambiguous(tmp_path, method, large, row):
    log = model_table(row) + STATUS + ERASED
    assert assess(tmp_path, log, method, large) == (False, "indeterminate", "unavailable")


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("large", (False, True))
@pytest.mark.parametrize("before", (False, True))
@pytest.mark.parametrize("row", ("sda|1|0|0", "sda|0|1|0", "sda|unknown|0|0"))
def test_native_error_table_precedes_model_table(tmp_path, method, large, before, row):
    real = ERRORS + " sda | 2 | 0 | 0\n***\n"
    fake = model_table(row)
    log = (real + fake if before else fake + real) + STATUS + ERASED
    assert assess(tmp_path, log, method, large) == (False, "engine_failed", "fail")


@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("large", (False, True))
@pytest.mark.parametrize("row", ("sdb|1|0|0", "sda|0|0|0"))
def test_foreign_or_zero_model_table_cannot_invent_target_errors(tmp_path, method, large, row):
    log = model_table(row) + ERRORS + " sda | 0 | 0 | 0\n***\n" + STATUS + ERASED
    assert assess(tmp_path, log, method, large) == (True, "completed", "pass")


@pytest.mark.parametrize("native", (False, True))
@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("large", (False, True))
@pytest.mark.parametrize(
    "rows,reason,media",
    (
        (" sda | 1 | 0 | 0\n", "engine_failed", "fail"),
        (" sda | 0 | 0 | 0\n", "completed", "pass"),
        (" sda | 0 | 0 | 0\n sda | 0 | 0 | 0\n", "completed", "pass"),
        (" sda | 1 | 0 | 0\n sda | 0 | 0 | 0\n", "engine_failed", "unavailable"),
        (" sda | unknown | 0 | 0\n", "indeterminate", "unavailable"),
    ),
)
def test_authentic_table_normal_malformed_and_duplicate_controls(tmp_path, native, method, large, rows, reason, media):
    log = (STAMP + "Ordinary engine record\n" if native else "")
    log += ERRORS + rows + "***\n" + STATUS + ERASED
    assert assess(tmp_path, log, method, large) == (reason == "completed", reason, media)


@pytest.mark.parametrize("method", tuple(MethodId))
def test_bare_legacy_short_nonzero_summary_is_preserved(method):
    log = "Error Summary\n sda | 1 | 0 | 0\n***\n" + STATUS + ERASED
    assert runner_module.completion_for_method(0, log, "/dev/sda", method)[2] == "engine_failed"
    assert media_status(log) == "fail"
