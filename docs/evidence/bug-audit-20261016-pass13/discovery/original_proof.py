"""Run final classifier regressions against the exact starting source privately."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

repo=Path.cwd()
evidence=Path('/tmp/pass13-discovery')
with tempfile.TemporaryDirectory(prefix='pass13-discovery-original-') as temp:
    private=Path(temp)
    with tarfile.open('/tmp/pass13-primary/starting-source.tar.gz','r:gz') as archive:
        archive.extractall(private, filter='data')
    (private/'tests').mkdir()
    for name in ('conftest.py','test_contents_efi_token_pass13.py'):
        shutil.copy2(repo/'tests'/name, private/'tests'/name)
    (private/'pytest.ini').write_text('[pytest]\npythonpath=src\naddopts=-q\n')
    original=evidence/'discover-original.py'
    assert (private/'src/beamo_wipe/discover.py').read_bytes()==original.read_bytes()
    env=dict(os.environ,BEAMO_WIPE_DRY_RUN='1')
    env.pop('PYTHONPATH',None)
    with (evidence/'original-proof.log').open('w') as output:
        proc=subprocess.run([sys.executable,'-m','pytest','tests/test_contents_efi_token_pass13.py',
                             '--junitxml='+str(evidence/'original-proof.xml')],
                            cwd=private,env=env,stdout=output,stderr=subprocess.STDOUT)
    cases=list(ET.parse(evidence/'original-proof.xml').getroot().iter('testcase'))
    counts=dict(total=len(cases),failures=sum(c.find('failure') is not None for c in cases),
                errors=sum(c.find('error') is not None for c in cases),
                skipped=sum(c.find('skipped') is not None for c in cases),
                exit_code=proc.returncode)
    counts['passes']=counts['total']-counts['failures']-counts['errors']-counts['skipped']
    counts['original_discover_sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
    counts['test_sha256']=hashlib.sha256((repo/'tests/test_contents_efi_token_pass13.py').read_bytes()).hexdigest()
    (evidence/'original-proof.json').write_text(json.dumps(counts,indent=2)+'\n')
    print(json.dumps(counts,indent=2))
    assert counts['total']==104 and counts['failures']==32 and counts['passes']==72
    assert counts['errors']==counts['skipped']==0 and proc.returncode==1
