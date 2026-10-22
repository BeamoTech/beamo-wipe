import datetime,json,os,subprocess,time
from pathlib import Path
r=Path(__file__).parent
paths=json.loads(Path('/workspace/beamo-tools/audit-pass10-20261021/runner/selected-tests.json').read_text())
paths=sorted(set(paths+['tests/test_live_session_power.py','tests/test_laptop_power.py','tests/test_sleep_inhibit_diagnostic_retirement_pass11_20261021.py']))
(r/'selected-tests.json').write_text(json.dumps(paths,indent=2)+'\n')
command=['python3','-m','pytest','-q','-W','error','--junitxml='+str(r/'focused.xml'),*paths]
t=time.monotonic(); started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (r/'focused.log').open('wb') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
d={'command':command,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode,'child_umask':'022','private_72dpi_x11':True}
(r/'focused.status.json').write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d));raise SystemExit(p.returncode)
