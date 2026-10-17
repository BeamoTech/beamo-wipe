"""Freeze complete inputs and the exact incremental pass20 diff."""
import difflib,gzip,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass20-primary')
sys.path.insert(0,str(root/'src'))
from beamo_wipe.build_identity import runtime_source_sha256
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
prefixes=('src/','tests/','developer_tests/','scripts/','packaging/','desktop/','helper/','.github/')
selected=sorted({n for n in names if n.startswith(prefixes) or n in {'dev.py','preview','pyproject.toml'}})
freeze={n:hashlib.sha256((root/n).read_bytes()).hexdigest()for n in selected}
start=json.loads((out/'starting-freeze.json').read_text());changed=[n for n in start if start[n]!=freeze.get(n)];added=sorted(set(freeze)-set(start))
assert sorted(changed)==['src/beamo_wipe/audio_jobs.py','src/beamo_wipe/discover.py','src/beamo_wipe/ui/tk_wizard.py'],changed
assert len(added)==8 and all(n.startswith('tests/') and n.endswith('_pass20.py') for n in added),added
assert len(freeze)==779
parts=[]
with tarfile.open(out/'starting-inputs.tar.gz','r:gz')as archive:
 for name in sorted(changed):
  before=archive.extractfile(name).read().decode();after=(root/name).read_text()
  parts.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='starting/'+name,tofile='final/'+name))
(out/'pass20-source.diff').write_text(''.join(parts))
for group,args in [('source',['src']),('tracked-tests',['tests'])]:
 (out/(group+'.diff.gz')).write_bytes(gzip.compress(subprocess.check_output(['git','diff','--',*args]),mtime=0))
new_tests=sorted(n for n in selected if n.startswith('tests/') and subprocess.run(['git','ls-files','--error-unmatch',n],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode)
for label,inputs in [('new-tests',new_tests),('final-source-inputs',selected)]:
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w')as archive:
  for name in inputs:
   data=(root/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;archive.addfile(info,io.BytesIO(data))
 (out/(label+'.tar.gz')).write_bytes(gzip.compress(buffer.getvalue(),mtime=0))
(out/'new-tests-sha256.json').write_text(json.dumps({n:freeze[n]for n in new_tests},indent=2)+'\n')
(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
row=dict(head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),branch=subprocess.check_output(['git','branch','--show-current']).decode().strip(),frozen_inputs=len(freeze),runtime_source_sha256=runtime_source_sha256(),changed=changed,added=added,unchanged_start_inputs=len(start)-len(changed),new_untracked_test_modules=len(new_tests),index_empty=not subprocess.check_output(['git','diff','--cached','--name-only']))
assert row['index_empty'];(out/'source-review.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row,indent=2))
