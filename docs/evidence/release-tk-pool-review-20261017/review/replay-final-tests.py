"""Replay the final regression bytes against authenticated original Tk sources."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path('/root/dev/Beamo Wipe')
out = Path(__file__).parent
test = root / 'tests/test_tk_retired_pool_threads.py'
records = []
for label, source_name, selection, failures, passed in (
    ('original-race', 'original-tk_wizard.py',
     'test_foreign_drain_cannot_keep_last_record or test_drain_preserves_external_reference_until_creator_releases_it', 8, 2),
    ('original-warning', 'partition-v1-tk_wizard.py',
     'test_unregistered_thread_drain_does_not_construct_dummy_thread', 2, 0),
):
    directory = out / (label + '-replay')
    directory.mkdir()
    package = directory / 'src/beamo_wipe'
    shutil.copytree(root / 'src/beamo_wipe', package,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
    target = package / 'ui/tk_wizard.py'
    target.write_bytes((out / source_name).read_bytes())
    source_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    report = directory / 'result.xml'
    args = [str(test), '-c', '/dev/null', '--rootdir', str(directory), '-k', selection,
            '--junitxml=' + str(report), '-q']
    code = ('import sys,hashlib;sys.path.insert(0,' + repr(str(directory / 'src')) + ');'
            'from beamo_wipe.ui import tk_wizard as ui;'
            'assert ui.__file__==' + repr(str(target)) + ';'
            'assert hashlib.sha256(open(ui.__file__,"rb").read()).hexdigest()==' + repr(source_hash) + ';'
            'import pytest;raise SystemExit(pytest.main(' + repr(args) + '))')
    result = subprocess.run([sys.executable, '-c', code], cwd=directory,
                            env=dict(os.environ, BEAMO_WIPE_DRY_RUN='1', PYTHONDONTWRITEBYTECODE='1'),
                            capture_output=True, timeout=15, check=False)
    (directory / 'stdout.txt').write_bytes(result.stdout)
    (directory / 'stderr.txt').write_bytes(result.stderr)
    import xml.etree.ElementTree as ET
    cases = list(ET.parse(report).iter('testcase'))
    failed = sum(c.find('failure') is not None for c in cases)
    assert result.returncode == 1 and not result.stderr
    assert failed == failures and len(cases) - failed == passed
    assert not any(c.find('error') is not None or c.find('skipped') is not None for c in cases)
    records.append({'label': label, 'source_sha256': source_hash,
                    'test_sha256': hashlib.sha256(test.read_bytes()).hexdigest(),
                    'failed': failed, 'controls_passed': passed, 'exit_code': result.returncode,
                    'stderr_bytes': len(result.stderr), 'selection': selection})
(out / 'final-test-original-replay.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps(records, indent=2))
