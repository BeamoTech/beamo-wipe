"""Authenticate final runner fixtures, source peers and native GUI observations."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

root=Path.cwd(); out=Path('/tmp/pass16-primary'); runner=Path('/tmp/pass16-runner'); ui=Path('/tmp/pass16-ui')
freeze=json.loads((out/'source-freeze.json').read_text())
reviews={}
for group in ('discovery','ui','runner'):
    path=Path('/tmp/pass16-'+group)/'final-source-review.json'
    reviews[group]=json.loads(path.read_text())
    # Select the final map explicitly; historical review snapshots are kept
    # in these receipts but cannot be counted as final-source approval.
    matched={}
    key={'discovery':'final_sha256','ui':'hashes','runner':'reviewed_source_sha256'}[group]
    for name,digest in reviews[group][key].items():
        assert name in freeze and freeze[name]==digest,(group,name)
        matched[name]=digest
    assert matched,group
    reviews[group]={'exact_matched_final_files':sorted(matched)}

summary=json.loads((runner/'fresh-summary.json').read_text())
assert summary['short_cases']==summary['actual_large_cases']==153 and summary['successful_roundtrips']==90
assert summary['source_unchanged'] and summary['native_acquisitions']==summary['mismatches']==summary['semantic_errors']==0
assert not json.loads((runner/'fresh-mismatches.json').read_text())
assert not json.loads((runner/'fresh-semantic-errors.json').read_text())
actual=json.loads((runner/'fresh-actual.json').read_text())
assert len(actual)==153
files={}
for index,row in enumerate(actual,1):
    log=runner/'fixtures'/f'{index:04d}'/'fake.log'
    data=log.read_bytes()
    assert len(data)==row['bytes']>1024*1024
    assert hashlib.sha256(data).hexdigest()==row['sha256']
for path in sorted((runner/'fixtures').rglob('*')):
    if path.is_file(): files[str(path.relative_to(runner))]=path.read_bytes()
results=[name for name in files if name.endswith('.json')]
assert len(results)==90 and len(files)==333
for name in results:
    data=files[name]
    assert files[name+'.sha256'].decode().split()[0]==hashlib.sha256(data).hexdigest()
    evidence=json.loads(data)
    assert evidence['verification']['verified'] is (evidence['outcome']=='verified')
blob=io.BytesIO()
with tarfile.open(fileobj=blob,mode='w') as archive:
    for name,data in sorted(files.items()):
        info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0
        archive.addfile(info,io.BytesIO(data))
(out/'runner-final-fixtures.tar.gz').write_bytes(gzip.compress(blob.getvalue(),mtime=0))
(out/'runner-final-fixtures-sha256.json').write_text(json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in files.items()},indent=2)+'\n')
cancel=json.loads((runner/'cancel-summary.json').read_text())
assert cancel['cases']==144 and cancel['source_unchanged'] and cancel['native_acquisitions']==0
geometry=json.loads((ui/'geometry-matrix.json').read_text())
rows=geometry['rows']; assert len(rows)==270 and not geometry['forbidden_calls']
assert all(row['ok'] and not row['callback_errors'] for row in rows)
critical=[row for row in rows if row['surface']=='tk' and row['screen'] in {'KEYBOARD','OWNER','CONFIRM'}]
assert len(critical)==27 and all(row['focus_fully_visible'] for row in critical)
captures=[row['capture'] for row in rows if 'capture' in row]
assert len(captures)==5 and all((ui/name).is_file() for name in captures)
assert not any(term in (ui/'geometry-matrix.txt').read_text() for term in ('invalid command name','Traceback','bgerror','Exception in Tkinter'))
receipt={'peer_reviews':reviews,'runner_short':153,'runner_actual_large':153,
         'runner_fixture_files_hashed':len(files),'authenticated_evidence_sidecar_pairs':90,
         'runner_cancellation_cases':144,'geometry_cases':270,
         'critical_tk_fully_visible':27,'captures_for_primary_view':captures,
         'native_effects':0,'callback_errors':0}
(out/'campaign-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
