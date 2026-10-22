from pathlib import Path
import datetime
import json
import os
import subprocess
import tempfile
import time

r=Path(__file__).parent
modules=json.loads((r/'focused-modules.json').read_text())
command=['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--','xvfb-run','-a','-n','221','-s','-screen 0 1600x1000x24 -dpi 72','/workspace/beamo-wipe/.venv-linux/bin/python3','-m','pytest','-q','-W','error','-p','no:cacheprovider','-o','addopts=','--strict-markers','--junitxml='+str(r/'focused-ui.xml'),*modules]
started=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic()
with tempfile.TemporaryDirectory(prefix='pass11-ui-',dir=r) as private:
 child_env=os.environ.copy()
 for name in ('AT_SPI_BUS_ADDRESS','DBUS_SESSION_BUS_ADDRESS'):
  child_env.pop(name,None)
 for name,subdir in [('XDG_RUNTIME_DIR','runtime'),('XDG_CACHE_HOME','cache')]:
  target=Path(private)/subdir; target.mkdir(mode=0o700)
  child_env[name]=str(target)
 with (r/'focused-ui.log').open('wb') as output:
  p=subprocess.run(command,cwd='/workspace/beamo-wipe',stdout=output,stderr=subprocess.STDOUT,umask=0o022,env=child_env)
receipt={'command':command,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode,'private_72dpi':True,'private_xdg_runtime_cache':True,'inherited_atspi_dbus_selectors_cleared':True,'child_umask':'022','fake_devices_only':True}
(r/'focused-ui.status.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));raise SystemExit(p.returncode)
