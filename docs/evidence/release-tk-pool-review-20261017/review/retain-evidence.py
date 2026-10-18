"""Retain PR90 review evidence after the fresh local gate passes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path('/root/dev/Beamo Wipe')
BASE = Path('/tmp/beamo-release-20261017')
WORK = BASE / 'tk-pool-review'
GATES = WORK / 'local-gates-v2'
DEST = ROOT / 'docs/evidence/release-tk-pool-review-20261017'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


gate = json.loads((GATES / 'gate-verification.json').read_text())
native = json.loads((GATES / 'native-final-readback.json').read_text())
assert gate['failures'] == gate['errors'] == 0
assert gate['phases'] == 9 and native['canonical_child_results'] == 65
identity = json.loads((WORK / 'candidate-identity-v2.json').read_text())
assert gate['source_freeze_sha256'] == identity['source_freeze_sha256']
assert not DEST.exists()
DEST.mkdir()
for source in sorted(WORK.iterdir()):
    if not source.is_file() or source.name == 'pr-body-before.json':
        continue
    if source.name in ('original-tk_wizard.py', 'partition-v1-tk_wizard.py'):
        write(DEST / 'review' / (source.name + '.gz'), gzip.compress(source.read_bytes(), mtime=0))
    else:
        write(DEST / 'review' / source.name, source.read_bytes())
for label in ('original-race-replay', 'original-warning-replay'):
    for name in ('result.xml', 'stdout.txt', 'stderr.txt'):
        write(DEST / 'review' / label / name, (WORK / label / name).read_bytes())

canonical = ROOT / 'docs/evidence/bug-audit-20261017-pass21/primary/raw-evidence.tar.gz'
hashes = json.loads((canonical.parent / 'raw-evidence-sha256.json').read_text())
with tarfile.open(canonical, 'r:gz') as archive:
    assert sha(archive.extractfile('desktop-windows.test.exe').read()) == hashes['desktop-windows.test.exe']
for directory, label in ((GATES, 'local-gates'), (WORK / 'local-gates', 'initial-unqualified-local-gates')):
    binary = directory / 'desktop-windows.test.exe'
    assert sha(binary.read_bytes()) == hashes['desktop-windows.test.exe']
    for source in sorted(directory.iterdir()):
        if source.is_file() and source != binary:
            write(DEST / label / source.name, source.read_bytes())
    write(DEST / label / 'duplicate-compiled-artifact-map.json', (json.dumps({
        'desktop-windows.test.exe': {'sha256': hashes['desktop-windows.test.exe'],
            'bytes': binary.stat().st_size,
            'canonical_archive': '../bug-audit-20261017-pass21/primary/raw-evidence.tar.gz',
            'member': 'desktop-windows.test.exe',
            'meaning': 'Identical bytes only; this candidate independently reran the compile.'}}, indent=2) + '\n').encode())
    for name, digest in json.loads((directory / 'guard-manifest.json').read_text()).items():
        source = Path(name)
        assert sha(source.read_bytes()) == digest
        write(DEST / label / 'guards' / source.name, source.read_bytes())

codeql = BASE / 'codeql-review'
for name in ('trace-findings.py', 'trace-findings.json', 'focused-tests.log', 'focused-tests.xml',
             'focused-display-tests.log', 'focused-display-tests.xml'):
    write(DEST / 'codeql' / name, (codeql / name).read_bytes())
alerts = []
for number in (32, 33, 34, 35):
    before = json.loads((codeql / f'alert-{number}-before.json').read_text())
    after = json.loads((codeql / f'alert-{number}-dismissal.json').read_text())
    assert after['state'] == 'dismissed' and after['dismissed_reason'] == 'false positive'
    alerts.append({'number': number, 'url': after['html_url'],
                   'rule': before['rule']['id'], 'location': before['most_recent_instance']['location'],
                   'source_commit': before['most_recent_instance']['commit_sha'],
                   'state': after['state'], 'reason': after['dismissed_reason'],
                   'rationale': after['dismissed_comment'], 'dismissed_at': after['dismissed_at']})
write(DEST / 'codeql/reviewed-alerts.json', (json.dumps(alerts, indent=2) + '\n').encode())

readme = f'''# PR90 Tk retirement race and CodeQL review

2026-10-17–18 / Codex, BeamoTech/beamo-wipe, fix/safety-audit-20261015.
Parent commit: {identity['parent_sha']}.
This is local candidate evidence. Protected merge, exact-main hosted CI and
production publication remain pending; no physical hardware was tested.

Greptile's [summary](https://github.com/BeamoTech/beamo-wipe/pull/90#issuecomment-6243204273)
and [P1](https://github.com/BeamoTech/beamo-wipe/pull/90#discussion_r4304997909)
identify the same confirmed race in both native retirement pools. A foreign
collector snapshot retains record tuples without incrementing the native
resource's direct refcount. The creator can remove the shared pool entry,
leaving the foreign snapshot to release the final tuple on the wrong thread.

Records are now partitioned by their creating Thread before any snapshot is
taken. Empty metadata buckets remain to protect an in-progress pin from a
reentrant GC drain. Resource refcount checks, original destructors and creator
ownership remain. Only four helpers changed; the wizard class AST and every
other top-level definition are unchanged. Disk discovery, authorization and
nwipe command construction are unchanged.

The first full local run returned zero but was rejected for one material
unraisable GC warning: empty metadata buckets let unrelated thread teardown
call current_thread and construct DummyThread while the audio fixture had
replaced Thread.__init__. Its10137 main passes, one Orca pass,14 skips and
warning remain in initial-unqualified-local-gates/. Two raw-thread regressions
reproduce the same KeyError before correction. Actual Tk owners now tag their
creating thread using thread-local metadata during pinning. Drains read that
tag without creating thread wrappers for unrelated GC callers. Actual Thread
identity still selects each pool, without relying on reusable OS thread IDs.

| Verification | Observed result |
| --- | --- |
| Original deterministic regression v2 | 8 failures, 2 external-owner controls passed |
| Final test bytes replayed against archived original sources | Same8 ownership and2 callback failures;2 controls passed |
| Fixed deterministic regression | 10 passed |
| Unregistered-thread reproduction | 2 failures before correction |
| Final focused native/audio run | 87 passed with unraisable warnings fatal;65 native child results zero exit/empty stderr |
| Fresh full local gate | All9 phases passed; {gate['passed']} combined Python/Orca passes |
| Local artifact skips | {gate['skipped']} exact existing artifact-dependent skips; retained as skips |
| New and prior audit modules | {gate['regression_modules']} modules/{gate['regression_cases']} cases passed |
| Full-gate native children | 65 zero exits/empty stderr/no parent timeout; {native['direct_child_source_provenance']} direct source hashes |

The new native child invokes actual worker GC and original Font, Variable and
Image destructors on an isolated72DPI display, with application side effects
forbidden. It checks every native wrapper settles on its creating thread.
The original v1 reproduction inadvertently paused the empty asset pool before
the interpreter pool: four failures and six passes. Its output/test remain;
v2 corrects that fixture before product code changed. The final13-case module
adds the real-native child and two raw-thread cases after the original10-case
reproduction. The clean full gate is a fresh second run on a separate freeze;
the first run's warning is never counted as a successful qualification.

Runtime SHA-256: {identity['runtime_source_sha256']}.
Tk source SHA-256: {identity['tk_sha256']}.
Frozen876-input source map: {identity['source_freeze_sha256']}.
No source changed during the full gate. The Windows test binary is indexed to
its identical archived bytes; the current compile ran independently. This is
a crossbuild, with native Windows and hosted ISO/QEMU qualification required
for the new commit before release.

Four CodeQL URL findings (32–35) concern archived audit scripts checking for
visible support text in complete HTML reports. Every script matches committed
bytes;280 bundle files authenticate and16 failed reports parse with support
text and zero URL attributes. No URL validation/request/redirect/authorization
sink exists. All four alerts were dismissed as false positives with individual
rationale. GitHub CodeQL was then green on4f7ee8d. CodeQL configuration and
all historical archives remain unchanged. Focused23 report/support cases pass
at72DPI. An initial no-display22-pass/one-Tk-skip attempt is retained separately.
The initial long-comment API dismissal request exited1 (stderr not retained);
the concise request succeeded. No hosted retry or product change addressed
these false positives. This evidence does not pre-claim new-commit CodeQL.

Current local verification does not attribute historical native aborts,
SIGTERM, timing or loop incidents, or replace physical/firmware acceptance.
The receipt archive preserves failures, skips, source snapshots and commands;
SHA256SUMS authenticates retained files independently of Git text conversion.
'''
write(DEST / 'README.md', readme.encode())
scanner = (BASE / 'scan-delta-publication.py').read_text()
scanner = scanner.replace("Path('/tmp/beamo-release-20261017')", 'Path(' + repr(str(DEST)) + ')')
scanner = scanner.replace('publication-delta-inventory.json', 'content-inputs.json')
scanner = scanner.replace('publication-delta-content-review.json', 'publication-content-review.json')
write(DEST / 'review-publication-content.py', scanner.encode())
inputs = sorted(p for p in DEST.rglob('*') if p.is_file())
inputs.extend(ROOT / name for name in ('src/beamo_wipe/ui/tk_wizard.py', 'tests/test_tk_retired_pool_threads.py'))
write(DEST / 'content-inputs.json', (json.dumps({str(p): {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
    for p in inputs}, indent=2) + '\n').encode())
subprocess.run([sys.executable, str(DEST / 'review-publication-content.py')], check=True, cwd=ROOT)
content = json.loads((DEST / 'publication-content-review.json').read_text())
assert not content['potential_secret_patterns'] and not content['archive_media_members']
files = sorted(p for p in DEST.rglob('*') if p.is_file())
manifest = ''.join(sha(p.read_bytes()) + '  ' + str(p.relative_to(DEST)) + '\n' for p in files)
write(DEST / 'SHA256SUMS', manifest.encode())
assert all(sha((DEST / name).read_bytes()) == digest
           for digest, name in (line.split('  ', 1) for line in manifest.splitlines()))
print(json.dumps({'files': len(files), 'bytes': sum(p.stat().st_size for p in files),
                   'manifest_sha256': sha(manifest.encode()), 'directory': str(DEST)}))
