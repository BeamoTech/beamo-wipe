"""Verify exact fifth-pass source, retained artifacts, JUnit and Go identities."""
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
assert len(frozen)==804
assert hashlib.sha256(frozen_bytes).hexdigest()=='fcbe3ad83409ba91557fb5cd8584d25a42e72d3e71d4a7657e5b6cbc154144de'
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

summary=json.loads((dest/'final-summary.json').read_text())
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
assert passed==summary['canonical_unique_passed']==11155
assert skipped==summary['canonical_skipped_unverified']==28
new=cases(dest/'checks/new-regressions.xml.gz')
assert len(new)==summary['new_python_regressions_passed']==97
assert all(c.find(t)is None for c in new for t in ('failure','error','skipped'))
old=cases(dest.parent/'bug-audit-20261019-pass4/checks/resume-tests.xml.gz')
assert len(ids(old))==summary['baseline_main_test_ids_retained']==11085
assert ids(old)<=ids(final_cases)and ids(new)==ids(final_cases)-ids(old)
assert skips(old)==skips(final_cases)
assert summary['baseline_skip_ids_and_reasons_unchanged']is True
assert summary['new_case_breakdown']=={'recovery':47,'terminal':40,'linux_integration':1,'fifo_log_open':9}
for name,module,expected in (
    ('recovery-expanded-before.xml.gz','test_recovery_named_read_pass5_20261021',(29,18)),
    ('ui-expanded-before.xml.gz','test_console_key_origin_pass5_20261021',(18,22)),
    ('fifo-expanded-before.xml.gz','test_log_fifo_open_pass5_20261021',(3,6)),
):
    red=cases(dest/'proofs'/name)
    assert all(c.find(t)is None for c in red for t in ('error','skipped'))
    failures=sum(c.find('failure')is not None for c in red)
    assert (failures,len(red)-failures)==expected,name
    assert ids(red)==ids([c for c in new if c.get('classname').endswith(module)]),name

def events(name):
    return [json.loads(line)for line in gzip.decompress((dest/'checks'/name).read_bytes()).decode().splitlines()]

fixture=events('linux-fixture-race.jsonl.gz')
assert not any(e['Action']in{'fail','skip'}for e in fixture)
names={e['Test']for e in fixture if e['Action']=='pass'and'Test'in e}
assert len({n for n in names if '/'not in n})==summary['linux_integration_go_parent_passed']==1
assert len({n for n in names if '/'in n})==summary['linux_integration_named_subtests_passed']==15
assert summary['linux_integration_is_within_one_python_case']is True
assert summary['fifo_fixture_fresh_process']is True
for name in ('fifo-threaded-root.xml.gz','fifo-threaded-agent.xml.gz'):
    threaded=cases(dest/'checks'/name)
    assert len(threaded)==summary['fifo_threaded_strict_passed']==9
    assert all(c.find(t)is None for c in threaded for t in ('failure','error','skipped'))
spawn=json.loads((dest/'review/fifo-spawn-baseline.json').read_text())
assert spawn['test_sha256']==spawn['source_test_sha256']==frozen['tests/test_log_fifo_open_pass5_20261021.py']
go=events('go-race.jsonl.gz')
assert not any(e['Action']=='fail'for e in go)
assert go[-1]['Action']=='pass'and'Test'not in go[-1]
assert {e['Test']for e in go if e['Action']=='skip'}==set(summary['go_full_race_native_skips'])=={
    'TestLinuxInventoryRetainsPartitionParents',
    'TestWindowsInventoryReportsOnlyLauncherPartitionPass13',
}
execution=json.loads((dest/'checks/execution.json').read_text())
assert execution['canonical_tests']['exit_code']==0
assert execution['canonical_tests']['python_warning_count']==summary['canonical_python_warning_count']==0
assert 'warnings summary'not in(dest/'checks/full-source.log').read_text()
assert all(g['exit_code']==0 for g in execution['completed_groups'])
reuse=json.loads((dest/'review/final-freeze.json').read_text())['go_component_reuse']
assert reuse['exit_code']==0 and reuse['execution_session']==75493
assert all(frozen[n]==h for n,h in reuse['unchanged_inputs'].items())
manifest=json.loads((dest/'artifacts-sha256.json').read_text())
actual={str(p.relative_to(dest))for p in dest.rglob('*')if p.is_file()and p.name!='artifacts-sha256.json'}
assert actual==set(manifest)
for name,record in manifest.items():
    raw=(dest/name).read_bytes()
    assert len(raw)==record['bytes'],name
    assert hashlib.sha256(raw).hexdigest()==record['sha256'],name
print(json.dumps({'verified_source_files':len(frozen),'retained_artifacts':len(manifest),
                  'unique_passed':passed,'skipped_unverified':skipped,
                  'new_python_regressions_passed':97,'prior_main_ids_retained':11085,
                  'linux_fixture_go_parent':1,'linux_fixture_named_scenarios':15}))
