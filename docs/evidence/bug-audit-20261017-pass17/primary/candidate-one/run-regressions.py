import datetime,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass17-primary')
name=sys.argv[1]
tests=sys.argv[2:] or ['tests/test_descendant_hardware_ambiguity_pass17.py','tests/test_runner_model_lf_noerase_pass17.py','tests/test_startup_callback_retirement_pass17.py']
env=dict(os.environ,PATH='/tmp/beamo-pass17-python/bin:/tmp/beamo-pass17-fallback-guard:'+os.environ['PATH'],PYTHONPATH=str(root/'src'),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST','AT_SPI_BUS_ADDRESS','PULSE_SERVER'):
    env.pop(key,None)
command=['dbus-run-session','--','xvfb-run','-a','-n','160','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-pass17-python/bin/python3','-m','pytest','-q',*tests,'--junitxml='+str(out/(name+'.xml'))]
assert not (out/(name+'.xml')).exists()
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/(name+'.txt')).open('wb') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
(out/(name+'-status.json')).write_text(json.dumps(dict(command=command,exit_code=result.returncode,started_utc=started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
print(name,'exit',result.returncode,flush=True)
raise SystemExit(result.returncode)
