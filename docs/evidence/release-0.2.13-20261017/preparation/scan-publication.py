import bz2,gzip,hashlib,io,json,re,subprocess,tarfile,zipfile
from pathlib import Path
out=Path('/tmp/beamo-release-20261017');inventory=json.loads((out/'starting-worktree-inventory.json').read_text())
patterns={'github_token':re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})\b'),'private_key_block':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/=\r\n]{80,}'),'aws_access_key':re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),'google_service_account_private_key':re.compile(rb'"private_key"\s*:\s*"-----BEGIN PRIVATE KEY-----')}
hits=[];media=[];archives=0;members=0;bytes_scanned=0;formats={};large_streamed=0
def scan(label,data,depth=0):
 global archives,members,bytes_scanned,large_streamed
 bytes_scanned+=len(data)
 for kind,pattern in patterns.items():
  matches=list(pattern.finditer(data))
  if matches:hits.append({'path':label,'kind':kind,'matches':len(matches),'match_hashes':[hashlib.sha256(m.group()).hexdigest() for m in matches]})
 if depth>3:raise RuntimeError('nested archive limit')
 if label.endswith(('.tar.gz','.tgz')):
  archives+=1
  with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
   seen=set()
   for item in archive:
    assert item.name not in seen,(label,item.name);seen.add(item.name)
    assert not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
    if not item.isfile():continue
    members+=1
    if Path(item.name).suffix.lower() in {'.iso','.img','.raw','.squashfs'}:media.append({'archive':label,'member':item.name,'bytes':item.size})
    if item.size>=64*1024*1024:
     assert not item.name.endswith(('.gz','.zip','.tgz')),('large nested archive',label,item.name)
     large_streamed+=1;tail=b'';offset=0
     with archive.extractfile(item) as stream:
      while chunk:=stream.read(1024*1024):
       combined=tail+chunk
       scan(label+'::'+item.name+'::chunk'+str(offset),combined,depth+1)
       tail=combined[-8192:];offset+=len(chunk)
     assert offset==item.size
    else:
     scan(label+'::'+item.name,archive.extractfile(item).read(),depth+1)
 elif label.endswith('.gz'):
  scan(label+'::decompressed',gzip.decompress(data),depth+1)
for name,receipt in inventory.items():
 data=Path(name).read_bytes()
 assert hashlib.sha256(data).hexdigest()==receipt['sha256'] or name=='.ai/memory/unfinished-work.md'
 scan(name,data)
result={'files':len(inventory),'archive_files':archives,'large_members_streamed':large_streamed,'archive_regular_members':members,'bytes_scanned':bytes_scanned,'potential_secret_patterns':hits,'archive_media_members':media,'note':'Pattern inventory only. Values are never printed; controlled test fixtures require source review before classification.'}
(out/'publication-content-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files':len(inventory),'archives':archives,'large_members_streamed':large_streamed,'members':members,'bytes_scanned':bytes_scanned,'potential_secret_match_locations':len(hits),'archive_media_members':media,'hits':hits},indent=2))
