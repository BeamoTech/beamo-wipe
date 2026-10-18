"""Copy exact flat receipts plus owned nested fixtures into durable evidence."""
import gzip,hashlib,io,shutil,tarfile
from pathlib import Path
root=Path.cwd(); dest=root/'docs/evidence/bug-audit-20261017-pass16'
items={}
for group in ('primary','discovery','ui','runner'):
 source=Path('/tmp/pass16-'+group)
 for path in sorted(source.iterdir()):
  if path.is_file() and path.suffix not in {'.exe','.lock'}:
   data=path.read_bytes();name=group+'/'+path.name;items[name]=data
   target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
blob=io.BytesIO()
with tarfile.open(fileobj=blob,mode='w') as archive:
 for name,data in sorted(items.items()):
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0
  archive.addfile(info,io.BytesIO(data))
(dest/'original-transcripts.tar.gz').write_bytes(gzip.compress(blob.getvalue(),mtime=0))
(dest/'original-transcripts-sha256.txt').write_text(''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(items.items())))
print('retained',len(items),'exact flat artifacts')
