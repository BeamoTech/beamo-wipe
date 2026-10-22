from pathlib import Path
import datetime, hashlib, json, subprocess, time
r=Path(__file__).parent; repo=Path('/workspace/beamo-wipe')
old=json.loads(Path('/workspace/beamo-tools/audit-pass10-20261021/recovery/focused-umask022.status.json').read_text())['command']
modules=[x for x in old if x.startswith('tests/')]
(r/'focused-modules.json').write_text(json.dumps(modules,indent=2)+'\n')
(r/'focused-input-sha256.json').write_text(json.dumps({p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in modules},indent=2,sort_keys=True)+'\n')
command=['env','BEAMO_ISOLATED_X11_TEST=1','dbus-run-session','--','xvfb-run','-a','-n','211','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-W','error','-p','no:cacheprovider','-o','addopts=','-q',*modules,'--junitxml='+str(r/'focused.xml')]
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic()
with (r/'focused.log').open('wb') as f: p=subprocess.run(command,cwd=repo,stdout=f,stderr=subprocess.STDOUT)
status={'command':command,'modules':len(modules),'started_utc':start,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode,'umask':'022','fake_devices_only':True}
(r/'focused.status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status));raise SystemExit(p.returncode)
