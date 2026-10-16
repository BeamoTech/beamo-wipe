import copy
import itertools
import json
import os
from pathlib import Path
from unittest.mock import patch
from beamo_wipe.discover import discover
from beamo_wipe.safety import assert_boot_excluded, selectable_disks

os.environ['BEAMO_WIPE_DRY_RUN']='1'

def node(name, serial, **fields):
    return dict(name=name,path='/dev/'+name,type='disk',size=256_000_000_000,tran='sata',ro=False,model='Fixture',serial=serial,mountpoints=[None],**fields)
boot=node('sdb','BOOT')
boot['tran']='usb'
boot['children']=[dict(name='sdb1',path='/dev/sdb1',type='part',pkname='sdb',mountpoints=['/run/live/medium'],uuid='BOOTUUID')]
base=[boot,node('sda','ONE'),node('sdc','TWO'),node('sdd','THREE')]
count=0
for mode in ('mounted','readonly','remote','alias','healthy'):
    nodes=copy.deepcopy(base)
    if mode=='mounted': nodes[2]['mountpoints']=['/media/user/data']
    if mode=='readonly': nodes[2]['ro']=True
    if mode=='remote': nodes[2]['tran']='iscsi'
    if mode=='alias': nodes[2]['serial']='BOOT'
    for order in itertools.permutations(nodes):
        r=discover(lsblk_payload={'blockdevices':list(order)},mount_sources=['/dev/sdb1'],cmdline='boot=live')
        assert r.boot_identified and not r.error,(mode,r)
        assert_boot_excluded(r)
        paths={d.path for d in selectable_disks(r)}
        assert paths==({'/dev/sda','/dev/sdc','/dev/sdd'} if mode=='healthy' else {'/dev/sda','/dev/sdd'}),(mode,paths)
        count+=1
# Invalid inventories must neither poison a subsequent good scan nor select boot.
values=[None,False,True,0,1,{},'',{'bad':1},[1],['bad'],float('inf'),float('nan')]
for field in ('children','mountpoints','mountpoint','name','path','type','tran','serial','wwn','size','ro','uuid','pkname'):
    for value in values:
        nodes=copy.deepcopy(base)
        nodes[2][field]=value
        r=discover(lsblk_payload={'blockdevices':nodes},mount_sources=['/dev/sdb1'],cmdline='boot=live')
        assert '/dev/sdb' not in {d.path for d in selectable_disks(r)},(field,value,r)
        if r.boot_identified and not r.error: assert_boot_excluded(r)
        fresh=discover(lsblk_payload={'blockdevices':copy.deepcopy(base)},mount_sources=['/dev/sdb1'],cmdline='boot=live')
        assert len(selectable_disks(fresh))==3,(field,value,fresh)
        count+=2
# A production-supplied manual override cannot override actual live-mount identity.
for override in ('/dev/sda','/dev/sdc','/dev/missing','LABEL=BOGUS'):
    with patch('beamo_wipe.discover.run_lsblk',return_value={'blockdevices':copy.deepcopy(base)}),patch('beamo_wipe.discover.read_mount_sources',return_value=['/dev/sdb1']),patch('beamo_wipe.discover.read_cmdline',return_value='boot=live'):
        r=discover(boot_path=override,env={'BEAMO_WIPE_BOOT_DEVICE':override})
        assert r.boot and r.boot.path=='/dev/sdb',r
        count+=1
# Permission failures stay fail closed; a corrected retry has no stale state.
for function in ('run_lsblk','read_mount_sources','read_cmdline'):
    for errno in (1,5,13):
        with patch('beamo_wipe.discover.run_lsblk',return_value={'blockdevices':copy.deepcopy(base)}),patch('beamo_wipe.discover.read_mount_sources',return_value=['/dev/sdb1']),patch('beamo_wipe.discover.read_cmdline',return_value='boot=live'),patch('beamo_wipe.discover.'+function,side_effect=OSError(errno,'fixture denial')):
            r=discover(env={})
            assert r.error and not r.boot_identified and not selectable_disks(r),(function,errno,r)
        fresh=discover(lsblk_payload={'blockdevices':copy.deepcopy(base)},mount_sources=['/dev/sdb1'],cmdline='boot=live')
        assert len(selectable_disks(fresh))==3
        count+=2
print(json.dumps({'result':'PASS','controlled_observations':count,'permutation_cases':120,'malformed_then_valid_cases':312,'production_override_cases':4,'permission_then_valid_cases':18,'fake_only':True},indent=2))
