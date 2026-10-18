import hashlib,itertools,json,os,pathlib,sys,tempfile
sys.path.insert(0,str(pathlib.Path.cwd()/'src'))
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import nwipe_runner as n
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId
head='******************************** Error Summary *********************************\n'
close='********************************************************************************\n'
status='********************************* Drive Status *********************************\n'
erased='sda | Erased | 120MB/s | 01:25:04 | MODEL\n'
def progress(value,rounds=1,passes=1,dev='sda'):
 return f'/dev/{dev}: {value}%, round 1 of {rounds}, pass 1 of {passes}, eta 00:01:00, [writing]\n'
count=0
with tempfile.TemporaryDirectory(prefix='beamo-pass8-projection-review-') as td:
 path=pathlib.Path(td)/'fake.log'
 for mode,counts,closed,tailmode,interposed in itertools.product(range(6),['0 | 0 | 0','1 | 0 | 0','0 | 1 | 0','0 | 0 | 1','bad'],[False,True],range(5),[False,True]):
  first=progress(25)
  latest=progress(100,passes=3 if mode==2 else 1)
  if mode==0:before=first
  elif mode==1:before=first+latest
  elif mode==2:before=first+latest
  elif mode==3:before=progress(25,passes=3)+progress(50,passes=3)+latest
  elif mode==4:before=first+progress(100,dev='sdb')
  else:before=first+progress('100.0001')
  table=head+'sda | '+counts+'\n'+(close if closed else '')
  if interposed:table=head+first+'sda | '+counts+'\n'+(close if closed else '')
  tails=['',status+erased,latest,head+'sda | 1 | 0 | 0\n',close+latest+status+erased]
  text=before+table+tails[tailmode]
  path.write_text(text)
  projected=n.NwipeRunner()._scan_completion_log(str(path),'/dev/sda',n._log_signature(path.stat()))
  assert projected is not None
  assert check_payloads(projected,'/dev/sda')==check_payloads(text,'/dev/sda'),(mode,counts,closed,tailmode,interposed,projected,text)
  for method in MethodId:
   assert n.completion_for_method(0,projected,'/dev/sda',method)==n.completion_for_method(0,text,'/dev/sda',method),(mode,counts,closed,tailmode,interposed,method)
  # Projection never duplicates a progress record already retained.
  assert projected.count(latest.strip())<=text.count(latest.strip())
  count+=1
 # New-counter sample retained exactly once; final same-counter at original context.
 text=progress(10)+progress(20)+head+'sda | 0 | 0 | 0\n'
 path.write_text(text);p=n.NwipeRunner()._scan_completion_log(str(path),'/dev/sda',n._log_signature(path.stat()))
 assert p.index(progress(20).strip())<p.index('Error Summary')
 assert p.count(progress(10).strip())==1
 # Exact byte-bound and overbound: keep configured small ceiling for pure fixture.
 oldcap=n.NWIPE_COMPLETION_EVIDENCE_BYTES
 try:
  for cap in [0,1,40,80,100,200]:
   n.NWIPE_COMPLETION_EVIDENCE_BYTES=cap
   path.write_text(head+'sda | 1 | 0 | 0\n')
   p=n.NwipeRunner()._scan_completion_log(str(path),'/dev/sda',n._log_signature(path.stat()))
   assert (p is None)==(len(path.read_bytes())>cap)
 finally:n.NWIPE_COMPLETION_EVIDENCE_BYTES=oldcap
 for malformed in [b'x',b'\xff',b'/dev/sda: 100%, round 1 of 1',b'x'*(n.NWIPE_COMPLETION_SCAN_LINE_BYTES+1)+b'\n']:
  path.write_bytes(malformed)
  assert n.NwipeRunner()._scan_completion_log(str(path),'/dev/sda',n._log_signature(path.stat())) is None
  count+=1
print(json.dumps({'ordering_table_progress_combinations':count-4,'malformed_refusals':4,'cap_boundaries':6,'source_sha256':hashlib.sha256(pathlib.Path('src/beamo_wipe/nwipe_runner.py').read_bytes()).hexdigest()},indent=2))
