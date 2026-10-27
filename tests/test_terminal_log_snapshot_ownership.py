"""Progress refresh cannot replace terminal evidence with its smaller tail."""

from types import SimpleNamespace

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


TERMINAL = ("/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n"
            + "later diagnostic output\n" * 450)
PROGRESS = TERMINAL[-module.NWIPE_PROGRESS_LOG_BYTES:]


@pytest.mark.parametrize("state", ["finalizing", "_assessment_ready"])
@pytest.mark.parametrize("already_published", [False, True])
def test_progress_respects_terminal_snapshot(monkeypatch, state, already_published):
    runner = module.NwipeRunner()
    runner._proc = object()
    reads = []

    def read(*_args):
        reads.append(True)
        setattr(runner, state, True)
        runner._log_tail = TERMINAL
        return PROGRESS

    monkeypatch.setattr(runner, "_read_log_tail", read)
    if already_published:
        setattr(runner, state, True)
        runner._log_tail = TERMINAL
    runner._refresh_progress("/inert/log", "/dev/sda")
    assert runner._log_tail == TERMINAL
    assert len(reads) == (0 if already_published else 1)


def test_normal_progress_still_updates_tail(monkeypatch):
    runner = module.NwipeRunner()
    runner._proc = object()
    monkeypatch.setattr(runner, "_read_log_tail", lambda *_args: PROGRESS)
    runner._refresh_progress("/inert/log", "/dev/sda")
    assert runner._log_tail == PROGRESS


def test_progress_during_terminal_assessment_preserves_export_proof(monkeypatch):
    runner = module.NwipeRunner()
    runner._proc = SimpleNamespace(poll=lambda: 0)
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sdz", "/inert/log")
    monkeypatch.setattr(runner, "_read_log_tail", lambda _path, size: (
        PROGRESS if size == module.NWIPE_PROGRESS_LOG_BYTES else TERMINAL
    ))
    monkeypatch.setattr(runner, "_release_wipe_lock", lambda: None)
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    original = module.completion_for_method

    def assess(*args):
        runner._refresh_progress(request.logfile, request.device)
        return original(*args)

    monkeypatch.setattr(module, "completion_for_method", assess)
    result = runner.poll(request)
    assert result is not None and result.ok
    assert runner._assessment_log_text == TERMINAL
    assert runner._log_tail == TERMINAL
    assert original(result.exit_code, runner._log_tail, request.device, request.method)[0]
