"""Verify exact final source/test archives and retained audit artifact hashes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

root = Path.cwd()
dest = root / 'docs/evidence/bug-audit-20261016-pass10'
frozen = json.loads((dest / 'primary/source-freeze.json').read_text())
assert len(frozen) == 735
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in frozen.items())
assert gzip.decompress((dest / 'primary/source.diff.gz').read_bytes()) == subprocess.check_output(['git', 'diff', '--', 'src'])
tests = json.loads((dest / 'primary/new-tests-sha256.json').read_text())
assert len(tests) == 6
with tarfile.open(dest / 'primary/new-tests.tar.gz', 'r:gz') as archive:
    assert set(archive.getnames()) == set(tests)
    for name, digest in tests.items():
        data = archive.extractfile(name).read()
        assert data == (root / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
originals = {}
for line in (dest / 'original-transcripts-sha256.txt').read_text().splitlines():
    digest, name = line.split('  ', 1)
    originals[name] = digest
with tarfile.open(dest / 'original-transcripts.tar.gz', 'r:gz') as archive:
    assert set(archive.getnames()) == set(originals)
    for name, digest in originals.items():
        assert hashlib.sha256(archive.extractfile(name).read()).hexdigest() == digest
manifest = {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file() and p.name != 'artifacts-sha256.txt'}
(dest / 'artifacts-sha256.txt').write_text(''.join(f'{digest}  {name}\n' for name, digest in manifest.items()))
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
subprocess.run(['git', 'diff', '--check'], check=True)
print(json.dumps({'frozen_inputs_match': len(frozen), 'new_test_modules_exact': len(tests), 'exact_original_artifacts': len(originals), 'retained_artifacts_hashed': len(manifest), 'source_patch_matches': True, 'git_index_empty': True, 'diff_check': 'passed'}, indent=2))
