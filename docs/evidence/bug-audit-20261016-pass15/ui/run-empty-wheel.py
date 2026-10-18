"""Own private display/DBus; execute only when root admits the runtime lane."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

out = Path('/tmp/pass15-ui')
with tempfile.TemporaryDirectory(prefix='beamo-pass15-ui-') as private:
    runtime = Path(private) / 'runtime'
    runtime.mkdir(mode=0o700)
    env = dict(os.environ, BEAMO_ISOLATED_X11_TEST='1', BEAMO_WIPE_DRY_RUN='1',
               PYTHONPATH=str(Path.cwd() / 'src'), XDG_RUNTIME_DIR=str(runtime),
               PULSE_RUNTIME_PATH=str(runtime / 'pulse'))
    for key in ('AT_SPI_BUS_ADDRESS', 'PULSE_SERVER', 'BEAMO_WIPE_LIVE',
                'BEAMO_WIPE_BOOT_DEVICE', 'BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
        env.pop(key, None)
    command = ['dbus-run-session', '--', 'xvfb-run', '-a', '-n', '170', '-s',
               '-screen 0 800x600x24 -dpi 72 -nolisten tcp',
               '/tmp/beamo-wipe-audit-python/bin/python3', str(out / 'empty-wheel-probe.py')]
    with (out / 'empty-wheel-probe.txt').open('wb') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    (out / 'empty-wheel-exit.json').write_text(json.dumps(dict(command=command,
        exit_code=result.returncode, private_display=True, native_inventory=False,
        engine=False, hardware=False))+'\n')
    print('probe exit', result.returncode)
    raise SystemExit(result.returncode)
