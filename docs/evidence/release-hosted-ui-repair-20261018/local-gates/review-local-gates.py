"""Authenticate observed local results against their exact frozen inputs."""
import collections,datetime,hashlib,json,struct,subprocess,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path.cwd();out=Path('/tmp/beamo-release-20261017/hosted-ui-repair/local-gates')
status=json.loads((out/'local-gate-status.json').read_text())
expected_phases=['lint','preview','negative','go-version','go-race','go-vet','go-windows-crossbuild','go-fuzz','final']
assert [row['phase'] for row in status]==expected_phases
assert all(row['exit_code']==0 for row in status)
assert all(datetime.datetime.fromisoformat(row['ended_utc']) >= datetime.datetime.fromisoformat(row['started_utc']) for row in status)
assert all(datetime.datetime.fromisoformat(b['started_utc']) >= datetime.datetime.fromisoformat(a['ended_utc']) for a,b in zip(status,status[1:]))
assert all(row.get('pytest_plugins') is None and row.get('observer_sha256') is None for row in status)
assert status[0]['command']==['./scripts/ci-hosted.sh','lint'] and status[1]['command']==['./scripts/ci-hosted.sh','preview']
assert status[2]['command']==['./scripts/ci-hosted.sh','negative'] and status[-1]['command']==['./scripts/ci-hosted.sh','tests']
assert status[3]['command']==['go','version'] and status[4]['command']==['go','test','-count=1','-race','./...']
assert status[5]['command']==['go','vet','./...']
assert status[6]['command']==['go','test','-c','-o',str(out/'desktop-windows.test.exe')]
assert status[6]['crossbuild_env']=={'GOOS':'windows','GOARCH':'amd64'}
assert status[7]['command']==['go','test','-run=^$','-fuzz=FuzzBootOption','-fuzztime=350000x','-parallel=2']
assert all(not row['crossbuild_env'] for index,row in enumerate(status) if index!=6)
freeze=json.loads((out/'source-freeze.json').read_text())
assert len(freeze)==877
freeze_sha256=hashlib.sha256((out/'source-freeze.json').read_bytes()).hexdigest()
assert all(row['source_freeze_sha256']==freeze_sha256 for row in status)
for row in status:
    log=out/(row['phase']+'.txt')
    assert log.is_file() and not log.is_symlink()
    if log.stat().st_size:
        assert log.stat().st_mtime >= datetime.datetime.fromisoformat(row['started_utc']).timestamp()
    else:
        # Empty exclusive-created logs retain kernel creation time, which can
        # precede datetime.now() by sub-millisecond clock resolution. Bind them
        # to the previous phase's completed receipt and this phase's end.
        assert row['phase'] in {'go-vet','go-windows-crossbuild'}
        previous=status[status.index(row)-1]
        assert datetime.datetime.fromisoformat(previous['ended_utc']).timestamp() <= log.stat().st_mtime
        assert log.stat().st_mtime <= datetime.datetime.fromisoformat(row['ended_utc']).timestamp()
assert (out/'go-version.txt').read_text().strip()=='go version go1.26.8 linux/amd64'
assert not (out/'gate-verification.json').exists(), 'Do not overwrite prior verification'
changed=[n for n,h in freeze.items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
assert not changed,changed
assert 'PytestUnraisableExceptionWarning' not in (out/'final.txt').read_text()
assert 'warnings summary' not in (out/'final.txt').read_text()
reports=[out/'final.xml',out/'final.xml.orca.xml']
start=datetime.datetime.fromisoformat(status[-1]['started_utc']).timestamp()
assert all(p.stat().st_mtime>=start for p in reports)
cases=[c for p in reports for c in ET.parse(p).findall('.//testcase')]
ids=[(c.get('classname'),c.get('name')) for c in cases]
assert len(ids)==len(set(ids))
assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
skips={((c.get('classname') or ''),c.get('name')):c.find('skipped').get('message','') for c in cases if c.find('skipped') is not None}
prior=root/'docs/evidence/bug-audit-20261017-pass18/primary'
prior_hashes=json.loads((prior/'raw-evidence-sha256.json').read_text())
with tarfile.open(prior/'raw-evidence.tar.gz','r:gz') as archive:
    prior_reports=[]
    for name in ('final.xml','final.xml.orca.xml'):
        data=archive.extractfile(name).read()
        assert hashlib.sha256(data).hexdigest()==prior_hashes[name]
        prior_reports.append(ET.fromstring(data))
old_skips={(c.get('classname') or '',c.get('name')) for report in prior_reports for c in report.findall('.//testcase') if c.find('skipped') is not None}
assert set(skips)==old_skips and len(skips)==14
regression_files=json.loads((out/'new-tests-sha256.json').read_text())
assert len(regression_files)==61
assert all(freeze[n]==h==hashlib.sha256((root/n).read_bytes()).hexdigest() for n,h in regression_files.items())
regressions=collections.Counter()
for c in cases:
    name='tests/'+c.get('classname','').split('.')[-1]+'.py'
    if name in regression_files:
        assert c.find('skipped') is None
        regressions[name]+=1
assert set(regressions)==set(regression_files)
assert len(regressions)==61 and sum(regressions.values())==3943
guards=json.loads((out/'guard-manifest.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in guards.items())
assert not (out/'forbidden-fallback-attempts.txt').exists()
permitted=[json.loads(line) for line in (out/'permitted-offline-gcloud.jsonl').read_text().splitlines()]
assert all(row['command'][:2]==['meta','list-files-for-upload'] and 'test_cloud_upload_excludes_local_captures_and_env_files' in row['test'] for row in permitted)
binary=(out/'desktop-windows.test.exe').read_bytes();offset=struct.unpack_from('<I',binary,0x3c)[0]
assert binary[:2]==b'MZ' and binary[offset:offset+4]==b'PE\0\0'
assert struct.unpack_from('<H',binary,offset+4)[0]==0x8664
assert struct.unpack_from('<H',binary,offset+24)[0]==0x20b
# All nine current phases are fresh; no observer or prior admission/reuse receipt is accepted.
assert status[-1]['pytest_plugins'] is None and status[-1].get('observer_sha256') is None
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
subprocess.run(['git','diff','--check'],check=True)
receipt=dict(source_freeze_sha256=freeze_sha256, all_nine_phases_fresh=True, observer=None, status_sha256=hashlib.sha256((out/'local-gate-status.json').read_bytes()).hexdigest(), report_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in reports}, phases=len(status),passed=len(cases)-len(skips),skipped=len(skips),skips=[dict(classname=k[0],name=k[1],reason=v) for k,v in sorted(skips.items())],duplicates=0,failures=0,errors=0,frozen_inputs=len(freeze),changed_after_freeze=changed,regression_modules=len(regressions),regression_cases=sum(regressions.values()),regressions=dict(regressions),permitted_offline_sdk_calls=len(permitted),forbidden_fallbacks=0,windows_crossbuild=dict(bytes=len(binary),sha256=hashlib.sha256(binary).hexdigest(),format='PE32+ AMD64',native_acceptance=False))
with (out/'gate-verification.json').open('x') as handle:
    handle.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in {'skips','regressions'}},indent=2))
