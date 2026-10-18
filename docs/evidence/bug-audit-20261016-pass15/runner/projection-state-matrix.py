"""Fresh pass15 method/collision/context boundaries. Fake processes + ordinary logs only."""
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import sys
import tarfile
import time
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe import nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.methods import METHODS

BASE = Path('/tmp/pass15-runner')
BASE.mkdir(exist_ok=True)
paths = ['src/beamo_wipe/nwipe_runner.py', 'src/beamo_wipe/engine_checks.py', 'src/beamo_wipe/methods.py']
source = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
notes = []
m._try_log_diag = lambda *args: notes.append(args)
forbidden_calls = []
def forbid(*args, **kwargs):
    forbidden_calls.append(str(args[:1]))
    raise AssertionError('forbidden native process or inventory')
m.subprocess.Popen = forbid
m.subprocess.run = forbid
m.pinned_nwipe_already_running = forbid
m._recheck_identity_under_lock = forbid
STAMP = '[2026/10/16 12:00:00] info: '
EH = '******************************** Error Summary *********************************\n'
SH = m.NWIPE_DRIVE_STATUS_HEADER + '\n'
CLOSE = '********************************************************************************\n'
padding = ('x' * 65535 + '\n') * 16 + 'padding\n'

def sample(target, pct, pass_i, total, phase):
    return f'{target}: {pct}%, round 1 of 1, pass {pass_i} of {total}, eta 00:00:00, [{phase}]\n'

def status(target):
    return SH + f'{m.nwipe_status_device_field(target)} | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n' + CLOSE

class Exited:
    returncode = 0
    def poll(self):
        return self.returncode
    def terminate(self):
        raise AssertionError('already exited fake process must not be signalled')

class Stopped:
    def __init__(self):
        self.returncode = None
        self.signals = []
    def poll(self):
        return self.returncode
    def terminate(self):
        self.signals.append('terminate')
        self.returncode = -15
    def wait(self, timeout):
        return self.returncode

cases = []
for target in ['/dev/sda', '/dev/nvme0n100', '/dev/mmcblk100']:
    column = m.nwipe_status_device_field(target).strip()
    colliding = '/dev/sdx' + column
    for method, phase in itertools.product(MethodId, ['writing', 'verifying', 'syncing', 'retrying']):
        spec = METHODS[method]
        good = sample(target, '100.00', spec.overwrite_passes, spec.overwrite_passes, phase)
        weak = sample(target, '99.99999999999999999', spec.overwrite_passes, spec.overwrite_passes, phase)
        wrong = sample(target, '010.00', 1, spec.overwrite_passes + 1, phase)
        complete = status(target)
        variants = {
            'terminal_then_partial': complete + sample(target, '020.00', 1, spec.overwrite_passes, phase),
            'partial_then_terminal': weak + complete,
            'wrong_counter_before_terminal': wrong + complete,
            'wrong_counter_after_terminal': complete + wrong,
            'completion_phase_without_table': good,
            'counter_before_collision': wrong + f'observed {colliding}\n' + complete,
            'collision_then_progress': f'observed {colliding}\n' + complete + good,
            'collision_failed_then_progress': f'observed {colliding}\n' + SH + f'{column} |-FAILED-| 1MB/s | 00:01:00 | FAKE\n' + CLOSE + good,
            'zero_summary_then_terminal': EH + f' {column} | 0 | 0 | 0\n' + CLOSE + complete,
            'negative_summary_then_terminal': EH + STAMP + f'! {column} | 0 | 1 | 0\n' + CLOSE + complete,
            'model_failure_then_terminal': STAMP + f'Model: {target}: >>> FAILURE! <<<\n' + complete,
            'unicode_model_then_terminal': STAMP + f'Model: x\u2028{target}: >>> FAILURE! <<<\n' + complete,
        }
        for name, text in variants.items():
            cases.append((target, method, phase, name, text))

