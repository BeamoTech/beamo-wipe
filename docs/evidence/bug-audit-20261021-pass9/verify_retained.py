"""Verify PASS9 source, assertions, exact test identities and retained bytes."""
import ast
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
assert len(frozen) == 818
assert hashlib.sha256(raw).hexdigest() == '74323f9ed2ff1b64fceca4d43fd907d6f936471b8eea27f0406e1da1685c3a46'
for name, digest in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=repo).decode().split('\0')
selected = {n for n in names if n and (n.startswith(('src/', 'tests/', 'scripts/', 'packaging/', 'desktop/', 'developer_tests/'))
            or n in {'dev.py', 'pyproject.toml', 'requirements-dev.txt', 'preview'}) and (repo / n).is_file()}
assert selected == set(frozen)
start = load(out / 'review/starting-source-sha256.json')
assert len(start) == 817
review = load(out / 'review/independent-review.json')
fixtures = set(review['fixture_adaptations'])
assert fixtures == {'tests/test_accessible_boot_option.py', 'tests/test_app_poweroff_recheck_pass7.py'}
for n, h in start.items():
    if n.startswith(('tests/', 'developer_tests/', 'desktop/')) and n not in fixtures:
        assert frozen[n] == h, n
for name in fixtures:
    old = ast.parse(subprocess.check_output(['git', 'show', review['baseline_commit'] + ':' + name], cwd=repo, text=True))
    new = ast.parse((repo / name).read_text())
    if name.endswith('test_app_poweroff_recheck_pass7.py'):
        changed = 0
        for node in ast.walk(new):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == '_run_one_session':
                for kw in node.keywords:
                    if kw.arg == 'session_store':
                        assert isinstance(kw.value, ast.Name) and kw.value.id == 'store'
                        kw.value = ast.Constant(None)
                        changed += 1
        assert changed == 1
    assertions = lambda tree: [ast.dump(x, include_attributes=False) for x in ast.walk(tree) if isinstance(x, ast.Assert)]
    assert assertions(old) == assertions(new), name
assert review['old_behavior_assertions_preserved'] is True and review['verified_root_causes'] == 1
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
assert passed == summary['canonical_unique_passed'] == 11676
assert skipped == summary['canonical_skipped_unverified'] == 28
old = cases(out.parent / 'bug-audit-20261021-pass8/checks/final-tests.xml.gz')
new = green(out / 'checks/final-new-regressions.xml.gz', 64)
assert len(ids(old)) == 11639 and ids(old) <= ids(main) and ids(main) - ids(old) == ids(new)
assert skips(old) == skips(main) and summary['baseline_skip_ids_and_reasons_unchanged'] is True
for path, failures, controls in [
    ('reviewers/discovery/ownership-expanded-before.xml.gz', 48, 16),
    ('proofs/expanded-independent-before.xml.gz', 48, 16),
    ('reviewers/discovery/transient-live-ownership-red.xml.gz', 2, 2),
    ('proofs/live-ownership-independent-before.xml.gz', 1, 2),
]:
    c = cases(out / path)
    assert len(c) == len(ids(c)) == failures + controls
    assert all(x.find(t) is None for x in c for t in ('error', 'skipped'))
    assert sum(x.find('failure') is not None for x in c) == failures
    if failures == 48:
        assert {x.get('name') for x in c} == {x.get('name') for x in new}
proof = load(out / 'reviewers/discovery/ownership-expanded-before.status.json')
assert proof['exit_code'] == 1
assert proof['app_sha256'] == start['src/beamo_wipe/app.py']
assert proof['test_sha256'] == frozen['tests/test_app_live_ownership_pass9_20261021.py']
independent = load(out / 'review/expanded-independent-before-inputs.json')
assert independent['baseline'] == review['baseline_commit']
assert independent['archive_exact_bytes'] == {
    'src/beamo_wipe/app.py': start['src/beamo_wipe/app.py'],
    'tests/test_app_live_ownership_pass9_20261021.py': frozen['tests/test_app_live_ownership_pass9_20261021.py'],
}
assert load(out / 'proofs/expanded-independent-before.status.json')['exit_code'] == 1
for path, count in [
    ('checks/final-original-probes.xml.gz', 7), ('checks/system-browser-tests.xml.gz', 9),
    ('checks/ownership-final-adjacent.xml.gz', 210), ('checks/root-adjacent-x11.xml.gz', 358),
    ('reviewers/discovery/ownership-focused-after.xml.gz', 68),
    ('reviewers/runner/adjacent.xml.gz', 1430), ('reviewers/runner/engine-evidence-adjacent.xml.gz', 213),
    ('reviewers/ui/focused-ui.xml.gz', 310), ('reviewers/recovery/focused.xml.gz', 714),
    ('reviewers/boot/python-adjacent.xml.gz', 255),
]:
    green(out / path, count)
