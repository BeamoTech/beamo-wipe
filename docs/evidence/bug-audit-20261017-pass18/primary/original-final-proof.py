"""Replay final high-level regression families on exact private starting source."""
import datetime,hashlib,json,os,subprocess,tarfile,tempfile
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass18-primary')
names=json.loads((out/'source-review.json').read_text())['added']
start=json.loads((out/'starting-freeze.json').read_text())
with tempfile.TemporaryDirectory(prefix='beamo-pass18-original-') as temporary:
    private=Path(temporary)
    source={}
    with tarfile.open(out/'starting-inputs.tar.gz','r:gz') as archive:
        for member in archive.getmembers():
            if member.name.startswith(('src/','tests/')):
                assert member.isfile() and '..' not in Path(member.name).parts and not member.name.startswith('/')
                data=archive.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==start[member.name]
                target=private/member.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                source[member.name]=hashlib.sha256(data).hexdigest()
    for name in names:
        (private/name).write_bytes((root/name).read_bytes())
    config=private/'pytest.ini';config.write_text('[pytest]\npythonpath = src tests\n')
    env=dict(os.environ,PATH='/tmp/beamo-pass18-python/bin:/tmp/beamo-pass18-fallback-guard:'+os.environ['PATH'],PYTHONPATH=str(private/'src'),BEAMO_WIPE_DRY_RUN='1',BEAMO_ISOLATED_X11_TEST='1')
    for key in ('BEAMO_WIPE_LIVE','BEAMO_WIPE_BOOT_DEVICE','BEAMO_DESKTOP_NATIVE_INVENTORY_TEST','AT_SPI_BUS_ADDRESS','PULSE_SERVER'):
        env.pop(key,None)
    command=['dbus-run-session','--','xvfb-run','-a','-n','160','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-pass18-python/bin/python3','-m','pytest','-q','-c',str(config),*names,'--junitxml='+str(out/'original-final-proof.xml')]
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (out/'original-final-proof.txt').open('wb') as log:
        result=subprocess.run(command,cwd=private,env=env,stdout=log,stderr=subprocess.STDOUT)
    receipt=dict(command=command,exit_code=result.returncode,source=source,tests={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names},started_utc=started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),private_source_only=True,omitted='none; all332 final regression cases replayed')
    (out/'original-final-proof-status.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert result.returncode==1,result.returncode
    print('original final high-level proof finished, expected failing exit1',flush=True)
