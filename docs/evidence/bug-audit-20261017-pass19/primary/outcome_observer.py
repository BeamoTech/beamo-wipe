"""Bounded diagnostic prefix and immediate failure receipt; no monkeypatching."""
import json
from pathlib import Path
import sys
import threading
import traceback

rows = []
selection = {}


def pytest_collection_modifyitems(config, items):
    last = max(i for i, item in enumerate(items)
               if item.nodeid.startswith('tests/test_checkrow_trace_lifetime_pass18.py::')) + 1
    removed = items[last:]
    selection.update(total=len(items), retained=last, deselected=len(removed),
                     last=items[last - 1].nodeid)
    items[:] = items[:last]
    config.hook.pytest_deselected(items=removed)


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
    with Path('/tmp/pass19-primary/prefix-failures.jsonl').open('a') as log:
        log.write(json.dumps(row) + '\n')


def pytest_sessionfinish(session, exitstatus):
    Path('/tmp/pass19-primary/prefix-outcome.json').write_text(
        json.dumps(dict(exit_code=exitstatus, failures=rows, selection=selection), indent=2) + '\n')
