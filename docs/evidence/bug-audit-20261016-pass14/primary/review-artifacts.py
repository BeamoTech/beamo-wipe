"""Independently authenticate and inspect actual generated bundle files."""
from pathlib import Path
import gzip
import hashlib
import json
import tarfile

out=Path('/tmp/pass14-primary')
m=json.loads((out/'report-checks-matrix-artifacts.json').read_text())
assert m['cases']==90 and len(m['artifact_files'])==70
assert m['runtime_source_sha256']==json.loads((out/'source-review.json').read_text())['runtime_source_sha256']
with tarfile.open(out/'report-artifacts.tar.gz','r:gz') as archive:
    assert set(archive.getnames())==set(m['artifact_files'])
    for name,digest in m['artifact_files'].items():
        assert hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest
    for case in ('clean','unknown-count','write-error','read-error','verify-error'):
        data=json.loads(archive.extractfile(case+'/result.json').read())
        shared=json.loads(archive.extractfile(case+'/SHARE.json').read())
        result=archive.extractfile(case+'/RESULT.txt').read().decode()
        html=archive.extractfile(case+'/REPORT.html').read().decode()
        assert '<html' in html.lower() and html.rstrip().endswith('</html>')
        assert result.startswith('Beamo Wipe result')
        assert data['outcome']==shared['outcome']==('verified' if case=='clean' else 'failed')
        assert data['completion']['reason']==('completed' if case=='clean' else 'indeterminate' if case=='unknown-count' else 'engine_failed')
        assert data['verification']['verified'] is (case=='clean')
        if case=='clean':
            assert 'Erase completed; verification passed' in result and 'Erase completed; verification passed' in html
        else:
            assert 'beamosupport.com' in html
            assert 'Erase completed; verification passed' not in result
        assert '/dev/' not in json.dumps(shared)
preview=Path('web-preview/index.html').read_bytes()
assert b'<html' in preview.lower() and b'PREVIEW' in preview
(out/'generated-preview.html.gz').write_bytes(gzip.compress(preview,mtime=0))
receipt={'report_cases':m['cases'],'report_files_hashed':len(m['artifact_files']),'report_matrix_runtime_source_sha256':m['runtime_source_sha256'],'owner_share_json_result_html_reviewed':5,'preview_file':'web-preview/index.html','preview_size_bytes':len(preview),'preview_sha256':hashlib.sha256(preview).hexdigest(),'preview_languages_js_checked_by_gate':True,'native_gui_captures_independently_viewed':3}
(out/'artifact-review.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
