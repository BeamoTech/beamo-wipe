"""Serialize final original-source replay and controlled boundary campaigns."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass15-primary')
python = '/tmp/beamo-wipe-audit-python/bin/python3'
env = dict(os.environ, PYTHONPATH=str(root / 'src'), BEAMO_WIPE_DRY_RUN='1')
assert not env.get('BEAMO_DESKTOP_NATIVE_INVENTORY_TEST')
frozen = json.loads((out / 'source-freeze.json').read_text())
status = []

def read(path):
    return json.loads(Path(path).read_text())

def validate(name):
    if name == 'original':
        data = read(out / 'original-summary.json')
        assert (data['cases'], data['failures'], data['errors'], data['skipped'], data['pytest_exit']) == (578, 298, 0, 0, 1), data
        cases = ET.parse(out / 'original.xml').findall('.//testcase')
        assert sum(not list(case) for case in cases) == 280
    elif name == 'alias':
        data = read(out / 'omitted-alias-context.json')
        assert (data['cases'], data['passed'], data['violations']) == (288, 288, 0)
        assert not data['native_attempts']
    elif name == 'duplicate':
        data = read(out / 'omitted-duplicate-observation.json')
        assert (data['cases'], data['passed'], data['violations']) == (36, 36, 0)
        assert not data['native_attempts']
    elif name == 'wheel':
        data = read(out / 'empty-wheel-probe.json')
        assert data['cases'] == 8 and data['behavior_failures'] == 0 and not data['effects']
        assert all(row['hit_is_reader'] and row['reader_scrolled'] and row['parent_unchanged'] and row['state_unchanged'] and row['focus_unchanged'] and not row['callback_errors'] and not row['engine_started'] for row in data['rows'])
    elif name == 'utf8':
        data = read(out / 'utf8-tail-probe.json')
        assert data['cases'] == 30 and data['boundary_cuts'] == 18 and data['runner_success_presentation_indeterminate'] == data['native_effects'] == 0
        for row in data['rows']:
            expected = 'unverified' if row['method'] == 'quick_zero' else 'verified'
            expected_read = 'tail' if row['raw_file_bytes'] > 1024 * 1024 else 'complete'
            assert row['export_ready'] and row['snapshot_read_status'] == expected_read, row
            assert row['presentation_code'] == row['direct_presentation_code'] == row['recovery_code'] == expected, row
        with tarfile.open(out / 'final-utf8-owned-files.tar.gz', 'w:gz') as archive:
            archive.add(out / 'utf8-tail-probe', arcname='utf8-tail-probe')
    elif name == 'runner':
        data = read('/tmp/pass15-runner/projection-summary.json')
        assert (data['short_differential_cases'], data['actual_large_cases'], data['large_fixtures'], data['mismatches'], data['native_acquisition_calls']) == (432, 324, 108, 0, 0), data
        assert data['source_unchanged']
        assert all(frozen[name] == value for name, value in data['source'].items())
    elif name == 'geometry':
        data = read('/tmp/pass15-ui/geometry-summary.json')
        assert data['cases'] == data['passed'] == 270 and not data['failed'] and not data['forbidden_calls']
        assert data['hashes'] == data['final_hashes']
        assert all(frozen[name] == value for name, value in data['hashes'].items())
        rows = read('/tmp/pass15-ui/geometry-matrix.json')['rows']
        critical = [row for row in rows if row['surface'] == 'tk' and row['screen'] in ('OWNER', 'KEYBOARD', 'CONFIRM')]
        assert len(critical) == 27 and all(row['focus_fully_visible'] for row in critical)
        assert all(row['ok'] and not row['callback_errors'] for row in rows)
        log = Path('/tmp/pass15-ui/geometry-matrix.txt').read_text()
        assert 'Traceback' not in log and 'bgerror' not in log
    assert all(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest for name, digest in frozen.items())

phases = [
    ('original', out / 'original-proof.py'),
    ('alias', out / 'independent-alias-probe.py'),
    ('duplicate', out / 'independent-duplicate-probe.py'),
    ('wheel', out / 'run-empty-wheel.py'),
    ('utf8', out / 'independent-utf8-tail.py'),
    ('runner', Path('/tmp/pass15-runner/projection-state-matrix.py')),
    ('geometry', Path('/tmp/pass15-ui/run-geometry.py')),
]
if os.environ.get('PASS15_RESUME_RECEIPT') == 'utf8':
    status = read(out / 'fresh-verification-status.json')
    assert len(status) == 5 and status[-1]['phase'] == 'utf8' and status[-1]['exit_code'] == 0
    validate('utf8')
    status[-1]['receipt_validated'] = True
    (out / 'fresh-verification-status.json').write_text(json.dumps(status, indent=2) + '\n')
    phases = phases[5:]
for name, script in phases:
    print(name + ' started', flush=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (out / ('fresh-' + name + '.txt')).open('wb') as log:
        result = subprocess.run([python, str(script)], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    row = dict(phase=name, command=[python, str(script)], exit_code=result.returncode, started_utc=started,
               ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), receipt_validated=False)
    status.append(row)
    (out / 'fresh-verification-status.json').write_text(json.dumps(status, indent=2) + '\n')
    assert result.returncode == 0, row
    validate(name)
    row['receipt_validated'] = True
    (out / 'fresh-verification-status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(name + ' passed and receipt validated', flush=True)
