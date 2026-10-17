import difflib,gzip,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass19-primary')
sys.path.insert(0,str(root/'src'))
from beamo_wipe.build_identity import runtime_source_sha256
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
prefixes=('src/','tests/','developer_tests/','scripts/','packaging/','desktop/','helper/','.github/')
selected=sorted({n for n in names if n.startswith(prefixes) or n in {'dev.py','preview','pyproject.toml'}})
freeze={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in selected}
start=json.loads((out/'starting-freeze.json').read_text())
changed=[n for n in start if start[n]!=freeze.get(n)]
added=sorted(set(freeze)-set(start))
assert sorted(changed)==['src/beamo_wipe/discover.py','src/beamo_wipe/ui/tk_wizard.py','tests/test_accessible_runtime.py','tests/test_checkrow_trace_lifetime_pass18.py'],changed
assert len(added)==5 and all(n.startswith('tests/') and n.endswith('_pass19.py') for n in added),added
parts=[]
with tarfile.open(out/'starting-inputs.tar.gz','r:gz') as archive:
    for name in sorted(changed):
        old=archive.extractfile(name).read().decode();new=(root/name).read_text()
        parts.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='starting/'+name,tofile='final/'+name))
(out/'pass19-source.diff').write_text(''.join(parts))
for group,args in [('source',['src']),('tracked-tests',['tests'])]:
    (out/(group+'.diff.gz')).write_bytes(gzip.compress(subprocess.check_output(['git','diff','--',*args]),mtime=0))
new_tests=sorted(n for n in selected if n.startswith('tests/') and subprocess.run(['git','ls-files','--error-unmatch',n],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode)
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as archive:
    for name in new_tests:
        data=(root/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;archive.addfile(info,io.BytesIO(data))
(out/'new-tests.tar.gz').write_bytes(gzip.compress(buf.getvalue(),mtime=0))
(out/'new-tests-sha256.json').write_text(json.dumps({n:freeze[n] for n in new_tests},indent=2)+'\n')
(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
receipt=dict(head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),branch=subprocess.check_output(['git','branch','--show-current']).decode().strip(),frozen_inputs=len(freeze),runtime_source_sha256=runtime_source_sha256(),changed=changed,added=added,new_untracked_test_modules=len(new_tests),index_empty=not subprocess.check_output(['git','diff','--cached','--name-only']))
assert receipt['index_empty'];(out/'source-review.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
