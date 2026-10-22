"""Finite queue model: three submissions, protected lanes, cancellation, close.
All worker threads are captured callbacks; no OS thread/process/device executes.
"""
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json
from beamo_wipe import audio_jobs

traces = []
counts = dict(states=0, accepted_actions=0, cancelled_tickets=0, closed_refusals=0, native_callbacks=0)
class CapturedThread:
    def __init__(self, *, target, name, daemon):
        assert name == 'beamo-audio' and daemon
        self.target = target
    def start(self): pass
    def join(self, timeout): assert timeout == 0.6

for lanes in product((False, True), repeat=3):
    for cancelled in product((False, True), repeat=3):
        for close_first in (False, True):
            counts['states'] += 1
            actions, tickets = [], []
            with patch.object(audio_jobs.threading, 'Thread', CapturedThread):
                worker = audio_jobs.AudioWorker()
                for n, protected in enumerate(lanes):
                    tickets.append(worker.submit(lambda n=n: actions.append(n) or n, protected=protected))
                thread = worker._thread
                for n, cancel in enumerate(cancelled):
                    if cancel: tickets[n].cancel()
                expected = []
                if close_first:
                    worker.close()
                    counts['closed_refusals'] += 1
                else:
                    for lane in (True, False):
                        candidates = [n for n in range(3) if lanes[n] is lane]
                        if candidates and not cancelled[candidates[-1]]:
                            expected.append(candidates[-1])
                def retire(timeout):
                    assert timeout == 1.0
                    worker._closed = True
                worker._condition.wait = retire
                assert thread is not None
                thread.target()
                assert actions == expected, (lanes, cancelled, close_first, actions, expected)
                assert worker._active is None
                for n, ticket in enumerate(tickets):
                    if n in expected:
                        assert ticket.poll() == (True, n)
                        counts['accepted_actions'] += 1
                    else:
                        assert ticket.cancelled.is_set()
                        assert ticket.poll() == (True, None)
                        counts['cancelled_tickets'] += 1
                worker.close()
                closed = worker.submit(lambda: (_ for _ in ()).throw(AssertionError('closed callback ran')))
                ready, value = closed.poll()
                assert ready and isinstance(value, RuntimeError)
                traces.append(dict(lanes=lanes, cancelled=cancelled, close_first=close_first, actions=actions))
result = dict(**counts, mismatches=[], scope='supporting fake-only finite model; counts overlap canonical tests')
output = Path(__file__).parent
(output / 'audio-queue-model.json').write_text(json.dumps(result, indent=2) + '\n')
(output / 'audio-queue-trace.json').write_text(json.dumps(traces, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
