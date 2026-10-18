"""Retain pass20 once, preserving checkpoints and every historical run.

Prepared only. Root owns admission and execution after final evidence review.
Duplicate original/private source trees are authenticated against retained source
archives and indexed rather than copied again. No existing file is overwritten.
"""
import datetime
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

root = Path.cwd()
out = Path('/tmp/pass20-primary')
destination = root / 'docs/evidence/bug-audit-20261017-pass20'
primary = destination / 'primary'
runner = Path('/tmp/pass20-runner')
ui = Path('/tmp/pass20-ui')
sha = lambda data: hashlib.sha256(data).hexdigest()


def write_once(path, data):
    assert not path.is_symlink(), path
    if path.exists():
        assert path.is_file() and path.read_bytes() == data, ('preserve existing bytes', path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)


def json_once(path, value):
    write_once(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


assert not (primary / 'raw-evidence.tar.gz').exists(), 'Retain once; preserve prior history'
assert not (primary / 'retention-verification.json').exists()
assert not (destination / 'SHA256SUMS').exists(), 'Do not replace an earlier retained manifest'
checkpoint = primary / 'inflight-checkpoint'
checkpoint_before = {
    str(path.relative_to(checkpoint)): sha(path.read_bytes())
    for path in checkpoint.rglob('*') if path.is_file()
}
freeze = json.loads((out / 'source-freeze.json').read_text())
assert len(freeze) == 779
assert all(sha((root / name).read_bytes()) == digest for name, digest in freeze.items())
freeze_hash = sha((out / 'source-freeze.json').read_bytes())

# Resolve each omitted source byte to a retained exact member. These archives
# also retain starting snapshots and both failed full-source candidates.
source_archive_names = [
    'starting-inputs.tar.gz', 'final-source-inputs.tar.gz',
    'failed-gate-1/final-source-inputs.tar.gz',
    'failed-gate-2/final-source-inputs.tar.gz',
]
archive_index = {}
for name in source_archive_names:
    path = out / name
    assert path.is_file() and not path.is_symlink()
    archive_hash = sha(path.read_bytes())
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        assert len({member.name for member in members}) == len(members)
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert '..' not in Path(member.name).parts
            if member.name.startswith('src/'):
                digest = sha(archive.extractfile(member).read())
                archive_index.setdefault((member.name, digest), dict(
                    archive=name, archive_sha256=archive_hash, member=member.name))

raw = {}
stage_hashes = {}
omitted = {}
fallback_sources = {}
for path in sorted(out.rglob('*')):
    if '__pycache__' in path.parts or path.suffix in {'.pyc', '.pyo'}:
        continue
    assert not path.is_symlink(), path
    if not path.is_file():
        continue
    name = path.relative_to(out).as_posix()
    data = path.read_bytes()
    stage_hashes[name] = sha(data)
    prefix = next((p for p in ('original-replay/', 'private-graph/')
                   if name.startswith(p + 'src/')), None)
    if prefix is not None:
        member = name[len(prefix):]
        key = (member, stage_hashes[name])
        if key in archive_index:
            omitted[name] = dict(sha256=stage_hashes[name], **archive_index[key])
            continue
        # A historical private tree may contain one unique intermediate file.
        # Preserve that file normally rather than dropping it or copying the
        # entire source tree merely because no archive covers these bytes.
        fallback_sources[name] = dict(sha256=stage_hashes[name], retained_path=name)
    is_raw = path.suffix in {'.xml', '.exe'} or (
        path.suffix in {'.txt', '.jsonl'} and len(data) > 64 * 1024)
    if is_raw:
        assert not (primary / name).exists(), ('raw target collision', name)
        raw[name] = data
    else:
        write_once(primary / name, data)

# Failed runs and candidate source archives remain identifiable under their
# original names. A later successful gate does not replace their histories.
for failed in ('failed-gate-1', 'failed-gate-2'):
    assert all(f'{failed}/{name}' in stage_hashes for name in (
        'failure-receipt.json', 'local-gate-status.json', 'source-freeze.json',
        'source-review.json', 'final-source-inputs.tar.gz', 'lint.txt'))
assert 'failed-gate-2/final.xml' in raw

retained_guards = {}
for name, expected in json.loads((out / 'guard-manifest.json').read_text()).items():
    path = Path(name)
    assert path.is_file() and not path.is_symlink()
    data = path.read_bytes()
    assert sha(data) == expected
    target = primary / 'guards' / path.name
    write_once(target, data)
    retained_guards[name] = dict(retained_path=str(target.relative_to(primary)), sha256=expected)
json_once(primary / 'guard-retention-map.json', retained_guards)
json_once(primary / 'omitted-duplicate-source-map.json', omitted)
json_once(primary / 'unique-private-source-map.json', fallback_sources)

for source, target in ((ui, destination / 'ui'),):
    assert source.is_dir()
    for path in sorted(source.rglob('*')):
        if '__pycache__' in path.parts or path.suffix in {'.pyc', '.pyo'}:
            continue
        assert not path.is_symlink(), path
        if path.is_file():
            write_once(target / path.relative_to(source), path.read_bytes())
if runner.exists():
    for path in sorted(runner.glob('*.json')):
        assert path.is_file() and not path.is_symlink()
        write_once(destination / 'runner' / path.name, path.read_bytes())

raw_archive = primary / 'raw-evidence.tar.gz'
with tarfile.open(raw_archive, 'x:gz') as archive:
    for name, data in sorted(raw.items()):
        info = tarfile.TarInfo(name)
        info.size = len(data)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(data))
