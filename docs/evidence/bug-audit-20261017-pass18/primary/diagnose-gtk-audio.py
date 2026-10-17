"""One bounded observational replay; original source/assertions stay unchanged."""
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

root = Path.cwd()
out = Path('/tmp/pass18-primary')
assert sys.executable == '/tmp/beamo-pass18-python/bin/python3'
assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
assert os.environ.get('DISPLAY') not in {None, ':1', ':99'}
sys.path[:0] = [str(root / 'src'), str(root / 'tests')]
freeze = json.loads((out / 'source-freeze.json').read_text())
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
rows = []
barriers = []
reports = []
original_event = threading.Event


def observe(label, original):
    def wrapped(*args, **kwargs):
        wall, cpu, thread = time.perf_counter(), time.thread_time(), threading.get_ident()
        error = None
        try:
            return original(*args, **kwargs)
        except BaseException as exc:
            error = type(exc).__name__
            raise
        finally:
            rows.append(dict(label=label, thread=thread, started_wall=wall,
                             elapsed_wall=time.perf_counter() - wall,
                             elapsed_thread_cpu=time.thread_time() - cpu, error=error))
    return wrapped


class Barrier(original_event):
    def __init__(self, label):
        super().__init__()
        self.label = label

    def set(self):
        rows.append(dict(label=self.label + '.set', thread=threading.get_ident(), at=time.perf_counter()))
        return super().set()

    def wait(self, timeout=None):
        return observe(self.label + '.wait', super().wait)(timeout)


class Observations:
    @pytest.fixture(autouse=True)
    def measured(self, monkeypatch, request):
        if request.node.name != 'test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog':
            yield
            return
        import test_accessible_runtime as case
        from beamo_wipe.ui.accessible_wizard import AccessibleWizard
        from beamo_wipe.ui.sound_dialog import SoundDialog
        from beamo_wipe.audio_jobs import worker

        def event_factory():
            if len(barriers) < 2:
                event = Barrier('entered' if not barriers else 'release')
                barriers.append(event)
                return event
            return original_event()

        monkeypatch.setattr(threading, 'Event', event_factory)
        for cls, names in ((AccessibleWizard, ('open_sound_check', 'render', '_focus_active_window', 'tick')),
                           (SoundDialog, ('__init__', '_submit', '_discover', 'poll', '_destroyed'))):
            for name in names:
                monkeypatch.setattr(cls, name, observe(cls.__name__ + '.' + name, getattr(cls, name)))
        monkeypatch.setattr(worker, 'submit', observe('AudioWorker.submit', worker.submit))
        monkeypatch.setattr(case, 'drain', observe('GTK.drain', case.drain))
        try:
            yield
        finally:
            # Original first assertion is outside its release-finally. This
            # diagnostic owns the barrier cleanup even when that assertion fails.
            before = [event.is_set() for event in barriers]
            if len(barriers) == 2:
                barriers[1].set()
            deadline = time.monotonic() + 1
            while worker._active is not None and time.monotonic() < deadline:
                time.sleep(.005)
            rows.append(dict(label='diagnostic.cleanup', original_barrier_states=before,
                             active_worker_after_release=worker._active is not None))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        result = yield
        report = result.get_result()
        reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                            duration=report.duration, failure=str(report.longrepr) if report.failed else None))


targets = sys.argv[1:] or [
    'tests/test_accessible_runtime.py::test_sound_check_dialog_plays_test_and_switches_output',
    'tests/test_accessible_runtime.py::test_sound_check_dialog_reports_no_audio_and_orca_failure',
    'tests/test_accessible_runtime.py::test_sound_check_dialog_toggles_and_hears_outcome_sounds',
    'tests/test_accessible_runtime.py::test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog',
]
code = pytest.main(['-q', *targets, '--junitxml=' + str(out / 'audio-diagnostic.xml')], plugins=[Observations()])
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
(out / 'audio-diagnostic-observations.json').write_text(json.dumps(dict(
    exit_code=code, rows=rows, reports=reports, original_source_unchanged=len(freeze),
    original_assertions_unchanged=True, observer_only=True), indent=2) + '\n')
raise SystemExit(code)
