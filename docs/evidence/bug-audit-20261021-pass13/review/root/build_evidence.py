"""Retain the complete PASS13 proof after the final frozen sequence succeeds."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as E

repo=Path('/workspace/beamo-wipe')
r=Path(__file__).parent
w=r.parent
out=repo/'docs/evidence/bug-audit-20261021-pass13'
load=lambda p:json.loads(p.read_text())
freeze=load(r/'final-freeze.json')
assert load(r/'final-sequence.status.json')['exit_code']==0
assert load(r/'final-tests.status.json')['exit_code']==0
assert not out.exists(),'retain once; preserve failed curation attempts separately'
source=load(r/'final-source-sha256.json')
assert len(source)==831 and all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in source.items())
log=(r/'final-tests.log').read_text()
assert '[ci-hosted] PASS phase=tests' in log and 'warnings summary' not in log
assert not re.search(r'\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b',log)
groups=['final-new-regressions','final-independent-probes',
 'final-model-probe_typed_source_ownership','final-model-audio_queue_model',
 'final-model-terminal_provenance_model','final-model-shutdown_overlay_epoch_model',
 'final-lint','final-preview','final-negative','doctor-test','doctor-desktop',
 'final-go-new','final-go-independent-probe','final-go-media-model','final-go-race',
 'final-go-vet','final-go-fuzz','final-windows-test-build','final-desktop-build',
 'actual-preview-inspect','artifact-inspection','system-browser-tests','final-tests']
statuses={n:load(r/(n+'.status.json')) for n in groups}
assert all(st['exit_code']==0 for st in statuses.values())

def report(path,passed,skipped):
    cases=list(E.parse(path).iter('testcase'))
    assert len(cases)==len({(c.get('classname'),c.get('name')) for c in cases})==passed+skipped
    assert all(c.find(kind) is None for c in cases for kind in ('failure','error'))
    skip=[c for c in cases if c.find('skipped') is not None]
    assert len(skip)==skipped
    return {'cases':len(cases),'passed':passed,'skipped':skipped,'failures':0,'errors':0,
     'junit_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
     'skips':[{'id':c.get('classname')+'::'+c.get('name'),'message':c.find('skipped').get('message')} for c in skip]}

reports={'final-tests.xml':report(r/'final-tests.xml',11967,28),
 'final-tests.xml.orca.xml':report(r/'final-tests.xml.orca.xml',1,0)}
out.mkdir(parents=True)
def retain(src,target,compress=False):
    dst=out/(target+('.gz' if compress else ''))
    dst.parent.mkdir(parents=True,exist_ok=True)
    data=src.read_bytes()
    dst.write_bytes(gzip.compress(data,mtime=0) if compress else data)

retain(r/'final-source-sha256.json','source-sha256.json')
root_files=['baseline.json','runtime-observation.json','starting-source-sha256.json',
 'final-freeze.json','exact-baseline-receipt.json','run_group.py','run_final_sequence.py',
 'freeze_source.py','replay_exact_baseline.py','build_evidence.py','verify_retained.py',
 'inspect_live_preview.py','review_artifacts.py','system_browser_check.py',
 'test_gate_log_probe.py','test_remaining_probes.py','test_gtk_independent_probe.py',
 'media_hash_independent_test.go','media-hash-overlay.json','baseline-media.go',
 'exact-go-baseline-overlay.json']
for n in root_files:retain(r/n,'review/root/'+n)
for p in sorted((r/'model-replays').iterdir()):
    if p.is_file() and p.suffix in {'.py','.go','.json','.jsonl'}:
        retain(p,'review/model-replays/'+p.name,compress=p.suffix=='.jsonl')
for n in groups:
    retain(r/(n+'.status.json'),'checks/status/'+n+'.json')
    retain(r/(n+'.log'),'checks/'+n+'.log',True)
retain(r/'final-sequence.status.json','checks/status/final-sequence.json')
retain(r/'final-sequence.log','checks/final-sequence.log',True)
for n in ['final-tests.xml','final-tests.xml.orca.xml','final-new-regressions.xml',
 'final-independent-probes.xml','system-browser-tests.xml']:
    retain(r/n,'checks/'+n,True)
for n in ['actual-preview.json','actual-preview.log','artifact-review.json','system-browser-runtime.json']:
    retain(r/n,'checks/'+n)
for p in sorted(r.iterdir()):
    if not p.is_file() or not ('before' in p.name or p.name.startswith(('exact-python-baseline.','exact-go-baseline.'))):continue
    if p.suffix in {'.py','.go','.json','.xml','.log','.exit'}:
        retain(p,'proofs/root/'+p.name,compress=p.suffix in {'.xml','.log'})
for owner in ['discovery','runner','ui','recovery','boot']:
    for p in sorted((w/owner).iterdir()):
        if not p.is_file() or 'checkpoint' in p.name.lower():continue
        if p.suffix in {'.py','.go','.json','.xml','.log','.txt','.exit','.jsonl','.md','.patch','.diff'}:
            retain(p,'reviewers/'+owner+'/'+p.name,compress=p.suffix in {'.xml','.log','.jsonl'})
execution={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'client_timezone':'America/Chicago','container':load(r/'final-sequence.status.json'),
 'groups':statuses,'source_frozen':True,'child_umask':'022','private_display_dpi':72,
 'actual_device_or_power_actions':False,'remote_write_or_release':False}
(out/'checks/execution.json').write_text(json.dumps(execution,indent=2)+'\n')
shutil.copyfile(r/'README.final.md',out/'README.md')
shutil.copyfile(r/'verify_retained.py',out/'verify_retained.py')
count=sum(p.is_file() for p in out.rglob('*'))+1
summary={'base_commit':freeze['baseline_commit'],'branch':'fix/safety-audit-20261019',
 'audit_date':'2026-10-21','client_timezone':'America/Chicago','verified_root_causes':6,
 'canonical_reports':reports,'canonical_unique_passed':11968,'canonical_main_passed':11967,
 'canonical_orca_passed':1,'unchanged_skips_unverified':28,'canonical_python_warning_count':0,
 'new_python_regression_cases':170,'baseline_main_test_ids_retained':11825,
 'baseline_skip_ids_and_reasons_unchanged':True,'verified_source_files':831,
 'source_manifest_sha256':freeze['source_manifest_sha256'],
 'all_existing_test_files_byte_identical':True,'old_assertions_preserved':True,
 'go_full_race_named_pass_events':467,'go_native_skips_unverified':2,
 'new_go_leaf_cases':7,'new_go_named_pass_events':8,'baseline_go_named_results_retained':461,
 'system_browser_supplement_passed':9,'system_browser_is_pinned':False,'go_fuzz_executions':350000,
 'retained_artifacts':count,'native_or_physical_qualification':False,'remote_write_or_release_performed':False}
(out/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 for p in sorted(out.rglob('*')) if p.is_file()}
assert len(manifest)==count
(out/'artifacts-sha256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
subprocess.run(['python3',str(out/'verify_retained.py')],cwd=repo,check=True)
print(json.dumps({'sources':831,'retained_artifacts':count,'unique_python_passes':11968,
 'unchanged_skips':28,'go_named_passes':467,'verified_roots':6}))
