"""Supplemental report consistency checks; all devices and logs are fixtures."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

sys.path[:0] = ['/workspace/beamo-wipe/tests', '/workspace/beamo-wipe/src']
from beamo_wipe import lang
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy, encode_sharing_copy
from beamo_wipe.support_export import _bundle_files
from test_result_presentations import CASES, case_evidence

results = []
mutations = [
    (('schema_version',), True),
    (('exit_evidence', 'exit_code'), False),
    (('exit_evidence', 'signal'), 0),
    (('method', 'rounds'), 1.0),
    (('method', 'noblank'), 1),
    (('method', 'overwrite_passes'), -1),
    (('method', 'verification_passes'), 0.0),
    (('verification', 'verified'), 1),
    (('completion', 'validated'), False),
    (('locale', 'language'), ['en']),
    (('interruption', 'interrupted'), 0),
    (('interruption', 'cancelled'), 0),
]
checks = 0
try:
    for language in lang.LANGUAGE_ORDER:
        lang.set_language(language)
        for case in CASES:
            _, evidence, log = case_evidence(case)
            expected = present_evidence(evidence)
            assert expected.code == case[0]
            for index in range(12):
                token = f'PASS2-PRIVATE-{index:03d}'
                planted = deepcopy(evidence)
                for key in ('serial', 'wwn', 'name', 'label'):
                    planted['device'][key] = token + '-' + key
                planted['device']['path'] = '/dev/' + token
                planted['device']['realpath'] = '/dev/' + token
                planted['device']['model'] = 'Fixture ' + token + '-serial'
                planted['warnings'] = ['Do not share ' + token + '-wwn']
                original = deepcopy(planted)
                shared = make_sharing_copy(planted)
                assert present_evidence(shared).code == expected.code
                encoded = encode_sharing_copy(shared)
                assert token.lower().encode() not in encoded.lower()
                bundle = _bundle_files(json.dumps(planted).encode(), log.encode(),
                                       'complete' if log else 'unavailable',
                                       privacy_reduced=True)
                assert token.lower().encode() not in bundle['SHARE.json'].lower()
                assert token.lower().encode() not in bundle['SHARE.txt'].lower()
                assert json.loads(bundle['result.json']) == planted
                assert planted == original
                manifest = json.loads(bundle['COMPLETE'])
                assert manifest['safe_to_remove'] is False
                assert all(hashlib.sha256(bundle[name]).hexdigest() == digest
                           for name, digest in manifest['files'].items())
                checks += 1
            for keys, value in mutations:
                malformed = deepcopy(evidence)
                parent = malformed
                for key in keys[:-1]:
                    parent = parent[key]
                parent[keys[-1]] = value
                assert present_evidence(malformed).code == 'indeterminate', (case[0], keys)
                checks += 1
            results.append({'language': language, 'result': expected.code,
                            'sharing_and_bundle_variants': 12,
                            'malformed_core_variants': len(mutations)})
finally:
    lang.set_language('en')
output = {'status': 'pass', 'supplemental_cases': checks, 'rows': results,
          'canonical_test_count': False,
          'limits': 'Fixture-based report checks; no device, mount or USB operation'}
Path(__file__).with_suffix('.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'supplemental_cases': checks}))
