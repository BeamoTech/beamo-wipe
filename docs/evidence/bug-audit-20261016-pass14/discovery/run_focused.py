"""Bounded discovery/authorization adjacency under fake acquisition guards."""
import builtins
import io
import json
import os
from pathlib import Path
import subprocess
import sys
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
original_open = builtins.open
original_run = subprocess.run
observed = {}

def guarded_open(path, *args, **kwargs):
    text = str(path)
    if text in {'/proc/cmdline', '/proc/self/mountinfo'}:
        observed[text] = observed.get(text, 0) + 1
        return io.StringIO('')
    return original_open(path, *args, **kwargs)

def guarded_run(argv, *args, **kwargs):
    if isinstance(argv, (list, tuple)) and argv:
        name = Path(str(argv[0])).name
        if name == 'findmnt':
            observed['fake_findmnt'] = observed.get('fake_findmnt', 0) + 1
            return subprocess.CompletedProcess(argv, 1, stdout='', stderr='')
        if name in {'lsblk', 'nwipe'}:
            raise AssertionError('Forbidden native acquisition: ' + str(argv[0]))
    return original_run(argv, *args, **kwargs)

builtins.open = guarded_open
subprocess.run = guarded_run
import pytest
files = json.loads(Path('/tmp/pass13-discovery/selected-files.json').read_text())
files += [
    'tests/test_boolean_boot_proof_pass36.py',
    'tests/test_live_overmount_pass14_discovery.py',
    'tests/test_identity.py',
    'tests/test_identity_soft_break.py',
    'tests/test_method_operation_copy.py',
    'tests/test_refresh_phases.py',
    'tests/test_refresh_confirm.py',
    'tests/test_refresh_scan_flow.py',
    'tests/test_refresh_baseexception_regression.py',
]
files = list(dict.fromkeys(files))
Path('/tmp/pass14-discovery/selected-files.json').write_text(json.dumps(files, indent=2) + '\n')
rc = pytest.main(['-q', *files, '--junitxml=/tmp/pass14-discovery/focused.xml'])
Path('/tmp/pass14-discovery/focused-boundary-receipt.json').write_text(json.dumps(dict(exit_code=rc, fake_host_boundary_reads=observed), indent=2) + '\n')
print('fake_host_boundary_reads', observed, flush=True)
sys.exit(rc)
