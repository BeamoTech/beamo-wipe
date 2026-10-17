"""Observe the existing GTK latency assertions; never change their limits."""
import functools
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import pytest

TARGET = 'test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog'
rows = []
reports = []
barriers = []


def observe(label, original):
    @functools.wraps(original)
    def measured(*args, **kwargs):
        wall, cpu = time.perf_counter(), time.thread_time()
        thread = threading.get_ident()
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
    return measured


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    if item.name != TARGET:
        yield
        return
    from beamo_wipe.audio_jobs import AudioWorker
    from beamo_wipe.ui.accessible_wizard import AccessibleWizard
    from beamo_wipe.ui.sound_dialog import SoundDialog
    case = item.module
    original_event = threading.Event

    class Barrier(original_event):
        def set(self):
            rows.append(dict(label=('entered' if self is barriers[0] else 'release') + '.set',
                             thread=threading.get_ident(), at=time.perf_counter()))
            return super().set()

        def wait(self, timeout=None):
            label = 'entered' if self is barriers[0] else 'release'
            return observe(label + '.wait', super().wait)(timeout)

    def event_factory():
        if len(barriers) < 2:
            event = Barrier()
            barriers.append(event)
            return event
        return original_event()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(threading, 'Event', event_factory)
        for cls, names in (
            (AccessibleWizard, ('open_sound_check', 'render', '_focus_active_window', 'tick')),
            (SoundDialog, ('__init__', '_submit', '_discover', 'poll', '_destroyed')),
            (AudioWorker, ('submit', 'close')),
            (threading.Thread, ('start',)),
        ):
            for name in names:
                patch.setattr(cls, name, observe(cls.__name__ + '.' + name, getattr(cls, name)))
        patch.setattr(case, 'drain', observe('GTK.drain', case.drain))
        try:
            yield
        finally:
            rows.append(dict(label='observer.finally', barrier_states=[event.is_set() for event in barriers]))


def pytest_runtest_logreport(report):
    if report.nodeid.endswith('::' + TARGET):
        reports.append(dict(when=report.when, outcome=report.outcome, duration=report.duration,
                            failure=str(report.longrepr) if report.failed else None))


def pytest_sessionfinish(session, exitstatus):
    if not rows:
        return  # The separate Orca process never executes this target.
    root = Path.cwd()
    out = Path('/tmp/pass19-primary')
    freeze = json.loads((out / 'source-freeze.json').read_text())
    unchanged = all(hashlib.sha256((root / n).read_bytes()).hexdigest() == digest for n, digest in freeze.items())
    result = dict(observer_only=True, original_assertions_unchanged=True,
                  native_call_interception=False, source_unchanged=unchanged,
                  frozen_inputs=len(freeze), rows=rows, reports=reports,
                  orca_child=os.environ.get('BEAMO_TEST_ORCA_CHILD') == '1', suite_exit_code=exitstatus)
    (out / 'gtk-timing-observations.json').write_text(json.dumps(result, indent=2) + '\n')
