"""Final applicable local phases, serialized, with immutable source admission."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

root=Path.cwd(); out=Path('/tmp/pass21-primary')
freeze=json.loads((out/'source-freeze.json').read_text())
def authenticate():
    changed=[n for n,h in freeze.items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
    assert not changed, changed
    assert not subprocess.check_output(['git','diff','--cached','--name-only'])
env=dict(os.environ)
assert not env.get('PYTEST_PLUGINS') and not env.get('PYTEST_ADDOPTS')
for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST','BEAMO_TK_PROBE_SOURCE','BEAMO_TK_PROBE_SHA256'):
    assert not env.get(key), key
env.update(PATH='/tmp/beamo-pass21-python/bin:/tmp/beamo-pass21-fallback-guard:/root/.local/state/beamo-setup/workspaces/f37aa1b2ab37a572bca6/tools/go-1.26.8-linux-amd64/go/bin:'+env['PATH'],GOTOOLCHAIN='local',BEAMO_WIPE_DRY_RUN='1',BEAMO_GATE_CHILD='1',BEAMO_GATE_JUNIT=str(out/'final.xml'))
phases=[('lint',['./scripts/ci-hosted.sh','lint'],root),('preview',['./scripts/ci-hosted.sh','preview'],root),('negative',['./scripts/ci-hosted.sh','negative'],root),('go-version',['go','version'],root/'desktop'),('go-race',['go','test','-count=1','-race','./...'],root/'desktop'),('go-vet',['go','vet','./...'],root/'desktop'),('go-windows-crossbuild',['go','test','-c','-o',str(out/'desktop-windows.test.exe')],root/'desktop'),('go-fuzz',['go','test','-run=^$','-fuzz=FuzzBootOption','-fuzztime=350000x','-parallel=2'],root/'desktop'),('final',['./scripts/ci-hosted.sh','tests'],root)]
assert not (out/'local-gate-status.json').exists()
status=[]
for name,command,cwd in phases:
    authenticate()
    for suffix in ('.txt','.xml','.xml.orca.xml'):
        assert not (out/(name+suffix)).exists()
    phase_env=dict(env)
    if name=='go-windows-crossbuild': phase_env.update(GOOS='windows',GOARCH='amd64')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(name+' started '+started,flush=True)
    with (out/(name+'.txt')).open('xb') as log:
        result=subprocess.run(command,cwd=cwd,env=phase_env,stdout=log,stderr=subprocess.STDOUT)
    authenticate()
    row=dict(phase=name,command=command,exit_code=result.returncode,started_utc=started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_freeze_sha256=hashlib.sha256((out/'source-freeze.json').read_bytes()).hexdigest(),crossbuild_env=({'GOOS':'windows','GOARCH':'amd64'}if name=='go-windows-crossbuild'else{}),pytest_plugins=None)
    status.append(row)
    (out/'local-gate-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(name+' exit '+str(result.returncode),flush=True)
    if result.returncode: raise SystemExit(result.returncode)
