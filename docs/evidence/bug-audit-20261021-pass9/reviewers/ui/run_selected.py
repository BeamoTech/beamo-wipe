from pathlib import Path
import datetime,json,subprocess,sys,time
r=Path(__file__).parent
names=json.loads((r/'selected-tests.json').read_text())
command=['dbus-run-session','--','xvfb-run','-a','-n','169','-s','-screen 0 1600x1000x24 -dpi 72',sys.executable,'-m','pytest','-q','-W','error','--strict-markers','--junitxml='+str(r/'focused-ui.xml'),*names]
t=time.monotonic();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (r/'focused-ui.log').open('wb') as log: code=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT,cwd='/workspace/beamo-wipe')
(r/'focused-ui.status.json').write_text(json.dumps({'command':command,'started_utc':start,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':code},indent=2)+'\n')
print(code);sys.exit(code)
