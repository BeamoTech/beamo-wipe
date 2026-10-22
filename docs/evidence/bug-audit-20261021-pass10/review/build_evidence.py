"""Retain PASS10 only after actual completed gates and exact identities."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as E

repo = Path('/workspace/beamo-wipe')
r = Path(__file__).parent
w = r.parent
out = repo / 'docs/evidence/bug-audit-20261021-pass10'
load = lambda p: json.loads(p.read_text())
freeze = load(r / 'final-freeze.json')


def cases(p):
    return list(E.parse(p).iter('testcase'))


def ids(c):
    return {(x.get('classname'), x.get('name')) for x in c}


def skips(c):
    return {(x.get('classname'), x.get('name')): x.find('skipped').get('message')
            for x in c if x.find('skipped') is not None}


def green(p, count):
    c = cases(p)
    assert len(c) == len(ids(c)) == count, (p, len(c), len(ids(c)))
    assert all(x.find(t) is None for x in c for t in ('failure', 'error', 'skipped')), p
    return c


assert load(r / 'final-sequence.status.json')['exit_code'] == 0
assert load(r / 'final-tests.status.json')['exit_code'] == 0
log = (r / 'final-tests.log').read_text()
assert '[ci-hosted] PASS phase=tests' in log and 'warnings summary' not in log
assert not re.search(r'\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b', log)
new = green(r / 'final-new-regressions.xml', 38)
green(r / 'final-original-probes.xml', 8)
green(r / 'system-browser-tests.xml', 9)
green(r / 'app-fixed-adjacent.xml', 249)
prior = list(E.fromstring(gzip.decompress((out.parent / 'bug-audit-20261021-pass9/checks/final-tests.xml.gz').read_bytes())).iter('testcase'))
assert len(ids(prior)) == 11703
main = cases(r / 'final-tests.xml')
orca = green(r / 'final-tests.xml.orca.xml', 1)
assert len(main) == len(ids(main)) == 11741
assert all(x.find(t) is None for x in main for t in ('failure', 'error'))
assert ids(prior) <= ids(main) and ids(main) - ids(prior) == ids(new)
assert skips(prior) == skips(main) and len(skips(main)) == 28
assert not ids(main).intersection(ids(orca))
frozen = load(r / 'final-source-sha256.json')
assert len(frozen) == 820
assert all(hashlib.sha256((repo / n).read_bytes()).hexdigest() == h for n, h in frozen.items())
names = ['final-new-regressions', 'final-original-probes',
         'final-model-typed_source_contract_matrix', 'final-model-log_snapshot_epoch_matrix',
         'final-model-refresh_generation_matrix', 'final-model-bundle_readback_matrix',
         'final-lint', 'final-preview', 'final-negative', 'doctor-test', 'doctor-desktop',
         'final-go-new', 'final-go-original-probes', 'final-retirement-model',
         'final-go-race', 'final-go-vet', 'final-go-fuzz', 'final-windows-test-build',
         'final-desktop-build', 'actual-preview-inspect', 'system-browser-tests', 'artifact-inspection']
groups = [load(r / (n + '.status.json')) for n in names]
assert all(g['exit_code'] == 0 for g in groups)
for phase in ('lint', 'preview', 'negative'):
    assert '[ci-hosted] PASS phase=' + phase in (r / ('final-' + phase + '.log')).read_text()
go = [json.loads(line) for line in (r / 'final-go-race.log').read_text().splitlines()]
assert not any(x['Action'] == 'fail' for x in go)
assert go[-1]['Action'] == 'pass' and 'Test' not in go[-1]
assert sum(x['Action'] == 'pass' and 'Test' in x for x in go) == 366
assert '(cached)' not in (r / 'final-go-race.log').read_text()
go_skips = [x['Test'] for x in go if x['Action'] == 'skip']
assert set(go_skips) == {'TestLinuxInventoryRetainsPartitionParents', 'TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert 'execs: 350000' in (r / 'final-go-fuzz.log').read_text()
assert load(r / 'artifact-review.json')['independent_bundle_verifier'].startswith('PASS:')
execution = {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'client_timezone': 'America/Chicago', 'source_manifest_sha256': freeze['source_manifest_sha256'],
             'canonical_tests': {**load(r / 'final-tests.status.json'), 'python_warning_count': 0,
                                 'main_passed': 11713, 'main_skipped': 28, 'separate_orca_passed': 1},
             'completed_groups': groups, 'container_context': load(r / 'final-sequence.status.json'),
             'context': 'Serial checks in one unprivileged container, child-only umask022/private72DPI X11. Host artifact byte inspection. Source frozen.',
             'actual_device_or_power_actions': False, 'remote_write_or_release': False}
(r / 'final-check-status.json').write_text(json.dumps(execution, indent=2) + '\n')
assert not out.exists(), 'Retain once; preserve any failed attempt before correction'
out.mkdir(parents=True)


def retain(src, target):
    p = out / target
    p.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    if p.suffix == '.gz':
        data = gzip.compress(data, mtime=0)
    p.write_bytes(data)


for name in ['baseline.json', 'runtime-observation.json', 'starting-source-sha256.json',
             'final-freeze.json', 'independent-review.json', 'independent-reviewer-junit.json',
             'late-decode-expanded-before-inputs.json', 'close-expanded-independent-before-inputs.json',
             'model-replay-provenance.json', 'retirement_idle_matrix_test.go', 'retirement-overlay.json',
             'retirement-idle-matrix.json', 'close_authority_probe_test.go', 'close-probe-overlay.json',
             'close-originals-overlay.json', 'run_group.py', 'run_final_sequence.py', 'build_evidence.py',
             'review_artifacts.py', 'inspect_live_preview.py', 'system_browser_check.py', 'test_late_decode_probe.py']:
    retain(r / name, 'review/' + name)
retain(r / 'final-source-sha256.json', 'source-sha256.json')
retain(r / 'artifact-review.json', 'artifact-review.json')
retain(r / 'final-check-status.json', 'checks/execution.json')
for p in sorted((r / 'model-replays').iterdir()):
    if p.is_file() and p.suffix in {'.py', '.json'}:
        retain(p, 'review/model-replays/' + p.name)
for name in [*names, 'final-tests']:
    retain(r / (name + '.status.json'), 'checks/status/' + name + '.json')
    suffix = '.jsonl.gz' if name in {'final-go-race', 'final-go-new', 'final-go-original-probes', 'final-retirement-model'} else '.log'
    retain(r / (name + '.log'), 'checks/' + name + suffix)
for name in ['final-tests.xml', 'final-tests.xml.orca.xml', 'final-new-regressions.xml',
             'final-original-probes.xml', 'system-browser-tests.xml', 'app-fixed-adjacent.xml']:
    retain(r / name, 'checks/' + name + '.gz')
for name in ['actual-preview.json', 'actual-preview.log', 'system-browser-runtime.json',
             'app-fixed-adjacent.log', 'app-fixed-adjacent.status.json']:
    retain(r / name, 'checks/' + name)
for prefix in ['late-decode-independent-before', 'late-decode-expanded-before',
               'close-authority-independent-before', 'close-expanded-independent-before']:
    for p in sorted(r.glob(prefix + '.*')):
        if p.is_file():
            retain(p, 'proofs/' + p.name + ('.gz' if p.suffix in {'.xml', '.log'} and prefix.startswith('close-') else '.gz' if p.suffix == '.xml' else ''))
for owner in ['discovery', 'runner', 'ui', 'recovery', 'boot']:
    for p in sorted((w / owner).iterdir()):
        if not p.is_file() or 'checkpoint' in p.name.lower():
            continue
        if p.suffix not in {'.py', '.go', '.json', '.xml', '.log', '.txt', '.exit', '.jsonl', '.stderr', '.md', '.patch', '.diff'}:
            continue
        history = any(s in p.name for s in ['history-', 'initial-', 'headless', 'setup-failure'])
        if owner == 'recovery' and p.name in {'focused.log', 'focused.xml', 'focused.status.json'}:
            history = True
        retain(p, ('history/' if history else 'reviewers/') + owner + '/' + p.name + ('.gz' if p.suffix in {'.xml', '.jsonl'} else ''))
reports = {}
for name, c in [('final-tests.xml', main), ('final-tests.xml.orca.xml', orca)]:
    reports[name] = {'cases': len(c), 'passed': len(c) - len(skips(c)), 'skipped': len(skips(c)),
                     'failures': 0, 'errors': 0, 'junit_sha256': hashlib.sha256((r / name).read_bytes()).hexdigest(),
                     'skips': [{'id': a + '::' + b, 'message': v} for (a, b), v in skips(c).items()]}
summary = {'base_commit': freeze['baseline_commit'], 'branch': 'fix/safety-audit-20261019',
           'audit_date': '2026-10-21', 'client_timezone': 'America/Chicago', 'verified_root_causes': 2,
           'canonical_reports': reports, 'canonical_unique_passed': 11714,
           'canonical_skipped_unverified': 28, 'canonical_python_warning_count': 0,
           'new_python_regressions_passed': 38, 'baseline_main_test_ids_retained': 11703,
           'baseline_skip_ids_and_reasons_unchanged': True, 'verified_source_files': 820,
           'source_manifest_sha256': freeze['source_manifest_sha256'],
           'all_existing_test_files_byte_identical': True, 'old_assertions_preserved': True,
           'go_full_race_named_pass_events': 366, 'go_full_race_native_skips': go_skips,
           'new_go_parent_tests': 4, 'new_go_leaf_cases': 24, 'new_go_named_pass_events': 28,
           'baseline_go_named_results_retained': 340, 'external_go_model_tests': 1,
           'system_browser_supplement_passed': 9, 'system_browser_is_pinned': False,
           'configured_mypy': 'PASS: no issues in 52 source files',
           'native_or_physical_qualification': False, 'remote_write_or_release_performed': False}
(out / 'final-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
shutil.copyfile(r / 'README.final.md', out / 'README.md')
shutil.copyfile(r / 'verify_retained.py', out / 'verify_retained.py')
manifest = {str(p.relative_to(out)): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(out.rglob('*')) if p.is_file()}
(out / 'artifacts-sha256.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
subprocess.run(['python3', str(out / 'verify_retained.py')], cwd=repo, check=True)
print(json.dumps({'sources': 820, 'retained_artifacts': len(manifest), 'unique_python_passes': 11714,
                  'unchanged_skips': 28, 'new_python_cases': 38, 'new_go_scenarios': 24, 'verified_roots': 2}))
