import builtins, copy, hashlib, io, itertools, json, os, pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path.cwd()/'src'))
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import discover as d, safety as s
from beamo_wipe.models import MethodId, WipeRequest
COUNTS={}
def count(k): COUNTS[k]=COUNTS.get(k,0)+1
def node(name, **kw):
    out=dict(name=name,path='/dev/'+name,type='disk',size=256000000000,model='Model '+name,serial='serial-'+name,wwn='wwn-'+name,tran='sata',ro=False,mountpoints=[None],rota=False)
    out.update(kw);return out
BOOT=node('sdz',size=16000000000,tran='usb',children=[dict(name='sdz1',path='/dev/sdz1',type='part',pkname='sdz',size=15900000000,label='BEAMO_WIPE',mountpoints=['/run/live/medium'])])
TARGET=node('sda')
BASE={'blockdevices':[BOOT,TARGET]}
def scan(payload,**kw):
    result=d.discover(lsblk_payload=payload,boot_path='/dev/sdz',mount_sources=['/dev/sdz1'],cmdline='boot=live',env={'BEAMO_WIPE_DRY_RUN':'1'},**kw)
    assert not any(x.path=='/dev/sdz' or x.is_boot for x in result.selectable)
    if not result.boot_identified: assert not result.selectable
    for disk in result.selectable: assert s.normalize_whole_disk(disk.path)==disk.path
    return result
real_open=builtins.open
real_run=subprocess.run
def guarded_open(path,*args,**kw):
    if str(path) in {'/proc/cmdline','/proc/self/mountinfo'}: raise AssertionError('Unexpected native probe '+str(path))
    return real_open(path,*args,**kw)
def guarded_run(argv,*args,**kw):
    if isinstance(argv,(tuple,list)) and any(pathlib.Path(str(x)).name in {'lsblk','findmnt','nwipe'} for x in argv[:1]): raise AssertionError('Unexpected native subprocess')
    return real_run(argv,*args,**kw)
with patch('builtins.open',guarded_open),patch('subprocess.run',guarded_run),patch.object(d,'read_mount_sources',side_effect=AssertionError('native mounts')),patch.object(d,'read_cmdline',side_effect=AssertionError('native cmdline')):
    assert {x.path for x in scan(BASE).selectable}=={'/dev/sda'}
    vals=[None,'',False,True,0,1,-1,[],{},['x'],{'x':1},'\n','\x00','\u2028','x'*129,'x'*1000]
    for field in ['name','path','type','size','model','serial','wwn','tran','ro','mountpoint','mountpoints','children','pkname','uuid','label','parttype']:
        for v in vals:
            p=copy.deepcopy(BASE);p['blockdevices'][1][field]=v
            scan(p);count('malformed_single_field')
    for mp in ['/','/home/a','/mnt/data','[SWAP]','\t','\x00','x'*300]:
        for form in ['scalar','plural','child','flat']:
            p=copy.deepcopy(BASE)
            if form=='scalar':p['blockdevices'][1]['mountpoint']=mp
            if form=='plural':p['blockdevices'][1]['mountpoints']=[mp]
            if form=='child':p['blockdevices'][1]['children']=[dict(name='sda1',path='/dev/sda1',type='part',pkname='sda',mountpoints=[mp])]
            if form=='flat':p['blockdevices'].append(dict(name='sda1',path='/dev/sda1',type='part',pkname='sda',mountpoints=[mp]))
            assert not scan(p).selectable;count('mounted_refused')
    for tran in ['iscsi','fc','fcoe','nbd','nvmeof','nvme-of','nvmf','tcp','rdma','',None,'unknown']:
        for pad in ['', ' ', '\t']:
            p=copy.deepcopy(BASE);p['blockdevices'][1]['tran']=pad+(tran or '')+pad
            assert not scan(p).selectable;count('remote_unknown_transport')
    for field,value in [('ro',True),('ro',1),('ro','true'),('mountpoints',['/mnt/data']),('serial',BOOT['serial']),('wwn',BOOT['wwn'])]:
        p=copy.deepcopy(BASE);duplicate=copy.deepcopy(TARGET);duplicate[field]=value;p['blockdevices'].append(duplicate)
        result=scan(p)
        try:s.assert_disk_identity(next(x for x in result.disks if x.path=='/dev/sda'),result)
        except (s.SafetyError,StopIteration):pass
        else:raise AssertionError(('accepted duplicate',field,value))
        count('conflicting_duplicate_refused')
    p=copy.deepcopy(BASE);p['blockdevices'].append(copy.deepcopy(TARGET));r=scan(p)
    try:s.assert_disk_identity(r.selectable[0],r)
    except s.SafetyError:pass
    else:raise AssertionError('accepted identical duplicate')
    count('identical_duplicate_refused')
    bad=copy.deepcopy(BASE);bad['blockdevices'][1]['mountpoints']=['/mnt/data']
    for i in range(100):
        assert not scan(bad).selectable
        assert {x.path for x in scan(BASE).selectable}=={'/dev/sda'}
        count('retry_bad_then_good')
    def worker(i):
        p=copy.deepcopy(BASE)
        if i%2:p['blockdevices'][1]['ro']=True
        r=scan(p)
        assert bool(r.selectable)==(not i%2)
        return bool(r.selectable)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(worker,range(320)))
    assert sum(results)==160;COUNTS['concurrent_independent_scans']=320
    for field in ['serial','wwn','model','size','tran','uuid','label']:
        old=scan(BASE);disk=old.selectable[0];request=WipeRequest(disk.path,MethodId.EVERYDAY,old.boot.path,'/tmp/not-opened',device_identity=s.disk_identity(disk),boot_identity=s.disk_identity(old.boot))
        p=copy.deepcopy(BASE);p['blockdevices'][1][field]=('changed' if field!='size' else 257000000000)
        new=scan(p)
        try:s.assert_rediscovered_identity(request,new)
        except s.SafetyError:pass
        else:raise AssertionError(('changed identity accepted',field))
        count('changed_identity_refused')
    s.assert_rediscovered_identity(request,scan(BASE));count('unchanged_identity_accepted')
    # Production branch with every acquisition boundary replaced, then retry.
    with patch.object(d,'read_mount_sources',return_value=['/dev/sdz1']),patch.object(d,'read_cmdline',return_value='boot=live'),patch.object(d,'run_lsblk',side_effect=PermissionError('fixture denied')):
        r=d.discover(env={});assert not r.selectable and r.error;count('production_permission_denied')
print(json.dumps({'counts':COUNTS,'total':sum(COUNTS.values()),'source_sha256':{f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() for f in ['src/beamo_wipe/discover.py','src/beamo_wipe/safety.py','src/beamo_wipe/identity.py','src/beamo_wipe/inventory.py']}},indent=2))
