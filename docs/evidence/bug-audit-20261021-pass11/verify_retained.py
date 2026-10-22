"""Verify PASS11 frozen source, old assertions, exact results and retained bytes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as E

out = Path(__file__).resolve().parent
repo = out.parents[2]
load = lambda p: json.loads(p.read_text())


def raw(p):
    data = p.read_bytes()
    return gzip.decompress(data) if p.suffix == '.gz' else data


def cases(p):
    return list(E.fromstring(raw(p)).iter('testcase'))


def ids(c):
    return {(x.get('classname'), x.get('name')) for x in c}


def skips(c):
    return {(x.get('classname'), x.get('name')): x.find('skipped').get('message')
            for x in c if x.find('skipped') is not None}


def outcome(p, passes, failures=0, skipped=0):
    c = cases(p)
    assert len(c) == len(ids(c)) == passes + failures + skipped, p
    assert all(x.find('error') is None for x in c), p
    assert sum(x.find('failure') is not None for x in c) == failures, p
    assert len(skips(c)) == skipped, p
    return c


source = out / 'source-sha256.json'
frozen = load(source)
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert len(frozen) == 822 and digest == 'c5bd0ad6cf663f5231c88a3bddd9df1a9405f529109a92c62fa23ccef1a83992'
for name, h in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == h, name
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=repo).decode().split('\0')
selected = {n for n in names if n and (n.startswith(('src/', 'tests/', 'scripts/', 'packaging/', 'desktop/', 'developer_tests/'))
            or n in {'dev.py', 'pyproject.toml', 'requirements-dev.txt', 'preview'}) and (repo / n).is_file()}
assert selected == set(frozen)
start = load(out / 'review/starting-source-sha256.json')
assert len(start) == 820
for name, h in start.items():
    if name.startswith(('tests/', 'developer_tests/')) or (name.startswith('desktop/') and name.endswith('_test.go')):
        assert frozen[name] == h, name
review = load(out / 'review/independent-review.json')
freeze = load(out / 'review/final-freeze.json')
summary = load(out / 'final-summary.json')
assert review['verified_root_causes'] == freeze['verified_root_causes'] == summary['verified_root_causes'] == 3
assert review['all_existing_test_files_byte_identical'] and review['old_assertions_preserved']
assert summary['source_manifest_sha256'] == freeze['source_manifest_sha256'] == digest
main = outcome(out / 'checks/final-tests.xml.gz', 11769, skipped=28)
orca = outcome(out / 'checks/final-tests.xml.orca.xml.gz', 1)
assert not ids(main).intersection(ids(orca))
assert summary['canonical_unique_passed'] == 11770 and summary['canonical_skipped_unverified'] == 28
old = cases(out.parent / 'bug-audit-20261021-pass10/checks/final-tests.xml.gz')
new = outcome(out / 'checks/final-new-regressions.xml.gz', 56)
assert len(ids(old)) == 11741 and ids(old) <= ids(main) and ids(main) - ids(old) == ids(new)
assert skips(old) == skips(main) and summary['baseline_skip_ids_and_reasons_unchanged']
for name, c in [('final-tests.xml', main), ('final-tests.xml.orca.xml', orca)]:
    assert hashlib.sha256(raw(out / 'checks' / (name + '.gz'))).hexdigest() == summary['canonical_reports'][name]['junit_sha256']
outcome(out / 'checks/final-original-probes.xml.gz', 16)
outcome(out / 'checks/system-browser-tests.xml.gz', 9)
for path, passes, failures in [
    ('proofs/python-expanded-independent-before.xml.gz', 38, 18),
    ('reviewers/runner/expanded-before.xml.gz', 38, 18),
    ('proofs/inhibit-independent-before.xml.gz', 6, 6),
    ('reviewers/runner/inhibitor-diagnostic-before.xml.gz', 2, 2),
]:
    c = outcome(out / path, passes, failures)
    if failures == 18:
        assert {x.get('name') for x in c} == {x.get('name') for x in new}
for path in ['review/python-expanded-before-inputs.json', 'reviewers/runner/expanded-before-inputs.json']:
    p = load(out / path)
    assert p['baseline'] == review['baseline_commit']
    assert p['product_sha256'] == start['src/beamo_wipe/sleep_inhibit.py']
    assert p['test_sha256'] == frozen['tests/test_sleep_inhibit_diagnostic_retirement_pass11_20261021.py']
for path, passed, skip in [
    ('reviewers/discovery/focused.xml.gz', 2598, 6), ('reviewers/runner/focused.xml.gz', 1744, 0),
    ('reviewers/ui/focused-ui.xml.gz', 444, 0), ('reviewers/recovery/focused.xml.gz', 1063, 0),
    ('reviewers/recovery/adjacent.xml.gz', 449, 0), ('reviewers/boot/python-focused.xml.gz', 464, 1),
]:
    c = outcome(out / path, passed, skipped=skip)
    assert all(skips(old).get(i) == reason for i, reason in skips(c).items())
execution = load(out / 'checks/execution.json')
assert execution['canonical_tests']['exit_code'] == execution['container_context']['exit_code'] == 0
assert execution['canonical_tests']['python_warning_count'] == summary['canonical_python_warning_count'] == 0
assert all(g['exit_code'] == 0 for g in execution['completed_groups'])
for phase in ('lint', 'preview', 'negative', 'tests'):
    log = raw(out / 'checks' / ('final-' + phase + '.log.gz')).decode()
    assert '[ci-hosted] PASS phase=' + phase in log
assert 'warnings summary' not in raw(out / 'checks/final-tests.log.gz').decode()


def events(p):
    return [json.loads(line) for line in raw(p).decode().splitlines()]


def goresults(e):
    results = [x for x in e if 'Test' in x and x['Action'] in {'pass', 'fail', 'skip'}]
    assert len(results) == len({(x['Package'], x['Test']) for x in results})
    assert not any('DATA RACE' in x.get('Output', '') for x in e)
    return {(x['Package'], x['Test']): x['Action'] for x in results}


full_events = events(out / 'checks/final-go-race.log.gz')
assert not any(x['Action'] == 'fail' for x in full_events)
assert full_events[-1]['Action'] == 'pass' and 'Test' not in full_events[-1]
assert '(cached)' not in raw(out / 'checks/final-go-race.log.gz').decode()
full_go = goresults(full_events)
assert list(full_go.values()).count('pass') == summary['go_full_race_named_pass_events'] == 418
assert {t for (_, t), action in full_go.items() if action == 'skip'} == {'TestLinuxInventoryRetainsPartitionParents', 'TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
old_go = goresults(events(out.parent / 'bug-audit-20261021-pass10/checks/final-go-race.jsonl.gz'))
new_go = goresults(events(out / 'checks/final-go-new.log.gz'))
assert len(old_go) == 368 and len(full_go) == 420 and len(new_go) == 52
assert old_go.items() <= full_go.items() and set(full_go) - set(old_go) == set(new_go)
assert set(new_go.values()) == {'pass'} and sum('/' in t for _, t in new_go) == 47
for path, failures, controls in [
    ('proofs/go-expanded-independent-before.log.gz', 17, 30),
    ('reviewers/boot/expanded-before.log.gz', 17, 30),
    ('proofs/pipe-independent-before.log.gz', 3, 2),
    ('proofs/size-independent-before.log.gz', 4, 3),
    ('reviewers/boot/output-cancel-before.log.gz', 1, 2),
]:
    results = goresults(events(out / path))
    leaves = {t: action for (_, t), action in results.items() if '/' in t}
    assert len(leaves) == failures + controls
    assert list(leaves.values()).count('fail') == failures and list(leaves.values()).count('pass') == controls
    if failures == 17:
        assert set(results) == set(new_go)
for path in ['review/go-expanded-before-inputs.json', 'reviewers/boot/expanded-before-inputs.json']:
    p = load(out / path)
    assert p['baseline'] == review['baseline_commit']
    assert p['product_sha256'] == start['desktop/io.go']
    assert p['test_sha256'] == frozen['desktop/output_deadline_pass11_20261021_test.go']
for path, count in [('checks/final-go-original-probes.log.gz', 18), ('checks/final-plan-model.log.gz', 1)]:
    c = goresults(events(out / path))
    assert len(c) == count and set(c.values()) == {'pass'}
assert 'execs: 350000' in raw(out / 'checks/final-go-fuzz.log.gz').decode()
models = out / 'review/model-replays'
alias = load(models / 'protected-alias-capacity-matrix.json')
assert (alias['states'], alias['calls'], alias['positive_leaf_observations'], alias['protected_leaf_refusals'], alias['capacity_or_readonly_refusals']) == (2880, 8640, 2592, 4320, 1728)
cancel = load(models / 'cancellation-ownership-matrix.json')
assert (cancel['states'], cancel['initial_positive_completions'], cancel['initial_negative_terminal_results'], cancel['cancelled_results'], cancel['uncertain_ownership_preserved'], cancel['recovery_terminal_classifications'], cancel['duplicate_terminal_calls']) == (216, 24, 78, 66, 48, 48, 216)
detour = load(models / 'review_detour_layout_matrix.json')
assert (detour['review_scenarios'], detour['layout_scenarios'], detour['detours'], detour['fresh_countdown_checks'], detour['blocked_erase_calls'], detour['explicit_fake_starts'], detour['expiry_ticks_without_autostart']) == (360, 63, 720, 975, 3132, 423, 423)
transaction = load(models / 'volatile-transaction-matrix.json')
assert transaction['counts'] == {'cases': 240, 'positive_transactions': 30, 'injected_refusals': 210, 'precommit_old_bytes_preserved': 120, 'postcommit_new_bytes_retained': 90, 'postcommit_journals_block_further_save': 54, 'fresh_reopen_checks': 240, 'successful_retries': 240, 'quiescent_controls': 144, 'native_callbacks': 0}
plan = load(out / 'review/plan-freshness-matrix.json')
assert plan['counts'] == {'states': 162, 'positive_plans': 162, 'order_controls': 162, 'unrelated_entry_controls': 162, 'sensitive_field_changes': 161, 'refusals': 1620, 'restored_controls': 1620, 'native_callbacks': 0, 'mismatches': 0}
for model in (alias, cancel, detour, transaction, plan):
    counts = model.get('counts', model)
    assert counts['native_callbacks'] == 0 and not model.get('mismatches', counts.get('mismatches'))
    for name, h in model['source_sha256'].items():
        assert frozen[name] == h, name
for name, record in load(out / 'review/model-replay-provenance.json').items():
    original = (out / 'reviewers' / record['reviewer'] / name).read_bytes()
    if name.endswith('.py'):
        script = (models / name).read_bytes()
        assert original == script and hashlib.sha256(script).hexdigest() == record['exact_script_sha256']
    else:
        script = (out / 'review' / name).read_bytes()
        assert hashlib.sha256(original).hexdigest() == record['original_sha256']
        assert hashlib.sha256(script).hexdigest() == record['replay_sha256']
        assert original.decode().replace(record['only_change']['from'], record['only_change']['to']) == script.decode()
preview = load(out / 'checks/actual-preview.json')
assert preview['normal_close_acceptance'] and preview['returncode'] == 0
assert preview['fake_disks_only'] and preview['welcome_content_observed_before_capture']
assert load(out / 'checks/system-browser-runtime.json')['pinned_playwright_runtime'] is False
assert load(out / 'artifact-review.json')['independent_bundle_verifier'].startswith('PASS:')
manifest = load(out / 'artifacts-sha256.json')
actual = {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p != out / 'artifacts-sha256.json'}
assert actual == set(manifest)
for name, record in manifest.items():
    data = (out / name).read_bytes()
    assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'], name
print(json.dumps({'verified_source_files': 822, 'retained_artifacts': len(manifest), 'unique_passed': 11770,
                  'skipped_unverified': 28, 'new_python_regressions_passed': 56, 'new_go_leaf_cases': 47,
                  'new_go_named_pass_events': 52, 'prior_main_ids_retained': 11741,
                  'all_old_test_files_byte_identical': True, 'verified_root_causes': 3}))
