"""Observe guard ownership at pytest boundaries without changing fixtures."""
import json
from pathlib import Path
import subprocess

rows = []


def pytest_runtest_setup(item):
    rows.append(dict(nodeid=item.nodeid, when="before-setup", fixtures=list(item.fixturenames)))


def pytest_runtest_logreport(report):
    code = getattr(subprocess.Popen, "__code__", None)
    rows.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                     popen_source=code.co_filename if code is not None else "native class"))


def pytest_sessionfinish(session, exitstatus):
    Path('/tmp/pass19-primary/guard-prefix-observations.json').write_text(
        json.dumps(dict(exit_code=exitstatus, rows=rows), indent=2) + '\n')
