"""Serialize final focused campaigns; a failure stops dependent verification."""
import datetime,json,os,subprocess
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass14-primary');env=dict(os.environ,PYTHONPATH=str(root/'src'),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
 env.pop(key,None)
python='/tmp/beamo-wipe-audit-python/bin/python3'
phases=[('independent-original',[python,str(out/'original-proof.py')]),('adjacent-final',[python,str(out/'run-adjacent.py')]),('discovery-matrix',[python,'/tmp/pass14-discovery/permutation_matrix.py']),('runner-differential',[python,'/tmp/pass14-runner/differential-matrix.py']),('ui-geometry',[python,'/tmp/pass14-ui/run-geometry.py'])]
status=[]
for name,cmd in phases:
 print(name+' started',flush=True)
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (out/(name+'-driver.txt')).open('wb') as log:r=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 status.append(dict(phase=name,command=cmd,started_utc=started,exit_code=r.returncode,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 (out/'focused-campaign-status.json').write_text(json.dumps(status,indent=2)+'\n')
 print(name+' exit '+str(r.returncode),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