raw_hashes = {name: sha(data) for name, data in raw.items()}
with tarfile.open(raw_archive, 'r:gz') as archive:
    members = archive.getmembers()
    assert len(members) == len(raw_hashes) and {m.name for m in members} == set(raw_hashes)
    assert all(m.isfile() and sha(archive.extractfile(m).read()) == raw_hashes[m.name] for m in members)
json_once(primary / 'raw-evidence-sha256.json', raw_hashes)
json_once(primary / 'working-stage-sha256.json', stage_hashes)
assert all(sha((out / name).read_bytes()) == digest for name, digest in stage_hashes.items())
assert all(sha((root / name).read_bytes()) == digest for name, digest in freeze.items())
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
subprocess.run(['git', 'diff', '--check'], check=True)
write_once(primary / 'final-git-status.txt', subprocess.check_output(['git', 'status', '--short']))

gate = json.loads((out / 'local-gate-status.json').read_text())
gate_ok = len(gate) == 9 and all(row['exit_code'] == 0 and
                              row['source_freeze_sha256'] == freeze_hash for row in gate)
gate_receipt = json.loads((out / 'gate-verification.json').read_text()) if (out / 'gate-verification.json').exists() else None
if gate_ok:
    assert gate_receipt and gate_receipt['source_freeze_sha256'] == freeze_hash
    assert gate_receipt['all_nine_phases_fresh'] and gate_receipt['failures'] == gate_receipt['errors'] == 0
campaigns = json.loads((out / 'campaign-verification.json').read_text()) if (out / 'campaign-verification.json').exists() else None
view = json.loads((out / 'primary-capture-review.json').read_text()) if (out / 'primary-capture-review.json').exists() else None
if campaigns:
    assert gate_ok and view and view['reviewed'] == campaigns['captures_for_primary_view']
    assert campaigns['source_freeze_sha256'] == freeze_hash
assert checkpoint_before == {
    str(path.relative_to(checkpoint)): sha(path.read_bytes())
    for path in checkpoint.rglob('*') if path.is_file()
}
receipt = dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               compacted_raw_files=len(raw), raw_original_bytes=sum(map(len, raw.values())),
               raw_archive_bytes=raw_archive.stat().st_size, raw_archive_readback=True,
               source_freeze_sha256=freeze_hash, source_inputs_unchanged=779,
               duplicate_source_files_indexed=len(omitted), unique_private_sources_preserved=len(fallback_sources),
               source_archives_retained=source_archive_names,
               inflight_checkpoint_unchanged=True, existing_files_overwritten=0,
               index_empty=True, staged_files=0, working_staging_retained=str(out),
               runner_fixture_files=campaigns['runner_fixture_files_hashed'] if campaigns else 0,
               report_artifact_files=campaigns['retained_report_files'] if campaigns else 0,
               screenshots=len(campaigns['captures_for_primary_view']) if campaigns else 0,
               final_campaigns='PASS; exact artifact readback' if campaigns else 'HELD; no acceptance claimed',
               local_gate='PASS; all nine fresh phases' if gate_ok else 'FAILED or incomplete; see logs/status',
               historical_runs='Both failed pass20 gates, all prior candidate logs and source archives retained; no earlier abort/signal/latency attribution',
               source_committed=False, pushed=False, deployed=False)
json_once(primary / 'retention-verification.json', receipt)
files = sorted(p for p in destination.rglob('*') if p.is_file() and
               p.name != 'SHA256SUMS' and '__pycache__' not in p.parts)
assert all(not p.is_symlink() for p in files)
manifest = ''.join(sha(p.read_bytes()) + '  ' + str(p.relative_to(destination)) + '\n' for p in files)
write_once(destination / 'SHA256SUMS', manifest.encode())
assert all(sha((destination / line.split('  ', 1)[1]).read_bytes()) == line.split('  ', 1)[0]
           for line in manifest.splitlines())
print(json.dumps(dict(receipt, retained_files_hashed=len(files),
                      retained_bytes=sum(p.stat().st_size for p in files)), indent=2))
