import collections,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'src'))
from beamo_wipe.verification_evidence import parse_junit_xml
from beamo_wipe.build_identity import runtime_source_sha256
reports=[Path('/tmp/beamo-pass9-final.xml'),Path('/tmp/beamo-pass9-final.xml.orca.xml')]
summary={'baseline':'35107a8d1a701093eac876a58ab4efd50e291673','runtime_source_sha256':runtime_source_sha256(),'reports':{}}
ids=[]
for p in reports:
    counts=parse_junit_xml(p.read_text())
    summary['reports'][p.name]=counts
    assert counts['failed']==counts['errors']==0
    ids.extend((case.get('classname'),case.get('name')) for case in ET.parse(p).findall('.//testcase'))
summary['duplicate_ids']=[list(i) for i,n in collections.Counter(ids).items() if n>1]
summary['combined_passed']=sum(r['passed'] for r in summary['reports'].values())
summary['combined_skipped']=sum(r['skipped'] for r in summary['reports'].values())
summary['combined_xfailed']=sum(r['xfailed'] for r in summary['reports'].values())
assert not summary['duplicate_ids']
assert summary['combined_skipped']==14 and summary['combined_xfailed']==0
sound=[c for c in ET.parse(reports[0]).findall('.//testcase') if c.get('name')=='test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog']
assert len(sound)==1 and len(sound[0])==0
summary['sound_timing_case_full_gate']='passed'
frozen=json.loads(Path('/tmp/beamo-pass9-source-freeze.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in frozen.items())
summary['frozen_source_test_files_matched']=len(frozen)
Path('/tmp/beamo-pass9-final-summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='reports'},indent=2))
