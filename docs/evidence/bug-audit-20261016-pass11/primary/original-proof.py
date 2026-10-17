"""Independently reproduce all new regressions on exact pass11 starting bytes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass11-primary')
scratch = Path(tempfile.mkdtemp(prefix='beamo-pass11-original-'))
for name in ('src', 'tests'):
    shutil.copytree(root / name, scratch / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name, original in [('ui/accessible_wizard.py', 'accessible_wizard-before.py'), ('nwipe_runner.py', 'nwipe_runner-before.py')]:
    (scratch / 'src/beamo_wipe' / name).write_bytes((out / original).read_bytes())
frozen = json.loads((out / 'starting-inputs.json').read_text())
source = {n: h for n, h in frozen.items() if n.startswith('src/')}
assert len(source) == 58
assert all(hashlib.sha256((scratch / n).read_bytes()).hexdigest() == h for n, h in source.items())
runtime = scratch / 'runtime'
runtime.mkdir(mode=0o700)
env = dict(os.environ, PYTHONPATH=str(scratch / 'src'), XDG_RUNTIME_DIR=str(runtime), PULSE_RUNTIME_PATH=str(runtime / 'pulse'), BEAMO_ISOLATED_X11_TEST='1')
for key in ('AT_SPI_BUS_ADDRESS', 'PULSE_SERVER'):
    env.pop(key, None)
tests = ['test_accessible_focus_input_pass11.py', 'test_runner_projection_summary_context_pass11.py', 'test_accessible_fullscreen_geometry_pass11.py']
command = ['dbus-run-session', '--', 'xvfb-run', '-a', '-s', '-screen 0 1600x1000x24 -dpi 72', '/tmp/beamo-wipe-audit-python/bin/python3', '-m', 'pytest', '-c', str(root / 'pyproject.toml'), '-o', 'pythonpath=' + str(scratch / 'src'), '--rootdir=' + str(scratch), *[str(scratch / 'tests' / n) for n in tests], '--junitxml=' + str(out / 'original.xml')]
with (out / 'original.txt').open('wb') as log:
    result = subprocess.run(command, cwd=scratch, env=env, stdout=log, stderr=subprocess.STDOUT)
cases = ET.parse(out / 'original.xml').findall('.//testcase')
summary = {'starting_source_files_hash_verified': len(source), 'cases': len(cases), 'failures': sum(c.find('failure') is not None for c in cases), 'errors': sum(c.find('error') is not None for c in cases), 'skipped': sum(c.find('skipped') is not None for c in cases), 'pytest_exit': result.returncode, 'failed_ids': [c.get('name') for c in cases if c.find('failure') is not None]}
(out / 'original-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert result.returncode == 1 and len(cases) == 103 and summary['failures'] == 35 and summary['errors'] == summary['skipped'] == 0
