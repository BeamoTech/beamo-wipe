"""Verify PASS7 exact source, original assertions, receipts and unique test IDs."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as E

out=Path(__file__).resolve().parent
repo=out.parents[2]
def load(p):return json.loads(p.read_text())
def cs(p):return list(E.fromstring(gzip.decompress(p.read_bytes())).iter('testcase'))
def ids(items):return {(c.get('classname'),c.get('name'))for c in items}
def skips(items):return {(c.get('classname'),c.get('name')):c.find('skipped').get('message')for c in items if c.find('skipped')is not None}
def green(p,count,unique_count=None):
 items=cs(p);assert len(items)==count and len(ids(items))==(count if unique_count is None else unique_count),(p,len(items),len(ids(items)))
 assert all(c.find(t)is None for c in items for t in ('failure','error','skipped')),p
 return items
raw=(out/'source-sha256.json').read_bytes();frozen=json.loads(raw)
assert len(frozen)==814
assert hashlib.sha256(raw).hexdigest()=='d57686503509b70773b42e6827d496c07f237ac807c74006f9ad9a6cc546faf1'
for name,h in frozen.items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=repo).decode().split('\0')
actual={n for n in names if n and (n.startswith(('src/','tests/','scripts/','packaging/','desktop/','developer_tests/'))or n in {'dev.py','pyproject.toml','requirements-dev.txt','preview'})and(repo/n).is_file()}
assert actual==set(frozen),actual.symmetric_difference(frozen)
starting=load(out/'review/starting-source-sha256.json');assert len(starting)==809
review=load(out/'review/independent-review.json')
assert review['existing_test_files_modified']==['tests/test_storage_io_recovery.py']and review['existing_assertions_preserved']is True
for n,h in starting.items():
 if n.startswith(('tests/','developer_tests/'))and n!='tests/test_storage_io_recovery.py':assert frozen[n]==h,n
old=(out/'review/original-storage-fixture.py.txt').read_text();new=(repo/'tests/test_storage_io_recovery.py').read_text()
assert hashlib.sha256(old.encode()).hexdigest()==starting['tests/test_storage_io_recovery.py']
assert [ast.dump(a)for a in ast.walk(ast.parse(old))if isinstance(a,ast.Assert)]==[ast.dump(a)for a in ast.walk(ast.parse(new))if isinstance(a,ast.Assert)]
old_block='''        if kind == "evidence":
            identity = SimpleNamespace(st_dev=1, st_ino=2)
            patch.setattr(os, "fstat", Mock(return_value=identity))
            patch.setattr(os, "stat", Mock(return_value=identity))'''
new_block='''        identity = SimpleNamespace(st_dev=1, st_ino=2)
        patch.setattr(os, "fstat", Mock(return_value=identity))
        patch.setattr(os, "stat", Mock(return_value=identity))'''
assert old.count(old_block)==1 and old.replace(old_block,new_block)==new
summary=load(out/'final-summary.json');assert summary['verified_root_causes']==5
assert summary['source_manifest_sha256']==hashlib.sha256(raw).hexdigest()
seen=set();passed=skipped=0
for name,record in summary['canonical_reports'].items():
 p=out/'checks'/(name+'.gz');items=cs(p)
 assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==record['junit_sha256']
 assert len(items)==record['cases']and len(ids(items))==len(items)
 assert not seen.intersection(ids(items));seen.update(ids(items))
 assert all(c.find(t)is None for c in items for t in ('failure','error'))
 passed+=len(items)-len(skips(items));skipped+=len(skips(items))
 if name=='final-tests.xml':main=items
assert passed==summary['canonical_unique_passed']==11525
assert skipped==summary['canonical_skipped_unverified']==28
oldcases=cs(out.parent/'bug-audit-20261021-pass6/checks/final-tests.xml.gz');assert len(ids(oldcases))==11382
newcases=green(out/'checks/final-new-regressions.xml.gz',170)
assert ids(oldcases)<=ids(main)and ids(main)-ids(oldcases)==ids(newcases)
assert skips(oldcases)==skips(main)and summary['baseline_skip_ids_and_reasons_unchanged']is True
assert summary['new_case_breakdown']=={'live_filesystem_proof':64,'refresh_claim_retirement':18,'plain_visible_review':8,'persistent_publication_binding':40,'development_runtime_decode':40}
for path,module,failed,controls in (
 ('reviewers/discovery/expanded-original.xml.gz','test_live_filesystem_kind_pass7_20261021',30,34),
 ('reviewers/ui/refresh-expanded-before.xml.gz','test_refresh_diagnostic_retirement_pass7_20261021',8,10),
 ('reviewers/ui/plain-expanded-before.xml.gz','test_plain_review_flush_pass7_20261021',4,4),
 ('proofs/recovery-final-exact-baseline.xml.gz','test_recovery_publication_binding_pass7_20261021',23,17),
 ('reviewers/boot/bounded-repair-baseline.xml.gz','test_dev_runtime_decode_pass7_20261021',18,22),
):
 items=cs(out/path)
 assert all(c.find(t)is None for c in items for t in ('error','skipped')),path
 failures=sum(c.find('failure')is not None for c in items)
 assert (failures,len(items)-failures)==(failed,controls),path
 final=[c for c in newcases if c.get('classname').endswith(module)]
 assert len(final)==len(items)and {c.get('name')for c in final}=={c.get('name')for c in items},path
for receipt,key,module,product in (
 ('reviewers/discovery/expanded-original-receipt.json','test_sha256','tests/test_live_filesystem_kind_pass7_20261021.py','src/beamo_wipe/discover.py'),
 ('reviewers/ui/new-refresh-red-receipt.json','test_sha256','tests/test_refresh_diagnostic_retirement_pass7_20261021.py','src/beamo_wipe/wizard.py'),
 ('reviewers/ui/new-plain-red-receipt.json','test_sha256','tests/test_plain_review_flush_pass7_20261021.py','src/beamo_wipe/ui/console_wizard.py'),
):
 proof=load(out/receipt)
 assert proof['baseline']==summary['base_commit'] and proof[key]==frozen[module],receipt
 product_key='product_source_sha256'if 'product_source_sha256'in proof else'product_sha256'
 assert proof[product_key]==starting[product],receipt
correction=load(out/'review/root-lint-correction.json')
assert correction['final_sha256']==frozen[correction['path']] and correction['old_assertion_ast_identical']is True
boot=load(out/'reviewers/boot/repair-summary.json')
assert boot['baseline_commit']==summary['base_commit']
for n,h in boot['approved_paths_final_sha256'].items():assert frozen[n]==h
for stem,failed,controls in [('refresh-diagnostic',2,2),('intent-publish',1,1),('intent-restart',1,1),('journal-publish',1,1),('live-filesystem',12,9),('plain-buffered',1,1),('plain-real-buffered',1,1),('dev-cmdline',1,3)]:
 items=cs(out/'proofs'/(stem+'-independent-before.xml.gz'))
 assert all(c.find(t)is None for c in items for t in ('error','skipped'))
 f=sum(c.find('failure')is not None for c in items);assert (f,len(items)-f)==(failed,controls),stem
for p,n in [('checks/final-original-probes.xml.gz',39),('checks/system-browser-tests.xml.gz',9),('reviewers/discovery/adjacent-fixed.xml.gz',2200),('reviewers/ui/refresh-expanded-after.xml.gz',52),('reviewers/ui/native-adjacent-after.xml.gz',56),('reviewers/recovery/candidate-adjacent.xml.gz',560),('reviewers/boot/developer-fixed.xml.gz',251),('reviewers/boot/readiness-fixed.xml.gz',24),('reviewers/runner/baseline.xml.gz',1355),('reviewers/runner/adjacent.xml.gz',154)]:green(out/p,n)
# Two distinct external proof modules have empty classname and the same names.
# Validate all 54 pass events, exactly 52 JUnit IDs and only those two collisions.
plain=green(out/'reviewers/ui/plain-expanded-after.xml.gz',54,52)
from collections import Counter
counts=Counter((c.get('classname'),c.get('name'))for c in plain)
assert {k:v for k,v in counts.items()if v>1}=={
 ('','test_plain_review_delay_starts_after_warning_flush[visible-normal-control]'):2,
 ('','test_plain_review_delay_starts_after_warning_flush[buffered-output]'):2,
}
execution=load(out/'checks/execution.json');assert execution['canonical_tests']['exit_code']==0
assert execution['canonical_tests']['python_warning_count']==summary['canonical_python_warning_count']==0
assert all(g['exit_code']==0 for g in execution['completed_groups'])
for phase in ('tests','lint','preview','negative'):
 assert '[ci-hosted] PASS phase='+phase in(out/'checks'/('final-'+phase+'.log')).read_text()
assert 'warnings summary'not in(out/'checks/final-tests.log').read_text()
go=[json.loads(line)for line in gzip.decompress((out/'checks/final-go-race.jsonl.gz').read_bytes()).decode().splitlines()]
assert not any(e['Action']=='fail'for e in go)and go[-1]['Action']=='pass'and'Test'not in go[-1]
assert sum(e['Action']=='pass'and'Test'in e for e in go)==summary['go_full_race_named_pass_events']==338
assert {e['Test']for e in go if e['Action']=='skip'}==set(summary['go_full_race_native_skips'])=={'TestLinuxInventoryRetainsPartitionParents','TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert '(cached)'not in gzip.decompress((out/'checks/final-go-race.jsonl.gz').read_bytes()).decode()
assert 'execs: 350000'in(out/'checks/final-go-fuzz.log').read_text()
for name,h in review['go_component_inputs'].items():assert frozen[name]==starting[name]==h
matrix=load(out/'reviewers/runner/projection_boundary_matrix.json')
assert matrix['comparisons']==39000 and matrix['sequences']==3000 and matrix['mismatch_count']==0
assert matrix['source_sha256']['runner']==frozen['src/beamo_wipe/nwipe_runner.py']
model=load(out/'review/consent-sequences.json')
assert model['counts']['sessions']==360 and model['counts']['actions']==9528
assert model['counts']['authorized_starts']==model['counts']['completed_sessions']==102
assert model['native_callbacks']==0 and model['failures']==[]
for n,h in model['source_sha256'].items():assert starting[n]==h
preview=load(out/'checks/actual-preview.json')
assert preview['normal_close_acceptance']is True and preview['returncode']==0 and preview['fake_disks_only']is True
assert preview['welcome_content_observed_before_capture']is True
assert load(out/'checks/system-browser-runtime.json')['pinned_playwright_runtime']is False
manifest=load(out/'artifacts-sha256.json')
files={str(p.relative_to(out))for p in out.rglob('*')if p.is_file()and p.name!='artifacts-sha256.json'}
assert files==set(manifest),files.symmetric_difference(manifest)
for n,record in manifest.items():
 data=(out/n).read_bytes();assert len(data)==record['bytes']and hashlib.sha256(data).hexdigest()==record['sha256'],n
print(json.dumps({'verified_source_files':len(frozen),'retained_artifacts':len(manifest),'unique_passed':passed,'skipped_unverified':skipped,'new_python_regressions_passed':170,'prior_main_ids_retained':11382,'existing_assertions_preserved':True}))
