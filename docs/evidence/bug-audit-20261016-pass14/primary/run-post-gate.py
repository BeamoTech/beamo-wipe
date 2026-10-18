"""Serial final-source artifact campaigns admitted only after all gate phases pass."""
import datetime,json,os,shutil,subprocess
from pathlib import Path
out=Path('/tmp/pass14-primary')
s=json.loads((out/'local-gate-status.json').read_text())
assert len(s)==9 and all(p['exit_code']==0 for p in s)
ui=Path('/tmp/pass14-ui')
for name in ('geometry-matrix.json','geometry-summary.json','geometry-matrix.txt','geometry-exit.json'):
    shutil.copyfile(ui/name,ui/('before-owned-cleanup-'+name))
python='/tmp/beamo-wipe-audit-python/bin/python3'
env=dict(os.environ,PYTHONPATH=str(Path.cwd()/'src'),BEAMO_WIPE_DRY_RUN='1')
phases=[('geometry-final',[python,str(ui/'run-geometry.py')]),('report-checks-matrix-artifacts',[python,str(out/'report-checks-matrix.py')]),('final-summary-driver',[python,str(out/'summarize.py')]),('artifact-review-driver',[python,str(out/'review-artifacts.py')]),('focused-final-review-driver',[python,str(out/'verify-focused-final.py')])]
status=[]
for name,command in phases:
    print(name+' started',flush=True)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=out/(name+('.json' if name=='report-checks-matrix-artifacts' else '.txt'))
    with log.open('wb') as f:
        result=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
    status.append({'phase':name,'command':command,'exit_code':result.returncode,'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (out/'post-gate-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(name+' exit '+str(result.returncode),flush=True)
    if result.returncode: raise SystemExit(result.returncode)
