"""Retain and read back exact final evidence without self-hash/count cycles."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

root=Path.cwd(); out=Path('/tmp/pass16-primary');dest=root/'docs/evidence/bug-audit-20261017-pass16'
freeze=json.loads((out/'source-freeze.json').read_text())
assert len(freeze)==754
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in freeze.items())
assert gzip.decompress((out/'source.diff.gz').read_bytes())==subprocess.check_output(['git','diff','--','src'])
assert gzip.decompress((out/'tracked-test-fixture.diff.gz').read_bytes())==subprocess.check_output(['git','diff','--','tests'])
tests=json.loads((out/'new-tests-sha256.json').read_text());assert len(tests)==25
with tarfile.open(out/'new-tests.tar.gz','r:gz') as archive:
    assert set(archive.getnames())==set(tests)
    for name,digest in tests.items():
        data=archive.extractfile(name).read()
        assert data==(root/name).read_bytes() and hashlib.sha256(data).hexdigest()==digest
guides=json.loads((out/'guide-hashes.json').read_text())
assert hashlib.sha256((root/'AGENTS.md').read_bytes()).hexdigest()==guides['AGENTS.md']
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
subprocess.run(['git','diff','--check'],check=True)
assert not (out/'forbidden-fallback-attempts.txt').exists()
guards=json.loads((out/'fallback-guard-manifest.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in guards.items())
fixture_hashes=json.loads((out/'runner-final-fixtures-sha256.json').read_text())
with tarfile.open(out/'runner-final-fixtures.tar.gz','r:gz') as archive:
    assert set(archive.getnames())==set(fixture_hashes)
    assert all(hashlib.sha256(archive.extractfile(n).read()).hexdigest()==h for n,h in fixture_hashes.items())
with tarfile.open(out/'runner-original-fixtures.tar.gz','r:gz') as archive:
    regular=[m for m in archive.getmembers() if m.isfile()]
    assert len(regular)==333
    for member in regular:
        # Archive keeps the fixtures/ prefix while original source directory
        # was moved aside before the final independent campaign.
        relative=Path(member.name)
        if relative.parts[0]=='fixtures': relative=Path(*relative.parts[1:])
        source=Path('/tmp/pass16-runner/original-fixtures')/relative
        assert archive.extractfile(member).read()==source.read_bytes()
items={}
for group in ('primary','discovery','ui','runner'):
    for path in sorted(Path('/tmp/pass16-'+group).iterdir()):
        if path.is_file() and path.suffix not in {'.exe','.lock'} and path.name!='retention-verification.json':
            items[group+'/'+path.name]=path.read_bytes()
report=dict(frozen_inputs_match=754,new_test_modules_exact=25,exact_original_artifacts=len(items)+1,
            final_runner_fixture_files=333,original_runner_fixture_files=333,
            source_patch_matches=True,tracked_fixture_patch_matches=True,
            fallback_guard_attempts=0,git_index_empty=True,diff_check='passed',
            all_retained_hashes_index='artifacts-sha256.txt',
            derived_receipt_in_exact_archive=True)
data=(json.dumps(report,indent=2)+'\n').encode()
(out/'retention-verification.json').write_bytes(data)
items['primary/retention-verification.json']=data
blob=io.BytesIO()
with tarfile.open(fileobj=blob,mode='w') as archive:
    for name,data in sorted(items.items()):
        target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0
        archive.addfile(info,io.BytesIO(data))
(dest/'original-transcripts.tar.gz').write_bytes(gzip.compress(blob.getvalue(),mtime=0))
(dest/'original-transcripts-sha256.txt').write_text(''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(items.items())))
with tarfile.open(dest/'original-transcripts.tar.gz','r:gz') as archive:
    assert set(archive.getnames())==set(items) and len(items)==report['exact_original_artifacts']
    assert all(archive.extractfile(n).read()==data==(dest/n).read_bytes() for n,data in items.items())
manifest={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='artifacts-sha256.txt'}
(dest/'artifacts-sha256.txt').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
assert all(hashlib.sha256((dest/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
assert json.loads((dest/'primary/retention-verification.json').read_text())==report
print(json.dumps(dict(report,retained_artifacts_hashed=len(manifest)),indent=2))
