"""Rejected worker launches cannot consume a replacement worker's audio queue."""
import threading

import pytest

from beamo_wipe import audio_jobs


@pytest.mark.parametrize('rejected_protected', [False, True])
@pytest.mark.parametrize('active_protected', [False, True])
@pytest.mark.parametrize('next_protected', [False, True])
def test_start_error_after_spawn_never_leaves_a_competing_worker(monkeypatch, rejected_protected, active_protected, next_protected):
    real_thread = threading.Thread
    old_gate, active_entered, next_entered, release = [threading.Event() for _ in range(4)]
    threads, rejected_actions = [], []

    class StartedThenRaised(real_thread):
        def __init__(self, *args, **kwargs):
            first = not threads
            target = kwargs['target']
            if first:
                def delayed():
                    assert old_gate.wait(2)
                    target()
                kwargs['target'] = delayed
            super().__init__(*args, **kwargs)
            self.first = first
            threads.append(self)

        def start(self):
            super().start()
            if self.first:
                raise RuntimeError('controlled start error after owned spawn')

    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs.threading, 'Thread', StartedThenRaised)
    try:
        rejected = worker.submit(lambda: rejected_actions.append(True), protected=rejected_protected)
        ready, value = rejected.poll()
        assert ready and isinstance(value, RuntimeError)

        def active():
            active_entered.set()
            assert release.wait(2)
            return 'active'

        def following():
            next_entered.set()
            return 'following'

        worker.submit(active, protected=active_protected)
        assert active_entered.wait(1)
        old_gate.set()
        worker.submit(following, protected=next_protected)
        overlapped = next_entered.wait(0.1)
        assert not rejected_actions
        assert not overlapped, 'Two audio actions ran together after rejected launch'
        release.set()
        assert next_entered.wait(1)
    finally:
        old_gate.set()
        release.set()
        worker.close()
        for thread in threads:
            thread.join(2)
        assert all(not thread.is_alive() for thread in threads)


@pytest.mark.parametrize('protected', [False, True])
def test_launch_refused_before_spawn_can_retry(monkeypatch, protected):
    real_thread = threading.Thread

    class Refused(real_thread):
        def start(self):
            raise RuntimeError('controlled refusal before spawn')

    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs.threading, 'Thread', Refused)
    try:
        first = worker.submit(lambda: 'rejected', protected=protected)
        ready, value = first.poll()
        assert ready and isinstance(value, RuntimeError)
        monkeypatch.setattr(audio_jobs.threading, 'Thread', real_thread)
        done = threading.Event()
        worker.submit(lambda: done.set(), protected=protected)
        assert done.wait(1)
    finally:
        worker.close()
