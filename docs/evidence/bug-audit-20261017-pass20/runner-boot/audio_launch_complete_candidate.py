"""Fake-only constructor/start interruption ownership and retry proof."""
import pytest
from beamo_wipe import audio_jobs


@pytest.mark.parametrize("stage", ("construct", "start-before", "start-after"))
@pytest.mark.parametrize("protected", (False, True))
@pytest.mark.parametrize("failure", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_rejected_launch_releases_ticket_and_allows_retry(monkeypatch, stage, protected, failure):
    constructed = []
    actions = []

    class FakeThread:
        def __init__(self, *, target, name, daemon):
            assert name == "beamo-audio" and daemon is True
            self.target = target
            self.first = not constructed
            self.handed_off = False
            constructed.append(self)
            if self.first and stage == "construct":
                raise failure("controlled launch rejection")

        def start(self):
            if self.first:
                self.handed_off = stage == "start-after"
                raise failure("controlled launch rejection")

        def join(self, timeout):
            assert timeout == 0.6

    monkeypatch.setattr(audio_jobs.threading, "Thread", FakeThread)
    worker = audio_jobs.AudioWorker()
    try:
        if failure is RuntimeError:
            rejected = worker.submit(lambda: actions.append("rejected"), protected=protected)
            ready, value = rejected.poll()
            assert ready and isinstance(value, RuntimeError)
        else:
            with pytest.raises(failure, match="controlled launch rejection"):
                worker.submit(lambda: actions.append("rejected"), protected=protected)
        if constructed[0].handed_off:
            constructed[0].target()
        assert actions == []
        assert worker._pending is None and worker._pending_outcome is None
        following = worker.submit(lambda: actions.append("following"), protected=not protected)
        assert not following.poll()[0]
        assert len(constructed) == 2, "Rejected launch stranded the worker slot"
        assert worker._thread is constructed[1]
        assert actions == []
    finally:
        worker.close()