rows, mismatches, actual = [], [], []
fixtures = {}
logfile = BASE / 'ordinary-matrix.log'
started = time.monotonic()
for index, (target, method, phase, name, text) in enumerate(cases):
    raw = text.encode()
    logfile.write_bytes(raw)
    runner = m.NwipeRunner()
    projected = runner._scan_completion_log(str(logfile), target, m._log_signature(logfile.stat()))
    assert projected is not None
    full = m.completion_for_method(0, text, target, method)
    projected_outcome = m.completion_for_method(0, projected, target, method)
    checks = check_payloads(text, target)
    same = projected_outcome == full and check_payloads(projected, target) == checks
    row = {'index': index, 'target': target, 'method': method.value, 'phase': phase, 'variant': name,
           'full_outcome': full, 'projection_outcome': projected_outcome, 'checks': [c['status'] for c in checks],
           'same': same, 'source_sha256': hashlib.sha256(raw).hexdigest(),
           'projection_sha256': hashlib.sha256(projected.encode()).hexdigest()}
    rows.append(row)
    if not same:
        mismatches.append({**row, 'full_text': text, 'projected_text': projected,
                           'full_checks': checks, 'projected_checks': check_payloads(projected, target)})
    # Explicit semantic expectations independent of the differential comparison.
    if name == 'negative_summary_then_terminal':
        assert not full[0] and full[2] == 'engine_failed'
    if name in {'wrong_counter_before_terminal', 'wrong_counter_after_terminal'}:
        assert not full[0] and full[2] == 'indeterminate'
    if name in {'partial_then_terminal', 'terminal_then_partial', 'model_failure_then_terminal', 'unicode_model_then_terminal', 'zero_summary_then_terminal'}:
        assert full[0] and full[2] == 'completed'
    assert logfile.read_bytes() == raw
    # Each target/method uses twelve structurally distinct large cases and all
    # phases; alternate natural poll, late Stop and running Stop.
    if phase == 'verifying':
        large = padding + text if index % 2 else text + padding
        big = large.encode()
        fixtures[f'{index:03d}-{name}.log'] = big
        for finish in ['poll', 'late_stop', 'running_stop']:
            logfile.write_bytes(big)
            process = Stopped() if finish == 'running_stop' else Exited()
            runner = m.NwipeRunner()
            runner._proc = process
            request = WipeRequest(target, method, '/dev/sr0', str(logfile))
            runner._active_request = request
            runner._last_logfile = str(logfile)
            if finish == 'poll':
                result = runner.poll(request)
            else:
                runner.cancel()
                result = runner.result
            assert result is not None
            if finish == 'running_stop':
                assert not result.ok and result.reason == 'cancelled'
                assert process.signals == ['terminate']
            else:
                expected = m.completion_for_method(0, large, target, method)
                assert (result.ok, result.reason) == (expected[0], expected[2])
            assert runner._assessment_log_text is not None
            assert check_payloads(runner._assessment_log_text, target) == check_payloads(large, target)
            assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
            assert logfile.read_bytes() == big
            actual.append({'index': index, 'finish': finish, 'method': method.value, 'target': target,
                           'variant': name, 'bytes': len(big), 'sha256': hashlib.sha256(big).hexdigest(),
                           'ok': result.ok, 'reason': result.reason})
with tarfile.open(BASE / 'exact-large-fixtures.tar.gz', 'w:gz') as archive:
    for name, data in fixtures.items():
        info = tarfile.TarInfo(name)
        info.size, info.mode, info.mtime = len(data), 0o600, 0
        archive.addfile(info, io.BytesIO(data))
for name, data in [('projection-rows.json', rows), ('projection-mismatches.json', mismatches), ('actual-large-results.json', actual)]:
    (BASE / name).write_text(json.dumps(data, indent=2) + '\n')
summary = {'source': source, 'short_differential_cases': len(rows), 'actual_large_cases': len(actual),
           'large_fixtures': len(fixtures), 'mismatches': len(mismatches),
           'native_acquisition_calls': len(forbidden_calls), 'elapsed_s': time.monotonic() - started,
           'source_unchanged': source == {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}}
(BASE / 'projection-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
assert not mismatches and not forbidden_calls and summary['source_unchanged']
