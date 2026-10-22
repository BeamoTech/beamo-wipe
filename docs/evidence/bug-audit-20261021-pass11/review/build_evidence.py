"""Retain PASS11 only after completed gates and exact source/result checks."""
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
out = repo / 'docs/evidence/bug-audit-20261021-pass11'
load = lambda p: json.loads(p.read_text())
freeze = load(r / 'final-freeze.json')
assert load(r / 'final-sequence.status.json')['exit_code'] == 0
assert load(r / 'final-tests.status.json')['exit_code'] == 0
log = (r / 'final-tests.log').read_text()
assert '[ci-hosted] PASS phase=tests' in log and 'warnings summary' not in log
assert not re.search(r'\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b', log)
frozen = load(r / 'final-source-sha256.json')
assert len(frozen) == 822
assert all(hashlib.sha256((repo / n).read_bytes()).hexdigest() == h for n, h in frozen.items())
names = ['final-new-regressions', 'final-original-probes',
         'final-model-protected_alias_capacity_matrix', 'final-model-cancellation_ownership_matrix',
         'final-model-review_detour_layout_matrix', 'final-model-volatile_transaction_matrix',
         'final-lint', 'final-preview', 'final-negative', 'doctor-test', 'doctor-desktop',
         'final-go-new', 'final-go-original-probes', 'final-plan-model', 'final-go-race',
         'final-go-vet', 'final-go-fuzz', 'final-windows-test-build', 'final-desktop-build',
         'actual-preview-inspect', 'artifact-inspection', 'system-browser-tests']
groups = [load(r / (n + '.status.json')) for n in names]
assert all(g['exit_code'] == 0 for g in groups)
reports = {}
seen = set()
for name, passed, skipped in [('final-tests.xml', 11769, 28), ('final-tests.xml.orca.xml', 1, 0)]:
    c = list(E.parse(r / name).iter('testcase'))
    ids = {(x.get('classname'), x.get('name')) for x in c}
    assert len(c) == len(ids) == passed + skipped and not ids.intersection(seen)
    assert all(x.find(t) is None for x in c for t in ('failure', 'error'))
    s = [x for x in c if x.find('skipped') is not None]
    assert len(s) == skipped
    seen.update(ids)
    reports[name] = {'cases': len(c), 'passed': passed, 'skipped': skipped,
                     'failures': 0, 'errors': 0, 'junit_sha256': hashlib.sha256((r / name).read_bytes()).hexdigest(),
                     'skips': [{'id': x.get('classname') + '::' + x.get('name'), 'message': x.find('skipped').get('message')} for x in s]}
assert len(seen) - 28 == 11770
execution = {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'client_timezone': 'America/Chicago', 'source_manifest_sha256': freeze['source_manifest_sha256'],
             'canonical_tests': {**load(r / 'final-tests.status.json'), 'python_warning_count': 0,
                                 'main_passed': 11769, 'main_skipped': 28, 'separate_orca_passed': 1},
             'completed_groups': groups, 'container_context': load(r / 'final-sequence.status.json'),
             'context': 'Serial checks in one unprivileged container; child umask022/private72DPI X11. Source frozen. Independent bundle byte inspection.',
             'actual_device_or_power_actions': False, 'remote_write_or_release': False}
(r / 'final-check-status.json').write_text(json.dumps(execution, indent=2) + '\n')
assert not out.exists(), 'Retain once; preserve any failed attempt before correction'
out.mkdir(parents=True)


def retain(src, target, compress=False):
    p = out / (target + ('.gz' if compress else ''))
    p.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    p.write_bytes(gzip.compress(data, mtime=0) if compress else data)


for name in ['baseline.json', 'runtime-observation.json', 'starting-source-sha256.json',
             'final-freeze.json', 'independent-review.json', 'independent-reviewer-junit.json',
             'python-expanded-before-inputs.json', 'go-expanded-before-inputs.json',
             'inhibit-before-inputs.json', 'pipe-before-inputs.json', 'size-before-inputs.json',
             'model-replay-provenance.json', 'plan_freshness_matrix_test.go', 'plan-model-overlay.json',
             'plan-freshness-matrix.json', 'pipe_deadline_probe_test.go', 'pipe_lifetime_helper.py',
             'output_size_probe_test.go', 'output_size_helper.py', 'test_inhibit_optional_probe.py',
             'go-originals-overlay.json', 'pipe-probe-overlay.json', 'size-baseline-overlay.json',
             'go-expanded-baseline-overlay.json', 'baseline-io.go', 'replay_python_baseline.py',
             'run_group.py', 'run_final_sequence.py', 'build_evidence.py', 'review_artifacts.py',
             'inspect_live_preview.py', 'system_browser_check.py']:
    retain(r / name, 'review/' + name)
