"""Pinned status predicates reject malformed whitespace without quadratic work."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from negative_gate_child import owned_gate_child


pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="bounded parser child uses the POSIX negative-gate owner"
)


@pytest.mark.parametrize("predicate_name,line,expected", [
    ("_status_column_has_name", "      sda | Erased | 1MB/s | 00:00:01 |", True),
    ("_status_column_has_name", " \t!  sda | Erased |", True),
    ("_status_column_has_name", "  sdb | Erased |", False),
    ("_status_column_has_name", "ordinary message", False),
    ("_status_failure_has_name", "      sda |-FAILED-|", True),
    ("_status_failure_has_name", " \t! sda | UABORTED |", True),
    ("_status_failure_has_name", "  sda | Erased |", False),
    ("_status_failure_has_name", "ordinary message", False),
    ("NWIPE_ERROR_ROW_RE", "      fake | 0 | 0 | 0", True),
    ("NWIPE_ERROR_ROW_RE", " \t! fake | 1 | 2 | 3", True),
    ("NWIPE_ERROR_ROW_RE", " fake | ordinary message", False),
    ("_target_reported_success", "      fake | Erased | 1MB/s | 00:00:01 |", True),
    ("_target_reported_success", " \t! fake | Erased | 1MB/s | 00:00:01 |", True),
    ("_target_reported_success", " fake | Erased |\r\t1MB/s | 00:00:01 |", True),
    ("_target_reported_success", " fake | Erased |\r\r 1 MB/s | 00:00:01 |", True),
    ("_target_reported_success", " fake | Erased |\u2028 1MB/s | 00:00:01 |", True),
    ("_target_reported_success", " fake | Erased |   /s | 00:00:01 |", True),
    ("_target_reported_success", " fake | Erased |1MB/s | malformed timing |", False),
    ("_target_reported_success", " fake |-FAILED-|", False),
    ("_target_reported_success", "ordinary message", False),
])
def test_status_predicate_normal_controls(predicate_name, line, expected):
    from beamo_wipe import nwipe_runner

    if predicate_name == "NWIPE_ERROR_ROW_RE":
        assert (nwipe_runner.NWIPE_ERROR_ROW_RE.match(line) is not None) is expected
    elif predicate_name == "_target_reported_success":
        text = nwipe_runner.NWIPE_DRIVE_STATUS_HEADER + "\n" + line + "\n"
        assert nwipe_runner._target_reported_success(text, "/dev/fake") is expected
    else:
        predicate = getattr(nwipe_runner, predicate_name)
        assert predicate(line, "sda") is expected


CHILD = r"""
from pathlib import Path
import sys
import time
from beamo_wipe import nwipe_runner

ready, trigger = Path(sys.argv[2]), Path(sys.argv[3])
if sys.argv[1] == 'NWIPE_ERROR_ROW_RE':
    # Exercise the raw error-row regex through its reachable completion caller.
    # A matching target prefix passes _status_column_has_name immediately;
    # malformed numeric columns expose the overlapping whitespace quantifiers.
    def predicate(line):
        return nwipe_runner._target_error_summary_conflict(
            'Error Summary\n' + line + '\n', '/dev/fake')
    assert predicate('      fake | 0 | 0 | 0') == ''
    assert predicate('fake | ordinary message') == 'indeterminate'
    expected = 'indeterminate'
    suffix = 'fake | ordinary message'
elif sys.argv[1] in {'failure-status-prefix', 'failure-status-rate', 'failure-status-timing'}:
    def predicate(line):
        text = ('[2026/10/24 12:00:00] info: fixture\n' +
                nwipe_runner.NWIPE_DRIVE_STATUS_HEADER + '\n' + line + '\n')
        return next(trusted for record, trusted in
                    nwipe_runner._iter_negative_log_lines(text) if record == line)
    assert predicate('      fake |-FAILED-| 1MB/s | 00:00:01 |') is True
    assert predicate('ordinary message') is False
    expected = False
    suffix = 'ordinary message'
elif sys.argv[1] in {'_target_reported_success', 'success-throughput-padding',
                     'success-throughput-timing'}:
    def predicate(line):
        return nwipe_runner._target_reported_success(
            nwipe_runner.NWIPE_DRIVE_STATUS_HEADER + '\n' + line + '\n',
            '/dev/fake')
    assert predicate('      fake | Erased | 1MB/s | 00:00:01 |') is True
    assert predicate('ordinary message') is False
    expected = False
    suffix = 'ordinary message'
else:
    target_predicate = getattr(nwipe_runner, sys.argv[1])
    def predicate(line):
        return target_predicate(line, 'sda')
    positive = ('      sda | Erased | 1MB/s | 00:00:01 |'
                if sys.argv[1] == '_status_column_has_name'
                else '      sda |-FAILED-|')
    assert predicate(positive) is True
    assert predicate('ordinary message') is False
    expected = False
    suffix = 'ordinary message'
ready.write_text('ready', encoding='ascii')
deadline = time.monotonic() + 15
while not trigger.exists():
    if time.monotonic() >= deadline:
        raise RuntimeError('parent did not trigger the owned parser fixture')
    time.sleep(0.005)
if sys.argv[1] == 'failure-status-rate':
    malformed = 'fake |-FAILED-|' + ' ' * 65535 + 'ordinary message'
elif sys.argv[1] == 'failure-status-timing':
    malformed = 'fake |-FAILED-|' + ' ' * 65535 + '1MB/s | malformed timing'
elif sys.argv[1] == 'success-throughput-padding':
    malformed = 'fake | Erased |' + ' ' * 65535 + 'ordinary message'
elif sys.argv[1] == 'success-throughput-timing':
    malformed = 'fake | Erased |' + ' ' * 65535 + '1MB/s | malformed timing'
else:
    malformed = ' ' * 65535 + suffix
assert predicate(malformed) == expected
print('malformed status rejected', flush=True)
"""


@pytest.mark.parametrize("predicate_name", [
    "_status_column_has_name", "_status_failure_has_name",
    "NWIPE_ERROR_ROW_RE", "_target_reported_success",
    "success-throughput-padding", "success-throughput-timing",
    "failure-status-prefix", "failure-status-rate", "failure-status-timing",
])
def test_status_predicate_large_whitespace_is_bounded(tmp_path, predicate_name):
    # Child import/startup is outside the compute deadline. Only a regular
    # fixture file releases computation after the parent observes readiness.
    ready, trigger = tmp_path / "ready", tmp_path / "trigger"
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    previous_pythonpath = env.get("PYTHONPATH")
    source_path = str(root / "src")
    env["PYTHONPATH"] = (
        source_path if previous_pythonpath is None
        else source_path + os.pathsep + previous_pythonpath
    )
    with owned_gate_child(
        [sys.executable, "-c", CHILD, predicate_name, str(ready), str(trigger)],
        cwd=root,
        env=env,
    ) as proc:
        deadline = time.monotonic() + 15
        while not ready.exists():
            if proc.poll() is not None:
                try:
                    output, _ = proc.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    pytest.fail("parser child exited but its output did not close in 1 second")
                pytest.fail(
                    f"owned parser child exited {proc.returncode} before readiness:\n"
                    + output[-2000:]
                )
            if time.monotonic() >= deadline:
                pytest.fail("owned parser child did not become ready in 15 seconds")
            time.sleep(0.005)
        trigger.write_text("go", encoding="ascii")
        try:
            output, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pytest.fail("status predicate did not reject malformed whitespace in 5 seconds")
        assert proc.returncode == 0, output
        assert output.strip() == "malformed status rejected"
