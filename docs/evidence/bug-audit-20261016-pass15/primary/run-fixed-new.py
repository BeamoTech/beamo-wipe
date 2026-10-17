"""Focused fake-only report/export/power/audio local baseline."""
import json,os,subprocess,tempfile
from pathlib import Path
out=Path('/tmp/pass15-primary')
with tempfile.TemporaryDirectory(prefix='beamo-pass15-baseline-') as private:
    runtime=Path(private)/'runtime'; runtime.mkdir(mode=0o700)
    env=dict(os.environ,PYTHONPATH=str(Path.cwd()/'src'),XDG_RUNTIME_DIR=str(runtime),PULSE_RUNTIME_PATH=str(runtime/'pulse'),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
    for key in ('AT_SPI_BUS_ADDRESS','PULSE_SERVER','BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
        env.pop(key,None)
    cmd=['dbus-run-session','--','xvfb-run','-a','-n','150','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-wipe-audit-python/bin/python3','-m','pytest','-q',*json.loads((out/'new-files.json').read_text()),'--junitxml='+str(out/'fixed-new.xml')]
    with (out/'fixed-new.txt').open('wb') as log:
        result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    (out/'fixed-new-exit.json').write_text(json.dumps({'command':cmd,'exit_code':result.returncode})+'\n')
    print('fixed new exit',result.returncode)
    raise SystemExit(result.returncode)
