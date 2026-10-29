"""A model LF cannot establish that a real erase never touched the disk."""

from __future__ import annotations

import os

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import completion_for_method
from beamo_wipe.outcomes import VIEWS, may_have_erased
from beamo_wipe.recovery import MEANING_UNCHANGED, recovery_for_view


TARGETS = ("/dev/sda", "/dev/vda", "/dev/nvme0n1")
GUARDS = (
    ("{device} is reported as IN USE", "occupied"),
    ("Unable to open device '{device}'.", "open_failed"),
    ("{device}: No sane device geometry", "geometry_unusable"),
)
STAMP = "[2026/10/17 12:00:00]    info: "
WARN = "[2026/10/17 12:00:01] warning: "
PROGRESS = (
    "{device}: 5.00%, round 1 of 1, pass 1 of 1, "
    "eta 00:30:00, [writing]\n"
)


@pytest.fixture(autouse=True)
def no_native_actions(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("pure fake-log regression attempted a native action")

    monkeypatch.setattr(runner_module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(runner_module.subprocess, "run", forbidden)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(runner_module, "_recheck_identity_under_lock", forbidden)
    monkeypatch.setattr(runner_module, "_reserve_target_under_lock", forbidden)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)
    realpath = os.path.realpath

    def fake_device_realpath(path, *args, **kwargs):
        if os.fsdecode(path).startswith("/dev/"):
            return os.fspath(path)
        return realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_device_realpath)
    native_open = os.open

    def ordinary_open(path, *args, **kwargs):
        if os.fsdecode(path).startswith(("/dev/", "/sys/", "/proc/")):
            forbidden()
        return native_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", ordinary_open)


@pytest.mark.parametrize("device", TARGETS)
@pytest.mark.parametrize("template,_legacy_reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1, -15, 143))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_model_lf_cannot_establish_nothing_erased(
    device, template, _legacy_reason, exit_code, method
):
    # Matches the initial device-info shape used by the established pass38
    # regression. A real model has a nonspace first character, then an LF;
    # bookworm libparted preserving that LF is the existing source contract.
    model = "X\n" + template.format(device=device)
    assert len(model.encode("ascii")) <= 40
    log = STAMP + device + ", ATA, " + model + "\n"
    log += STAMP + "Program options are set as follows\n"
    ok, _summary, reason = completion_for_method(exit_code, log, device, method)
    assert not ok
    assert may_have_erased(reason), reason
    recovery = recovery_for_view(VIEWS[reason])
    assert recovery is not None
    assert recovery.meaning != MEANING_UNCHANGED


@pytest.mark.parametrize("device", TARGETS)
@pytest.mark.parametrize("template,reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1, -15, 143))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_real_timestamped_skip_records_remain_attributed(
    device, template, reason, exit_code, method
):
    log = STAMP + device + ", ATA, Ordinary model\n"
    log += WARN + template.format(device=device) + "\n"
    assert completion_for_method(exit_code, log, device, method)[2] == reason


