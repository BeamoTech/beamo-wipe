"""Bounded fake-only inventory ownership and boot source matrix."""
from __future__ import annotations
import builtins, copy, hashlib, itertools, json, os, pathlib, subprocess, sys
os.environ['BEAMO_WIPE_DRY_RUN']='1'
sys.path.insert(0,str(pathlib.Path.cwd()/'src'))
from beamo_wipe.discover import discover
from beamo_wipe.safety import assert_disk_identity, SafetyError

native_attempts=[]
def forbidden(*args,**kwargs):
 native_attempts.append(repr(args[:1]));raise AssertionError('native subprocess forbidden')
subprocess.run=forbidden
subprocess.Popen=forbidden
orig_open=builtins.open
def guarded_open(path,*args,**kwargs):
 name=str(path)
 if name.startswith(('/proc/','/sys/')):
  native_attempts.append(name);raise AssertionError('native machine read forbidden')
 return orig_open(path,*args,**kwargs)
builtins.open=guarded_open
cases=[]
def check(label,payload,sources,want):
 result=discover(lsblk_payload=payload,mount_sources=sources,cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})
 got=sorted(d.path for d in result.selectable)
 assert got==want,(label,got,want,result.error,result.diagnostic)
 if result.boot:
  assert all(d.path!=result.boot.path and not d.is_boot for d in result.selectable)
 cases.append({'case':label,'targets':got,'identified':result.boot_identified,'error':bool(result.error)})
 return result

def disk(name,tran,serial):
 return {'name':name,'path':'/dev/'+name,'type':'disk','size':500000000000,'tran':tran,'serial':serial,'wwn':'WWN-'+serial,'model':'Fake '+name,'ro':False,'mountpoints':[]}

for boot_kind,(target_name,target_tran),shape,mount_kind,parent_kind,fs in itertools.product(
 ('usb','rom'),(('sda','sata'),('nvme0n1','nvme'),('vda','virtio')),('tree','flat'),('none','list','scalar','single','malformed'),('correct','missing','wrong'),('ext4','ntfs','crypto_LUKS')):
 boot=disk('sdb' if boot_kind=='usb' else 'sr0',boot_kind,'BOOT')
 if boot_kind=='rom':boot['type']='rom'
 target=disk(target_name,target_tran,'TARGET')
 part_name=target_name+('p1' if target_name[-1].isdigit() else '1')
 part={'name':part_name,'path':'/dev/'+part_name,'type':'part','size':200000000000,'fstype':fs,'uuid':'UUID-TARGET','mountpoints':[]}
 if parent_kind=='correct':part['pkname']=target_name
 elif parent_kind=='wrong':part['pkname']=boot['name']
 if mount_kind=='list':part['mountpoints']=['/media/fake']
 elif mount_kind=='scalar':part['mountpoints']='/media/fake'
 elif mount_kind=='single':part['mountpoint']='/media/fake'
 elif mount_kind=='malformed':part['mountpoints']=[{'bad':'entry'}]
 payload={'blockdevices':[boot,target]}
 if shape=='tree':target['children']=[part]
 else:payload['blockdevices'].append(part)
 refused=(parent_kind=='wrong' or (shape=='flat' and parent_kind=='missing') or mount_kind=='malformed')
 want=[] if refused or mount_kind!='none' else [target['path']]
 label=f'ownership/{boot_kind}/{target_name}/{shape}/{mount_kind}/{parent_kind}/{fs}'
 result=check(label,payload,[boot['path']],want)
 if not refused and mount_kind=='none':
  assert result.selectable[0].layout_id,label

for source in ('/dev/sdb','/dev/sdb1','UUID=BOOT-UUID','LABEL=BEAMO_WIPE','PARTUUID=BOOT-PART','PARTLABEL=boot partition'):
 for addition in (None,'/dev/sda','UUID=TARGET-UUID','UUID=MISSING','overlay','/dev/loop99'):
  boot=disk('sdb','usb','BOOT')
  boot['children']=[{'name':'sdb1','path':'/dev/sdb1','type':'part','size':1000000000,'uuid':'BOOT-UUID','label':'BEAMO_WIPE','partuuid':'BOOT-PART','partlabel':'boot partition','mountpoints':[]}]
  target=disk('sda','sata','TARGET');target['uuid']='TARGET-UUID'
  check(f'boot/{source}/{addition}',{'blockdevices':[boot,target]},[source]+([addition] if addition else []),[] if addition else ['/dev/sda'])

for alias in ('shared-serial','shared-wwn','distinct-wwn','zero-serial'):
 for mounted in (False,True):
  boot=disk('sdb','usb','BOOT');a=disk('sda','sata','A');b=disk('sdc','sata','B')
  if alias=='shared-serial':a['serial']=b['serial']='SAME';a['wwn']=b['wwn']=''
  elif alias=='shared-wwn':a['wwn']=b['wwn']='SAME-WWN'
  elif alias=='distinct-wwn':a['serial']=b['serial']='SAME'
  else:a['serial']=b['serial']='0000';a['wwn']=b['wwn']=''
  if mounted:b['mountpoints']=['/media/fake']
  want=['/dev/sda','/dev/sdc'] if not mounted else (['/dev/sda'] if alias in ('distinct-wwn','zero-serial') else [])
  check(f'aliases/{alias}/{mounted}',{'blockdevices':[boot,a,b]},['/dev/sdb'],want)

for duplicate in ('identical','size','ro','mount'):
 boot=disk('sdb','usb','BOOT');target=disk('sda','sata','TARGET');second=copy.deepcopy(target)
 if duplicate=='size':second['size']+=1
 elif duplicate=='ro':second['ro']=True
 elif duplicate=='mount':second['mountpoints']=['/media/fake']
 result=check('duplicate/'+duplicate,{'blockdevices':[boot,target,second]},['/dev/sdb'],['/dev/sda','/dev/sda'] if duplicate=='identical' else [])
 if duplicate=='identical':
  try:assert_disk_identity(result.selectable[0],result)
  except SafetyError:pass
  else:raise AssertionError('duplicate target identity accepted')

assert not native_attempts,native_attempts
out={'cases':len(cases),'targets_present':sum(bool(x['targets']) for x in cases),'safe_refusals':sum(not x['targets'] for x in cases),'native_attempts':native_attempts,'cases_sha256':hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest(),'observations':cases}
pathlib.Path('/tmp/pass11-discovery/matrix.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='observations'},indent=2))
