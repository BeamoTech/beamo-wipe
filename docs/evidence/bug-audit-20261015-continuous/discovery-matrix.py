"""Fake-only fresh mounted-alias/malformed-graph invariants."""
import copy
import os
from beamo_wipe.discover import discover
os.environ['BEAMO_WIPE_DRY_RUN']='1'

def disk(name, **changes):
    node=dict(name=name,path='/dev/'+name,type='disk',size=100_000_000_000,
              tran='sata',model='Ordinary',vendor='Vendor',serial=name,wwn='',
              mountpoints=[],mountpoint=None,ro=False)
    node.update(changes)
    return node

mutations=[('model','bad\nmodel'),('model','m'*129),('vendor','bad\x00vendor'),
           ('serial','bad\nserial'),('wwn','bad\nwwn'),('size',None),('size',float('nan')),
           ('size',-1),('size',0),('size',float('inf')),('name','bad\nname'),
           ('path','/dev/sdc\n'),('type','DISK'),('type','loop'),('type','ram'),
           ('ro',True),('tran','iscsi'),('fstype','bad\nfstype'),('uuid','bad\nuuid'),
           ('label','bad\nlabel'),('path',None),('name',None)]
checked=0
for shape in ['raw','nested','flat']:
    for alias in ['wwn','serial']:
        for field,value in mutations:
            boot=disk('sdb',tran='usb',mountpoints=['/run/live/medium'])
            target=disk('sda',serial='SHARED',wwn='0x5000abc')
            source=disk('sdc',serial='SHARED',wwn='0x5000abc' if alias=='wwn' else '')
            child=dict(name='sdc1',path='/dev/sdc1',type='part',pkname='sdc',size=99_000_000_000,mountpoints=['/media/data'],mountpoint=None)
            rows=[boot,target,source]
            if shape=='raw':source['mountpoints']=['/media/data']
            elif shape=='nested':source['children']=[child]
            else:rows.append(child)
            source[field]=value
            result=discover(lsblk_payload={'blockdevices':rows},mount_sources=['/dev/sdb'],env={})
            assert '/dev/sda' not in {item.path for item in result.selectable}, (shape,alias,field,value,result)
            checked+=1
print('Fresh malformed raw/nested/flat mounted-alias matrix:',checked,'cases passed')
