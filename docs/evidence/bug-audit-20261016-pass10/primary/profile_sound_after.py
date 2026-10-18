"""Measure unmodified GTK regressions; no device or real sound operations."""
import functools
import json
import resource
import sys
import threading
import time
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / 'src'))
sys.path.insert(0, str(root / 'tests'))
import pytest
from beamo_wipe.ui.sound_dialog import SoundDialog
from beamo_wipe.audio_jobs import AudioWorker
from beamo_wipe.ui.accessible_wizard import Gtk

records = []
current_test = None

def measured(owner, name, label):
    original = getattr(owner, name)
    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        start = time.perf_counter_ns()
        cpu = time.thread_time_ns()
        before = resource.getrusage(resource.RUSAGE_THREAD)
        try:
            return original(*args, **kwargs)
        finally:
            end = time.perf_counter_ns()
            after = resource.getrusage(resource.RUSAGE_THREAD)
            records.append({'test': current_test, 'call': label,
                'thread': threading.current_thread().name,
                'wall_ms': (end-start)/1e6,
                'thread_cpu_ms': (time.thread_time_ns()-cpu)/1e6,
                'voluntary_switches': after.ru_nvcsw-before.ru_nvcsw,
                'involuntary_switches': after.ru_nivcsw-before.ru_nivcsw})
    setattr(owner, name, wrapped)

for cls, name in [(SoundDialog,'__init__'),(SoundDialog,'_submit'),
                  (SoundDialog,'_discover'),(AudioWorker,'submit')]:
    measured(cls,name,cls.__name__+'.'+name)
measured(Gtk.Widget,'show_all','Gtk.Widget.show_all')

class Measurements:
    def pytest_runtest_setup(self,item):
        global current_test
        current_test=item.nodeid
    def pytest_runtest_logreport(self,report):
        if report.when=='call':
            records.append({'test':report.nodeid,'outcome':report.outcome,'duration_s':report.duration})
    def pytest_sessionfinish(self,session,exitstatus):
        Path('/tmp/pass10-primary/sound-profile-after.json').write_text(json.dumps({'pytest_exit':int(exitstatus),'records':records},indent=2)+'\n')

args=['-o','addopts=','-q','tests/test_accessible_runtime.py','-k',
      'sound_check_dialog or slow_sound_discovery or done_auto_plays_once',
      '--junitxml=/tmp/pass10-primary/sound-profile-after.xml']
raise SystemExit(pytest.main(args,plugins=[Measurements()]))
