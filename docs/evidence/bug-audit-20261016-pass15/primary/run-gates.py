"""Execute applicable local phases once, sequentially, without installations."""
import datetime,json,os,subprocess
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass15-primary');env=dict(os.environ)
env.update(PATH='/tmp/beamo-wipe-audit-python/bin:/tmp/beamo-audit-go.oeGvle/go/bin:'+env['PATH'],GOTOOLCHAIN='local',BEAMO_GATE_CHILD='1',BEAMO_GATE_JUNIT=str(out/'final.xml'))
assert env.get('BEAMO_DESKTOP_NATIVE_INVENTORY_TEST') is None
phases=[('lint',['./scripts/ci-hosted.sh','lint'],root),('preview',['./scripts/ci-hosted.sh','preview'],root),('negative',['./scripts/ci-hosted.sh','negative'],root),('go-version',['go','version'],root/'desktop'),('go-race',['go','test','-count=1','-race','./...'],root/'desktop'),('go-vet',['go','vet','./...'],root/'desktop'),('go-windows-crossbuild',['go','test','-c','-o',str(out/'desktop-windows.test.exe')],root/'desktop'),('go-fuzz',['go','test','-run=^$','-fuzz=FuzzBootOption','-fuzztime=350000x','-parallel=2'],root/'desktop'),('final',['./scripts/ci-hosted.sh','tests'],root)]
status=[]
for name,command,cwd in phases:
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(name+' started',flush=True)
    with (out/(name+'.txt')).open('wb') as log:
        phase_env=dict(env)
        if name=='go-windows-crossbuild': phase_env.update(GOOS='windows',GOARCH='amd64')
        result=subprocess.run(command,cwd=cwd,env=phase_env,stdout=log,stderr=subprocess.STDOUT)
    status.append({'phase':name,'command':command,'exit_code':result.returncode,'crossbuild_env':({'GOOS':'windows','GOARCH':'amd64'} if name=='go-windows-crossbuild' else {}),'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (out/'local-gate-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(name+' exit '+str(result.returncode),flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
