import os, itertools, json, tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe.discover import discover
from beamo_wipe.models import Disk, DiskKind, MethodId, WipeRequest
from beamo_wipe.safety import SafetyError, confirm_spec, token_matches
from beamo_wipe.nwipe_runner import build_nwipe_argv, validate_argv
import beamo_wipe.safety as safety
counts={'mounted_target':0,'boot_resolution':0,'token_pairs':0,'argv_refusals':0}
def disk(n, **extra):
 d=dict(name=n,path='/dev/'+n,type='disk',size=500_000_000_000,model='FAKE',serial='FAKE-'+n,tran='sata',rota=True,ro=False,mountpoints=[None]);d.update(extra);return d
boot=disk('sr0',type='rom',tran='usb',size=1_000_000_000)
for mounted, ro, tran, duplicate in itertools.product([None,'/','/data','/run/live/medium'],[False,True],['sata','usb','iscsi','fc'],[False,True]):
 target=disk('sda',mountpoints=[mounted],ro=ro,tran=tran)
 rows=[boot,target]+([dict(target)] if duplicate else [])
 result=discover(lsblk_payload={'blockdevices':rows},mount_sources=['/dev/sr0'],env={'BEAMO_WIPE_DRY_RUN':'1'})
 if mounted or ro or tran in ('iscsi','fc'): assert not result.selectable,(mounted,ro,tran,duplicate)
 assert not any(d.path=='/dev/sr0' for d in result.selectable)
 counts['mounted_target']+=1
for sources in [[],['/dev/sr0'],['/dev/sr0','/dev/sda'],['/dev/unknown'],['UUID=missing'],['overlay'],['/dev/loop0']]:
 result=discover(lsblk_payload={'blockdevices':[boot,disk('sda')]},mount_sources=sources,env={})
 if sources!=['/dev/sr0']:assert not result.selectable,sources
 else:assert [d.path for d in result.selectable]==['/dev/sda']
 counts['boot_resolution']+=1
values=['','0000','UNKNOWN','sda','sdb','ABCD','XABCD','500','1000','AAA1234','BBB1234']
for a,b,other_size in itertools.product(values,values,['500','1000']):
 ds=[Disk('/dev/sda','sda','FAKE',a,500_000_000_000,'500',DiskKind.HDD,'SATA',''),Disk('/dev/sdb','sdb','FAKE',b,int(other_size)*10**9,other_size,DiskKind.HDD,'SATA','')]
 specs=[]
 for d in ds:
  try:specs.append(confirm_spec(d,ds))
  except SafetyError:specs.append(None)
 if all(specs):assert not token_matches(specs[0].token,specs[1]),(a,b,other_size,specs)
 counts['token_pairs']+=1
with tempfile.TemporaryDirectory(prefix='beamo-pass6-argv-') as tmp, patch.object(safety,'DEFAULT_LOG_DIR',Path(tmp)):
 for method in MethodId:
  req=WipeRequest('/dev/sda',method,'/dev/sr0',tmp+'/log')
  argv=build_nwipe_argv(req); validate_argv(argv,req)
  mutants=[argv+['/dev/sdb'],argv[:-1],argv[:-1]+['--force',argv[-1]],argv[:-1]+['--exclude=/dev/sdb',argv[-1]],argv[:-1]+['--method=zero',argv[-1]],argv[:-1]+['--autonuke',argv[-1]]]
  mutants += [argv[:i]+argv[i+1:] for i in range(1,len(argv)-1)]
  for candidate in mutants:
   try:validate_argv(candidate,req)
   except SafetyError:counts['argv_refusals']+=1
   else:raise AssertionError(candidate)
print(json.dumps({'cases':counts,'total':sum(counts.values()),'failures':0},indent=2))
