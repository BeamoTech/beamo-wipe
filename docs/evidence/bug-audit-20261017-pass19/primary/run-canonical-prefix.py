"""Capture the first failure under the final phase's actual environment."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path.cwd()
out = Path('/tmp/pass19-primary')
assert not (out / 'canonical-prefix.xml').exists()
env = dict(os.environ)
assert not env.get('PYTEST_PLUGINS') and not env.get('PYTEST_ADDOPTS')
env.update(
    PATH='/tmp/beamo-pass19-python/bin:/tmp/beamo-pass19-fallback-guard:/root/.local/state/beamo-setup/workspaces/f37aa1b2ab37a572bca6/tools/go-1.26.8-linux-amd64/go/bin:' + env['PATH'],
    PYTHONPATH=str(root / 'src') + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else ''),
    GOTOOLCHAIN='local', BEAMO_GATE_CHILD='1', BEAMO_GATE_JUNIT=str(out / 'final.xml'),
    BEAMO_WIPE_DRY_RUN=env.get('BEAMO_WIPE_DRY_RUN', '1'),
    BEAMO_ISOLATED_X11_TEST='1', BEAMO_HOSTED_ORCA_SEPARATE='1', DEBIAN_FRONTEND='noninteractive',
    PIP_CACHE_DIR=env.get('PIP_CACHE_DIR', str(root / '.ci-cache/pip')),
)
for key in ('AT_SPI_BUS_ADDRESS', 'PULSE_SERVER'):
    env.pop(key, None)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with tempfile.TemporaryDirectory(prefix='beamo-p19-canonical-prefix-') as runtime:
    Path(runtime).chmod(0o700)
    env.update(XDG_RUNTIME_DIR=runtime, PULSE_RUNTIME_PATH=runtime + '/pulse')
    command = ['dbus-run-session', '--', 'xvfb-run', '-a', '-n', '200', '-s',
               '-screen 0 1600x1000x24 -dpi 72', '/tmp/beamo-pass19-python/bin/python3',
               '-m', 'pytest', '--deselect=tests/test_accessible_runtime.py::test_orca_announces_every_result',
               '--maxfail=1', '-p', 'docs.evidence.bug-audit-20261017-pass19.primary.canonical_prefix_observer',
               '--junitxml=' + str(out / 'canonical-prefix.xml')]
    with (out / 'canonical-prefix.txt').open('xb') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
receipt = dict(command=command, exit_code=result.returncode,
               started_utc=started, ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               observer='parent-only, scalar failure records, no monkeypatch',
               final_phase_environment=True, concurrent_orca=False)
(out / 'canonical-prefix-status.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
raise SystemExit(result.returncode)
