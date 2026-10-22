from pathlib import Path
import datetime,json,subprocess,sys,time
r=Path(__file__).parent;name=sys.argv[1];command=sys.argv[2:]
t=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (r/(name+'.log')).open('wb') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
d={'name':name,'command':command,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,3),'exit_code':p.returncode}
(r/(name+'.status.json')).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d));raise SystemExit(p.returncode)
