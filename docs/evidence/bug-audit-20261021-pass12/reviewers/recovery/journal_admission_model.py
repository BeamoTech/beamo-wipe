"""Bounded journal admission/rotation state model, owned regular files only."""
from __future__ import annotations
import copy
import fcntl
import hashlib
import itertools
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
from beamo_wipe import session_recovery as recovery
from beamo_wipe.safety import SafetyError
from test_session_recovery import armed

ROOT = Path('/workspace/beamo-wipe')
OUT = Path('/workspace/beamo-tools/audit-pass12-20261021/recovery')
BOOT = '00000000-0000-0000-0000-000000000001'
BUILD = 'a'*64
PHASES = ('preflight', 'armed')
SHAPES = ('canonical', 'pretty', 'reverse', 'duplicate-envelope', 'duplicate-payload', 'digest', 'boot', 'schema-bool', 'nan', 'future', 'missing-context', 'unknown-phase')
LOCKS = ('free', 'busy', 'replaced-interface')
ENGINES = ('absent', 'busy', 'unknown', 'error')
counts = {'states': 0, 'valid_admissions': 0, 'invalid_refusals': 0, 'rotations': 0, 'unchanged_refusals': 0, 'lock_refusals': 0, 'native_callbacks': 0}
rows = []
mismatches = []

def encode(record):
    return recovery._bytes({'payload': record, 'sha256': hashlib.sha256(recovery._bytes(record)).hexdigest()})

for phase, shape, lock, engine in itertools.product(PHASES, SHAPES, LOCKS, ENGINES):
    with tempfile.TemporaryDirectory(prefix='beamo-pass12-journal-') as temporary:
        directory = Path(temporary)/'private'
        initial = recovery.SessionStore(directory, boot=BOOT, build=BUILD).open()
        if phase == 'armed':
            armed(initial)
        initial.close()
        path = directory/recovery.NAME
        envelope = json.loads(path.read_bytes())
        record = envelope['payload']
        if shape == 'pretty':
            data = json.dumps(envelope, indent=4).encode()
        elif shape == 'reverse':
            data = json.dumps(dict(reversed(list(envelope.items()))), separators=(', ', ': ')).encode()
        elif shape == 'duplicate-envelope':
            data = b'{"payload":{},"payload":'+recovery._bytes(record)+b',"sha256":'+json.dumps(envelope['sha256']).encode()+b'}'
        elif shape == 'duplicate-payload':
            raw = recovery._bytes(record)
            data = b'{"payload":'+raw[:-1]+b',"schema":1},"sha256":'+json.dumps(envelope['sha256']).encode()+b'}'
        elif shape == 'nan':
            record['created'] = float('nan')
            data = json.dumps({'payload': record, 'sha256': '0'*64}).encode()
        else:
            if shape == 'digest':
                envelope['sha256'] = 'b'*64
                data = recovery._bytes(envelope)
            else:
                if shape == 'boot': record['boot'] = BOOT[:-1]+'2'
                if shape == 'schema-bool': record['schema'] = True
                if shape == 'future': record['created'] = 10**30
                if shape == 'missing-context': record.pop('context')
                if shape == 'unknown-phase': record['phase'] = 'finished'
                data = encode(record)
        path.write_bytes(data)
        path.chmod(0o600)
        store = recovery.SessionStore(directory, boot=BOOT, build=BUILD).open()
        valid = shape in {'canonical', 'pretty', 'reverse'}
        if store.previous is not True or store.invalid is valid:
            mismatches.append({'state': [phase,shape,lock,engine], 'stage': 'admission'})
        counts['valid_admissions' if valid else 'invalid_refusals'] += 1
        holder = -1
        if lock == 'busy':
            holder = os.open(directory/'wipe.lock', os.O_RDWR|os.O_CREAT, 0o600)
            fcntl.flock(holder, fcntl.LOCK_EX|fcntl.LOCK_NB)
        elif lock == 'replaced-interface':
            (directory/'interface.lock').rename(directory/'retired-interface.lock')
            (directory/'interface.lock').touch(mode=0o600)
        before = path.read_bytes()
        def probe(**_kwargs):
            if engine == 'error': raise OSError('fake process uncertainty')
            return {'absent': False, 'busy': True, 'unknown': None}[engine]
        result = False
        raised = None
        with patch('beamo_wipe.nwipe_runner.pinned_nwipe_already_running', probe):
            try:
                result = store.resume_previous_preflight()
            except (OSError, SafetyError) as exc:
                raised = type(exc).__name__
        expected_rotate = valid and phase == 'preflight' and lock == 'free' and engine == 'absent'
        if bool(result) != expected_rotate:
            mismatches.append({'state': [phase,shape,lock,engine], 'stage': 'rotation', 'result': result, 'raised': raised})
        if expected_rotate:
            if store.previous or store.invalid or store.record['phase'] != 'preflight' or path.read_bytes() == before:
                mismatches.append({'state': [phase,shape,lock,engine], 'stage': 'rotated-state'})
            counts['rotations'] += 1
        else:
            if path.read_bytes() != before:
                mismatches.append({'state': [phase,shape,lock,engine], 'stage': 'refusal-mutated-journal'})
            counts['unchanged_refusals'] += 1
        if raised == 'SafetyError': counts['lock_refusals'] += 1
        if holder >= 0: os.close(holder)
        store.close()
        rows.append({'phase':phase,'shape':shape,'lock':lock,'engine':engine,'valid':valid,'rotated':bool(result),'raised':raised})
        counts['states'] += 1
sources = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT/'src/beamo_wipe/session_recovery.py', ROOT/'src/beamo_wipe/report_intent.py', ROOT/'src/beamo_wipe/wizard.py', ROOT/'tests/test_session_recovery.py', ROOT/'tests/test_usb_report_workflow.py']}
report = {'baseline':'b462e62005a752b0e5f2a066bda19bd9c79bbd8b','counts':counts,'mismatches':mismatches,'source_sha256':sources,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'states':rows,'limits':['Owned regular tempfiles and fake pinned process probe only.','No real device, engine, inventory, mount, firmware, network or remote operation.','Model overlaps existing coverage and is not additional canonical test count.']}
(OUT/'journal-admission-model.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counts':counts,'mismatches':mismatches,'source_sha256':sources},indent=2))
raise SystemExit(bool(mismatches))
