"""Preserve both candidate runs once; exclude future downloaded customer media."""
import hashlib,io,json,tarfile
from pathlib import Path
root=Path.cwd();base=Path('/tmp/beamo-release-20261017');dest=root/'docs/evidence/release-0.2.13-20261017';sha=lambda b:hashlib.sha256(b).hexdigest()
assert len(json.loads((base/'local-gates-candidate2/local-gate-status.json').read_text()))==9
assert all(r['exit_code']==0 for r in json.loads((base/'local-gates-candidate2/local-gate-status.json').read_text()))
assert (base/'local-gates-candidate2/gate-verification.json').is_file()

def copy(source,target):
 data=source.read_bytes();assert not target.is_symlink()
 if target.exists():assert target.read_bytes()==data,target;return
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(data)

canonical_archive=root/'docs/evidence/bug-audit-20261017-pass21/primary/raw-evidence.tar.gz'
canonical_hashes=json.loads((canonical_archive.parent/'raw-evidence-sha256.json').read_text())
canonical_sha=canonical_hashes['desktop-windows.test.exe']
with tarfile.open(canonical_archive,'r:gz') as archive:assert sha(archive.extractfile('desktop-windows.test.exe').read())==canonical_sha
for label,directory in [('candidate1','local-gates'),('candidate2','local-gates-candidate2')]:
 source=base/directory;target=dest/label;target.mkdir(exist_ok=True)
 duplicates={}
 for p in sorted(source.iterdir()):
  if not p.is_file():continue
  assert not p.is_symlink()
  if p.suffix=='.exe' and sha(p.read_bytes())==canonical_sha:
   duplicates[p.name]={'sha256':canonical_sha,'bytes':p.stat().st_size,'canonical_archive':'../bug-audit-20261017-pass21/primary/raw-evidence.tar.gz','member':'desktop-windows.test.exe','meaning':'Byte-identical artifact only; current compile execution/freshness is proved by this candidate phase receipt.'}
   continue
  if p.suffix=='.exe':
   with tarfile.open(target/'unique-compiled-artifacts.tar.gz','x:gz') as archive:
    data=p.read_bytes();info=tarfile.TarInfo(p.name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
   continue
  copy(p,target/p.name)
 for name in ('guard-manifest.json',):
  guards=json.loads((source/name).read_text())
  for filename,h in guards.items():
   p=Path(filename);assert sha(p.read_bytes())==h;copy(p,target/'guards'/p.name)
 with (target/'duplicate-compiled-artifact-map.json').open('x') as f:f.write(json.dumps(duplicates,indent=2)+'\n')
for p in sorted(base.iterdir()):
 if p.is_file():
  assert p.suffix not in {'.iso','.img','.raw','.squashfs'}
  copy(p,dest/'preparation'/p.name)
files=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
assert all(not p.is_symlink() for p in files)
manifest=''.join(sha(p.read_bytes())+'  '+str(p.relative_to(dest))+'\n' for p in files)
with (dest/'SHA256SUMS').open('x') as f:f.write(manifest)
assert all(sha((dest/n).read_bytes())==h for h,n in (line.split('  ',1) for line in manifest.splitlines()))
print(json.dumps({'retained_files':len(files),'retained_bytes':sum(p.stat().st_size for p in files),'manifest_sha256':sha(manifest.encode()),'customer_media_in_git':False,'all_retained_hashes_reread':True},indent=2))
