"""Verify exact retained evidence and the runtime source used by the audit."""
from pathlib import Path
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET


dest = Path(__file__).resolve().parent
repo = dest.parents[2]
frozen = json.loads((dest / 'source-sha256.json').read_text())
assert len(frozen) == 787
for name, digest in frozen.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
summary = json.loads((dest / 'final-summary.json').read_text())
seen = set()
passed = skipped = new_passed = 0
for name, report in summary['canonical_reports'].items():
    raw = gzip.decompress((dest / 'checks' / (name + '.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == report['junit_sha256']
    cases = list(ET.fromstring(raw).iter('testcase'))
    assert len(cases) == report['cases']
    for case in cases:
        identity = case.get('classname'), case.get('name')
        assert identity not in seen, identity
        seen.add(identity)
        assert case.find('failure') is None and case.find('error') is None, identity
        if case.find('skipped') is not None:
            skipped += 1
        else:
            passed += 1
            new_passed += '20261019' in case.get('classname', '')
assert passed == summary['canonical_unique_passed']
assert skipped == summary['canonical_skipped']
assert new_passed == summary['new_regressions_passed'] == 276
manifest = json.loads((dest / 'artifacts-sha256.json').read_text())
actual_paths = {str(path.relative_to(dest)) for path in dest.rglob('*')
                if path.is_file() and path.name != 'artifacts-sha256.json'}
assert actual_paths == set(manifest)
for name, record in manifest.items():
    raw = (dest / name).read_bytes()
    assert len(raw) == record['bytes'], name
    assert hashlib.sha256(raw).hexdigest() == record['sha256'], name
print(json.dumps({'verified_source_files': len(frozen),
                  'retained_artifacts': len(manifest),
                  'unique_passed': passed, 'skipped_unverified': skipped,
                  'new_regressions_passed': new_passed}, indent=2))
