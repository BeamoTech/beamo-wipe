"""Serial fake-only campaigns, admitted only after the canonical gate ends."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path.cwd()
out = Path('/tmp/pass17-primary')
python = '/tmp/beamo-pass17-python/bin/python3'
gate = json.loads((out / 'local-gate-status.json').read_text())
verified = json.loads((out / 'gate-verification.json').read_text())
assert len(gate) == 9 and all(row['exit_code'] == 0 for row in gate)
assert verified['phases'] == 9 and verified['failures'] == verified['errors'] == 0
freeze = json.loads((out / 'source-freeze.json').read_text())
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
assert not (out / 'campaign-status.json').exists(), 'Do not overwrite an earlier campaign run'
env = dict(os.environ)
env.update(PATH='/tmp/beamo-pass17-python/bin:/tmp/beamo-pass17-fallback-guard:' + env['PATH'],
           PYTHONPATH=str(root / 'src'), BEAMO_WIPE_DRY_RUN='1')
for key in ('BEAMO_WIPE_LIVE', 'BEAMO_WIPE_BOOT_DEVICE', 'BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
    env.pop(key, None)
evidence = root / 'docs/evidence/bug-audit-20261017-pass17'
phases = [
    ('runner-fresh', evidence / 'runner/fresh-boundaries.py'),
    ('runner-cancel', evidence / 'runner/cancel-boundaries.py'),
    ('geometry', Path('/tmp/pass17-ui/run-geometry.py')),
    ('reports', out / 'report-checks-matrix.py'),
]
status = []
for name, script in phases:
    print(name + ' started', flush=True)
    command = [python, str(script)]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_name = 'report-checks-matrix-artifacts.json' if name == 'reports' else name + '.txt'
    with (out / log_name).open('xb') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    status.append(dict(phase=name, command=command, script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                       started_utc=start, ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       exit_code=result.returncode, output=log_name))
    (out / 'campaign-status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(name + ' exit ' + str(result.returncode), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
