"""Run the canonical Python/Orca phase after the proved harness correction.

Reuse the exact-source first eight successful phases. Preserve the failed
instrumented run and do not inject any observer into this acceptance run.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path.cwd()
out = Path('/tmp/pass19-primary')
failed = out / 'failed-gate-1'
old = json.loads((out / 'local-gate-status.json').read_text())
assert len(old) == 9 and all(r['exit_code'] == 0 for r in old[:8])
assert old[-1]['exit_code'] == 1
assert json.loads((failed / 'local-gate-status.json').read_text()) == old
freeze = json.loads((out / 'source-freeze.json').read_text())
assert len(freeze) == 771
assert not [n for n, h in freeze.items() if hashlib.sha256((root / n).read_bytes()).hexdigest() != h]
for name in ('final.txt', 'final.xml.orca.xml', 'source-freeze.json', 'desktop-windows.test.exe'):
    assert (failed / name).read_bytes() == (out / name).read_bytes(), name
assert not (out / 'final.xml').exists()
assert not (out / 'canonical-final-admission.json').exists()
env = dict(os.environ)
assert not env.get('PYTEST_PLUGINS') and not env.get('PYTEST_ADDOPTS')
assert not env.get('BEAMO_DESKTOP_NATIVE_INVENTORY_TEST')
env.update(
    PATH='/tmp/beamo-pass19-python/bin:/tmp/beamo-pass19-fallback-guard:/root/.local/state/beamo-setup/workspaces/f37aa1b2ab37a572bca6/tools/go-1.26.8-linux-amd64/go/bin:' + env['PATH'],
    GOTOOLCHAIN='local', BEAMO_GATE_CHILD='1', BEAMO_GATE_JUNIT=str(out / 'final.xml'),
)
command = ['./scripts/ci-hosted.sh', 'tests']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
admission = dict(
    started_utc=started, frozen_inputs=771,
    source_freeze_sha256=hashlib.sha256((out / 'source-freeze.json').read_bytes()).hexdigest(),
    reused_phases=old[:8], preserved_failure='failed-gate-1',
    corrected_harness='No PYTEST_PLUGINS or PYTEST_ADDOPTS; canonical command unchanged',
    plugin_inheritance_proof=json.loads((out / 'plugin-inheritance-proof.json').read_text()),
    abort_cause='UNEXPLAINED; not attributed to the proved child-import failure',
)
(out / 'canonical-final-admission.json').write_text(json.dumps(admission, indent=2) + '\n')
(out / 'final.xml.orca.xml').unlink()
print('canonical Python/Orca phase started ' + started, flush=True)
with (out / 'final.txt').open('wb') as log:
    result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
row = dict(phase='final', command=command, exit_code=result.returncode,
           crossbuild_env={}, pytest_plugins=None, observer_sha256=None,
           started_utc=started, ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out / 'local-gate-status.json').write_text(json.dumps(old[:8] + [row], indent=2) + '\n')
print('canonical Python/Orca phase exit ' + str(result.returncode), flush=True)
raise SystemExit(result.returncode)
