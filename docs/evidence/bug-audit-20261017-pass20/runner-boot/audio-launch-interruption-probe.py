"""Root-run candidate proof; no OS thread, subprocess, UI or device is created.

The fake Thread models a rejected start before/after target handoff. Its
rejected target is invoked only after submit's launch decision has completed.
RuntimeError controls preserve the current returned-ticket contract; control
interruptions must still propagate, while retiring the rejected worker slot.
"""

import pytest

from beamo_wipe import audio_jobs


@pytest.mark.parametrize("after_handoff", [False, True])
@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_rejected_audio_launch_retires_its_slot(monkeypatch, after_handoff, failure):
    constructed = []
    actions = []

    class FakeThread:
        def __init__(self, *, target, name, daemon):
            assert name == "beamo-audio" and daemon is True
            self.target = target
            self.first = not constructed
            self.handed_off = False
            constructed.append(self)

        def start(self):
            if self.first:
                self.handed_off = after_handoff
                raise failure("controlled audio thread start rejection")

        def join(self, timeout):
            assert timeout == 0.6

    monkeypatch.setattr(audio_jobs.threading, "Thread", FakeThread)
    worker = audio_jobs.AudioWorker()
    try:
        if failure is RuntimeError:
            rejected = worker.submit(lambda: actions.append("rejected"))
            ready, value = rejected.poll()
            assert ready and isinstance(value, RuntimeError)
        else:
            with pytest.raises(failure, match="controlled audio thread start rejection"):
                worker.submit(lambda: actions.append("rejected"))
        if constructed[0].handed_off:
            # The decision event is now set. A rejected handoff must never
            # enter _run or consume a future request, so this is synchronous.
            constructed[0].target()
        assert actions == []
        following = worker.submit(lambda: actions.append("following"))
        assert not following.poll()[0]
        assert len(constructed) == 2, "A rejected launch stranded the audio worker slot"
        assert worker._thread is constructed[1]
        assert actions == []
    finally:
        worker.close()
