"""Root-run candidate: rejected acceptance cannot authorize an old target.

Pure synchronous fake Events/Threads. _run is a sentinel; no audio action,
OS thread, process, UI or device can execute. This injects an exception after
the allowed flag's mutation, as asynchronous interruption can do.
"""

import pytest

from beamo_wipe import audio_jobs


@pytest.mark.parametrize("protected", (False, True))
@pytest.mark.parametrize("failure", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_failed_acceptance_rejects_handed_off_target(monkeypatch, protected, failure):
    events = []
    threads = []
    entered = []

    class FakeEvent:
        def __init__(self):
            self.flag = False
            self.reject = len(events) == 2  # ticket cancellation, decision, allowed
            events.append(self)

        def set(self):
            self.flag = True
            if self.reject:
                self.reject = False
                raise failure("controlled interruption after acceptance mutation")

        def clear(self):
            self.flag = False

        def is_set(self):
            return self.flag

        def wait(self):
            assert self.flag, "This probe never waits on an actual thread"

    class FakeThread:
        def __init__(self, *, target, name, daemon):
            assert name == "beamo-audio" and daemon is True
            self.target = target
            threads.append(self)

        def start(self):
            pass  # target handoff waits for the caller's final decision

        def join(self, timeout):
            assert timeout == 0.6

    monkeypatch.setattr(audio_jobs.threading, "Event", FakeEvent)
    monkeypatch.setattr(audio_jobs.threading, "Thread", FakeThread)
    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(worker, "_run", lambda: entered.append("old worker admitted"))
    try:
        if failure is RuntimeError:
            ticket = worker.submit(lambda: None, protected=protected)
            ready, value = ticket.poll()
            assert ready and isinstance(value, RuntimeError)
        else:
            with pytest.raises(failure, match="controlled interruption after acceptance mutation"):
                worker.submit(lambda: None, protected=protected)
        assert worker._thread is None
        threads[0].target()
        assert entered == [], "Rejected acceptance still authorized the old worker"
        following = worker.submit(lambda: None, protected=not protected)
        assert not following.poll()[0]
        assert len(threads) == 2 and worker._thread is threads[1]
    finally:
        worker.close()