@pytest.mark.parametrize("template,reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1, -15, 143))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_legacy_bare_parser_contract_is_explicit(template, reason, exit_code, method):
    log = template.format(device="/dev/sda") + "\n"
    assert completion_for_method(exit_code, log, "/dev/sda", method)[2] == reason


@pytest.mark.parametrize("template,_reason", GUARDS)
@pytest.mark.parametrize("prefixed", (False, True))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_actual_erase_activity_remains_contradictory(template, _reason, prefixed, method):
    prefix = WARN if prefixed else ""
    log = prefix + template.format(device="/dev/sda") + "\n"
    log += PROGRESS.format(device="/dev/sda")
    assert completion_for_method(0, log, "/dev/sda", method)[2] == "indeterminate"


@pytest.mark.parametrize("template,_reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_same_line_model_phrase_remains_data(template, _reason, exit_code, method):
    log = STAMP + "/dev/sda, ATA, X " + template.format(device="/dev/sda") + "\n"
    expected = "completion_missing" if exit_code == 0 else "process_failed"
    assert completion_for_method(exit_code, log, "/dev/sda", method)[2] == expected


class ExitedFakeProcess:
    def __init__(self, code):
        self.returncode = code

    def poll(self):
        return self.returncode


@pytest.mark.parametrize("device", TARGETS)
@pytest.mark.parametrize("template,_legacy_reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1, -15, 143))
@pytest.mark.parametrize("method", tuple(MethodId))
def test_large_log_projection_cannot_promote_model_lf_to_noerase_proof(
    tmp_path, device, template, _legacy_reason, exit_code, method
):
    model = "X\n" + template.format(device=device)
    assert len(model.encode("ascii")) <= 40
    header = STAMP + device + ", ATA, " + model + "\n"
    # Full initial info context falls outside the last 1 MiB. The projection
    # must preserve ambiguity instead of turning a data continuation into a
    # plausible standalone legacy record.
    padding = ("p" * 65535 + "\n") * 18
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_text(header + padding, encoding="ascii")
    assert logfile.stat().st_size > runner_module.NWIPE_COMPLETION_LOG_BYTES
    request = WipeRequest(
        device=device,
        method=method,
        boot_device="/dev/sr0",
        logfile=str(logfile),
    )
    runner = runner_module.NwipeRunner()
    runner._proc = ExitedFakeProcess(exit_code)
    runner._active_request = request
    runner._last_logfile = str(logfile)
    runner._sleep_inhibit.stop = lambda: None
    observed = runner.poll(request)
    assert observed is not None and not observed.ok
    assert runner._assessment_ready
    assert may_have_erased(observed.reason), observed.reason
    recovery = recovery_for_view(VIEWS[observed.reason])
    assert recovery is not None
    assert recovery.meaning != MEANING_UNCHANGED
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None


@pytest.mark.parametrize(
    "forged_prefix", ("info: ", "INFO: ", "iNfO:\t", "\tinfo: ", "[x] ", "[2026] ", "[] ")
)
@pytest.mark.parametrize("exit_code", (0, 1))
def test_short_optional_prefix_cannot_authenticate_a_model_continuation(
    forged_prefix, exit_code
):
    model = "X\n" + forged_prefix + "/dev/sda is reported as IN USE"
    assert len(model.encode("ascii")) <= 40
    log = STAMP + "/dev/sda, ATA, " + model + "\n"
    ok, _summary, reason = completion_for_method(
        exit_code, log, "/dev/sda", MethodId.EVERYDAY
    )
    assert not ok and may_have_erased(reason), reason


@pytest.mark.parametrize(
    "native_prefix",
    (
        STAMP,
        "[2026/10/17 12:00:00] INFO: ",
        "\t[2026/10/17 12:00:00]\tinfo:\t",
    ),
)
@pytest.mark.parametrize("template,legacy_reason", GUARDS)
@pytest.mark.parametrize("exit_code", (0, 1))
@pytest.mark.parametrize("genuine", (False, True))
def test_timestamp_record_mode_preserves_supported_prefix_forms(
    native_prefix, template, legacy_reason, exit_code, genuine
):
    guard = template.format(device="/dev/sda")
    if genuine:
        log = native_prefix + "/dev/sda, ATA, Ordinary model\n"
        log += native_prefix + guard + "\n"
    else:
        model = "X\n" + guard
        assert len(model.encode("ascii")) <= 40
        log = native_prefix + "/dev/sda, ATA, " + model + "\n"
    ok, _summary, reason = completion_for_method(
        exit_code, log, "/dev/sda", MethodId.EVERYDAY
    )
    assert not ok
    if genuine:
        assert reason == legacy_reason
    else:
        assert may_have_erased(reason), reason


def test_projected_native_context_consumes_the_existing_evidence_byte_budget(
    tmp_path, monkeypatch
):
    context = STAMP + "Ordinary engine record " + "c" * 120 + "\n"
    raw = context + "Unable to open device '/dev/sda'.\n"
    raw += ("p" * 65535 + "\n") * 18
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_text(raw, encoding="ascii")
    monkeypatch.setattr(
        runner_module, "NWIPE_COMPLETION_EVIDENCE_BYTES", len(context.encode("ascii")) - 1
    )
    runner = runner_module.NwipeRunner()
    assert runner._scan_completion_log(
        str(logfile), "/dev/sda", runner_module._log_signature(logfile.stat())
    ) is None


def test_projected_native_context_retains_its_original_record_order(tmp_path):
    first = "Nwipe was aborted by the user\n"
    context = STAMP + "Ordinary engine record\n"
    guard = "Unable to open device '/dev/sda'.\n"
    padding = ("p" * 65535 + "\n") * 18
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_text(first + context + guard + padding, encoding="ascii")
    runner = runner_module.NwipeRunner()
    projection = runner._scan_completion_log(
        str(logfile), "/dev/sda", runner_module._log_signature(logfile.stat())
    )
    assert projection is not None
    assert projection == first + context + guard
