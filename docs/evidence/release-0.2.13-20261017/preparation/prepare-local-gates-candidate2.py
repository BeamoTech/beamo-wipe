import gzip,hashlib,io,json,os,subprocess,sys,tarfile
from pathlib import Path
root=Path.cwd();base=Path('/tmp/beamo-release-20261017');out=base/'local-gates-candidate2';out.mkdir()
guard=Path('/tmp/beamo-release-20261017-guard-candidate2');guard.mkdir()
for old in Path('/tmp/beamo-pass21-fallback-guard').iterdir():
 target=guard/old.name;target.write_text(old.read_text().replace('/tmp/pass21-primary',str(out)));target.chmod(0o755)
(out/'guard-manifest.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(guard.iterdir())},indent=2)+'\n')
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
selected=sorted({n for n in names if n and not n.startswith(('docs/evidence/','.ai/memory/'))})
assert all((root/n).is_file() and not (root/n).is_symlink() for n in selected)
freeze={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in selected}
(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
with tarfile.open(out/'source-inputs.tar.gz','x:gz') as archive:
 for n in selected:
  data=(root/n).read_bytes();info=tarfile.TarInfo(n);info.size=len(data);info.mtime=0;archive.addfile(info,io.BytesIO(data))
sys.path.insert(0,str(root/'src'))
from beamo_wipe.build_identity import runtime_source_sha256
(out/'source-identity.json').write_text(json.dumps({'version':'0.2.13','starting_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'frozen_inputs':len(freeze),'runtime_source_sha256':runtime_source_sha256(),'source_freeze_sha256':hashlib.sha256((out/'source-freeze.json').read_bytes()).hexdigest(),'excluded_mutable_metadata':['.ai/memory/','docs/evidence/'],'source_committed':False},indent=2)+'\n')
s=(Path('/tmp/pass21-primary/run-gates.py').read_text().replace('/tmp/pass21-primary',str(out)).replace('/tmp/beamo-pass21-fallback-guard',str(guard)))
(out/'run-gates.py').write_text(s)
print((out/'source-identity.json').read_text())
