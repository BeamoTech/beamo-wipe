"""Authenticate fresh ordinary-file artifacts against final source and receipts."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile

root = Path.cwd()
out = Path('/tmp/pass18-primary')
runner = Path('/tmp/pass18-runner')
ui = Path('/tmp/pass18-ui')
evidence = root / 'docs/evidence/bug-audit-20261017-pass18'
freeze = json.loads((out / 'source-freeze.json').read_text())
assert len(freeze) == 766
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
statuses = json.loads((out / 'campaign-status.json').read_text())
assert [r['phase'] for r in statuses] == ['runner-fresh', 'runner-cancel', 'geometry', 'reports']
assert all(r['exit_code'] == 0 for r in statuses)
gate = json.loads((out / 'local-gate-status.json').read_text())
assert statuses[0]['started_utc'] >= gate[-1]['ended_utc']
assert all(b['started_utc'] >= a['ended_utc'] for a, b in zip(statuses, statuses[1:]))
for row in statuses:
    assert hashlib.sha256(Path(row['command'][1]).read_bytes()).hexdigest() == row['script_sha256']
    assert Path(row['command'][0]).samefile(root / '.venv-linux/bin/python3')

peer = json.loads((evidence / 'ui-boot/final-cross-review.json').read_text())
peer_hashes = {n: row['reviewed_sha256'] for n, row in peer['runtime'].items()}
peer_hashes.update(peer['tests'])
assert len(peer_hashes) == 7
assert all(freeze[n] == h for n, h in peer_hashes.items())
summary = json.loads((runner / 'fresh-summary.json').read_text())
assert summary['short_cases'] == summary['actual_large_cases'] == 153
assert summary['successful_roundtrips'] == 90 and summary['mixed_advisory_traces'] == 54
assert summary['source_unchanged'] and summary['native_acquisitions'] == summary['mismatches'] == summary['semantic_errors'] == 0
assert not json.loads((runner / 'fresh-mismatches.json').read_text())
assert not json.loads((runner / 'fresh-semantic-errors.json').read_text())
assert all(freeze['src/beamo_wipe/' + n] == h for n, h in summary['source'].items())
actual = json.loads((runner / 'fresh-actual.json').read_text())
assert len(actual) == 153
for index, row in enumerate(actual, 1):
    data = (runner / 'fixtures' / f'{index:04d}' / 'fake.log').read_bytes()
    assert len(data) == row['bytes'] > 1024 * 1024
    assert hashlib.sha256(data).hexdigest() == row['sha256']

files = {}
for directory in ('fixtures', 'cancellation'):
    for path in sorted((runner / directory).rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            files[str(path.relative_to(runner))] = path.read_bytes()
assert sum(n.startswith('fixtures/') for n in files) == 333
assert sum(n.startswith('cancellation/') for n in files) == 288
results = [n for n in files if n.endswith('.json')]
assert len(results) == 90 and len(files) == 621
for name in results:
    data = files[name]
    assert files[name + '.sha256'].decode().split()[0] == hashlib.sha256(data).hexdigest()
    result = json.loads(data)
    assert result['verification']['verified'] is (result['outcome'] == 'verified')
cancel = json.loads((runner / 'cancel-summary.json').read_text())
assert cancel['cases'] == 144 and cancel['source_unchanged'] and cancel['native_acquisitions'] == 0
assert all(freeze['src/beamo_wipe/' + n] == h for n, h in cancel['source'].items())
cancel_rows = json.loads((runner / 'cancel-results.json').read_text())
assert len(cancel_rows) == len({r['index'] for r in cancel_rows}) == 144
for row in cancel_rows:
    log = Path(row['logfile'])
    lock = Path(row['lockfile'])
    assert log.parent == lock.parent == runner / 'cancellation' / f"{row['index']:04d}"
    assert hashlib.sha256(log.read_bytes()).hexdigest() == row['log_sha256']
    assert row['free_after_terminal']
    assert row['retried'] == row['retained_on_uncertainty'] == (row['mode'] in {'never_exits', 'wait_error_once'})
with tarfile.open(out / 'runner-final-fixtures.tar.gz', 'w:gz') as archive:
    for name, data in sorted(files.items()):
        info = tarfile.TarInfo(name)
        info.size = len(data)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(data))
hashes = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
(out / 'runner-final-fixtures-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
with tarfile.open(out / 'runner-final-fixtures.tar.gz', 'r:gz') as archive:
    assert set(archive.getnames()) == set(hashes)
    assert all(m.isfile() and hashlib.sha256(archive.extractfile(m).read()).hexdigest() == hashes[m.name] for m in archive)

geometry = json.loads((ui / 'geometry-matrix.json').read_text())
geometry_summary = json.loads((ui / 'geometry-summary.json').read_text())
assert geometry_summary['hashes'] == geometry_summary['final_hashes'] == geometry['hashes']
assert all(freeze[n] == h for n, h in geometry['hashes'].items())
rows = geometry['rows']
assert len(rows) == geometry_summary['cases'] == geometry_summary['passed'] == 270
assert not geometry['forbidden_calls'] and not geometry_summary['failed']
assert all(row['ok'] and not row['callback_errors'] for row in rows)
critical = [r for r in rows if r['surface'] == 'tk' and r['screen'] in {'KEYBOARD', 'OWNER', 'CONFIRM'}]
assert len(critical) == 27 and all(row['focus_fully_visible'] for row in critical)
captures = [r['capture'] for r in rows if 'capture' in r]
assert len(captures) == len(set(captures)) == 5
for name in captures:
    assert name == Path(name).name and (ui / name).read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
assert not any(term in (ui / 'geometry-matrix.txt').read_text() for term in ('invalid command name', 'Traceback', 'bgerror', 'Exception in Tkinter'))

report = json.loads((out / 'report-checks-matrix-artifacts.json').read_text())
assert report['cases'] == len(report['rows']) == 90
assert report['runtime_source_sha256'] == json.loads((out / 'source-review.json').read_text())['runtime_source_sha256']
with tarfile.open(out / 'report-artifacts.tar.gz', 'r:gz') as archive:
    reports = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
assert len(reports) == len(report['artifact_files']) == 70
assert {n: hashlib.sha256(b).hexdigest() for n, b in reports.items()} == report['artifact_files']
bundles = {Path(n).parts[0] for n in reports}
assert len(bundles) == 5
for bundle in bundles:
    manifest = json.loads(reports[bundle + '/COMPLETE'])
    payload = {n.split('/', 1)[1]: b for n, b in reports.items() if n.startswith(bundle + '/')}
    assert set(payload) == set(manifest['files']) | {'COMPLETE'}
    assert all(hashlib.sha256(payload[n]).hexdigest() == h for n, h in manifest['files'].items())
    assert json.loads(payload['result.json'])['outcome'] == json.loads(payload['SHARE.json'])['outcome']
    assert '<html' in payload['REPORT.html'].decode().lower()
    assert payload['RESULT.txt'] and payload['SHARE.txt']
assert not (out / 'forbidden-fallback-attempts.txt').exists()
receipt = dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               serial_phases=len(statuses), exact_peer_files=len(peer_hashes), frozen_inputs=766,
               runner_short=153, runner_actual_large=153, runner_fixture_files_hashed=len(files),
               authenticated_evidence_sidecar_pairs=90, runner_cancellation_cases=144,
               retained_cancellation_files=288, geometry_cases=270, critical_tk_fully_visible=27,
               captures_for_primary_view=captures, report_cases=90, retained_report_files=70,
               retained_bundles=5, native_effects=0, callback_errors=0, archive_readback=True)
(out / 'campaign-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
