"""Verify public0.2.13 downloads as regular files, never write physical media."""
import datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path

root=Path('/root/dev/Beamo Wipe');base=Path('/tmp/beamo-release-20261017')
python='/tmp/beamo-pass21-python/bin/python3';version='0.2.13';tag='v'+version
stem='beamo-wipe-'+version+'-amd64';source=sys.argv[1]
assert re.fullmatch('[0-9a-f]{40}',source)
expected={stem+'.iso',stem+'.iso.sha256',stem+'.img.gz',stem+'.img.gz.sha256',stem+'.img.sha256',stem+'.img.json',stem+'.manifest.json',stem+'.manifest.json.sha256',stem+'.manifest.json.sig','SHA256SUMS','keys.json','verification-evidence.tar.gz','BUILD-RECEIPT.json','release-downloads.json','release-downloads.json.sig','RELEASE_COMPLETE.txt'}
release=json.loads(subprocess.check_output(['gh','api','repos/BeamoTech/beamo-wipe/releases/tags/'+tag]))
assert release['tag_name']==tag and not release['draft'] and not release['prerelease'] and release['published_at']
assets={a['name']:a for a in release['assets']};assert set(assets)==expected and len(assets)==len(release['assets'])
assert all(re.fullmatch('sha256:[0-9a-f]{64}',a['digest']) for a in assets.values())
out=base/'public-verification';out.mkdir(mode=0o700)
(out/'public-release-before.json').write_text(json.dumps(release,indent=2)+'\n')

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()


def download(name):
 a=assets[name];url=a['browser_download_url']
 assert url.startswith('https://github.com/BeamoTech/beamo-wipe/releases/download/'+tag+'/')
 part=out/(name+'.part');final=out/name
 assert not final.exists() and not final.is_symlink()
 fd=os.open(part,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 print('Download '+name+' ('+str(a['size'])+' bytes)',flush=True)
 with os.fdopen(fd,'wb') as stream:
  result=subprocess.run(['curl','--fail','--location','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','1800','--silent','--show-error',url],stdout=stream,stderr=subprocess.PIPE)
 if result.returncode:raise RuntimeError('Download failed: '+name+': '+result.stderr.decode(errors='replace'))
 assert part.stat().st_size==a['size'] and 'sha256:'+digest(part)==a['digest'],name
 os.link(part,final);part.unlink()


def run(label,args,cwd=root):
 with (out/(label+'.txt')).open('xb') as log:
  result=subprocess.run(args,cwd=cwd,env=dict(os.environ,PYTHONPATH=str(root/'src'),BEAMO_WIPE_DRY_RUN='1'),stdout=log,stderr=subprocess.STDOUT)
 assert result.returncode==0,(label,result.returncode)
 print(label+' PASS',flush=True)

priority=['release-downloads.json','release-downloads.json.sig',stem+'.manifest.json',stem+'.manifest.json.sig',stem+'.img.json']
for name in priority:download(name)
verify=[python,str(root/'scripts/verify-usb-download.py'),'metadata','--directory',str(out),'--registry',str(root/'packaging/release-keys/keys.json'),'--trusted-key-sha256','93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7','--version',version,'--expected-source',source]
run('authenticate-metadata',verify)
for name in sorted(expected-set(priority)-{stem+'.iso',stem+'.img.gz'}):download(name)
assert (out/'keys.json').read_bytes()==(root/'packaging/release-keys/keys.json').read_bytes()
for name in (stem+'.iso',stem+'.img.gz'):download(name)
verify[2]='extract';run('extract-authenticated-usb',verify)
verify[2]='verify';run('verify-authenticated-usb',verify)
run('verify-iso-manifest',[python,'-c','from pathlib import Path; from beamo_wipe.release_manifest import verify_manifest; verify_manifest(Path('+repr(str(out/(stem+'.manifest.json')))+')); print("Manifest, seven gate receipts, package inventory and actual ISO PASS")'])
run('verify-checksum-list',['sha256sum','-c','SHA256SUMS'],out)
manifest=json.loads((out/(stem+'.manifest.json')).read_text());assert manifest['source']['commit']==source and not manifest['source']['dirty']
inventory=json.loads((out/'release-downloads.json').read_text())
for name,a in assets.items():
 p=out/name
 assert p.stat().st_size==a['size'] and 'sha256:'+digest(p)==a['digest']
 if name in inventory['files']:assert inventory['files'][name]=={'sha256':digest(p),'bytes':p.stat().st_size}
raw=out/(stem+'.img');assert raw.is_file() and not raw.is_symlink()
latest=json.loads(subprocess.check_output(['gh','api','repos/BeamoTech/beamo-wipe/releases/latest']))
assert latest['id']==release['id'] and latest['tag_name']==tag and not latest['draft']
assert {(a['id'],a['name'],a['size'],a['digest']) for a in latest['assets']}=={(a['id'],a['name'],a['size'],a['digest']) for a in assets.values()}
(out/'public-release-after.json').write_text(json.dumps(latest,indent=2)+'\n')
receipt={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tag':tag,'source_commit':source,'release_url':release['html_url'],'release_id':release['id'],'latest_confirmed':True,'public_assets':{n:{'bytes':a['size'],'sha256':a['digest'].removeprefix('sha256:')} for n,a in assets.items()},'raw_usb':{'bytes':raw.stat().st_size,'sha256':digest(raw)},'publisher_fingerprint':'93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7','signature_floor':version,'all_downloads_actual_bytes_verified':True,'iso_manifest_and_required_evidence_verified':True,'physical_media_written':False,'physical_hardware_acceptance':'NOT TESTED'}
(out/'public-verification-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
