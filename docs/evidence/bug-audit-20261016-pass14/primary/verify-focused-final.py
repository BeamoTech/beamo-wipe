"""Authenticate final matrix receipts and exact native captures without effects."""
import hashlib,json,struct,xml.etree.ElementTree as ET
from pathlib import Path
out=Path('/tmp/pass14-primary')
freeze=json.loads((out/'source-freeze.json').read_text())
g=json.loads(Path('/tmp/pass14-ui/geometry-summary.json').read_text())
j=json.loads(Path('/tmp/pass14-ui/geometry-matrix.json').read_text())
assert g['cases']==g['passed']==len(j['rows'])==270 and not g['failed']
assert not j['forbidden_calls'] and not g['forbidden_calls']
assert all(r['ok'] and r['state_unchanged'] for r in j['rows'])
log = Path('/tmp/pass14-ui/geometry-matrix.txt').read_text()
assert 'bgerror' not in log and 'Traceback' not in log and 'Exception in Tkinter callback' not in log
assert all(not r['callback_errors'] for r in j['rows'])
for name,h in g['final_hashes'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h==j['hashes'][name]==freeze[name]
focus=[r for r in j['rows'] if r['surface']=='tk' and r['screen'] in ('KEYBOARD','OWNER','CONFIRM')]
assert len(focus)==27 and all(r['focus_fully_visible'] for r in focus)
captures={}
for size,screen in [('standard','OWNER'),('extra','KEYBOARD'),('large','CONFIRM')]:
    row=next(r for r in focus if r['language']=='en' and r['text_size']==size and r['screen']==screen)
    p=Path('/tmp/pass14-ui')/row['capture'];blob=p.read_bytes()
    assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(800,600)
    assert row['focus_visible'] and row['focus_fully_visible'] and not row['erase_enabled']
    captures[p.name]={'sha256':hashlib.sha256(blob).hexdigest(),'size_bytes':len(blob),'native_dimensions':[800,600],'geometry':row}
for name,total in [('adjacent',1645),('ui-adjacent-fixed',100)]:
    cases=ET.parse(out/(name+'.xml')).findall('.//testcase')
    assert len(cases)==total and all(not list(c) for c in cases)
d=json.loads(Path('/tmp/pass14-discovery/permutation-matrix.json').read_text())
assert d['cases']==len(d['observations'])==558 and not d['native_attempts']
for name,h in d['source_sha256'].items(): assert h==freeze[name]==hashlib.sha256(Path(name).read_bytes()).hexdigest()
old=out/'focused-independent-review.json'
if not (out/'initial-focused-independent-review.json').exists():
    (out/'initial-focused-independent-review.json').write_bytes(old.read_bytes())
r={'runtime_source_sha256':json.loads((out/'source-review.json').read_text())['runtime_source_sha256'],'geometry_rows':270,'targeted_focus_full_visibility':27,'no_bgerror_after_owned_fixture_cleanup':True,'native_application_effects':0,'captures_to_visually_review':captures,'adjacent_cases_passed_before_annotation_only_cleanup':1645,'affected_ui_sequence_passed_before_annotation_only_cleanup':100,'final_gate_validates_exact_final_bytes':True,'discovery_cases':558,'starting_inputs_preserved_except_five_authorized_paths':True,'independent_final_peer_approval':False}
old.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='captures_to_visually_review'},indent=2))
