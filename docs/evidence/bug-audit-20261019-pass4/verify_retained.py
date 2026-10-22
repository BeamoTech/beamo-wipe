"""Verify fourth-pass source, artifacts, exact JUnit IDs and separate Go cases."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

dest = Path(__file__).resolve().parent
repo = dest.parents[2]
frozen_bytes = (dest / 'source-sha256.json').read_bytes()
frozen = json.loads(frozen_bytes)
assert len(frozen) == 800
assert hashlib.sha256(frozen_bytes).hexdigest() == (
    '9b4c0e6b0be2153e4349c01a61b813518f834da789e1f206df8db260fc515342'
)
for name, digest in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name

def cases(path):
    return list(ET.fromstring(gzip.decompress(path.read_bytes())).iter('testcase'))

def identities(items):
    return {(c.get('classname'), c.get('name')) for c in items}

def skips(items):
    return {(c.get('classname'), c.get('name')): c.find('skipped').get('message')
            for c in items if c.find('skipped') is not None}

summary = json.loads((dest / 'final-summary.json').read_text())
seen = set()
passed = skipped = 0
for name, record in summary['canonical_reports'].items():
    path = dest / 'checks' / (name + '.gz')
    raw = gzip.decompress(path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == record['junit_sha256']
    items = cases(path)
    assert len(items) == record['cases']
    for case in items:
        identity = case.get('classname'), case.get('name')
        assert identity not in seen, identity
        seen.add(identity)
        assert case.find('failure') is None and case.find('error') is None, identity
        if case.find('skipped') is None:
            passed += 1
        else:
            skipped += 1
    historical_name = ('initial-full-tests.xml.gz' if name == 'resume-tests.xml'
                       else 'initial-orca.xml.gz')
    historical = cases(dest / 'history' / historical_name)
    assert identities(historical) == identities(items)
    assert skips(historical) == skips(items)
    assert all(c.find('failure') is None and c.find('error') is None for c in historical)
    if name == 'resume-tests.xml':
        final_cases = items
assert passed == summary['canonical_unique_passed'] == 11058
assert skipped == summary['canonical_skipped_unverified'] == 28
new = cases(dest / 'checks/new-regressions.xml.gz')
assert len(new) == summary['new_python_regressions_passed'] == 97
assert all(not list(case) for case in new)
old = cases(dest.parent / 'bug-audit-20261019-pass3/checks/final-tests.xml.gz')
old_ids, final_ids = identities(old), identities(final_cases)
assert len(old_ids) == summary['baseline_main_test_ids_retained'] == 10988
assert old_ids <= final_ids
assert identities(new) == final_ids - old_ids
assert skips(old) == skips(final_cases)
assert summary['baseline_skip_ids_and_reasons_unchanged'] is True

def events(name):
    return [json.loads(line) for line in gzip.decompress(
        (dest / 'checks' / name).read_bytes()).decode().splitlines()]

new_go = events('new-go-regressions.jsonl.gz')
assert not any(e['Action'] in {'fail', 'skip'} for e in new_go)
names = {e['Test'] for e in new_go if e['Action'] == 'pass' and 'Test' in e}
assert len({name for name in names if '/' not in name}) == summary['new_go_top_level_passed'] == 4
assert len({name for name in names if '/' in name}) == summary['new_go_named_subtests_passed'] == 137
full_go = events('go-race.jsonl.gz')
assert not any(e['Action'] == 'fail' for e in full_go)
assert full_go[-1]['Action'] == 'pass' and 'Test' not in full_go[-1]
assert {e['Test'] for e in full_go if e['Action'] == 'skip'} == set(summary['go_full_race_native_skips']) == {
    'TestLinuxInventoryRetainsPartitionParents',
    'TestWindowsInventoryReportsOnlyLauncherPartitionPass13',
}
execution = json.loads((dest / 'checks/execution.json').read_text())
assert execution['canonical_tests']['exit_code'] == 0
assert all(group['exit_code'] == 0 for group in execution['completed_groups'])
manifest = json.loads((dest / 'artifacts-sha256.json').read_text())
actual = {str(path.relative_to(dest)) for path in dest.rglob('*')
          if path.is_file() and path.name != 'artifacts-sha256.json'}
assert actual == set(manifest)
for name, record in manifest.items():
    raw = (dest / name).read_bytes()
    assert len(raw) == record['bytes'], name
    assert hashlib.sha256(raw).hexdigest() == record['sha256'], name
print(json.dumps({'verified_source_files': len(frozen), 'retained_artifacts': len(manifest),
                  'unique_passed': passed, 'skipped_unverified': skipped,
                  'new_python_regressions_passed': len(new),
                  'new_go_top_level_passed': 4, 'new_go_named_subtests_passed': 137,
                  'prior_main_ids_retained': len(old_ids)}))
