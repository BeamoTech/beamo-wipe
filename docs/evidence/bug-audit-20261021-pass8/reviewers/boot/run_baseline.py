from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
repo=Path('/workspace/beamo-wipe');out=Path(__file__).parent
assert 'BEAMO_DESKTOP_NATIVE_INVENTORY_TEST' not in os.environ
selection=json.loads(Path('/workspace/beamo-tools/audit-pass7-20261021/boot/focused-selection.json').read_text())
selection.append('developer_tests/test_dev_runtime_decode_pass7_20261021.py')
(out/'focused-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
sources=[*repo.glob('desktop/*.go'),repo/'dev.py',repo/'scripts/build_desktop.py',repo/'scripts/build-iso.sh',repo/'scripts/build-usb-image.sh',repo/'scripts/stage_live_assets.py',repo/'scripts/stage_wrapper_sources.py',repo/'scripts/preview.sh']
(out/'source-sha256.json').write_text(json.dumps({str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},indent=2)+'\n')
for name,cmd,cwd in [('focused-baseline',['python3','-m','pytest','-W','error','-p','no:cacheprovider','-q',*selection,'--junitxml='+str(out/'focused-baseline.xml')],repo),('go-baseline-race',['go','test','-count=1','-race','-json','./...'],repo/'desktop'),('go-vet',['go','vet','./...'],repo/'desktop')]:
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic()
 with(out/(name+'.log')).open('wb')as f:p=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
 receipt={'name':name,'command':cmd,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode}
 (out/(name+'.status.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
