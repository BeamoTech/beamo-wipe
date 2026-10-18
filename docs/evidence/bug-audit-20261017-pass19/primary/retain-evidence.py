"""Retain owned pass19 bytes and authenticate compacted evidence readback."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

root = Path.cwd()
out = Path('/tmp/pass19-primary')
destination = root / 'docs/evidence/bug-audit-20261017-pass19'
primary = destination / 'primary'
assert not (primary / 'raw-evidence.tar.gz').exists(), 'Retain once; preserve prior history'
guards = json.loads((out / 'guard-manifest.json').read_text())
retained_guards = {}
for name, expected in guards.items():
    path = Path(name)
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected
    target = out / 'guards' / path.name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)
    retained_guards[name] = dict(retained_path=str(target.relative_to(out)), sha256=expected)
(out / 'guard-retention-map.json').write_text(json.dumps(retained_guards, indent=2) + '\n')
for source, target in ((out, primary), (Path('/tmp/pass19-ui'), destination / 'ui')):
    target.mkdir(exist_ok=True)
    for path in source.rglob('*'):
        assert not path.is_symlink(), path
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        final = target / path.relative_to(source)
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, final)
runner = Path('/tmp/pass19-runner')
if runner.exists():
    for path in runner.glob('*.json'):
        assert path.is_file() and not path.is_symlink()
        shutil.copy2(path, destination / 'runner' / path.name)
raw_archive = primary / 'raw-evidence.tar.gz'
raw = {}
for path in sorted(primary.rglob('*')):
    if path.is_file() and (path.suffix in {'.xml', '.exe'} or
                          (path.suffix in {'.txt', '.jsonl'} and path.stat().st_size > 64 * 1024)):
        raw[str(path.relative_to(primary))] = path.read_bytes()
with tarfile.open(raw_archive, 'w:gz') as archive:
    for name, data in raw.items():
        info = tarfile.TarInfo(name)
        info.size = len(data)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(data))
raw_hashes = {n: hashlib.sha256(b).hexdigest() for n, b in raw.items()}
with tarfile.open(raw_archive, 'r:gz') as archive:
    assert set(archive.getnames()) == set(raw_hashes)
    assert all(m.isfile() and hashlib.sha256(archive.extractfile(m).read()).hexdigest() == raw_hashes[m.name] for m in archive)
(primary / 'raw-evidence-sha256.json').write_text(json.dumps(raw_hashes, indent=2) + '\n')
for name in raw:
    (primary / name).unlink()
freeze = json.loads((out / 'source-freeze.json').read_text())
assert len(freeze) == 771
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
subprocess.run(['git', 'diff', '--check'], check=True)
(primary / 'final-git-status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short']))
gate = json.loads((out / 'local-gate-status.json').read_text())
gate_ok = len(gate) == 9 and all(row['exit_code'] == 0 for row in gate)
campaigns = json.loads((out / 'campaign-verification.json').read_text()) if (out / 'campaign-verification.json').exists() else None
view = json.loads((out / 'primary-capture-review.json').read_text()) if (out / 'primary-capture-review.json').exists() else None
if campaigns:
    assert gate_ok and view and view['reviewed'] == campaigns['captures_for_primary_view']
receipt = dict(compacted_raw_files=len(raw), raw_original_bytes=sum(map(len, raw.values())),
               raw_archive_bytes=raw_archive.stat().st_size, raw_archive_readback=True,
               source_inputs_unchanged=771, index_empty=True, staged_files=0,
               working_staging_retained=str(out),
               runner_fixture_files=campaigns['runner_fixture_files_hashed'] if campaigns else 0,
               report_artifact_files=campaigns['retained_report_files'] if campaigns else 0,
               screenshots=len(campaigns['captures_for_primary_view']) if campaigns else 0,
               final_campaigns='PASS; exact artifact readback' if campaigns else 'HELD; no acceptance claimed',
               local_gate='PASS; canonical uninstrumented Python/Orca' if gate_ok else 'FAILED; see final logs/status',
               historical_abort='UNEXPLAINED; both uncanceled full aborts retained separately; owned native-asset gap proved',
               source_committed=False, pushed=False, deployed=False)
(primary / 'retention-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
files = sorted(p for p in destination.rglob('*') if p.is_file() and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts)
manifest = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(destination)) + '\n' for p in files)
(destination / 'SHA256SUMS').write_text(manifest)
assert all(hashlib.sha256((destination / line.split('  ', 1)[1]).read_bytes()).hexdigest() == line.split('  ', 1)[0] for line in manifest.splitlines())
print(json.dumps(dict(receipt, retained_files_hashed=len(files), retained_bytes=sum(p.stat().st_size for p in files)), indent=2))
