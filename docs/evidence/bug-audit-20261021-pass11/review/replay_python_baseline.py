"""Run exact final regression bytes against independently archived old source."""
from pathlib import Path
import hashlib
import json
import sys

r = Path(__file__).parent
repo = Path('/workspace/beamo-wipe')
baseline = r / 'baseline-src'
sys.path[:0] = [str(baseline), str(repo / 'tests')]
from beamo_wipe import sleep_inhibit

start = json.loads((r / 'starting-source-sha256.json').read_text())
assert Path(sleep_inhibit.__file__).resolve() == baseline / 'beamo_wipe/sleep_inhibit.py'
assert hashlib.sha256(Path(sleep_inhibit.__file__).read_bytes()).hexdigest() == start['src/beamo_wipe/sleep_inhibit.py']
test = repo / 'tests/test_sleep_inhibit_diagnostic_retirement_pass11_20261021.py'
receipt = {
    'baseline': json.loads((r / 'baseline.json').read_text())['head'],
    'product_sha256': start['src/beamo_wipe/sleep_inhibit.py'],
    'test_path': str(test.relative_to(repo)),
    'test_sha256': hashlib.sha256(test.read_bytes()).hexdigest(),
    'actual_process_or_device_actions': False,
}
(r / 'python-expanded-before-inputs.json').write_text(json.dumps(receipt, indent=2) + '\n')
import pytest

raise SystemExit(pytest.main([
    '-W', 'error', '-p', 'no:cacheprovider', '-o', 'addopts=',
    '-o', 'pythonpath=' + str(baseline) + ' ' + str(repo / 'tests'), '-q',
    str(test), '--junitxml=' + str(r / 'python-expanded-independent-before.xml'),
]))
