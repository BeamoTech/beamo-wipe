"""Verify PASS13 hashes, source, preserved tests, exact proofs and test deltas."""
from pathlib import Path
import gzip
import hashlib
import json
import xml.etree.ElementTree as E

out=Path(__file__).resolve().parent
repo=out.parents[2]
load=lambda p:json.loads(p.read_text())
manifest=load(out/'artifacts-sha256.json')
assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}==set(manifest)|{'artifacts-sha256.json'}
for name,record in manifest.items():
    p=out/name
    assert p.stat().st_size==record['bytes'],name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],name
summary=load(out/'final-summary.json')
freeze=load(out/'review/root/final-freeze.json')
source=load(out/'source-sha256.json')
assert len(source)==summary['verified_source_files']==831
assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in source.items())
assert hashlib.sha256((out/'source-sha256.json').read_bytes()).hexdigest()==summary['source_manifest_sha256']==freeze['source_manifest_sha256']
start=load(out/'review/root/starting-source-sha256.json')
changed={n for n,h in start.items() if source[n]!=h}
assert changed=={'desktop/media.go','scripts/build_desktop.py','src/beamo_wipe/ci_evidence.py',
 'src/beamo_wipe/evidence.py','src/beamo_wipe/sound.py','src/beamo_wipe/ui/accessible_wizard.py'}
assert all(source[n]==h for n,h in start.items() if n.startswith(('tests/','developer_tests/')) or n.endswith('_test.go'))

def junit(path,allow_fail=False):
    with gzip.open(path,'rb') as stream: cases=list(E.fromstring(stream.read()).iter('testcase'))
    ids={(c.get('classname'),c.get('name')) for c in cases}
    assert len(ids)==len(cases)
    counts={kind:sum(c.find(kind) is not None for c in cases) for kind in ('failure','error','skipped')}
    if not allow_fail:assert counts['failure']==counts['error']==0
    skips={(c.get('classname'),c.get('name')):c.find('skipped').get('message') for c in cases if c.find('skipped') is not None}
    return cases,ids,counts,skips

main,ids,counts,skips=junit(out/'checks/final-tests.xml.gz')
orca,orca_ids,orca_counts,_=junit(out/'checks/final-tests.xml.orca.xml.gz')
new,new_ids,new_counts,_=junit(out/'checks/final-new-regressions.xml.gz')
prior,prior_ids,prior_counts,prior_skips=junit(repo/'docs/evidence/bug-audit-20261021-pass12/checks/final-tests.xml.gz')
assert len(main)==11995 and counts['skipped']==28
assert len(orca)==1 and not any(orca_counts.values()) and not ids&orca_ids
assert len(new)==170 and not any(new_counts.values())
assert prior_ids<ids and ids-prior_ids==new_ids and skips==prior_skips
assert summary['canonical_unique_passed']==len(ids)-28+len(orca)==11968
baseline,_,baseline_counts,_=junit(out/'proofs/root/exact-python-baseline.xml.gz',True)
assert len(baseline)==170 and baseline_counts=={'failure':100,'error':0,'skipped':0}
receipt=load(out/'review/root/exact-baseline-receipt.json')
assert all(source[n]==h for n,h in receipt['final_tests'].items())

def events(path):
    with gzip.open(path,'rt') as stream: rows=[json.loads(line) for line in stream if line.startswith('{')]
    return {kind:{(r.get('Package'),r['Test']) for r in rows if r.get('Action')==kind and r.get('Test')} for kind in ('pass','skip','fail')}

go=events(out/'checks/final-go-race.log.gz')
old=events(repo/'docs/evidence/bug-audit-20261021-pass12/checks/final-go-race.log.gz')
new_go=events(out/'checks/final-go-new.log.gz')
assert len(go['pass'])==467 and len(go['skip'])==2 and not go['fail']
assert old['pass']<go['pass'] and go['pass']-old['pass']==new_go['pass'] and len(new_go['pass'])==8
assert go['skip']==old['skip'] and not new_go['skip']
red=events(out/'proofs/root/exact-go-baseline.log.gz')
assert sum('/' in name for _,name in red['fail'])==5
assert len(red['pass'])==2 and not red['skip']
for p in (out/'checks/status').glob('*.json'):assert load(p)['exit_code']==0,p
assert summary['verified_root_causes']==6 and summary['remote_write_or_release_performed'] is False
assert summary['all_existing_test_files_byte_identical'] is True
print(json.dumps({'retained_artifacts':len(manifest),'source_files':len(source),
 'canonical_unique_passed':11968,'unchanged_skips':28,'go_named_passes':467,'go_native_skips':2}))
