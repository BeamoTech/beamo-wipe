from pathlib import Path
import json, os, subprocess, sys, tempfile, time, xml.etree.ElementTree as ET
root = Path(__file__).parent
name = sys.argv[1]
args = sys.argv[2:]
command=['dbus-run-session','--','xvfb-run','-a','-n','271','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-q','-W','error','-p','no:cacheprovider','-o','addopts=','--strict-markers','--junitxml='+str(root/(name+'.xml')),*args]
started=time.monotonic()
with tempfile.TemporaryDirectory(prefix='private-',dir=root) as private:
    env=os.environ.copy()
    for key in ('AT_SPI_BUS_ADDRESS','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER'):
        env.pop(key,None)
    for key,part in [('XDG_RUNTIME_DIR','runtime'),('XDG_CACHE_HOME','cache')]:
        path=Path(private)/part;path.mkdir(mode=0o700);env[key]=str(path)
    env['BEAMO_ISOLATED_X11_TEST']='1';env['BEAMO_WIPE_DRY_RUN']='1'
    with (root/(name+'.log')).open('wb') as log:
        done=subprocess.run(command,cwd='/workspace/beamo-wipe',stdout=log,stderr=subprocess.STDOUT,env=env,umask=0o022)
receipt={'command':command,'exit_code':done.returncode,'elapsed_seconds':round(time.monotonic()-started,2),'private_display_72dpi':True,'native_inventory_opt_in':os.environ.get('BEAMO_ALLOW_NATIVE_INVENTORY'),'child_umask':'022'}
if (root/(name+'.xml')).exists():
    cases=list(ET.parse(root/(name+'.xml')).iter('testcase'))
    receipt.update(cases=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skips=sum(c.find('skipped') is not None for c in cases))
(root/(name+'.status.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(done.returncode)
