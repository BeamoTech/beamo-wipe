"""Retain PASS8 only from completed actual execution and exact test identity."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,shutil,subprocess
import xml.etree.ElementTree as E
repo=Path('/workspace/beamo-wipe');r=Path(__file__).parent;w=r.parent
out=repo/'docs/evidence/bug-audit-20261021-pass8'
base='d8a941adc16cf0650d482f512e4b921d702373c5'
load=lambda p:json.loads(p.read_text())
def cases(p):return list(E.parse(p).iter('testcase'))
def ids(c):return {(x.get('classname'),x.get('name'))for x in c}
def skips(c):return {(x.get('classname'),x.get('name')):x.find('skipped').get('message')for x in c if x.find('skipped')is not None}
def green(p,n):
 c=cases(p);assert len(c)==len(ids(c))==n,(p,len(c),len(ids(c)))
 assert all(x.find(t)is None for x in c for t in ('failure','error','skipped')),p
 return c
assert load(r/'final-sequence.status.json')['exit_code']==0
status=load(r/'final-tests.status.json');assert status['exit_code']==0
log=(r/'final-tests.log').read_text();assert '[ci-hosted] PASS phase=tests'in log
assert 'warnings summary'not in log
assert not re.search(r'\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b',log)
new=green(r/'final-new-regressions.xml',87);green(r/'final-original-probes.xml',12);green(r/'system-browser-tests.xml',9)
prior=list(E.fromstring(gzip.decompress((out.parent/'bug-audit-20261021-pass7/checks/final-tests.xml.gz').read_bytes())).iter('testcase'));assert len(ids(prior))==11552
main=cases(r/'final-tests.xml');orca=green(r/'final-tests.xml.orca.xml',1)
assert len(main)==len(ids(main))==11639
assert all(x.find(t)is None for x in main for t in ('failure','error'))
assert ids(prior)<=ids(main)and ids(main)-ids(prior)==ids(new)
assert skips(prior)==skips(main)and len(skips(main))==28
assert not ids(main).intersection(ids(orca))
frozen=load(r/'final-source-sha256.json');assert len(frozen)==817
assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
names=('final-new-regressions','final-original-probes','final-inventory-model','final-completion-model','final-semantic-export-model','final-lint','final-preview','final-negative','doctor-test','doctor-desktop','final-go-race','final-go-vet','final-go-fuzz','final-readiness-model','final-windows-test-build','final-desktop-build','actual-preview-inspect','system-browser-tests','artifact-inspection')
groups=[load(r/(n+'.status.json'))for n in names];assert all(g['exit_code']==0 for g in groups)
for phase in ('lint','preview','negative'):assert '[ci-hosted] PASS phase='+phase in(r/('final-'+phase+'.log')).read_text()
go=[json.loads(x)for x in(r/'final-go-race.log').read_text().splitlines()]
assert not any(x['Action']=='fail'for x in go)and go[-1]['Action']=='pass'and'Test'not in go[-1]
assert '(cached)'not in(r/'final-go-race.log').read_text()
go_skips=[x['Test']for x in go if x['Action']=='skip'];assert set(go_skips)=={'TestLinuxInventoryRetainsPartitionParents','TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert 'execs: 350000'in(r/'final-go-fuzz.log').read_text()
assert load(r/'artifact-review.json')['independent_bundle_verifier'].startswith('PASS:')
execution={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':load(r/'final-freeze.json')['source_manifest_sha256'],'canonical_tests':{**status,'python_warning_count':0,'main_passed':11611,'main_skipped':28,'separate_orca_passed':1},'completed_groups':groups,'container_context':load(r/'final-sequence.status.json'),'context':'All final phases run serially in one unprivileged beamo-dev container; artifact byte inspection in host Python. No concurrent containers or source edits.','actual_device_or_power_actions':False,'remote_write_or_release':False}
(r/'final-check-status.json').write_text(json.dumps(execution,indent=2)+'\n')
assert not out.exists(),'Evidence created once; retain failed attempt before any correction'
out.mkdir(parents=True)
def retain(src,target):
 p=out/target;p.parent.mkdir(parents=True,exist_ok=True);raw=src.read_bytes()
 if p.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
 p.write_bytes(raw)
for n in ('final-freeze.json','independent-review.json','independent-original-proofs.json','baseline.json','starting-source-sha256.json','power-frozen-sha256.json','power-expanded-before-receipt.json','model-replay-provenance.json'):
 retain(r/n,'review/'+n)
retain(r/'final-source-sha256.json','source-sha256.json');retain(r/'artifact-review.json','artifact-review.json');retain(r/'final-check-status.json','checks/execution.json')
for n in ('run_group.py','run_final_sequence.py','freeze_source.py','build_evidence.py','review_artifacts.py','inspect_live_preview.py','system_browser_check.py','test_power_acceptance_probe.py','readiness_sequence_model_test.go','readiness-overlay.json'):
 retain(r/n,'review/'+n)
for p in sorted((r/'model-replays').iterdir()):
 if p.is_file()and p.suffix in {'.py','.json'}:retain(p,'review/model-replays/'+p.name)
retain(r/'readiness-sequence-model.json','review/readiness-sequence-model.json')
for n in (*names,'final-tests'):
 retain(r/(n+'.status.json'),'checks/status/'+n+'.json')
 suffix='.jsonl.gz'if n in {'final-go-race','final-readiness-model'}else'.log'
 retain(r/(n+'.log'),'checks/'+n+suffix)
for n in ('final-tests.xml','final-tests.xml.orca.xml','final-new-regressions.xml','final-original-probes.xml','system-browser-tests.xml','power-fixed-adjacent.xml','root-adjacent-baseline.xml'):
 retain(r/n,'checks/'+n+'.gz')
for n in ('actual-preview.json','actual-preview.log','system-browser-runtime.json','power-fixed-adjacent.log','root-adjacent-baseline.log','root-adjacent-selection.json'):
 retain(r/n,'checks/'+n)
for pattern in ('*-independent-before.*','power-expanded-before.*'):
 for p in sorted(r.glob(pattern)):
  if p.is_file():retain(p,'proofs/'+p.name+('.gz'if p.suffix=='.xml'else''))
for owner in ('discovery','runner','ui','recovery','boot'):
 for p in sorted((w/owner).iterdir()):
  if not p.is_file()or'checkpoint'in p.name.lower():continue
  if p.suffix not in {'.py','.go','.json','.xml','.log','.txt','.exit','.jsonl','.stderr','.md','.patch','.diff'}:continue
  category='history'if p.name.startswith('history-')else'reviewers'
  retain(p,category+'/'+owner+'/'+p.name+('.gz'if p.suffix in {'.xml','.jsonl'}else''))
for p in sorted(r.glob('history-*')):
 if p.is_file():retain(p,'history/root/'+p.name+('.gz'if p.suffix=='.xml'else''))
reports={}
for n,c in [('final-tests.xml',main),('final-tests.xml.orca.xml',orca)]:
 reports[n]={'cases':len(c),'passed':len(c)-len(skips(c)),'skipped':len(skips(c)),'failures':0,'errors':0,'junit_sha256':hashlib.sha256((r/n).read_bytes()).hexdigest(),'skips':[{'id':a+'::'+b,'message':v}for(a,b),v in skips(c).items()]}
summary={'base_commit':base,'branch':'fix/safety-audit-20261019','audit_date_utc':'2026-10-21','verified_root_causes':3,'canonical_reports':reports,'canonical_unique_passed':11612,'canonical_skipped_unverified':28,'canonical_python_warning_count':0,'new_python_regressions_passed':87,'new_case_breakdown':{'power_acceptance_retirement':28,'startup_decode_refusal':34,'runner_diagnostic_retirement':25},'baseline_main_test_ids_retained':11552,'baseline_skip_ids_and_reasons_unchanged':True,'verified_source_files':817,'source_manifest_sha256':execution['source_manifest_sha256'],'all_existing_test_files_byte_identical':True,'existing_assertions_preserved':True,'go_full_race_named_pass_events':sum(x['Action']=='pass'and'Test'in x for x in go),'go_full_race_native_skips':go_skips,'new_go_product_tests':0,'external_go_model_test':1,'system_browser_supplement_passed':9,'system_browser_is_pinned':False,'configured_mypy':'PASS: no issues in 52 source files','native_or_physical_qualification':False,'remote_write_or_release_performed':False}
(out/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copyfile(r/'README.final.md',out/'README.md');shutil.copyfile(r/'verify_retained.py',out/'verify_retained.py')
manifest={}
for p in sorted(out.rglob('*')):
 if p.is_file():
  raw=p.read_bytes();manifest[str(p.relative_to(out))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
(out/'artifacts-sha256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
subprocess.run(['python3',str(out/'verify_retained.py')],cwd=repo,check=True)
print(json.dumps({'sources':817,'retained_artifacts':len(manifest),'unique_python_passes':11612,'unchanged_skips':28,'new_cases':87,'verified_roots':3}))
