"""Read back starting inputs, retained tests, final patches and proof lineage."""
import collections
import difflib
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass19-primary')
start = json.loads((out / 'starting-freeze.json').read_text())
freeze = json.loads((out / 'source-freeze.json').read_text())
assert len(start) == 766 and len(freeze) == 771
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
with tarfile.open(out / 'starting-inputs.tar.gz', 'r:gz') as archive:
    assert set(archive.getnames()) == set(start)
    assert all(m.isfile() for m in archive)
    starting = {n: archive.extractfile(n).read() for n in start}
assert {n: hashlib.sha256(b).hexdigest() for n, b in starting.items()} == start
previous = json.loads((root / 'docs/evidence/bug-audit-20261017-pass18/primary/source-freeze.json').read_text())
assert start == previous
changed = [n for n in start if start[n] != freeze[n]]
assert sorted(changed) == ['src/beamo_wipe/discover.py', 'src/beamo_wipe/ui/tk_wizard.py',
                           'tests/test_accessible_runtime.py', 'tests/test_checkrow_trace_lifetime_pass18.py']
parts = []
for name in sorted(changed):
    parts.extend(difflib.unified_diff(starting[name].decode().splitlines(True),
        (root / name).read_text().splitlines(True), fromfile='starting/' + name, tofile='final/' + name))
assert ''.join(parts) == (out / 'pass19-source.diff').read_text()
for group, path in [('source', 'src'), ('tracked-tests', 'tests')]:
    assert gzip.decompress((out / (group + '.diff.gz')).read_bytes()) == subprocess.check_output(['git', 'diff', '--', path])
new_tests = json.loads((out / 'new-tests-sha256.json').read_text())
assert len(new_tests) == 42
with tarfile.open(out / 'new-tests.tar.gz', 'r:gz') as archive:
    assert set(archive.getnames()) == set(new_tests)
    assert all(m.isfile() for m in archive)
    assert all(hashlib.sha256(archive.extractfile(n).read()).hexdigest() == freeze[n] == h for n, h in new_tests.items())
proof_status = json.loads((out / 'original-final-proof-status.json').read_text())
assert proof_status['exit_code'] == 1 and proof_status['private_source_only']
assert all(start[n] == h for n, h in proof_status['source'].items())
assert len(proof_status['tests']) == 6
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest() == h for n, h in proof_status['tests'].items())
cases = ET.parse(out / 'original-final-proof.xml').findall('.//testcase')
assert len(cases) == 222
assert not any(c.find('error') is not None or c.find('skipped') is not None for c in cases)
failures = [c for c in cases if c.find('failure') is not None]
assert len(failures) == 118
assert all('AssertionError' in (c.find('failure').text or '') for c in failures)
per_module = collections.Counter(c.get('classname') for c in failures)
assert len({(c.get('classname'), c.get('name')) for c in cases}) == 222
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
guidance = {}
for name in ('AGENTS.md', 'docs/ci.md', 'docs/remote-development.md', 'docs/claims.md',
             'README.md', 'docs/runbook.md', '.ai/memory/product-constraints.md'):
    path = root / name
    if path.is_file():
        guidance[name] = hashlib.sha256(path.read_bytes()).hexdigest()
receipt = dict(starting_inputs=766, starting_matches_prior_final=True, final_inputs=771,
               unchanged_starting_inputs=762, changed_inputs=sorted(changed), new_test_inputs=5,
               retained_regression_modules=42, source_and_test_archives_readback=True,
               exact_incremental_and_cumulative_patches=True, original_final_proof_cases=222,
               original_assertion_failures=118, original_passing_controls=104,
               original_errors=0, original_skips=0, original_failures_by_module=dict(per_module),
               original_helper_only_controls_deselected=0, index_empty=True,
               guidance_sha256=guidance, shared_parent_guide_present=Path('/root/dev/AGENTS.md').exists())
(out / 'source-artifact-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k not in {'guidance_sha256', 'original_failures_by_module'}}, indent=2))
