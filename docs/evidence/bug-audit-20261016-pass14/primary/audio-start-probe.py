"""Fake-only launch-error probe; event actions perform no audio I/O."""
import hashlib
import json
from pathlib import Path
import threading
from beamo_wipe import audio_jobs

out=Path('/tmp/pass14-primary')
source=Path(audio_jobs.__file__)
real_thread=threading.Thread
old_gate=threading.Event()
a_enter=threading.Event()
b_enter=threading.Event()
release=threading.Event()
handles=[]
starts=[]

class StartedThenRaised(real_thread):
    def __init__(self, *args, **kwargs):
        target=kwargs['target']
        first=not handles
        if first:
            def delayed():
                assert old_gate.wait(2), 'owned old worker gate did not open'
                target()
            kwargs['target']=delayed
        super().__init__(*args, **kwargs)
        handles.append(self)
        self.first=first

    def start(self):
        super().start()
        starts.append(self.ident)
        if self.first:
            raise RuntimeError('injected error after owned worker starts')

worker=audio_jobs.AudioWorker()
threading.Thread=StartedThenRaised
trace={}
try:
    rejected=worker.submit(lambda: 'must never execute')
    ready,value=rejected.poll()
    assert ready and isinstance(value,RuntimeError)
    def a():
        a_enter.set()
        assert release.wait(2)
        return 'A'
    def b():
        b_enter.set()
        assert release.wait(2)
        return 'B'
    second=worker.submit(a)
    assert a_enter.wait(1)
    old_gate.set()
    third=worker.submit(b)
    b_started=b_enter.wait(0.15)
    trace={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rejected_ticket_ready':ready,'rejected_ticket_type':type(value).__name__,'spawned_worker_threads':len(handles),'first_started_action_active':a_enter.is_set() and not release.is_set(),'second_action_also_started':b_started,'prior_ticket_cancelled':second.cancelled.is_set(),'all_actions_fake':True}
finally:
    threading.Thread=real_thread
    old_gate.set()
    release.set()
    worker.close()
    for handle in handles:
        handle.join(2)
    trace['owned_threads_retired']=all(not h.is_alive() for h in handles)
(out/'audio-start-probe.json').write_text(json.dumps(trace,indent=2)+'\n')
print(json.dumps(trace,indent=2))
assert trace['owned_threads_retired']
assert not trace['second_action_also_started'], 'bounded audio worker ran two fake actions concurrently after launch error'