retain(r / 'final-source-sha256.json', 'source-sha256.json')
retain(r / 'artifact-review.json', 'artifact-review.json')
retain(r / 'final-check-status.json', 'checks/execution.json')
for p in sorted((r / 'model-replays').iterdir()):
    if p.is_file() and p.suffix in {'.py', '.json'}:
        retain(p, 'review/model-replays/' + p.name)
for name in [*names, 'final-tests']:
    retain(r / (name + '.status.json'), 'checks/status/' + name + '.json')
    retain(r / (name + '.log'), 'checks/' + name + '.log', compress=True)
for name in ['final-tests.xml', 'final-tests.xml.orca.xml', 'final-new-regressions.xml',
             'final-original-probes.xml', 'system-browser-tests.xml']:
    retain(r / name, 'checks/' + name, compress=True)
for name in ['actual-preview.json', 'actual-preview.log', 'system-browser-runtime.json']:
    retain(r / name, 'checks/' + name)
for prefix in ['pipe-independent-before', 'size-independent-before', 'inhibit-independent-before',
               'python-expanded-independent-before', 'go-expanded-independent-before']:
    for p in sorted(r.glob(prefix + '.*')):
        if p.is_file():
            retain(p, 'proofs/' + p.name, compress=p.suffix in {'.xml', '.log'})
for owner in ['discovery', 'runner', 'ui', 'recovery', 'boot']:
    for p in sorted((w / owner).iterdir()):
        if not p.is_file() or 'checkpoint' in p.name.lower():
            continue
        if p.suffix not in {'.py', '.go', '.json', '.xml', '.log', '.txt', '.exit', '.jsonl', '.stderr', '.md', '.patch', '.diff'}:
            continue
        history = p.name.startswith(('history-', 'initial-'))
        target = ('history/' if history else 'reviewers/') + owner + '/' + p.name
        retain(p, target, compress=p.suffix in {'.xml', '.log', '.jsonl'})
summary = {'base_commit': freeze['baseline_commit'], 'branch': 'fix/safety-audit-20261019',
           'audit_date': '2026-10-21', 'client_timezone': 'America/Chicago', 'verified_root_causes': 3,
           'canonical_reports': reports, 'canonical_unique_passed': 11770,
           'canonical_skipped_unverified': 28, 'canonical_python_warning_count': 0,
           'new_python_regressions_passed': 56, 'baseline_main_test_ids_retained': 11741,
           'baseline_skip_ids_and_reasons_unchanged': True, 'verified_source_files': 822,
           'source_manifest_sha256': freeze['source_manifest_sha256'],
           'all_existing_test_files_byte_identical': True, 'old_assertions_preserved': True,
           'go_full_race_named_pass_events': 418, 'go_full_race_native_skips': ['TestLinuxInventoryRetainsPartitionParents', 'TestWindowsInventoryReportsOnlyLauncherPartitionPass13'],
           'new_go_leaf_cases': 47, 'new_go_top_level_tests_including_helper': 5,
           'new_go_named_pass_events': 52, 'baseline_go_named_results_retained': 368,
           'external_go_model_tests': 1, 'system_browser_supplement_passed': 9,
           'system_browser_is_pinned': False, 'configured_mypy': 'PASS: no issues in 52 source files',
           'native_or_physical_qualification': False, 'remote_write_or_release_performed': False}
(out / 'final-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
shutil.copyfile(r / 'README.final.md', out / 'README.md')
shutil.copyfile(r / 'verify_retained.py', out / 'verify_retained.py')
manifest = {str(p.relative_to(out)): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(out.rglob('*')) if p.is_file()}
(out / 'artifacts-sha256.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
subprocess.run(['python3', str(out / 'verify_retained.py')], cwd=repo, check=True)
print(json.dumps({'sources': 822, 'retained_artifacts': len(manifest), 'unique_python_passes': 11770,
                  'unchanged_skips': 28, 'new_python_cases': 56, 'new_go_scenarios': 47, 'verified_roots': 3}))
