"""Model LF continuations cannot prove an owner abort or media failure."""

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.engine_checks import evaluate_engine_checks
from beamo_wipe.models import MethodId, WipeRequest


STAMP = "[2026/10/19 00:30:00]    info: "
STATUS = runner_module.NWIPE_DRIVE_STATUS_HEADER + "\n"
ERRORS = (
    "******************************** Error Summary *********************************\n"
    " sda | 0 | 0 | 0\n***\n"
)
ERASED = "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
NEGATIVES = (
    ("Nwipe was aborted by the user", "interrupted"),
    ("/dev/sda: >>> FAILURE! <<<", "engine_failed"),
    ("Verification mismatch on '/dev/sda'", "verification_failed"),
    ("sda |-FAILED-|", "engine_failed"),
    ("sda |UABORTED|", "engine_failed"),
    ("sda |INSANITY|", "engine_failed"),
)


@pytest.fixture(autouse=True)
def fake_log_actions_only(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("fake-log regression attempted a native action")

    monkeypatch.setattr(runner_module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(runner_module.subprocess, "run", forbidden)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)


def model_record(payload):
    model = "X\n" + payload
    assert len(model.encode("ascii")) <= 40
    return STAMP + "/dev/sda, ATA, " + model + ", serial FAKE\n"


def media_status(log):
    return {row.id: row.status for row in evaluate_engine_checks(log, "/dev/sda")}["io_media"]


@pytest.mark.parametrize("payload,_reason", NEGATIVES)
@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("large", (False, True))
def test_model_continuation_remains_indeterminate(tmp_path, payload, _reason, method, large):
    log = model_record(payload) + ERRORS + STATUS + ERASED
    if not large:
        result = runner_module.completion_for_method(0, log, "/dev/sda", method)
        assert not result[0] and result[2] == "indeterminate", result
        return
    # The original model context is outside the terminal suffix. Streaming
    # assessment must retain its origin rather than promote a bare sentence.
    log = model_record(payload) + ("p" * 65535 + "\n") * 18 + ERRORS + STATUS + ERASED
    logfile = tmp_path / "fake.log"
    logfile.write_text(log, encoding="ascii")
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    runner._active_request = request
    result = runner.poll(request)
    assert result is not None and not result.ok and result.reason == "indeterminate"
    assert runner._assessment_ready and runner._assessment_log_text is not None
    assert len(log.encode()) > runner_module.NWIPE_COMPLETION_LOG_BYTES
    assert logfile.read_text(encoding="ascii") == log
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None


@pytest.mark.parametrize("payload,_reason", NEGATIVES[1:])
def test_model_continuation_cannot_prove_media_failure(payload, _reason):
    assert media_status(model_record(payload) + ERRORS + STATUS + ERASED) == "unavailable"


@pytest.mark.parametrize("status", ("-FAILED-", "UABORTED", "INSANITY"))
def test_continuation_in_status_table_cannot_prove_media_failure(status):
    # A status-table model is truncated to 17 bytes. An abbreviated cell
    # still fits, but a genuine row also carries rate and runtime fields.
    model = "X\nsda |" + status + "|"
    assert len(model.encode("ascii")) <= 17
    log = STAMP + "Program options are set as follows\n" + ERRORS + STATUS
    log += "      sdb | Erased | 120MB/s | 00:01:00 | " + model + "/FAKE\n"
    log += ERASED
    assert runner_module.completion_for_method(0, log, "/dev/sda", MethodId.EVERYDAY)[2] == "indeterminate"
    assert media_status(log) == "unavailable"


@pytest.mark.parametrize("payload,_reason", NEGATIVES)
@pytest.mark.parametrize("genuine,reason", NEGATIVES[:3])
@pytest.mark.parametrize("before", (False, True))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_genuine_negative_precedes_ambiguous_model(payload, _reason, genuine, reason, before, method):
    real = STAMP + genuine + "\n"
    model = model_record(payload)
    log = (real + model if before else model + real) + STATUS + ERASED
    assert runner_module.completion_for_method(0, log, "/dev/sda", method)[2] == reason
    if reason != "interrupted":
        assert media_status(log) == "fail"


@pytest.mark.parametrize("payload,reason", NEGATIVES)
@pytest.mark.parametrize("method", tuple(MethodId))
def test_bare_legacy_negative_contract_is_preserved(payload, reason, method):
    log = payload + "\n" + STATUS + ERASED
    assert runner_module.completion_for_method(0, log, "/dev/sda", method)[2] == reason


@pytest.mark.parametrize("status", ("-FAILED-", "UABORTED", "INSANITY"))
@pytest.mark.parametrize("method", tuple(MethodId))
@pytest.mark.parametrize("rate", ("120MB/s", "0"))
def test_native_complete_status_failure_remains_failure(status, method, rate):
    log = STAMP + "Program options are set as follows\n" + ERRORS + STATUS
    log += "!     sda |" + status + "| " + rate + " | 00:01:00 | FAKE/DISK\n"
    assert runner_module.completion_for_method(0, log, "/dev/sda", method)[2] == "engine_failed"
    assert media_status(log) == "fail"


@pytest.mark.parametrize("method", tuple(MethodId))
def test_clean_success_control(method):
    log = STAMP + "/dev/sda, ATA, ordinary model, serial FAKE\n" + ERRORS + STATUS + ERASED
    assert runner_module.completion_for_method(0, log, "/dev/sda", method) == (True, "finished", "completed")
    assert media_status(log) == "pass"
