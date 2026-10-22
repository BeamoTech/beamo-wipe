"""Verify exact third-pass source, retained artifacts and complete JUnit identity."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

dest = Path(__file__).resolve().parent
repo = dest.parents[2]
frozen_bytes = (dest / 'source-sha256.json').read_bytes()
frozen = json.loads(frozen_bytes)
assert len(frozen) == 796
assert hashlib.sha256(frozen_bytes).hexdigest() == (
    '0a559c0f6f9e60cd082b9b84d669d892f3240987ec7e5ec5ed1b5b2f721b2539'
)
for name, digest in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
summary = json.loads((dest / 'final-summary.json').read_text())
seen = set()
passed = skipped = 0
for name, record in summary['canonical_reports'].items():
    raw = gzip.decompress((dest / 'checks' / (name + '.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == record['junit_sha256']
    cases = list(ET.fromstring(raw).iter('testcase'))
    assert len(cases) == record['cases']
    for case in cases:
        identity = case.get('classname'), case.get('name')
        assert identity not in seen, identity
        seen.add(identity)
        assert case.find('failure') is None and case.find('error') is None, identity
        if case.find('skipped') is None:
            passed += 1
        else:
            skipped += 1
    if name == 'final-tests.xml':
        final_cases = cases
assert passed == summary['canonical_unique_passed'] == 10961
assert skipped == summary['canonical_skipped_unverified'] == 28
new_raw = gzip.decompress((dest / 'checks/new-regressions.xml.gz').read_bytes())
new_cases = list(ET.fromstring(new_raw).iter('testcase'))
assert len(new_cases) == summary['new_regressions_passed'] == 234
assert all(not list(case) for case in new_cases)
baseline = ET.fromstring(gzip.decompress((dest.parent / 'bug-audit-20261019-pass2/checks/final-tests.xml.gz').read_bytes()))
old_cases = list(baseline.iter('testcase'))
old_ids = {(c.get('classname'), c.get('name')) for c in old_cases}
final_ids = {(c.get('classname'), c.get('name')) for c in final_cases}
assert len(old_ids) == summary['baseline_main_test_ids_retained'] == 10754
assert old_ids <= final_ids
assert {(c.get('classname'), c.get('name')) for c in new_cases} == final_ids - old_ids
def skips(cases):
    return {(c.get('classname'), c.get('name')): c.find('skipped').get('message')
            for c in cases if c.find('skipped') is not None}
assert skips(old_cases) == skips(final_cases)
assert summary['baseline_skip_ids_and_reasons_unchanged'] is True
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
                  'new_regressions_passed': len(new_cases), 'prior_main_ids_retained': len(old_ids)}))
