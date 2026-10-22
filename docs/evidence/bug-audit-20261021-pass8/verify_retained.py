"""Verify PASS8 exact source, unchanged tests, unique IDs and retained results."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as E

out=Path(__file__).resolve().parent;repo=out.parents[2]
load=lambda p:json.loads(p.read_text())
def cases(p):return list(E.fromstring(gzip.decompress(p.read_bytes())).iter('testcase'))
def ids(c):return {(x.get('classname'),x.get('name'))for x in c}
def skips(c):return {(x.get('classname'),x.get('name')):x.find('skipped').get('message')for x in c if x.find('skipped')is not None}
def green(p,n):
 c=cases(p);assert len(c)==len(ids(c))==n,(p,len(c),len(ids(c)))
 assert all(x.find(t)is None for x in c for t in ('failure','error','skipped')),p
 return c
raw=(out/'source-sha256.json').read_bytes();frozen=json.loads(raw)
assert len(frozen)==817 and hashlib.sha256(raw).hexdigest()=='7cf60bb07b56282c50a329b6a7906561fa0944689465d24bf1acf1f9070da430'
for n,h in frozen.items():assert hashlib.sha256((repo/n).read_bytes()).hexdigest()==h,n
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=repo).decode().split('\0')
selected={n for n in names if n and(n.startswith(('src/','tests/','scripts/','packaging/','desktop/','developer_tests/'))or n in{'dev.py','pyproject.toml','requirements-dev.txt','preview'})and(repo/n).is_file()}
assert selected==set(frozen),selected.symmetric_difference(frozen)
starting=load(out/'review/starting-source-sha256.json');assert len(starting)==814
for n,h in starting.items():
 if n.startswith(('tests/','developer_tests/','desktop/')):assert frozen[n]==h,n
review=load(out/'review/independent-review.json');assert review['all_old_test_files_byte_identical']is True
assert review['all_old_assertions_preserved']is True and review['verified_root_causes']==3
summary=load(out/'final-summary.json');assert summary['source_manifest_sha256']==hashlib.sha256(raw).hexdigest()
assert summary['all_existing_test_files_byte_identical']is True and summary['existing_assertions_preserved']is True
seen=set();passed=skipped=0
for n,record in summary['canonical_reports'].items():
 p=out/'checks'/(n+'.gz');c=cases(p)
 assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==record['junit_sha256']
 assert len(c)==len(ids(c))==record['cases']and not seen.intersection(ids(c));seen.update(ids(c))
 assert all(x.find(t)is None for x in c for t in ('failure','error'))
 passed+=len(c)-len(skips(c));skipped+=len(skips(c))
 if n=='final-tests.xml':main=c
assert passed==summary['canonical_unique_passed']==11612
assert skipped==summary['canonical_skipped_unverified']==28
old=cases(out.parent/'bug-audit-20261021-pass7/checks/final-tests.xml.gz');assert len(ids(old))==11552
new=green(out/'checks/final-new-regressions.xml.gz',87)
assert ids(old)<=ids(main)and ids(main)-ids(old)==ids(new)
assert skips(old)==skips(main)and summary['baseline_skip_ids_and_reasons_unchanged']is True
assert summary['new_case_breakdown']=={'power_acceptance_retirement':28,'startup_decode_refusal':34,'runner_diagnostic_retirement':25}
for path,module,failed,controls in (
 ('proofs/power-expanded-before.xml.gz','test_power_acceptance_retirement_pass8_20261021',12,16),
 ('reviewers/discovery/expanded-before.xml.gz','test_app_live_decode_refusal_pass8_20261021',16,18),
 ('reviewers/runner/expanded-original.xml.gz','test_cancel_diagnostic_retirement_pass8_20261021',18,7),
):
 c=cases(out/path);assert all(x.find(t)is None for x in c for t in ('error','skipped')),path
 f=sum(x.find('failure')is not None for x in c);assert(f,len(c)-f)==(failed,controls),path
 final=[x for x in new if x.get('classname').endswith(module)]
 assert len(final)==len(c)and {x.get('name')for x in final}=={x.get('name')for x in c},path
for receipt,module,product in (
 ('review/power-expanded-before-receipt.json','tests/test_power_acceptance_retirement_pass8_20261021.py','src/beamo_wipe/power.py'),
 ('reviewers/discovery/expanded-baseline-receipt.json','tests/test_app_live_decode_refusal_pass8_20261021.py','src/beamo_wipe/app.py'),
 ('reviewers/runner/expanded-original-receipt.json','tests/test_cancel_diagnostic_retirement_pass8_20261021.py','src/beamo_wipe/nwipe_runner.py'),
):
 p=load(out/receipt);assert p['baseline']==summary['base_commit']and p['test_sha256']==frozen[module]
 key='product_source_sha256'if 'product_source_sha256'in p else'product_sha256';assert p[key]==starting[product]
for name,failed,controls in [('power-acceptance',3,1),('live-decode',2,2),('cancel-diagnostic',2,2)]:
 c=cases(out/'proofs'/(name+'-independent-before.xml.gz'))
 assert all(x.find(t)is None for x in c for t in ('error','skipped'))
 f=sum(x.find('failure')is not None for x in c);assert(f,len(c)-f)==(failed,controls)
for path,n in [('checks/final-original-probes.xml.gz',12),('checks/system-browser-tests.xml.gz',9),('checks/power-fixed-adjacent.xml.gz',229),('checks/root-adjacent-baseline.xml.gz',197),('reviewers/discovery/adjacent-baseline.xml.gz',2200),('reviewers/discovery/app-adjacent-after.xml.gz',326),('reviewers/discovery/focused-after.xml.gz',38),('reviewers/runner/fixed-focused.xml.gz',2600),('reviewers/ui/baseline.xml.gz',266),('reviewers/ui/native-baseline.xml.gz',137),('reviewers/ui/power-adjacent.xml.gz',91),('reviewers/recovery/adjacent-baseline.xml.gz',715),('reviewers/boot/focused-baseline.xml.gz',325)]:green(out/path,n)
execution=load(out/'checks/execution.json');assert execution['canonical_tests']['exit_code']==0
assert execution['canonical_tests']['python_warning_count']==summary['canonical_python_warning_count']==0
assert execution['container_context']['exit_code']==0
assert all(g['exit_code']==0 for g in execution['completed_groups'])
for phase in ('tests','lint','preview','negative'):
 assert '[ci-hosted] PASS phase='+phase in(out/'checks'/('final-'+phase+'.log')).read_text()
assert 'warnings summary'not in(out/'checks/final-tests.log').read_text()
def goevents(p):return [json.loads(x)for x in gzip.decompress(p.read_bytes()).decode().splitlines()]
go=goevents(out/'checks/final-go-race.jsonl.gz')
assert not any(x['Action']=='fail'for x in go)and go[-1]['Action']=='pass'and'Test'not in go[-1]
assert sum(x['Action']=='pass'and'Test'in x for x in go)==summary['go_full_race_named_pass_events']==338
assert {x['Test']for x in go if x['Action']=='skip'}==set(summary['go_full_race_native_skips'])=={'TestLinuxInventoryRetainsPartitionParents','TestWindowsInventoryReportsOnlyLauncherPartitionPass13'}
assert '(cached)'not in gzip.decompress((out/'checks/final-go-race.jsonl.gz').read_bytes()).decode()
assert 'execs: 350000'in(out/'checks/final-go-fuzz.log').read_text()
model=goevents(out/'checks/final-readiness-model.jsonl.gz')
assert not any(x['Action']in{'fail','skip'}for x in model)
assert [x['Test']for x in model if x['Action']=='pass'and'Test'in x]==['TestPass8ReadinessActionModel']
readiness=load(out/'review/readiness-sequence-model.json')
assert readiness['sessions']==200 and readiness['public_action_requests']==16000
assert readiness['authorized_fake_restarts']==278 and readiness['windows_manual_policy_cases']==1000
assert readiness['failures']==readiness['native_callbacks']==0
inventory=load(out/'review/model-replays/inventory-equivalence.json')
assert inventory['counts']=={'contexts':256,'discovery_calls':3528,'representation_permutation_checks':3072,'layout_mutations_checked':456}
assert inventory['failures']==[]and inventory['native_callbacks']==0
completion=load(out/'review/model-replays/completion-contract-matrix.json')
assert completion['cases']==5832 and completion['expected_completed_controls']==24 and completion['expected_refusal_controls']==5808
assert completion['failure_count']==completion['native_callbacks']==0
semantic=load(out/'review/model-replays/semantic-export-matrix.json')
assert semantic['cases']==16200 and semantic['original_successes']==54 and semantic['actual_bundles']==2025
assert semantic['semantic_failures']==[]and semantic['native_callbacks']==0
for model in (inventory,completion,semantic):
 for n,h in model['source_sha256'].items():assert frozen[n]==h
provenance=load(out/'review/model-replay-provenance.json')
for name,data in provenance['python_models'].items():
 assert hashlib.sha256((out/'review/model-replays'/name).read_bytes()).hexdigest()==data['exact_script_sha256']
 assert (out/'review/model-replays'/name).read_bytes()==(out/'reviewers'/data['reviewer']/name).read_bytes()
original=(out/'reviewers/boot/readiness_sequence_model_test.go').read_text();replay=(out/'review/readiness_sequence_model_test.go').read_text()
assert original.replace('/workspace/beamo-tools/audit-pass8-20261021/boot/readiness-sequence-model.json','/workspace/beamo-tools/audit-pass8-20261021/root/readiness-sequence-model.json')==replay
preview=load(out/'checks/actual-preview.json');assert preview['normal_close_acceptance']is True and preview['returncode']==0
assert preview['fake_disks_only']is True and preview['welcome_content_observed_before_capture']is True
assert load(out/'checks/system-browser-runtime.json')['pinned_playwright_runtime']is False
manifest=load(out/'artifacts-sha256.json')
actual={str(p.relative_to(out))for p in out.rglob('*')if p.is_file()and p.name!='artifacts-sha256.json'}
assert actual==set(manifest),actual.symmetric_difference(manifest)
for n,record in manifest.items():
 data=(out/n).read_bytes();assert len(data)==record['bytes']and hashlib.sha256(data).hexdigest()==record['sha256'],n
print(json.dumps({'verified_source_files':817,'retained_artifacts':len(manifest),'unique_passed':passed,'skipped_unverified':skipped,'new_python_regressions_passed':87,'prior_main_ids_retained':11552,'all_old_test_files_unchanged':True}))
