"""Verify exact pass-two source, compressed JUnit and retained artifact hashes."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


dest = Path(__file__).resolve().parent
repo = dest.parents[2]
frozen_bytes = (dest / 'source-sha256.json').read_bytes()
frozen = json.loads(frozen_bytes)
assert len(frozen) == 792
assert hashlib.sha256(frozen_bytes).hexdigest() == (
    '84fc73f381a6381aa990b12217a8a06de650e2f1728cba3f0a6669061d98f9bf'
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
new_raw = gzip.decompress((dest / 'checks/new-regressions.xml.gz').read_bytes())
new_cases = list(ET.fromstring(new_raw).iter('testcase'))
assert len(new_cases) == summary['new_regressions_passed'] == 319
assert all(not list(case) for case in new_cases)
assert {(c.get('classname'), c.get('name')) for c in new_cases} <= seen
assert passed == summary['canonical_unique_passed'] == 10727
assert skipped == summary['canonical_skipped_unverified'] == 28
assert summary['baseline_skip_ids_and_reasons_unchanged'] is True
manifest = json.loads((dest / 'artifacts-sha256.json').read_text())
actual = {str(path.relative_to(dest)) for path in dest.rglob('*')
          if path.is_file() and path.name != 'artifacts-sha256.json'}
assert actual == set(manifest)
for name, record in manifest.items():
    raw = (dest / name).read_bytes()
    assert len(raw) == record['bytes'], name
    assert hashlib.sha256(raw).hexdigest() == record['sha256'], name
print(json.dumps({'verified_source_files': len(frozen),
                  'retained_artifacts': len(manifest), 'unique_passed': passed,
                  'skipped_unverified': skipped, 'new_regressions_passed': len(new_cases)}))
