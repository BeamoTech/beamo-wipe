"""Seal final UI repair evidence only after the fresh full local gate passes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path('/root/dev/Beamo Wipe')
BASE = Path('/tmp/beamo-release-20261017')
WORK = BASE / 'hosted-ui-repair'
GATES = WORK / 'local-gates'
DEST = ROOT / 'docs/evidence/release-hosted-ui-repair-20261018'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


gate = json.loads((GATES / 'gate-verification.json').read_text())
native = json.loads((GATES / 'native-final-readback.json').read_text())
identity = json.loads((GATES / 'source-identity.json').read_text())
assert gate['phases'] == 9 and gate['failures'] == gate['errors'] == 0
assert gate['source_freeze_sha256'] == identity['source_freeze_sha256']
assert native['canonical_child_results'] == 65 and gate['regression_cases'] == 3943
assert not DEST.exists()
DEST.mkdir()
for source in sorted(WORK.iterdir()):
    if source.is_file():
        name = source.name
        data = source.read_bytes()
        if name.startswith('tk-') and name.endswith('.py'):
            name += '.gz'
            data = gzip.compress(data, mtime=0)
        put(DEST / 'preparation' / name, data)

canonical = ROOT / 'docs/evidence/bug-audit-20261017-pass21/primary/raw-evidence.tar.gz'
expected = json.loads((canonical.parent / 'raw-evidence-sha256.json').read_text())['desktop-windows.test.exe']
binary = GATES / 'desktop-windows.test.exe'
assert sha(binary.read_bytes()) == expected
with tarfile.open(canonical, 'r:gz') as archive:
    assert sha(archive.extractfile('desktop-windows.test.exe').read()) == expected
for source in sorted(GATES.iterdir()):
    if source.is_file() and source != binary:
        put(DEST / 'local-gates' / source.name, source.read_bytes())
put(DEST / 'local-gates/duplicate-compiled-artifact-map.json', (json.dumps({
    'desktop-windows.test.exe': {'sha256': expected, 'bytes': binary.stat().st_size,
        'canonical_archive': '../bug-audit-20261017-pass21/primary/raw-evidence.tar.gz',
        'member': 'desktop-windows.test.exe',
        'meaning': 'Identical bytes only; current compile execution remains independently recorded.'}}, indent=2) + '\n').encode())
for name, digest in json.loads((GATES / 'guard-manifest.json').read_text()).items():
    source = Path(name)
    assert sha(source.read_bytes()) == digest
    put(DEST / 'local-gates/guards' / source.name, source.read_bytes())
for source in sorted((BASE / 'bookworm-runtime').iterdir()):
    if source.is_file():
        put(DEST / 'bookworm' / source.name, source.read_bytes())
for source in sorted((BASE / 'ci-initial-evidence').rglob('*')):
    if source.is_file():
        put(DEST / 'failed-hosted' / source.relative_to(BASE / 'ci-initial-evidence'), source.read_bytes())
put(DEST / 'failed-hosted/console.log', (BASE / 'ci-initial-failed.log').read_bytes())
put(DEST / 'failed-hosted/artifact-metadata.json', (BASE / 'ci-initial-artifacts.json').read_bytes())
put(DEST / 'failed-hosted/archive-sha256.txt',
    (sha((BASE / 'ci-initial-evidence.zip').read_bytes()) + '  ci-initial-evidence.zip\n').encode())

readme = f'''# Final 0.2.13 hosted UI failure repair

2026-10-18 / Codex. BeamoTech/beamo-wipe, fix/safety-audit-20261015.
Parent commit {identity['parent_sha']}. This is local candidate evidence;
new-commit PR qualification, protected main CI and publication remain pending.
The earlier [Tk pool record](../release-tk-pool-review-20261017/README.md)
retains the original P1 proof and its separately qualified d8f527 snapshot.
This record supersedes its overall candidate qualification after later edits.

The [original PR run](https://github.com/BeamoTech/beamo-wipe/actions/runs/39079362211)
failed ten source tests: nine Tk callback lifetime failures and one fresh GTK
Return after closing sound controls. Its PR head was4f7ee8d; its actual tested
synthetic merge source was a77fbd94a7ce4d9079f7da0125a428ea4c94e30d.
Raw JUnit, five gate receipts and logs remain in failed-hosted/. The deliberate
negative mutant failure is an expected safety check, not an extra gate failure.
The run did not qualify ISO/QEMU; its15 skips are recorded separately from the
14 local artifact skips (the additional hosted skip is the absent legacy SDK).

An unprivileged local container used the exact CI Debian digest and matching
Python3.11.2, Tk8.6.13-2, Tcl8.6.13+dfsg-2, GTK3.24.38-2~deb12u3 and GI3.42.2.
The original three-module replay reproduced all9 Tk failures with47 controls.
Source was read-only; only owned output and public CA mounts were provided,
with no physical devices, Docker socket, privileged flags or host networking.
The positively identified container was stopped/removed after every test exec
finished. Its setup-only sleep exited137 during intentional Docker cleanup;
no test process was terminated. Mount/ID and cleanup receipts remain.

Owned roots now cancel their Tcl timers without deleting Tcl procedures.
Bookworm also queues a C-level theme notification absent from `after info`.
[Upstream Tk8.6.13](https://github.com/tcltk/tk/blob/core-8-6-13/generic/ttk/ttkTheme.c#L510)
confirms the native idle callback evaluates the Tcl notification procedure.
The retirement helper retains the original ThemeChanged body and adds a
root-existence guard, so obsolete notifications return before touching dead
widgets. Live notifications, failed-destroy retry behavior, ordinary Tcl errors
and other interpreters' queued work remain. All owned-root construction failure,
wizard teardown and startup close paths use the helper. No bgerror handler is
suppressed and no native destructor is replaced by the product.

The GTK native fixture requested zero-delay XTest presses. A real256-event
trace proves215 fresh synthetic presses reused the prior release timestamp
with heldFalse and were correctly rejected by the product's repeat guard.
The fixture now requests1ms server delay for fresh presses. A new256-event
regression requires every fresh press to have a distinct timestamp and remain
unblocked. Production GTK input code is byte-identical, all16 original assertion
predicates across14 parameterized cases remain, the exact same-time repeat
tests remain, and the original2s input bound is unchanged. The old single CI
failure had no recorded event timestamps: its exact retrospective attribution
is an inference. The verified fixture defect and new strict controls are the
concrete correction, rather than a claim about unrecorded old events.

| Verification | Observed result |
| --- | --- |
| Initial explicit native-timer regression | 4 failures before product edit |
| Timer-only attempt on Bookworm | 13 failures/33 controls; untracked native notification still failed |
| Corrected matching Debian UI modules | 62 passed, including all original failed cases |
| Matching Debian native lifetimes | 77 passed,65 native children zero exit/empty stderr |
| Ubuntu focused UI | 20 passed |
| Final fresh full local gate | All9 phases passed; {gate['passed']} combined Python/Orca passes, no warnings |
| Artifact-dependent local skips | {gate['skipped']} exact existing IDs; retained as skips |
| Audit regressions | {gate['regression_modules']} modules/{gate['regression_cases']} cases passed |
| Full native readback | 65 clean children;{native['direct_child_source_provenance']} direct source hashes |

Evidence-helper history remains explicit: the first request for40 identical
pytest node IDs ran only1 case because of de-duplication; a parameterized80-case
diagnostic then passed. A new Tcl control initially compared a Tcl string with
an integer; its failing fixture/log are preserved and conversion was corrected.
The earlier P1 native-output classifier correction is retained in its own record.
None of these helper outcomes replaces an applicable product check.

Frozen877-input map: {identity['source_freeze_sha256']}.
Runtime SHA-256: {identity['runtime_source_sha256']}.
Tk source SHA-256: {identity['tk_sha256']}.
All source inputs remain unchanged through the complete local gate. Windows
crossbuild bytes are indexed to their identical earlier archive; a new compile
ran, but this is not native Windows acceptance. Hosted ISO/QEMU and native
Windows still must qualify the exact new commit. Physical/firmware acceptance
and historical incident attribution remain unproved. No physical media was
written and no production release is established by this local record.
'''
put(DEST / 'README.md', readme.encode())
scanner = (BASE / 'scan-delta-publication.py').read_text()
scanner = scanner.replace("Path('/tmp/beamo-release-20261017')", 'Path(' + repr(str(DEST)) + ')')
scanner = scanner.replace('publication-delta-inventory.json', 'content-inputs.json')
scanner = scanner.replace('publication-delta-content-review.json', 'publication-content-review.json')
put(DEST / 'review-publication-content.py', scanner.encode())
inputs = sorted(p for p in DEST.rglob('*') if p.is_file())
inputs.extend(ROOT / name for name in ('src/beamo_wipe/ui/tk_wizard.py',
    'tests/test_tk_interpreter_callback_retirement.py', 'tests/test_accessible_focus_input_pass11.py'))
put(DEST / 'content-inputs.json', (json.dumps({str(p): {'sha256': sha(p.read_bytes()),
    'bytes': p.stat().st_size} for p in inputs}, indent=2) + '\n').encode())
subprocess.run([sys.executable, str(DEST / 'review-publication-content.py')], check=True, cwd=ROOT)
content = json.loads((DEST / 'publication-content-review.json').read_text())
assert not content['potential_secret_patterns'] and not content['archive_media_members']
files = sorted(p for p in DEST.rglob('*') if p.is_file())
manifest = ''.join(sha(p.read_bytes()) + '  ' + str(p.relative_to(DEST)) + '\n' for p in files)
put(DEST / 'SHA256SUMS', manifest.encode())
assert all(sha((DEST / name).read_bytes()) == digest
    for digest, name in (line.split('  ', 1) for line in manifest.splitlines()))
print(json.dumps({'files': len(files), 'bytes': sum(p.stat().st_size for p in files),
    'manifest_sha256': sha(manifest.encode()), 'directory': str(DEST)}))
