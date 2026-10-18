"""Serial final-source campaigns after the canonical local gate has ended."""
import datetime
import json
import os
from pathlib import Path
import subprocess

root=Path.cwd();out=Path('/tmp/pass16-primary')
assert all(row['exit_code']==0 for row in json.loads((out/'local-gate-status.json').read_text()))
assert len(json.loads((out/'local-gate-status.json').read_text()))==9
runner=Path('/tmp/pass16-runner')
assert (out/'runner-original-fixtures.tar.gz').is_file()
assert not (runner/'original-fixtures').exists()
(runner/'fixtures').rename(runner/'original-fixtures')
python='/tmp/beamo-pass16-python/bin/python3'
env=dict(os.environ,PATH='/tmp/beamo-pass16-fallback-guard:'+os.environ['PATH'],PYTHONPATH=str(root/'src'),BEAMO_WIPE_DRY_RUN='1')
for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST'):
    env.pop(key,None)
phases=[
    ('runner-fresh',[python,str(runner/'fresh-boundaries.py')],runner/'fresh-boundaries.txt'),
    ('runner-cancel',[python,str(runner/'cancel-boundaries.py')],runner/'cancel-boundaries.txt'),
    ('geometry',[python,'/tmp/pass16-ui/run-geometry.py'],out/'geometry-driver.txt'),
    ('reports',[python,str(out/'report-checks-matrix.py')],out/'report-checks-matrix-artifacts.json'),
]
status=[]
for name,command,logpath in phases:
    print(name+' started',flush=True)
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with logpath.open('wb') as log:
        result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    status.append(dict(phase=name,command=command,exit_code=result.returncode,
        started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    (out/'final-campaign-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(name+' exit '+str(result.returncode),flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    if name=='geometry':
        receipt=json.loads(Path('/tmp/pass16-ui/geometry-summary.json').read_text())
        assert receipt['cases']==receipt['passed']==270 and not receipt['failed'] and not receipt['forbidden_calls']
        assert receipt['hashes']==receipt['final_hashes']
        log=Path('/tmp/pass16-ui/geometry-matrix.txt').read_text()
        assert not any(term in log for term in ('invalid command name','Traceback','bgerror','Exception in Tkinter'))
