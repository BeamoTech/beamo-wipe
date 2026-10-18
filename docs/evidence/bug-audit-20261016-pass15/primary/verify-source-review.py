"""Authenticate exact final reviewed inputs and retained prior work."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

out = Path('/tmp/pass15-primary')
frozen = json.loads((out / 'source-freeze.json').read_text())
starting = json.loads((out / 'starting-inputs.json').read_text())
identity = json.loads((out / 'source-review.json').read_text())
digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert len(frozen) == 751 and len(starting) == 747
assert all(digest(name) == value for name, value in frozen.items())
changed = {name for name, value in starting.items() if frozen[name] != value}
assert changed == {'src/beamo_wipe/' + name for name in ('discover.py', 'models.py', 'safety.py', 'ui/tk_wizard.py', 'nwipe_runner.py', 'outcomes.py', 'engine_checks.py')}
assert len(set(starting) - changed) == 740
assert len(set(frozen) - set(starting)) == 4
assert gzip.decompress((out / 'source.diff.gz').read_bytes()) == subprocess.check_output(['git', 'diff', '--', 'src'])
assert gzip.decompress((out / 'tracked-test-fixture.diff.gz').read_bytes()) == subprocess.check_output(['git', 'diff', '--', 'tests'])
assert hashlib.sha256(gzip.decompress((out / 'source.diff.gz').read_bytes())).hexdigest() == identity['source_diff_sha256']
assert digest(out / 'pass15-source.diff') == identity['pass15_source_diff_sha256']
review_records = {}
discovery_review = Path('/tmp/pass15-discovery/final-source-review-path-api.md').read_text()
for path in ('src/beamo_wipe/discover.py', 'src/beamo_wipe/models.py', 'src/beamo_wipe/safety.py', 'tests/test_physical_observation_context_pass15.py'):
    assert frozen[path] in discovery_review
    review_records[path] = dict(sha256=frozen[path], review='discovery/final-source-review-path-api.md')
ui_review = Path('/tmp/pass15-ui/exact-tk-review.md').read_text()
for path in ('src/beamo_wipe/ui/tk_wizard.py', 'tests/test_empty_inventory_wheel_pass15.py'):
    assert frozen[path] in ui_review
    review_records[path] = dict(sha256=frozen[path], review='ui/exact-tk-review.md')
runner_review = json.loads(Path('/tmp/pass15-runner/patch-review.json').read_text())
for path in ('src/beamo_wipe/nwipe_runner.py', 'src/beamo_wipe/outcomes.py', 'src/beamo_wipe/engine_checks.py'):
    record = next(row for row in runner_review['source'] if row['path'] == path)
    assert record['reviewed_sha256'] == frozen[path]
    review_records[path] = dict(sha256=frozen[path], review='runner/patch-review.md and .json')
assert changed.issubset(review_records)
with tarfile.open(out / 'starting-source.tar.gz', 'r:gz') as archive:
    members = archive.getmembers()
    assert len(members) == 58
    assert all(hashlib.sha256(archive.extractfile(member).read()).hexdigest() == starting[member.name] for member in members)
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
assert subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip() == identity['head']
receipt = dict(runtime_source_sha256=identity['runtime_source_sha256'], final_inputs=751,
               changed_starting_paths=sorted(changed), unchanged_starting_inputs=740,
               new_modules=sorted(set(frozen) - set(starting)), retained_untracked_test_modules=22,
               source_and_fixture_patch_exact=True, starting_source_archive_members=58,
               independent_peer_approval_for_all_changed_source=True,
               exact_peer_review_records=review_records, git_index_empty=True,
               primary_review='Complete accumulated/incremental source diff, tracked fixtures, four new modules, exact peer reviews and all relevant adjacent safety contracts read. No source objection remains; final gates required.')
(out / 'final-code-review.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'exact_peer_review_records'}, indent=2))
