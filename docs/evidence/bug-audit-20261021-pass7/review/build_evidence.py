"""Retain seventh-pass evidence after actual full gate success."""
from pathlib import Path
import ast,datetime,gzip,hashlib,json,re,shutil,subprocess
import xml.etree.ElementTree as E
repo=Path('/workspace/beamo-wipe');r=Path(__file__).parent;w=r.parent
out=repo/'docs/evidence/bug-audit-20261021-pass7'
base='938fe60347c78f2a745d5d5b04e30dfa013da809'
def load(p):return json.loads(p.read_text())
def cases(p):return list(E.parse(p).iter('testcase'))
def identities(cs):return {(c.get('classname'),c.get('name'))for c in cs}
def skips(cs):return {(c.get('classname'),c.get('name')):c.find('skipped').get('message')for c in cs if c.find('skipped')is not None}
def pass_report(p,n):
 cs=cases(p);assert len(cs)==n,(p,len(cs));assert len(identities(cs))==n
 assert all(c.find(t)is None for c in cs for t in ('failure','error','skipped')),p
 return cs
status=load(r/'final-tests.status.json');assert status['exit_code']==0
assert load(r/'final-sequence.status.json')['exit_code']==0
log=(r/'final-tests.log').read_text();assert '[ci-hosted] PASS phase=tests'in log
assert 'warnings summary'not in log
assert not re.search(r'\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b',log)
new=pass_report(r/'final-new-regressions.xml',170);pass_report(r/'final-original-probes.xml',39);pass_report(r/'system-browser-tests.xml',9)
prior=list(E.fromstring(gzip.decompress((out.parent/'bug-audit-20261021-pass6/checks/final-tests.xml.gz').read_bytes())).iter('testcase'));assert len(identities(prior))==11382
main=cases(r/'final-tests.xml');orca=pass_report(r/'final-tests.xml.orca.xml',1)
assert len(main)==11552 and len(identities(main))==11552
assert all(c.find(t)is None for c in main for t in ('failure','error'))
assert identities(prior)<=identities(main)and identities(main)-identities(prior)==identities(new)
assert skips(prior)==skips(main)and len(skips(main))==28
assert not identities(main).intersection(identities(orca))
frozen=load(r/'final-source-sha256.json');assert len(frozen)==814
assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
names=('final-new-regressions','final-original-probes','final-lint','final-preview','final-negative','final-go-race','final-go-vet','final-go-fuzz','final-windows-test-build','final-desktop-build','actual-preview-inspect','system-browser-tests','doctor-test','doctor-desktop','artifact-inspection')
groups=[load(r/(n+'.status.json'))for n in names];assert all(g['exit_code']==0 for g in groups)
for phase in ('lint','preview','negative'):assert '[ci-hosted] PASS phase='+phase in(r/('final-'+phase+'.log')).read_text()
go=[json.loads(line)for line in(r/'final-go-race.log').read_text().splitlines()]
assert not any(e['Action']=='fail'for e in go)and go[-1]['Action']=='pass'and'Test'not in go[-1]
assert '(cached)'not in(r/'final-go-race.log').read_text()
go_skips=[e['Test']for e in go if e['Action']=='skip'];assert set(go_skips)=={'TestLinuxInventoryRetainsPartitionParents','TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert 'execs: 350000'in(r/'final-go-fuzz.log').read_text()
assert load(r/'artifact-review.json')['independent_bundle_verifier'].startswith('PASS:')
execution={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':load(r/'final-freeze.json')['source_manifest_sha256'],'canonical_tests':{**status,'python_warning_count':0,'main_passed':11524,'main_skipped':28,'separate_orca_passed':1},'completed_groups':groups,'history':'Initial final-lint E731 in new test helper corrected without changing assertions; exact final baseline proof rechecked; earlier gate receipts retained as history only. No canonical suite was canceled or replaced.','actual_device_or_power_actions':False,'remote_write_or_release':False}
(r/'final-check-status.json').write_text(json.dumps(execution,indent=2)+'\n')
assert not out.exists(),'Evidence is created once after success; investigate rather than overwrite'
out.mkdir(parents=True)
def retain(source,target):
 target=out/target;target.parent.mkdir(parents=True,exist_ok=True)
 raw=source.read_bytes()
 if target.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
 target.write_bytes(raw)
for n in ('final-source-sha256.json','final-freeze.json','independent-original-proofs.json','independent-review.json','baseline.json','starting-source-sha256.json','go-component-source-sha256.json','root-lint-correction.json'):
 retain(r/n,'review/'+n if n!='final-source-sha256.json'else'source-sha256.json')
retain(r/'artifact-review.json','artifact-review.json');retain(r/'final-check-status.json','checks/execution.json')
for n in ('run_group.py','run_go.sh','run_final_sequence.py','freeze_source.py','build_evidence.py','review_artifacts.py','inspect_live_preview.py','system_browser_check.py','probe_consent_sequences.py','consent-sequences.json','consent-sequences.log','consent-sequences.status.json'):
 retain(r/n,'review/'+n)
for n in ('final-tests','final-new-regressions','final-original-probes','final-lint','final-preview','final-negative','final-go-race','final-go-vet','final-go-fuzz','final-windows-test-build','final-desktop-build','actual-preview-inspect','system-browser-tests','doctor-test','doctor-desktop','artifact-inspection'):
 retain(r/(n+'.status.json'),'checks/status/'+n+'.json')
 suffix='.jsonl.gz'if n=='final-go-race'else'.log';retain(r/(n+'.log'),'checks/'+n+suffix)
for n in ('final-tests.xml','final-tests.xml.orca.xml','final-new-regressions.xml','final-original-probes.xml','system-browser-tests.xml'):
 retain(r/n,'checks/'+n+'.gz')
for n in ('actual-preview.json','actual-preview.log','system-browser-runtime.json'):
 retain(r/n,'checks/'+n)
for p in sorted(r.glob('*-independent-before.*')):
 retain(p,'proofs/'+p.name+('.gz'if p.suffix=='.xml'else''))
for p in sorted(r.glob('recovery-final-exact-baseline.*')):
 retain(p,'proofs/'+p.name+('.gz'if p.suffix=='.xml'else''))
for p in sorted(r.glob('history-*')):
 if p.is_file():retain(p,'history/root/'+p.name+('.gz'if p.suffix=='.xml'else''))
# Bounded fake-only reviewer receipts, including failures and setup history.
# Full checkout archives, caches, environment diagnostics and operational notes stay local.
for owner in ('discovery','ui','recovery','boot','runner'):
 for p in sorted((w/owner).iterdir()):
  if not p.is_file()or'checkpoint'in p.name.lower()or p.name=='test_storage_io_recovery.original.py':continue
  if p.suffix not in {'.json','.xml','.log','.txt','.exit','.py','.patch','.diff','.jsonl','.stderr','.md'}:continue
  category='history'if p.name.startswith('history-')else'reviewers'
  retain(p,category+'/'+owner+'/'+p.name+('.gz'if p.suffix in {'.xml','.jsonl'}else''))
# Preserve initial exact module before a later lint-only import correction.
for p in sorted((w/'discovery/history-before-lint').glob('*')):
 if p.is_file()and p.suffix in {'.py','.log','.xml','.json'}:retain(p,'history/discovery/before-lint/'+p.name+('.gz'if p.suffix=='.xml'else''))
retain(w/'recovery/test_storage_io_recovery.original.py','review/original-storage-fixture.py.txt')
reports={}
for n,cs in [('final-tests.xml',main),('final-tests.xml.orca.xml',orca)]:
 reports[n]={'cases':len(cs),'passed':len(cs)-len(skips(cs)),'skipped':len(skips(cs)),'failures':0,'errors':0,'junit_sha256':hashlib.sha256((r/n).read_bytes()).hexdigest(),'skips':[{'id':a+'::'+b,'message':v}for(a,b),v in skips(cs).items()]}
summary={'base_commit':base,'branch':'fix/safety-audit-20261019','audit_date_utc':'2026-10-21','verified_root_causes':5,'canonical_reports':reports,'canonical_unique_passed':11525,'canonical_skipped_unverified':28,'canonical_python_warning_count':0,'new_python_regressions_passed':170,'new_case_breakdown':{'live_filesystem_proof':64,'refresh_claim_retirement':18,'plain_visible_review':8,'persistent_publication_binding':40,'development_runtime_decode':40},'baseline_main_test_ids_retained':11382,'baseline_skip_ids_and_reasons_unchanged':True,'verified_source_files':814,'source_manifest_sha256':execution['source_manifest_sha256'],'existing_assertions_preserved':True,'existing_fixture_metadata_completed':'tests/test_storage_io_recovery.py','go_full_race_named_pass_events':sum(e['Action']=='pass'and'Test'in e for e in go),'go_full_race_native_skips':go_skips,'new_go_tests':0,'system_browser_supplement_passed':9,'system_browser_is_pinned':False,'configured_mypy':'PASS: no issues in 52 source files','native_or_physical_qualification':False,'remote_write_or_release_performed':False}
(out/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copyfile(r/'README.final.md',out/'README.md');shutil.copyfile(r/'verify_retained.py',out/'verify_retained.py')
manifest={}
for p in sorted(out.rglob('*')):
 if p.is_file():
  raw=p.read_bytes();manifest[str(p.relative_to(out))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
(out/'artifacts-sha256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
subprocess.run(['python3',str(out/'verify_retained.py')],check=True,cwd=repo)
print(json.dumps({'evidence_directory':str(out),'sources':814,'artifacts':len(manifest),'canonical_unique_passed':11525,'skipped_unverified':28}))
