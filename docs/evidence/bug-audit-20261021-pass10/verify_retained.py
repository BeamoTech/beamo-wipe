"""Verify PASS10 source, preserved tests, exact outcomes and retained bytes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as E

out = Path(__file__).resolve().parent
repo = out.parents[2]
load = lambda p: json.loads(p.read_text())


def cases(p):
    return list(E.fromstring(gzip.decompress(p.read_bytes())).iter('testcase'))


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


raw = (out / 'source-sha256.json').read_bytes()
frozen = json.loads(raw)
assert len(frozen) == 820
assert hashlib.sha256(raw).hexdigest() == '822c1b77b4fe9bba5a86813cb5e98f9594975f26b98cf8c5146affa1779dc7a1'
for name, digest in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=repo).decode().split('\0')
selected = {n for n in names if n and (n.startswith(('src/', 'tests/', 'scripts/', 'packaging/', 'desktop/', 'developer_tests/'))
            or n in {'dev.py', 'pyproject.toml', 'requirements-dev.txt', 'preview'}) and (repo / n).is_file()}
assert selected == set(frozen)
start = load(out / 'review/starting-source-sha256.json')
assert len(start) == 818
for name, digest in start.items():
    if name.startswith(('tests/', 'developer_tests/')) or (name.startswith('desktop/') and name.endswith('_test.go')):
        assert frozen[name] == digest, name
review = load(out / 'review/independent-review.json')
assert review['all_existing_test_files_byte_identical'] is True
assert review['old_assertions_preserved'] is True and review['verified_root_causes'] == 2
summary = load(out / 'final-summary.json')
assert summary['source_manifest_sha256'] == hashlib.sha256(raw).hexdigest()
seen = set()
passed = skipped = 0
for name, record in summary['canonical_reports'].items():
    p = out / 'checks' / (name + '.gz')
    c = cases(p)
    assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest() == record['junit_sha256']
    assert len(c) == len(ids(c)) == record['cases'] and not seen.intersection(ids(c))
    seen.update(ids(c))
    assert all(x.find(t) is None for x in c for t in ('failure', 'error'))
    passed += len(c) - len(skips(c))
    skipped += len(skips(c))
    if name == 'final-tests.xml':
        main = c
assert passed == summary['canonical_unique_passed'] == 11714
assert skipped == summary['canonical_skipped_unverified'] == 28
old = cases(out.parent / 'bug-audit-20261021-pass9/checks/final-tests.xml.gz')
new = green(out / 'checks/final-new-regressions.xml.gz', 38)
assert len(ids(old)) == 11703 and ids(old) <= ids(main) and ids(main) - ids(old) == ids(new)
assert skips(old) == skips(main) and summary['baseline_skip_ids_and_reasons_unchanged'] is True
for path, failures, controls in [
    ('proofs/late-decode-expanded-before.xml.gz', 16, 22),
    ('proofs/late-decode-independent-before.xml.gz', 2, 2),
    ('reviewers/ui/late-decode-independent-before.xml.gz', 2, 2),
]:
    c = cases(out / path)
    assert len(c) == len(ids(c)) == failures + controls
    assert all(x.find(t) is None for x in c for t in ('error', 'skipped'))
    assert sum(x.find('failure') is not None for x in c) == failures
    if failures == 16:
        assert {x.get('name') for x in c} == {x.get('name') for x in new}
proof = load(out / 'review/late-decode-expanded-before-inputs.json')
assert proof['baseline'] == review['baseline_commit']
assert proof['app_sha256'] == start['src/beamo_wipe/app.py']
assert proof['test_sha256'] == frozen['tests/test_app_late_decode_refusal_pass10_20261021.py']
for path, count in [
    ('checks/final-original-probes.xml.gz', 8), ('checks/system-browser-tests.xml.gz', 9),
    ('checks/app-fixed-adjacent.xml.gz', 249), ('reviewers/runner/focused.xml.gz', 1643),
    ('reviewers/ui/focused-ui.xml.gz', 272), ('reviewers/recovery/focused-umask022.xml.gz', 1063),
    ('reviewers/boot/python-adjacent.xml.gz', 255),
]:
    green(out / path, count)
discovery = cases(out / 'reviewers/discovery/focused.xml.gz')
assert len(discovery) == len(ids(discovery)) == 2407 and len(skips(discovery)) == 6
assert all(x.find(t) is None for x in discovery for t in ('failure', 'error'))
assert all(skips(old).get(i) == reason for i, reason in skips(discovery).items())
execution = load(out / 'checks/execution.json')
assert execution['canonical_tests']['exit_code'] == execution['container_context']['exit_code'] == 0
assert execution['canonical_tests']['python_warning_count'] == summary['canonical_python_warning_count'] == 0
assert all(g['exit_code'] == 0 for g in execution['completed_groups'])
for phase in ('lint', 'preview', 'negative', 'tests'):
    assert '[ci-hosted] PASS phase=' + phase in (out / 'checks' / ('final-' + phase + '.log')).read_text()
assert 'warnings summary' not in (out / 'checks/final-tests.log').read_text()


def goevents(p):
    data = gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes()
    return [json.loads(line) for line in data.decode().splitlines()]


def goresults(events):
    c = [x for x in events if 'Test' in x and x['Action'] in {'pass', 'fail', 'skip'}]
    assert len(c) == len({(x['Package'], x['Test']) for x in c})
    return {(x['Package'], x['Test']): x['Action'] for x in c}


go = goevents(out / 'checks/final-go-race.jsonl.gz')
assert not any(x['Action'] == 'fail' for x in go)
assert go[-1]['Action'] == 'pass' and 'Test' not in go[-1]
assert sum(x['Action'] == 'pass' and 'Test' in x for x in go) == summary['go_full_race_named_pass_events'] == 366
assert {x['Test'] for x in go if x['Action'] == 'skip'} == set(summary['go_full_race_native_skips']) == {'TestLinuxInventoryRetainsPartitionParents', 'TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert '(cached)' not in gzip.decompress((out / 'checks/final-go-race.jsonl.gz').read_bytes()).decode()
assert 'execs: 350000' in (out / 'checks/final-go-fuzz.log').read_text()
old_go = goresults(goevents(out.parent / 'bug-audit-20261021-pass9/checks/final-go-race.jsonl.gz'))
full_go = goresults(go)
new_go = goresults(goevents(out / 'checks/final-go-new.jsonl.gz'))
assert len(old_go) == 340 and len(full_go) == 368 and len(new_go) == 28
assert old_go.items() <= full_go.items() and set(full_go) - set(old_go) == set(new_go)
assert set(new_go.values()) == {'pass'}
for path, failures, controls in [
    ('proofs/close-expanded-independent-before.log.gz', 18, 6),
    ('reviewers/boot/expanded-before.log', 18, 6),
    ('proofs/close-authority-independent-before.log.gz', 2, 2),
]:
    events = goevents(out / path)
    result = goresults(events)
    leaves = {name: value for (_, name), value in result.items() if '/' in name}
    assert len(leaves) == failures + controls
    assert list(leaves.values()).count('fail') == failures and list(leaves.values()).count('pass') == controls
    assert not any('DATA RACE' in x.get('Output', '') for x in events)
    if failures == 18:
        assert set(result) == set(new_go)
for path in ['review/close-expanded-independent-before-inputs.json', 'reviewers/boot/expanded-before-receipt.json']:
    proof = load(out / path)
    assert proof['baseline'] == review['baseline_commit']
    assert proof['product_sha256'] == start['desktop/main.go']
    assert proof['test_sha256'] == frozen['desktop/close_admission_pass10_20261021_test.go']
originals = goresults(goevents(out / 'checks/final-go-original-probes.jsonl.gz'))
assert len(originals) == 15 and set(originals.values()) == {'pass'}
retirement = goresults(goevents(out / 'checks/final-retirement-model.jsonl.gz'))
assert len(retirement) == 1 and set(retirement.values()) == {'pass'}
retirement_data = load(out / 'review/retirement-idle-matrix.json')
assert retirement_data['counts'] == {
    'age_refusals': 48, 'busy_preservations': 72, 'cases': 216, 'manual_restart_refusals': 4,
    'mismatches': 0, 'native_callbacks': 0, 'new_idle_retirements': 24, 'normal_checks': 12,
    'normal_closes': 12, 'normal_restarts': 4, 'post_retirement_refusals': 96,
    'preclosed_idempotence': 72, 'preview_restarts': 4, 'repeated_retirements': 96, 'state_reads': 12,
}
models = out / 'review/model-replays'
typed = load(models / 'typed-source-contract-matrix.json')
assert typed['states'] == typed['strict_resolver_calls'] == typed['parsed_strict_results'] == typed['public_fake_discovery_calls'] == 3360
assert (typed['strict_successes'], typed['strict_refusals'], typed['fake_successes'], typed['fake_refusals']) == (1488, 1872, 1584, 1776)
assert typed['missing_link_policy_controls'] == 96 and typed['selectable_target_observations'] == 3072
snapshot = load(models / 'log-snapshot-epoch-matrix.json')
assert (snapshot['cases'], snapshot['positive_completed_controls'], snapshot['refusal_controls']) == (384, 36, 348)
assert snapshot['cut_tail_cases'] == 240 and snapshot['concurrent_append_scans'] == 48
refresh = load(models / 'refresh_generation_matrix.json')
assert (refresh['scenarios'], refresh['refresh_claims'], refresh['invalid_outcome_refusals']) == (405, 720, 225)
assert (refresh['stale_completions_ignored'], refresh['duplicate_completions_ignored']) == (855, 135)
assert refresh['empty_inventory_controls'] == 45 and refresh['clean_retries'] == 315
assert refresh['blocked_erase_calls'] == 5715 and refresh['explicit_fake_starts'] == 405
bundle = load(models / 'bundle-readback-matrix.json')
assert bundle['contexts'] == bundle['positive_bundles'] == bundle['content_manifest_checks'] == 24
assert bundle['duplicate_session_refusals'] == bundle['extra_file_refusals'] == 24
assert bundle['tamper_refusals'] == bundle['restored_positive_rechecks'] == 1680
for model in (typed, snapshot, refresh, bundle):
    assert model['native_callbacks'] == 0 and not model['mismatches']
for model in (typed, snapshot, refresh, bundle, retirement_data):
    for name, digest in model['source_sha256'].items():
        assert frozen[name] == digest
for name, record in load(out / 'review/model-replay-provenance.json').items():
    script = (models / name).read_bytes()
    assert hashlib.sha256(script).hexdigest() == record['exact_script_sha256']
    assert script == (out / 'reviewers' / record['reviewer'] / name).read_bytes()
original = (out / 'reviewers/boot/retirement_idle_matrix_test.go').read_text()
replay = (out / 'review/retirement_idle_matrix_test.go').read_text()
assert original.replace('/workspace/beamo-tools/audit-pass10-20261021/boot/retirement-idle-matrix.json', '/workspace/beamo-tools/audit-pass10-20261021/root/retirement-idle-matrix.json') == replay
preview = load(out / 'checks/actual-preview.json')
assert preview['normal_close_acceptance'] is True and preview['returncode'] == 0
assert preview['fake_disks_only'] is True and preview['welcome_content_observed_before_capture'] is True
assert load(out / 'checks/system-browser-runtime.json')['pinned_playwright_runtime'] is False
assert load(out / 'artifact-review.json')['independent_bundle_verifier'].startswith('PASS:')
manifest = load(out / 'artifacts-sha256.json')
actual = {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p != out / 'artifacts-sha256.json'}
assert actual == set(manifest)
for name, record in manifest.items():
    data = (out / name).read_bytes()
    assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'], name
print(json.dumps({'verified_source_files': 820, 'retained_artifacts': len(manifest),
                  'unique_passed': passed, 'skipped_unverified': skipped, 'new_python_regressions_passed': 38,
                  'new_go_leaf_cases': 24, 'new_go_named_pass_events': 28,
                  'prior_main_ids_retained': 11703, 'all_old_test_files_byte_identical': True}))
