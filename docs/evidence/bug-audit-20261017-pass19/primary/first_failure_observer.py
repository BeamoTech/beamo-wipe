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
    with Path('/tmp/pass19-primary/full-first-failure-reports.jsonl').open('a') as log:
        log.write(json.dumps(row) + '\n')


def pytest_sessionfinish(session, exitstatus):
    Path('/tmp/pass19-primary/full-first-failure-outcome.json').write_text(
        json.dumps(dict(exit_code=exitstatus, failures=rows, selection=selection), indent=2) + '\n')
