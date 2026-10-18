"""Fresh fake-only whole-disk/partition namespace and stale-observation matrix."""
from __future__ import annotations
import builtins
import copy
import hashlib
import importlib
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['BEAMO_WIPE_DRY_RUN']='1'
sys.path.insert(0,str(Path.cwd()/'src'))
d=importlib.import_module('beamo_wipe.discover')
from beamo_wipe.safety import SafetyError, assert_disk_identity, confirm_spec, disk_identity, listed_disks, normalize_whole_disk
import beamo_wipe.diagnostics as diagnostics
records=[]
native_attempts=[]
def forbidden(*args,**kwargs):
    native_attempts.append(repr(args[:1]))
    raise AssertionError('Native acquisition forbidden')
subprocess.run=subprocess.Popen=forbidden
d.run_lsblk=d.read_mount_sources=d.read_cmdline=forbidden
def guarded_open(original):
    def guarded(path,*args,**kwargs):
        if str(path).startswith(('/proc/','/sys/','/dev/')):
            native_attempts.append(str(path))
            raise AssertionError('Machine read forbidden')
        return original(path,*args,**kwargs)
    return guarded
builtins.open=guarded_open(builtins.open)
io.open=guarded_open(io.open)
diagnostics.log_diag=diagnostics.emit_serial_marker=lambda *args,**kwargs:None
names=(('hda','sata'),('dasda','sas'),('xvda','virtio'),('mmcblk0',''),('nvme0n11','nvme'),('vdz','virtio'))
def machine(name,tran,shape):
    partname=name+('p1' if name[-1].isdigit() else '1')
    part=dict(name=partname,path='/dev/'+partname,type='part',pkname=name,
              size=100_000_000_000,fstype='ntfs',partlabel='Benefits',mountpoints=[])
    target=dict(name=name,path='/dev/'+name,type='disk',tran=tran,size=128_000_000_000,
                serial='TARGET',wwn='wwn-target',ro=False,mountpoints=[])
    boot=dict(name='sdb',path='/dev/sdb',type='disk',tran='usb',size=16_000_000_000,
              serial='BOOT',wwn='wwn-boot',ro=False,mountpoints=[])
    rows=[target,boot]
    if shape=='tree':target['children']=[part]
    else:rows.append(part)
    return {'blockdevices':rows},target,part
def scan(payload):
    return d.discover(lsblk_payload=payload,mount_sources=['/dev/sdb'],cmdline='',env={})
for (name,tran),shape in itertools.product(names,('tree','flat')):
    payload,target,part=machine(name,tran,shape)
    baseline=scan(payload)
    assert [x.path for x in baseline.selectable]==['/dev/'+name]
    before=baseline.selectable[0]
    assert before.contents=='data'
    assert confirm_spec(before,listed_disks(baseline)).token=='128'
    assert normalize_whole_disk(before.path)==before.path
    try:normalize_whole_disk(part['path'])
    except SafetyError:pass
    else:raise AssertionError('partition accepted')
    for change in ('normal','root_mount','part_mount','readonly','zero','duplicate_equal','duplicate_readonly','duplicate_mounted','peer_boot_wwn','serial_swap','layout_swap','bad_pkname','bad_partpath'):
        payload,target,part=machine(name,tran,shape)
        if change=='root_mount':target['mountpoints']=['/mnt/data']
        elif change=='part_mount':part['mountpoints']=['/mnt/data']
        elif change=='readonly':target['ro']=True
        elif change=='zero':target['size']=0
        elif change=='duplicate_equal':payload['blockdevices'].append(copy.deepcopy(target))
        elif change=='duplicate_readonly':payload['blockdevices'].append(dict(copy.deepcopy(target),ro=True))
        elif change=='duplicate_mounted':payload['blockdevices'].append(dict(copy.deepcopy(target),mountpoints=['/mnt/data']))
        elif change=='peer_boot_wwn':target['wwn']='wwn-boot'
        elif change=='serial_swap':target['serial']='REPLACEMENT'
        elif change=='layout_swap':part['partlabel']='Replacement data'
        elif change=='bad_pkname':part['pkname']='sdb'
        elif change=='bad_partpath':part['path']='/dev/sdb1'
        result=scan(payload)
        accepted=True
        try:assert_disk_identity(before,result)
        except SafetyError:accepted=False
        assert accepted==(change=='normal'),(name,shape,change,result)
        assert '/dev/sdb' not in [x.path for x in result.selectable]
        records.append(dict(case=f'{name}/{shape}/{change}',accepted=accepted,
                            targets=[x.path for x in result.selectable],boot=result.boot_identified,
                            refused=bool(result.error)))
assert not native_attempts
out=dict(cases=len(records),native_attempts=native_attempts,
         observations_sha256=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),observations=records)
Path('/tmp/pass13-discovery/namespace-matrix.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({key:value for key,value in out.items() if key!='observations'},indent=2))