discovery = cases(out / 'reviewers/discovery/focused.xml.gz')
assert len(discovery) == len(ids(discovery)) == 2326 and len(skips(discovery)) == 6
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
    return [json.loads(line) for line in gzip.decompress(p.read_bytes()).decode().splitlines()]


go = goevents(out / 'checks/final-go-race.jsonl.gz')
assert not any(x['Action'] == 'fail' for x in go)
assert go[-1]['Action'] == 'pass' and 'Test' not in go[-1]
assert sum(x['Action'] == 'pass' and 'Test' in x for x in go) == summary['go_full_race_named_pass_events'] == 338
assert {x['Test'] for x in go if x['Action'] == 'skip'} == set(summary['go_full_race_native_skips']) == {'TestLinuxInventoryRetainsPartitionParents', 'TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert '(cached)' not in gzip.decompress((out / 'checks/final-go-race.jsonl.gz').read_bytes()).decode()
assert 'execs: 350000' in (out / 'checks/final-go-fuzz.log').read_text()
model = goevents(out / 'checks/final-firmware-model.jsonl.gz')
assert not any(x['Action'] in {'fail', 'skip'} for x in model)
assert [x['Test'] for x in model if x['Action'] == 'pass' and 'Test' in x] == ['TestPass9FirmwareContractMatrix']
firmware = load(out / 'review/firmware-contract-metrics.json')
assert firmware == {'foreign_request_preservation_controls': 288, 'inventory_cases': 150,
                    'inventory_success_controls': 40, 'mismatches': 0, 'native_callbacks': 0,
                    'restart_success_controls': 9, 'transaction_cases': 6048, 'transaction_refusals': 6039}
models = out / 'review/model-replays'
graph = load(models / 'protected-graph-matrix.json')
assert graph['counts'] == {'contexts': 512, 'discovery_calls': 5120, 'order_representation_checks': 4096,
                           'protected_target_observations': 14504, 'positive_selectable_observations': 5976,
                           'ambiguous_boot_refusals': 512, 'duplicate_identity_refusals': 512}
assert graph['failures'] == [] and graph['native_callbacks'] == 0
completion = load(models / 'contradiction-projection-matrix.json')
assert completion['cases'] == 480 and completion['positive_controls'] == 96 and completion['refusal_controls'] == 384
assert completion['whole_log_projection_comparisons'] == 240 and completion['failure_count'] == completion['native_callbacks'] == 0
persistence = load(models / 'persistence-fault-matrix.json')
assert persistence['cases'] == persistence['reopens'] == 360 and persistence['successful_operations'] == 124
assert persistence['injected_refusals'] == 236 and persistence['clean_retries'] == 208
assert persistence['native_callbacks'] == 0 and persistence['unexpected'] == []
consent = load(models / 'visible_consent_sequence_model.json')
assert consent == {'sequences': 399, 'blocked_erase_calls': 4233, 'explicit_fake_starts': 396,
                   'automatic_starts': 0, 'nested_overlay_checks': 117, 'native_callbacks': 0}
for model in (graph, completion, persistence):
    for n, h in model['source_sha256'].items():
        assert frozen[n] == h
for name, record in load(out / 'review/model-replay-provenance.json').items():
    script = (models / name).read_bytes()
    assert hashlib.sha256(script).hexdigest() == record['exact_script_sha256']
    assert script == (out / 'reviewers' / record['reviewer'] / name).read_bytes()
original = (out / 'reviewers/boot/firmware_contract_matrix_test.go').read_text()
replay = (out / 'review/firmware_contract_matrix_test.go').read_text()
assert original.replace('/workspace/beamo-tools/audit-pass9-20261021/boot/firmware-contract-metrics.json', '/workspace/beamo-tools/audit-pass9-20261021/root/firmware-contract-metrics.json') == replay
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
print(json.dumps({'verified_source_files': 818, 'retained_artifacts': len(manifest),
                  'unique_passed': passed, 'skipped_unverified': skipped, 'new_python_regressions_passed': 64,
                  'prior_main_ids_retained': 11639, 'old_behavior_assertions_preserved': True}))
