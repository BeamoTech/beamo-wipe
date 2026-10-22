from pathlib import Path
import datetime,json,subprocess,sys,time
root=Path(__file__).parent
name=sys.argv[1]; command=sys.argv[2:]; started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic()
with (root/(name+'.log')).open('wb') as log:
 p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
r={'name':name,'command':command,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode}
(root/(name+'.status.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(p.returncode)
