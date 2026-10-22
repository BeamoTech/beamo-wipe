# SPDX-License-Identifier: GPL-3.0-or-later
"""A rejected startup thread must not run discovery behind a closed splash."""

from __future__ import annotations

import threading

import pytest

from beamo_wipe.startup_stages import STAGE_BOOT_USB, StartupRun


@pytest.mark.parametrize("error", [KeyboardInterrupt, SystemExit])
def test_native_thread_started_then_rejected_never_runs_builder(monkeypatch, error):
    calls: list[str] = []
    run = StartupRun(lambda report: calls.append("build") or object())
    real_start = threading.Thread.start

    def started_then_interrupted(worker):
        real_start(worker)
        raise error("startup launch interrupted")

    monkeypatch.setattr(threading.Thread, "start", started_then_interrupted)
    with pytest.raises(error, match="startup launch interrupted"):
        run.start()
    run.thread.join(timeout=1)

    assert not run.thread.is_alive()
    assert calls == []
    assert run.poll() is None


def test_interrupted_acceptance_wake_revokes_started_worker(monkeypatch):
    calls: list[str] = []
    run = StartupRun(lambda report: calls.append("build") or object())
    real_set = run._launch_decided.set

    def set_then_interrupt():
        real_set()
        raise KeyboardInterrupt("startup acceptance interrupted")

    monkeypatch.setattr(run._launch_decided, "set", set_then_interrupt)
    with pytest.raises(KeyboardInterrupt, match="startup acceptance interrupted"):
        run.start()
    run.thread.join(timeout=1)

    assert not run.thread.is_alive()
    assert calls == []
    assert run.poll() is None


def test_accepted_startup_worker_keeps_ordered_reports_and_outcome():
    wizard = object()

    def build(report):
        report(STAGE_BOOT_USB)
        return wizard

    run = StartupRun(build)
    run.start()
    run.thread.join(timeout=1)

    assert not run.thread.is_alive()
    assert run.poll() == ("wizard", wizard)
    assert run.stages.states[STAGE_BOOT_USB] == "done"
