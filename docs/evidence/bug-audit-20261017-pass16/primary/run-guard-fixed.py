"""Focused fake-only report/export/power/audio local guard-fixed."""
import json,os,subprocess,tempfile
from pathlib import Path
out=Path('/tmp/pass16-primary')
with tempfile.TemporaryDirectory(prefix='beamo-pass16-guard-fixed-') as private:
    runtime=Path(private)/'runtime'; runtime.mkdir(mode=0o700)
    env=dict(os.environ,PATH='/tmp/beamo-pass16-fallback-guard:'+os.environ['PATH'],PYTHONPATH=str(Path.cwd()/'src'),XDG_RUNTIME_DIR=str(runtime),PULSE_RUNTIME_PATH=str(runtime/'pulse'),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
    for key in ('AT_SPI_BUS_ADDRESS','PULSE_SERVER','BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
        env.pop(key,None)
    cmd=['dbus-run-session','--','xvfb-run','-a','-n','150','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-pass16-python/bin/python3','-m','pytest','-q',*json.loads((out/'guard-fixed-files.json').read_text()),'--junitxml='+str(out/'guard-fixed.xml')]
    with (out/'guard-fixed.txt').open('wb') as log:
        result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    (out/'guard-fixed-exit.json').write_text(json.dumps({'command':cmd,'exit_code':result.returncode})+'\n')
    print('guard-fixed exit',result.returncode)
    raise SystemExit(result.returncode)
