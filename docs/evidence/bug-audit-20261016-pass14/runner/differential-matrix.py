"""Pass14 exact full/project differential, fake processes and ordinary logs only."""
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe import nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest

BASE = Path('/tmp/pass14-runner')
BASE.mkdir(exist_ok=True)
notes = []
m._try_log_diag = lambda *args: notes.append(args)
# This campaign never starts a process or requests production inventory.
def forbid(*a, **k):
    raise AssertionError('forbidden native process/inventory acquisition')
m.subprocess.Popen = forbid
m.subprocess.run = forbid
m.pinned_nwipe_already_running = forbid
m._recheck_identity_under_lock = forbid

STAMP = '[2026/10/16 12:00:00] info: '
EH = '******************************** Error Summary *********************************'
SH = m.NWIPE_DRIVE_STATUS_HEADER
CLOSE = '********************************************************************************'
STATUS = SH + '\n sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
TARGET = '/dev/sda'
PADDING = ('x' * 65535 + '\n') * 16 + 'padding\n'

class Exited:
    returncode = 0
    def poll(self):
        return self.returncode
    def terminate(self):
        raise AssertionError('late Stop signaled an exited fake process')

cases = []
for header, row, delimiter in itertools.product(
    [EH, 'info: '+EH, STAMP+EH, 'Error Summary', 'Model: Error Summary'],
    [' sda | 0 | 0 | 0', ' sda | 1 | 0 | 0', ' sda | unknown | 0 | 0', ' sdb | 1 | 0 | 0'],
    [CLOSE, ' '+CLOSE, '\t'+CLOSE, 'info: '+CLOSE, STAMP+CLOSE, 'no delimiter'],
):
    cases.append(({'header': header, 'row': row, 'delimiter': delimiter},
                  header+'\n'+row+'\n'+delimiter+'\nnot a summary row\n'+STATUS))
# Explicit negative sentences, model continuations, terminal records and
# collision names each before/after tables. New combinations, no source edits.
for idx, (prefix, record, after) in enumerate(itertools.product(
    ['', 'info: ', STAMP],
    ['/dev/sda: >>> FAILURE! <<<', 'Verification mismatch on /dev/sda',
     'Model: /dev/sda: >>> FAILURE! <<<', ' sda |-FAILED-|',
     '/dev/sda is IN USE but --force is not set, not wiping it'],
    [False, True],
)):
    text = STATUS+prefix+record+'\n' if after else prefix+record+'\n'+STATUS
    cases.append(({'prefix': prefix, 'record': record, 'after': after}, text))

results = []
mismatches = []
start = time.monotonic()
logfile = BASE / 'ordinary-fake-engine.log'
for index, (params, text) in enumerate(cases):
    raw = text.encode()
    logfile.write_bytes(raw)
    runner = m.NwipeRunner()
    projection = runner._scan_completion_log(str(logfile), TARGET, m._log_signature(logfile.stat()))
    assert projection is not None
    full_checks = check_payloads(text, TARGET)
    projected_checks = check_payloads(projection, TARGET)
    full = [m.completion_for_method(0, text, TARGET, method) for method in MethodId]
    projected = [m.completion_for_method(0, projection, TARGET, method) for method in MethodId]
    same = full == projected and full_checks == projected_checks
    row = {'index': index, 'params': params, 'source_sha256': hashlib.sha256(raw).hexdigest(),
           'projection_sha256': hashlib.sha256(projection.encode()).hexdigest(),
           'same': same, 'outcomes': full, 'checks': [c['status'] for c in full_checks],
           'full_text': text, 'projection_text': projection}
    results.append(row)
    if not same:
        mismatch = {**row, 'full': text, 'projection': projection, 'projected_outcomes': projected,
                    'full_checks': full_checks, 'projected_checks': projected_checks}
        mismatches.append(mismatch)
    assert logfile.read_bytes() == raw
# Actual >1MiB dispatch and late Stop exercise the whole production projection
# path; one from every delimiter/header row outcome at deterministic positions.
(BASE/'differential-results.json').write_text(json.dumps(results,indent=2)+'\n')
(BASE/'differential-mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n')
print(json.dumps({'short_cases':len(results),'mismatches':len(mismatches)}),flush=True)
actual = []
fixtures = {}
for case_index in [0,1,2,3,4,6,12,18,24,30,60,90,119,120,126,149]:
    params, short = cases[case_index]
    text = short[:-len(STATUS)] + PADDING + STATUS if short.endswith(STATUS) else PADDING+short
    raw = text.encode()
    fixtures[f'large-case-{case_index:03d}.log'] = raw
    assert len(raw) > m.NWIPE_COMPLETION_LOG_BYTES
    for method, late in itertools.product(MethodId, [False, True]):
        logfile.write_bytes(raw)
        runner = m.NwipeRunner()
        runner._proc = Exited()
        request = WipeRequest(TARGET, method, '/dev/sr0', str(logfile))
        runner._active_request = request
        runner._last_logfile = str(logfile)
        if late:
            runner.cancel()
            result = runner.result
        else:
            result = runner.poll(request)
        expected = m.completion_for_method(0, text, TARGET, method)
        assert result is not None
        assert (result.ok, result.reason) == (expected[0], expected[2])
        assert check_payloads(runner._assessment_log_text, TARGET) == check_payloads(text,TARGET)
        assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
        assert logfile.read_bytes() == raw
        actual.append({'case_index':case_index, 'method':method.value, 'late_stop':late,
                       'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest(),
                       'ok':result.ok, 'reason':result.reason,
                       'assessment_text': runner._assessment_log_text})
# Intentional cap control: open Error Summary retains every padding line.
params, short = cases[5]
text = short[:-len(STATUS)]+PADDING+STATUS
logfile.write_bytes(text.encode())
runner = m.NwipeRunner()
runner._proc = Exited()
request = WipeRequest(TARGET,MethodId.EVERYDAY,'/dev/sr0',str(logfile))
runner._active_request=request
result=runner.poll(request)
assert result is not None and not result.ok and result.reason=='indeterminate'
assert runner._assessment_log_text is None
assert logfile.read_bytes()==text.encode()
cap_control={'indeterminate':True,'assessment':None,'bytes':len(text.encode()),'unchanged':True}
fixtures['cap-control.log'] = text.encode()
(BASE/'evidence-cap-control.json').write_text(json.dumps(cap_control,indent=2)+'\n')
with tarfile.open(BASE/'exact-large-fixtures.tar.gz','w:gz') as archive:
    for name, data in fixtures.items():
        member=tarfile.TarInfo(name)
        member.size=len(data)
        member.mode=0o600
        member.mtime=0
        archive.addfile(member,io.BytesIO(data))
summary = {'differential_cases':len(results),'differential_method_assessments':len(results)*3,
           'actual_large_log_polls':len(actual),'explicit_evidence_cap_controls':1,'mismatches':len(mismatches),
           'elapsed_s':time.monotonic()-start,'native_acquisition_calls':0,
           'files_unchanged':True, 'product_or_test_edits':False}
(BASE/'differential-results.json').write_text(json.dumps(results,indent=2)+'\n')
(BASE/'differential-mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n')
(BASE/'actual-large-polls.json').write_text(json.dumps(actual,indent=2)+'\n')
(BASE/'differential-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
assert not mismatches
