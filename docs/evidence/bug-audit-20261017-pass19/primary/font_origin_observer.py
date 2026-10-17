"""Bounded diagnostic prefix and immediate failure receipt; no monkeypatching."""
import json
from pathlib import Path
import sys
import threading
import traceback

rows = []
selection = {}




def pytest_runtest_logreport(report):
    if not report.failed:
        return
    frames = sys._current_frames()
    threads = [dict(name=thread.name, ident=thread.ident, alive=thread.is_alive(),
                    stack=[dict(file=s.filename, line=s.lineno, function=s.name)
                           for s in traceback.extract_stack(frames[thread.ident])])
               for thread in threading.enumerate() if thread.ident in frames]
    row = dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
               failure=str(report.longrepr), threads=threads)
    rows.append(row)
    with Path('/tmp/pass19-primary/font-origin-failures.jsonl').open('a') as log:
        log.write(json.dumps(row) + '\n')


def pytest_sessionfinish(session, exitstatus):
    Path('/tmp/pass19-primary/font-origin-outcome.json').write_text(
        json.dumps(dict(exit_code=exitstatus, failures=rows, selection=selection), indent=2) + '\n')


# Scalar provenance only: no Font/Tk/root/frame objects are retained.
_font_origins = {}
_font_log = None
_original_font_init = None
_original_font_del = None


def _font_event(event, font):
    import os
    import threading
    row = dict(event=event, font_id=id(font),
               name=getattr(font, 'name', None),
               delete_font=getattr(font, 'delete_font', None),
               thread=threading.get_ident())
    if event == 'created':
        row['creation_stack'] = [dict(file=f.filename, line=f.lineno, function=f.name)
                                 for f in traceback.extract_stack()[:-2]]
        _font_origins[id(font)] = row
    else:
        row['origin'] = _font_origins.get(id(font))
    try:
        _font_log.write(json.dumps(row) + '\n')
        _font_log.flush()
    except (OSError, ValueError):
        pass


def pytest_sessionstart(session):
    global _font_log, _original_font_init, _original_font_del
    import tkinter.font as font_module
    _font_log = Path('/tmp/pass19-primary/font-origin-events.jsonl').open('x')
    _original_font_init = font_module.Font.__init__
    _original_font_del = font_module.Font.__del__

    def observed_init(self, *args, **kwargs):
        _original_font_init(self, *args, **kwargs)
        _font_event('created', self)

    def observed_del(self):
        try:
            _font_event('delete-enter', self)
        finally:
            _original_font_del(self)
        _font_event('delete-exit', self)

    font_module.Font.__init__ = observed_init
    font_module.Font.__del__ = observed_del


_original_sessionfinish = pytest_sessionfinish


def pytest_sessionfinish(session, exitstatus):
    import tkinter.font as font_module
    font_module.Font.__init__ = _original_font_init
    font_module.Font.__del__ = _original_font_del
    try:
        _original_sessionfinish(session, exitstatus)
    finally:
        _font_log.close()
