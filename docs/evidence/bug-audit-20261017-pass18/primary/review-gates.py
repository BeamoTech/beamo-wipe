"""Authenticate observed local results against their exact frozen inputs."""
import collections,datetime,hashlib,json,struct,subprocess,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass18-primary')
status=json.loads((out/'local-gate-status.json').read_text())
assert len(status)==9 and all(row['exit_code']==0 for row in status)
freeze=json.loads((out/'source-freeze.json').read_text())
changed=[n for n,h in freeze.items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
assert not changed,changed
reports=[out/'final.xml',out/'final.xml.orca.xml']
start=datetime.datetime.fromisoformat(status[-1]['started_utc']).timestamp()
assert all(p.stat().st_mtime>=start for p in reports)
cases=[c for p in reports for c in ET.parse(p).findall('.//testcase')]
ids=[(c.get('classname'),c.get('name')) for c in cases]
assert len(ids)==len(set(ids))
assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
skips={((c.get('classname') or ''),c.get('name')):c.find('skipped').get('message','') for c in cases if c.find('skipped') is not None}
prior=root/'docs/evidence/bug-audit-20261017-pass17/primary'
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
regressions=collections.Counter()
for c in cases:
    name='tests/'+c.get('classname','').split('.')[-1]+'.py'
    if name in regression_files:
        assert c.find('skipped') is None
        regressions[name]+=1
assert set(regressions)==set(regression_files)
guards=json.loads((out/'guard-manifest.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in guards.items())
assert not (out/'forbidden-fallback-attempts.txt').exists()
permitted=[json.loads(line) for line in (out/'permitted-offline-gcloud.jsonl').read_text().splitlines()]
assert all(row['command'][:2]==['meta','list-files-for-upload'] and 'test_cloud_upload_excludes_local_captures_and_env_files' in row['test'] for row in permitted)
binary=(out/'desktop-windows.test.exe').read_bytes();offset=struct.unpack_from('<I',binary,0x3c)[0]
assert binary[:2]==b'MZ' and binary[offset:offset+4]==b'PE\0\0'
assert struct.unpack_from('<H',binary,offset+4)[0]==0x8664
assert struct.unpack_from('<H',binary,offset+24)[0]==0x20b
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
subprocess.run(['git','diff','--check'],check=True)
receipt=dict(phases=len(status),passed=len(cases)-len(skips),skipped=len(skips),skips=[dict(classname=k[0],name=k[1],reason=v) for k,v in sorted(skips.items())],duplicates=0,failures=0,errors=0,frozen_inputs=len(freeze),changed_after_freeze=changed,regression_modules=len(regressions),regression_cases=sum(regressions.values()),regressions=dict(regressions),permitted_offline_sdk_calls=len(permitted),forbidden_fallbacks=0,windows_crossbuild=dict(bytes=len(binary),sha256=hashlib.sha256(binary).hexdigest(),format='PE32+ AMD64',native_acceptance=False))
(out/'gate-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in {'skips','regressions'}},indent=2))
