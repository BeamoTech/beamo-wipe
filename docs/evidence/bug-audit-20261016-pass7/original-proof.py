import hashlib,io,json,os,subprocess,tarfile,tempfile
from pathlib import Path
root=Path.cwd(); scratch=Path(tempfile.mkdtemp(prefix='beamo-pass7-original-'))
raw=subprocess.check_output(['git','archive','f102dfb','src'])
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    for member in archive.getmembers():
        if member.isfile():
            path=scratch/member.name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(archive.extractfile(member).read())
tests=['test_export_hardware_padding_regression.py','test_gate_receipt_skip_kind_counts_pass7.py']
(scratch/'tests').mkdir()
for name in [*tests,'conftest.py']:
    (scratch/'tests'/name).write_bytes((root/'tests'/name).read_bytes())
env={**os.environ,'PYTHONPATH':str(scratch/'src')+':'+str(root/'tests')}
result=subprocess.run(['/tmp/beamo-wipe-audit-python/bin/python3','-m','pytest','-q','-c',str(root/'pyproject.toml'),'-o','pythonpath='+str(scratch/'src'),'--rootdir='+str(scratch),*[str(scratch/'tests'/name) for name in tests],'--junitxml=/tmp/beamo-pass7-original.xml'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
Path('/tmp/beamo-pass7-original.txt').write_bytes(result.stdout)
assert result.returncode==1,result.returncode
import xml.etree.ElementTree as ET
cases=ET.parse('/tmp/beamo-pass7-original.xml').findall('.//testcase')
failed=[c for c in cases if c.find('failure') is not None];errors=[c for c in cases if c.find('error') is not None]
assert len(cases)==75 and len(failed)==36 and not errors,(len(cases),len(failed),len(errors))
print('Exact f102dfb source:75 cases /36 intended assertion failures /39 passing controls; zero errors.')
for p in ['support_export.py','verification_evidence.py']:
    assert (scratch/'src/beamo_wipe'/p).read_bytes()==subprocess.check_output(['git','show','f102dfb:src/beamo_wipe/'+p])
print('Original module bytes verified against baseline commit; working tree untouched.')
