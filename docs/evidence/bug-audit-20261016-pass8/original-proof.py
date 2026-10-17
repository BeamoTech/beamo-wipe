import hashlib,io,os,subprocess,tarfile,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path.cwd();scratch=Path(tempfile.mkdtemp(prefix='beamo-pass8-original-'))
raw=subprocess.check_output(['git','archive','35107a8','src'])
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    for member in archive.getmembers():
        if member.isfile():
            path=scratch/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read())
tests=['test_diagnostic_malformed_bounds_pass8.py','test_runner_projection_progress_order_pass8.py']
(scratch/'tests').mkdir()
for name in [*tests,'conftest.py']:(scratch/'tests'/name).write_bytes((root/'tests'/name).read_bytes())
env={**os.environ,'PYTHONPATH':str(scratch/'src')}
with open('/tmp/beamo-pass8-original.txt','wb') as log:
    result=subprocess.run(['/tmp/beamo-wipe-audit-python/bin/python3','-m','pytest','-c',str(root/'pyproject.toml'),'-o','pythonpath='+str(scratch/'src'),'--rootdir='+str(scratch),*[str(scratch/'tests'/name) for name in tests],'--junitxml=/tmp/beamo-pass8-original.xml'],env=env,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==1,result.returncode
cases=ET.parse('/tmp/beamo-pass8-original.xml').findall('.//testcase')
assert len(cases)==20 and sum(c.find('failure') is not None for c in cases)==8 and not any(c.find('error') is not None for c in cases)
for name in ['diagnostic_report.py','nwipe_runner.py']:
    assert (scratch/'src/beamo_wipe'/name).read_bytes()==subprocess.check_output(['git','show','35107a8:src/beamo_wipe/'+name])
print('Exact baseline35107a8:20cases /8intended failures /12passing controls; zero setup errors; original module bytes verified.')
