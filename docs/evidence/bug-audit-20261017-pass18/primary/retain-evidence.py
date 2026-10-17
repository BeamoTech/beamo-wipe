"""Retain owned results, compact bulky raw bytes, and authenticate readback."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

root = Path.cwd()
out = Path('/tmp/pass18-primary')
destination = root / 'docs/evidence/bug-audit-20261017-pass18'
for source, target in ((out, destination / 'primary'), (Path('/tmp/pass18-ui'), destination / 'ui')):
    target.mkdir(exist_ok=True)
    for path in source.rglob('*'):
        assert not path.is_symlink(), path
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        final = target / path.relative_to(source)
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, final)
for path in Path('/tmp/pass18-runner').glob('*.json'):
    assert path.is_file() and not path.is_symlink()
    shutil.copy2(path, destination / 'runner' / path.name)

primary = destination / 'primary'
raw_archive = primary / 'raw-evidence.tar.gz'
assert not raw_archive.exists(), 'Retain once; do not silently overwrite archived history'
raw = {}
for path in sorted(primary.rglob('*')):
    if not path.is_file():
        continue
    if path.suffix in {'.xml', '.exe'} or (path.suffix == '.txt' and path.stat().st_size > 64 * 1024):
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
# Every compacted raw file is still available at its exact original relative
# path in the archive. The working staging directory is retained unchanged.
freeze = json.loads((out / 'source-freeze.json').read_text())
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
subprocess.run(['git', 'diff', '--check'], check=True)
(primary / 'final-git-status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short']))
receipt = dict(compacted_raw_files=len(raw), raw_original_bytes=sum(map(len, raw.values())),
               raw_archive_bytes=raw_archive.stat().st_size, raw_archive_readback=True,
               source_inputs_unchanged=766, index_empty=True, staged_files=0,
               working_staging_retained='/tmp/pass18-primary',
               runner_fixture_files=0, report_artifact_files=0,
               screenshots=0, final_campaigns='NOT RUN; failed local gate',
               local_gate='FAILED; GTK click latency assertion',
               source_committed=False, pushed=False, deployed=False)
(primary / 'retention-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
files = sorted(p for p in destination.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
manifest = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(destination)) + '\n' for p in files)
(destination / 'SHA256SUMS').write_text(manifest)
assert all(hashlib.sha256((destination / line.split('  ', 1)[1]).read_bytes()).hexdigest() == line.split('  ', 1)[0] for line in manifest.splitlines())
print(json.dumps(dict(receipt, retained_files_hashed=len(files), retained_bytes=sum(p.stat().st_size for p in files)), indent=2))
