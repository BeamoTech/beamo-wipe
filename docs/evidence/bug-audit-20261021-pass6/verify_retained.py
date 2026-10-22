"""Verify exact sixth-pass source, artifact hashes, JUnit IDs and Go results."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

dest=Path(__file__).resolve().parent
repo=dest.parents[2]
frozen_bytes=(dest/'source-sha256.json').read_bytes()
frozen=json.loads(frozen_bytes)
assert len(frozen)==809
assert hashlib.sha256(frozen_bytes).hexdigest()=='f7c98a059747973265ff37ce7e146833aef5e5c22a4123d551ea4a9c84f2e582'
for name,digest in frozen.items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest,name
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=repo).decode().split('\0')
selected={n for n in names if n and (n.startswith(('src/','tests/','scripts/','packaging/','desktop/','developer_tests/'))
          or n in {'dev.py','pyproject.toml','requirements-dev.txt','preview'})and(repo/n).is_file()}
assert selected==set(frozen),selected.symmetric_difference(frozen)

def cases(path):
    return list(ET.fromstring(gzip.decompress(path.read_bytes())).iter('testcase'))

def ids(items):
    return {(c.get('classname'),c.get('name'))for c in items}

def skips(items):
    return {(c.get('classname'),c.get('name')):c.find('skipped').get('message')
            for c in items if c.find('skipped')is not None}

def passed_cases(path,expected):
    items=cases(path)
    assert len(items)==expected,(path,len(items))
    assert all(c.find(t)is None for c in items for t in ('failure','error','skipped')),path
    return items

summary=json.loads((dest/'final-summary.json').read_text())
assert summary['verified_root_causes']==5
seen=set();passed=skipped=0
for name,record in summary['canonical_reports'].items():
    path=dest/'checks'/(name+'.gz')
    raw=gzip.decompress(path.read_bytes())
    assert hashlib.sha256(raw).hexdigest()==record['junit_sha256']
    items=cases(path)
    assert len(items)==record['cases']
    for case in items:
        identity=case.get('classname'),case.get('name')
        assert identity not in seen,identity
        seen.add(identity)
        assert case.find('failure')is None and case.find('error')is None,identity
        if case.find('skipped')is None:passed+=1
        else:skipped+=1
    if name=='final-tests.xml':final_cases=items
assert passed==summary['canonical_unique_passed']==11355
assert skipped==summary['canonical_skipped_unverified']==28
new=passed_cases(dest/'checks/new-regressions.xml.gz',200)
assert summary['new_python_regressions_passed']==200
old=cases(dest.parent/'bug-audit-20261021-pass5/checks/final-tests.xml.gz')
assert len(ids(old))==summary['baseline_main_test_ids_retained']==11182
assert ids(old)<=ids(final_cases)and ids(new)==ids(final_cases)-ids(old)
assert skips(old)==skips(final_cases)
assert summary['baseline_skip_ids_and_reasons_unchanged']is True
assert summary['new_case_breakdown']=={'mount_visibility':63,'cancel_receipt':111,'tk_callback_ownership':8,'curses_review_paint':18}
for name,modules,expected in (
    ('mount-expanded-before.xml.gz',('test_mount_visibility_pass6_20261021',),(30,33)),
    ('cancel-expanded-before.xml.gz',('test_cancel_delivery_receipt_pass6_20261021',),(48,63)),
    ('ui-expanded-before.xml.gz',('test_tk_callback_ownership_pass6_20261021','test_curses_review_paint_pass6_20261021'),(21,5)),
):
    red=cases(dest/'proofs'/name)
    assert all(c.find(t)is None for c in red for t in ('error','skipped'))
    failures=sum(c.find('failure')is not None for c in red)
    assert (failures,len(red)-failures)==expected,name
    # External baseline runs use different package roots; exact test names
    # must still match the corresponding final modules without omissions.
    actual=[c for c in new if c.get('classname').endswith(modules)]
    assert {c.get('name')for c in red}=={c.get('name')for c in actual},name
    assert len(red)==len(actual),name
passed_cases(dest/'checks/original-probes.xml.gz',59)
passed_cases(dest/'checks/system-browser.xml.gz',9)
passed_cases(dest/'checks/report-baseline.xml.gz',401)
for name,expected in [('mount-adjacent.xml.gz',834),('runner-adjacent.xml.gz',324),('ui-adjacent.xml.gz',263),('tk-controls.xml.gz',49),('boot-developer-baseline.xml.gz',285)]:
    passed_cases(dest/'checks'/name,expected)

def events(path):
    return [json.loads(line)for line in gzip.decompress(path.read_bytes()).decode().splitlines()]

go=events(dest/'checks/go-race.jsonl.gz')
assert not any(e['Action']=='fail'for e in go)
assert go[-1]['Action']=='pass'and'Test'not in go[-1]
assert sum(e['Action']=='pass'and'Test'in e for e in go)==summary['go_full_race_named_pass_events']==338
assert {e['Test']for e in go if e['Action']=='skip'}==set(summary['go_full_race_native_skips'])=={
    'TestLinuxInventoryRetainsPartitionParents',
    'TestWindowsInventoryReportsOnlyLauncherPartitionPass13',
}
prefix='TestUSBIdentityDirtyFieldMustBeBooleanPass620261021'
fixture={e['Test']for e in go if e['Action']=='pass'and e.get('Test','').startswith(prefix)}
assert prefix in fixture and len(fixture)==13
assert summary['new_go_parent_passed']==1 and summary['new_go_named_scenarios_passed']==12
red=events(dest/'proofs/identity-expanded-before.jsonl.gz')
assert not any(e['Action']=='skip'for e in red)
assert sum(e['Action']=='fail'and '/'in e.get('Test','')for e in red)==3
assert sum(e['Action']=='pass'and '/'in e.get('Test','')for e in red)==9
independent=events(dest/'checks/identity-independent-after.jsonl.gz')
assert not any(e['Action']in{'fail','skip'}for e in independent)
assert sum(e['Action']=='pass'and '/'in e.get('Test','')for e in independent)==3
execution=json.loads((dest/'checks/execution.json').read_text())
assert execution['canonical_tests']['exit_code']==0
assert execution['canonical_tests']['python_warning_count']==summary['canonical_python_warning_count']==0
assert 'warnings summary'not in(dest/'checks/full-source.log').read_text()
assert all(g['exit_code']==0 for g in execution['completed_groups'])
for phase in ('tests','lint','preview','negative'):
    log='full-source.log'if phase=='tests'else('safety-negative.log'if phase=='negative'else phase+'.log')
    assert '[ci-hosted] PASS phase='+phase in(dest/'checks'/log).read_text()
assert 'execs: 350000'in(dest/'checks/go-fuzz.log').read_text()
assert '(cached)'not in gzip.decompress((dest/'checks/go-race.jsonl.gz').read_bytes()).decode()
mount=json.loads((dest/'review/mount-model.json').read_text())
assert mount['source_sha256']==frozen['src/beamo_wipe/discover.py']
assert mount['unique_path_visibility_checks']==6106 and mount['mismatches']==[]
sharing=json.loads((dest/'review/sharing-matrix.json').read_text())
assert sharing['cases']==792
assert sharing['semantic_or_redaction_failures']==sharing['native_effects']==sharing['original_evidence_mutations']==0
for n,h in sharing['source_sha256'].items():assert frozen[n]==h
review=json.loads((dest/'review/independent-review.json').read_text())
assert review['existing_test_files_modified']is False
for n,h in review['go_component_inputs'].items():assert frozen[n]==h
manifest=json.loads((dest/'artifacts-sha256.json').read_text())
actual={str(p.relative_to(dest))for p in dest.rglob('*')if p.is_file()and p.name!='artifacts-sha256.json'}
assert actual==set(manifest)
for name,record in manifest.items():
    raw=(dest/name).read_bytes()
    assert len(raw)==record['bytes'],name
    assert hashlib.sha256(raw).hexdigest()==record['sha256'],name
print(json.dumps({'verified_source_files':len(frozen),'retained_artifacts':len(manifest),
                  'unique_passed':passed,'skipped_unverified':skipped,
                  'new_python_regressions_passed':200,'prior_main_ids_retained':11182,
                  'new_go_parent':1,'new_go_named_scenarios':12}))
