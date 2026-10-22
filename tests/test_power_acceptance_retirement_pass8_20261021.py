"""Rejected power workers cannot publish data as a later accepted sample."""
import json

import pytest

from beamo_wipe import power


@pytest.fixture
def controlled_workers(monkeypatch):
    events, threads, readings = [], [], []
    state = {"failure": None, "stage": "accept-after", "active": None}
    old = power.PowerStatus(ac=True, batteries=(99,), complete=True)
    fresh = power.PowerStatus(ac=False, batteries=(10,), complete=True)

    class Event:
        def __init__(self):
            self.flag = False
            self.first_allowed = len(events) == 1
            events.append(self)

        def set(self):
            failing = self.first_allowed and state["failure"] is not None
            if failing and state["stage"] == "accept-before":
                raise state["failure"]("Fake pre-acceptance interruption")
            self.flag = True
            if failing and state["stage"] == "accept-after":
                raise state["failure"]("Fake post-acceptance interruption")

        def clear(self):
            self.flag = False

        def is_set(self):
            return self.flag

        def wait(self):
            assert self.flag, "This proof must never wait on a real thread"

    class Thread:
        def __init__(self, *, target, daemon, name):
            assert daemon and name == "beamo-power"
            self.target = target
            self.index = len(threads)
            threads.append(self)
            if self.index == 0 and state["stage"] == "construct":
                raise state["failure"]("Fake constructor interruption")

        def start(self):
            if self.index == 0 and state["stage"] in {"start-before", "start-after"}:
                raise state["failure"]("Fake start interruption")

        def run(self):
            state["active"] = self.index
            self.target()

    def reader():
        readings.append(state["active"])
        return old if state["active"] == 0 else fresh

    monkeypatch.setattr(power.threading, "Event", Event)
    monkeypatch.setattr(power.threading, "Thread", Thread)
    return state, threads, readings, power.PowerMonitor(reader), old, fresh


@pytest.mark.parametrize("failure", [None, RuntimeError, KeyboardInterrupt, SystemExit],
                         ids=["normal", "runtime", "interrupt", "exit"])
@pytest.mark.parametrize("delivery", ["before-retry", "after-retry"])
@pytest.mark.parametrize("old_ac", [True, False], ids=["old-connected", "old-disconnected"])
def test_post_acceptance_interruption_cannot_supply_the_next_reading(
    controlled_workers, request, failure, delivery, old_ac,
):
    state, threads, readings, monitor, old, fresh = controlled_workers
    state["failure"] = failure
    # Both directions are meaningful: a stale good reading hides a warning,
    # while a stale disconnected reading can show an unnecessary warning.
    old = power.PowerStatus(ac=old_ac, batteries=(99,), complete=True)
    monitor.reader = lambda: (
        readings.append(state["active"]) or (old if state["active"] == 0 else fresh)
    )
    monitor.tick(0.0)
    if delivery == "before-retry" or failure is None:
        threads[0].run()
    monitor.tick(0.1)
    assert monitor.status.ac is (old_ac if failure is None else None)
    monitor.tick(power.REFRESH_SECONDS + 0.1)
    assert len(threads) == 2 and monitor.pending
    if failure is not None and delivery == "after-retry":
        threads[0].run()
    monitor.tick(power.REFRESH_SECONDS + 0.2)
    request.node.user_properties.append(("power_retry_trace", json.dumps({
        "failure": failure.__name__ if failure else None,
        "delivery": delivery, "old_ac": old_ac,
        "readings": readings, "reported_ac": monitor.status.ac,
        "pending": monitor.pending,
    })))
    assert monitor.status.ac is (old_ac if failure is None else None)
    assert monitor.pending
    assert readings == ([0] if failure is None else [])
    threads[1].run()
    monitor.tick(power.REFRESH_SECONDS + 0.3)
    assert monitor.status is fresh
    assert readings == ([0, 1] if failure is None else [1])
    assert not monitor.pending and monitor._results.empty()


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("stage", ["construct", "start-before", "start-after", "accept-before"])
def test_rejection_before_acceptance_preserves_a_clean_retry(controlled_workers, failure, stage):
    state, threads, readings, monitor, _old, fresh = controlled_workers
    state.update(failure=failure, stage=stage)
    monitor.tick(0.0)
    assert not monitor.pending and monitor.status.ac is None
    if stage != "construct":
        threads[0].run()
    assert readings == [] and monitor._results.empty()
    monitor.tick(power.REFRESH_SECONDS)
    assert monitor.pending and len(threads) == 2
    threads[1].run()
    monitor.tick(power.REFRESH_SECONDS + 0.1)
    assert monitor.status is fresh and readings == [1]
    assert not monitor.pending and monitor._results.empty()
