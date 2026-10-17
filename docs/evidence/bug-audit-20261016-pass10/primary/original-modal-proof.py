"""Independently reproduce the visual finding on exact initial three-fix bytes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass10-primary')
scratch = Path(tempfile.mkdtemp(prefix='beamo-pass10-modal-original-'))
for name in ('src', 'tests'):
    shutil.copytree(root / name, scratch / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
(scratch / 'src/beamo_wipe/ui/accessible_wizard.py').write_bytes((out / 'accessible_wizard-before-modal.py').read_bytes())
frozen = json.loads((out / 'initial-threefix-source-freeze.json').read_text())
source = {n: h for n, h in frozen.items() if n.startswith('src/')}
assert all(hashlib.sha256((scratch / n).read_bytes()).hexdigest() == h for n, h in source.items())
runtime = scratch / 'runtime'
runtime.mkdir(mode=0o700)
env = dict(os.environ, PYTHONPATH=str(scratch / 'src'), XDG_RUNTIME_DIR=str(runtime), PULSE_RUNTIME_PATH=str(runtime / 'pulse'), BEAMO_ISOLATED_X11_TEST='1')
for key in ('AT_SPI_BUS_ADDRESS', 'PULSE_SERVER'):
    env.pop(key, None)
command = ['dbus-run-session', '--', 'xvfb-run', '-a', '-s', '-screen 0 1600x1000x24 -dpi 72', '/tmp/beamo-wipe-audit-python/bin/python3', '-m', 'pytest', '-c', str(root / 'pyproject.toml'), '-o', 'pythonpath=' + str(scratch / 'src'), '--rootdir=' + str(scratch), str(scratch / 'tests/test_accessible_sound_modal_pass10.py'), '--junitxml=' + str(out / 'original-modal.xml')]
with (out / 'original-modal.txt').open('wb') as log:
    result = subprocess.run(command, cwd=scratch, env=env, stdout=log, stderr=subprocess.STDOUT)
cases = ET.parse(out / 'original-modal.xml').findall('.//testcase')
summary = {'initial_threefix_source_files_hash_verified': len(source), 'cases': len(cases), 'failures': sum(c.find('failure') is not None for c in cases), 'errors': sum(c.find('error') is not None for c in cases), 'skipped': sum(c.find('skipped') is not None for c in cases), 'exit': result.returncode, 'failed_ids': [c.get('name') for c in cases if c.find('failure') is not None]}
(out / 'original-modal-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert result.returncode == 1 and summary['failures'] >= 9 and summary['errors'] == summary['skipped'] == 0
