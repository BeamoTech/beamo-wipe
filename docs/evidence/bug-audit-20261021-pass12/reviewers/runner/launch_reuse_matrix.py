"""Bounded scripted-fake launch/reuse model; never invokes an engine or device."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from beamo_wipe import nwipe_runner as module
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError

ROOT = Path('/workspace/beamo-wipe')
OUT = Path(__file__).parent
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
os.environ.pop('BEAMO_WIPE_LIVE', None)
COUNTS = dict(states=0, accepted_generations=0, verified_success=0,
              negative_terminal=0, injected_refusals=0, retained_uncertain=0,
              duplicate_start_refusals=0, mismatched_poll_refusals=0,
              stale_generation_polls=0, clean_retries=0, native_callbacks=0)
TRACE = []


class FakeProcess:
    def __init__(self):
        self.returncode = None
        self.signals = []

    def poll(self):
        return self.returncode

    def send_signal(self, sig):
        self.signals.append(sig)

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9

    def wait(self, timeout):
        assert timeout <= 8
        assert self.returncode is not None
        return self.returncode


def refuse(action, error=SafetyError):
    try:
        action()
    except error:
        return
    raise AssertionError('expected refusal')


def terminal_text(target, method, terminal):
    spec = METHODS[method]
    phase = 'writing' if spec.verify == 'off' else 'verifying'
    row = f'{module.nwipe_status_device_field(target)} | Erased | 120MB/s | 00:01:00 | FAKE\n'
    complete = module.NWIPE_DRIVE_STATUS_HEADER + '\n' + row
    if terminal == 'complete':
        return complete
    if terminal == 'missing':
        return 'fake process exited without terminal evidence\n'
    if terminal == 'method_conflict':
        return (f'{target}: 100.00%, round 1 of 1, pass 1 of {spec.overwrite_passes + 1}, '
                f'eta 00:00:00, [{phase}]\n' + complete)
    if terminal == 'error':
        return f'Verification mismatch on {target}\n' + complete
    if terminal == 'unterminated':
        return complete.rstrip('\n')
    raise AssertionError(terminal)


for method, target, terminal, fault in itertools.product(
    list(MethodId), ['/dev/sda', '/dev/nvme0n100'],
    ['complete', 'missing', 'method_conflict', 'error', 'unterminated'],
    ['invalid_binary', 'log_prepare', 'known_exec', 'uncertain_spawn'],
):
    COUNTS['states'] += 1
    state = dict(method=method.value, target=target, terminal=terminal, fault=fault)
    with tempfile.TemporaryDirectory(prefix='beamo-pass12-runner-') as tmp:
        directory = Path(tmp)
        logfile = directory / 'engine.log'
        request = WipeRequest(target, method, '/dev/sr0', str(logfile))
        runner = module.NwipeRunner(str(directory / 'fake-engine'))
        processes = []

        def spawn(*args, **kwargs):
            assert kwargs['shell'] is False and kwargs['close_fds'] is True
            assert kwargs['pass_fds'] == (runner._lock_fd,)
            assert args[0][-1] == target
            proc = FakeProcess()
            processes.append(proc)
            return proc

        with patch('beamo_wipe.safety.default_log_dir', lambda: directory), \
             patch.object(module.subprocess, 'Popen', spawn):
            try:
                # The first failed launch is recoverable exactly when ownership
                # is known. Ambiguous spawn must retain both descriptors and
                # refuse replacement until the fake fixture owner retires them.
                original = runner.binary
                if fault == 'invalid_binary':
                    runner.binary = 'untrusted-relative-engine'
                    refuse(lambda: runner.start(request))
                    runner.binary = original
                elif fault == 'log_prepare':
                    with patch.object(module, 'truncate_log_file', side_effect=SafetyError('injected prepare refusal')):
                        refuse(lambda: runner.start(request))
                else:
                    error = (FileNotFoundError(2, 'injected exec refusal', original)
                             if fault == 'known_exec' else OSError('injected ambiguous parent spawn'))
                    with patch.object(module.subprocess, 'Popen', side_effect=error):
                        refuse(lambda: runner.start(request), OSError)
                COUNTS['injected_refusals'] += 1
                assert runner.result is None and runner._proc is None
                if fault == 'uncertain_spawn':
                    assert not runner.start_not_spawned()
                    held = (runner._lock_fd, runner._log_fd)
                    assert all(fd is not None for fd in held)
                    refuse(lambda: runner.start(request))
                    assert held == (runner._lock_fd, runner._log_fd)
                    COUNTS['retained_uncertain'] += 1
                    runner._release_wipe_lock()  # only fake process/ordinary files
                assert runner.start_not_spawned()

                old_proc = None
                for generation in range(3):
                    runner.start(request)
                    COUNTS['accepted_generations'] += 1
                    COUNTS['clean_retries'] += 1
                    assert runner.result is None and runner.progress is None
                    assert logfile.read_bytes() == b''
                    proc = runner._proc
                    assert proc is processes[-1]
                    if old_proc is not None:
                        assert runner.poll(request, expected_proc=old_proc) is None
                        assert runner._proc is proc and runner.result is None
                        COUNTS['stale_generation_polls'] += 1
                    progress = (f'{target}: 020.00%, round 1 of 1, pass 1 of {METHODS[method].overwrite_passes}, '
                                'eta 00:00:10, [writing]\n')
                    logfile.write_text(progress)
                    assert runner.poll(request) is None
                    assert runner.progress == 20 and runner.progress_observation.percent == 20
                    refuse(lambda: runner.start(request))
                    COUNTS['duplicate_start_refusals'] += 1
                    assert logfile.read_text() == progress
                    other = WipeRequest(target, method, '/dev/sr0', str(directory / 'other.log'))
                    refuse(lambda: runner.poll(other))
                    COUNTS['mismatched_poll_refusals'] += 1
                    logfile.write_text(terminal_text(target, method, terminal))
                    proc.returncode = 0
                    result = runner.poll(request)
                    assert result is not None and result.ok is (terminal == 'complete')
                    if terminal == 'complete':
                        assert runner.progress == 100
                        COUNTS['verified_success'] += 1
                    else:
                        assert runner.progress < 100
                        COUNTS['negative_terminal'] += 1
                    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
                    assert runner.poll(request) is result
                    runner.cancel()
                    assert runner.result is result
                    old_proc = proc
                TRACE.append(dict(state, generations=3, last_reason=runner.result.reason))
            finally:
                runner._release_wipe_lock()

sources = ['src/beamo_wipe/nwipe_runner.py', 'src/beamo_wipe/progress.py',
           'src/beamo_wipe/engine_checks.py', 'src/beamo_wipe/models.py',
           'src/beamo_wipe/methods.py', 'src/beamo_wipe/sleep_inhibit.py']
result = dict(COUNTS, mismatches=[], source_sha256={
    path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in sources
}, scope='Supporting fake process and owned regular-file model; overlaps focused/canonical tests. No engine, device, subprocess, signals or native callbacks.')
(OUT / 'launch-reuse-matrix.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'launch-reuse-trace.json').write_text(json.dumps(TRACE, indent=2) + '\n')
print(json.dumps(result, indent=2))
