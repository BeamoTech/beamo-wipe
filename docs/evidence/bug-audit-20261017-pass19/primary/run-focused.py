import datetime,json,os,subprocess
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass19-primary')
prior=json.loads((root/'docs/evidence/bug-audit-20261017-pass18/primary/new-tests-sha256.json').read_text())
extra=['tests/test_report_intent.py','tests/test_report_intent_identity_regression.py','tests/test_report_shutdown.py','tests/test_audio_responsiveness.py','tests/test_audio_launch_ownership_pass14.py','tests/test_laptop_power.py','tests/test_power_monitor_launch_pass8.py','tests/test_support_export_pass8.py','tests/test_diagnostic_malformed_bounds_pass8.py','tests/test_ci_hosted.py::test_cloud_upload_excludes_local_captures_and_env_files']
tests=list(dict.fromkeys([*prior,*extra]))
env=dict(os.environ,PATH='/tmp/beamo-pass19-python/bin:/tmp/beamo-pass19-fallback-guard:'+os.environ['PATH'],PYTHONPATH=os.pathsep.join((str(root/'src'),str(root/'tests'))),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST','AT_SPI_BUS_ADDRESS','PULSE_SERVER'):
    env.pop(key,None)
command=['dbus-run-session','--','xvfb-run','-a','-n','150','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-pass19-python/bin/python3','-m','pytest','-q',*tests,'--junitxml='+str(out/'focused.xml')]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'focused.txt').open('wb') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
(out/'focused-status.json').write_text(json.dumps(dict(command=command,exit_code=result.returncode,started_utc=started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
print('focused exit',result.returncode,flush=True)
raise SystemExit(result.returncode)
