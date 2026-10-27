"""Damaged later target progress cannot reuse stale terminal proof."""

from types import SimpleNamespace

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, WipeRequest


def completed(method):
    spec = METHODS[method]
    phase = "writing" if spec.verify == "off" else "verifying"
    return (f"/dev/sda: 100.00%, round 1 of 1, pass {spec.overwrite_passes} of "
            f"{spec.overwrite_passes}, eta 00:00:00, [{phase}]\n")


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("prefix", ["", "[2026/10/25 00:00:00] info: "])
@pytest.mark.parametrize("damaged", [
    "010.00%, round 1 of 1, pass 1 of",
    "010.00%, round 1 of",
    "010.00%, round 0 of 1, pass 1 of 1",
    "010.00%, round 1 of 1, pass 2 of 1",
    "101.00%, round 1 of 1, pass 1 of 1",
    "100.00000000000000001%, round 1 of 1, pass 1 of 1",
    "NaN%, round 1 of 1, pass 1 of 1",
    "010.00, round 1 of 1, pass 1 of 1",
    "010.00%, round 1 of 1, pass 1 of 1, eta damaged, [verifying]",
])
def test_poll_refuses_stale_completion_after_damaged_progress(monkeypatch, method, prefix, damaged):
    text = completed(method) + prefix + "/dev/sda: " + damaged + "\n"
    runner = module.NwipeRunner()
    runner._proc = SimpleNamespace(poll=lambda: 0)
    monkeypatch.setattr(runner, "_refresh_progress", lambda *_a, **_kw: None)
    monkeypatch.setattr(runner, "_read_log_tail", lambda *_a: text)
    monkeypatch.setattr(runner, "_release_wipe_lock", lambda: None)
    monkeypatch.setattr(module, "_try_log_diag", lambda *_a: None)
    result = runner.poll(WipeRequest("/dev/sda", method, "/dev/sdz", "/inert/log"))
    assert result is not None and not result.ok
    assert result.reason == "completion_missing"
    assert module.logged_last_pass_total(text, "/dev/sda", require_verifying=method != MethodId.QUICK_ZERO) is None


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("later", [
    "/dev/sdb: 010.00%, round 1 of 1, pass 1 of\n",
    "/dev/sda: Success\n",
    "diagnostic output after completion\n",
])
def test_unrelated_or_nonprogress_records_preserve_completion(method, later):
    assert module.completion_for_method(0, completed(method)+later, "/dev/sda", method)[0]


@pytest.mark.parametrize("method", list(MethodId))
def test_later_valid_final_sample_supersedes_damage(method):
    text = completed(method) + "/dev/sda: 010.00%, round 1 of\n" + completed(method)
    assert module.completion_for_method(0, text, "/dev/sda", method)[0]


@pytest.mark.parametrize("method", list(MethodId))
def test_erased_table_remains_independent_proof(method):
    text = (completed(method) + "/dev/sda: 010.00%, round 1 of\n"
            + module.NWIPE_DRIVE_STATUS_HEADER + "\n"
            + "     sda | Erased | 100 MB/s | 00:00:01 |\n")
    assert module.completion_for_method(0, text, "/dev/sda", method)[0]


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("has_table", [False, True])
def test_completion_projection_keeps_last_damaged_progress(tmp_path, method, has_table):
    text = completed(method) + "diagnostic output\n" * 1000
    text += "/dev/sda: 010.00%, round 1 of 1, pass 1 of\n"
    if has_table:
        text += module.NWIPE_DRIVE_STATUS_HEADER + "\n     sda | Erased | 100 MB/s | 00:00:01 |\n"
    logfile = tmp_path / "engine.log"
    logfile.write_text(text)
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat()),
    )
    assert projected is not None and "pass 1 of\n" in projected
    assert module.completion_for_method(0, projected, "/dev/sda", method)[0] is has_table
