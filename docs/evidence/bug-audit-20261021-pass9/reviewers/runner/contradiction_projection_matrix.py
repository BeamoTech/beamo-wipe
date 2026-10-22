"""PASS9: exact-method terminal proof versus ordered contradictions and projection.

Only fake /dev spellings and owned regular files are used. No inventory, child
process, engine or signal is allowed; this is supporting evidence, not acceptance.
"""
from pathlib import Path
import hashlib
import itertools
import json
import os
import tempfile
from unittest.mock import patch

from beamo_wipe import nwipe_runner as m
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId

root = Path(__file__).parent
target = '/dev/FAKEDATA'
other = '/dev/FAKEOTHER'
prefix = '[2026/10/21 12:34:56] info: '
original_realpath = os.path.realpath
native = []


def fake_realpath(value, *args, **kwargs):
    if os.fsdecode(value).startswith('/dev/'):
        return os.fspath(value)
    return original_realpath(value, *args, **kwargs)


def forbidden(*args, **kwargs):
    native.append(True)
    raise AssertionError('Native callback forbidden')


def table():
    return m.NWIPE_DRIVE_STATUS_HEADER + '\nFAKEDATA | Erased | 120MB/s | 01:25:04 | fake model\n'


def sample(method, *, wrong_total=False):
    passes = METHODS[method].overwrite_passes + int(wrong_total)
    phase = 'writing' if method is MethodId.QUICK_ZERO else 'verifying'
    return f'{target}: 100.00%, round 1 of 1, pass {passes} of {passes}, eta 00:00:00, [{phase}]\n'


cases = 0
positive = 0
negative = 0
projection_comparisons = 0
failures = []
with tempfile.TemporaryDirectory(prefix='pass9-runner-', dir=root) as tmp:
    log = Path(tmp) / 'fake.log'
    with patch.object(os.path, 'realpath', fake_realpath), patch.object(m.subprocess, 'run', forbidden), patch.object(m.subprocess, 'Popen', forbidden), patch.object(os, 'kill', forbidden):
        for method, native_origin, proof_kind, placement, padded, contradiction in itertools.product(
            MethodId, (False, True), ('progress', 'status'), ('before', 'after'), (False, True),
            ('none', 'foreign-failure', 'busy', 'open', 'geometry', 'abort', 'failure', 'mismatch', 'error-summary', 'method-total'),
        ):
            proof = sample(method) if proof_kind == 'progress' else table()
            records = {
                'none': '',
                'foreign-failure': f'{other}: >>> FAILURE! <<<\n',
                'busy': f'{target} is reported as IN USE\n',
                'open': f"Unable to open device '{target}'.\n",
                'geometry': f'No sane device geometry for {target}\n',
                'abort': 'Nwipe was aborted by the user\n',
                'failure': f'{target}: >>> FAILURE! <<<\n',
                'mismatch': f'Verification mismatch on {target}\n',
                'error-summary': m.NWIPE_ERROR_SUMMARY_HEADER + '\nFAKEDATA | 1 | 0 | 0\n' + '*' * 79 + '\n',
                'method-total': sample(method, wrong_total=True),
            }
            record = records[contradiction]
            if native_origin:
                # Table records remain bare just as in pinned logging.c.
                if proof_kind == 'progress':
                    proof = prefix + proof
                if contradiction not in ('none', 'error-summary'):
                    record = prefix + record
                context = prefix + 'Program options are set as follows\n'
            else:
                context = ''
            ordered = record + proof if placement == 'before' else proof + record
            padding = (('p' * 65535 + '\n') * 18) if padded else ''
            text = context + ordered + padding
            expected_ok = contradiction in ('none', 'foreign-failure')
            actual = m.completion_for_method(0, text, target, method)
            cases += 1
            positive += expected_ok
            negative += not expected_ok
            if actual[0] != expected_ok:
                failures.append({'case':cases,'method':method.value,'native_origin':native_origin,'proof_kind':proof_kind,'placement':placement,'padded':padded,'contradiction':contradiction,'expected_ok':expected_ok,'actual':actual})
            if padded:
                log.write_bytes(text.encode())
                runner = m.NwipeRunner()
                projected = runner._scan_completion_log(str(log), target, m._log_signature(log.stat()))
                projected_actual = None if projected is None else m.completion_for_method(0, projected, target, method)
                projection_comparisons += 1
                if projected_actual != actual:
                    failures.append({'case':cases,'projection_mismatch':True,'actual':actual,'projected':projected_actual})

result = {'cases':cases,'positive_controls':positive,'refusal_controls':negative,'whole_log_projection_comparisons':projection_comparisons,'failure_count':len(failures),'failures':failures[:30],'native_callbacks':len(native),'source_sha256':{'src/beamo_wipe/nwipe_runner.py':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()},'scope':'Pure fake terminal evidence law and owned-file projection matrix; supporting counts do not add to pytest totals or native acceptance.'}
(root / 'contradiction-projection-matrix.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k != 'failures'}))
raise SystemExit(bool(failures))
