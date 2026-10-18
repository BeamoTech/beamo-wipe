import copy
import itertools
import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
from beamo_wipe.discover import discover
from beamo_wipe.safety import confirm_spec, SafetyError
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
def node(name, **changes):
    result = dict(name=name, path='/dev/'+name, type='disk', size=100_000_000_000, model='Local disk', serial='SERIAL-'+name, ro=False, mountpoints=[], tran='sata')
    result.update(changes)
    return result
base={'blockdevices':[node('sda'),node('sdb',tran='usb',mountpoints=['/run/live/medium'])]}
count=0
for field, values in [
    ('mountpoints', [['/'], ['/media/data'], '\u2028', {}, False, 0, [False], [1], ['\x00'], [' ']]),
    ('mountpoint', ['/', '/media/data', '\u2028', {}, False, 0, ['x'], '\x00', ' ']),
    ('ro', [True, 1, '1', 'true']),
    ('tran', ['iscsi','fc','fcoe','tcp','rdma','nvme-of','nbd','']),
    ('size', [0,-1,None,'garbage','NaN','inf',float('nan'),float('inf')]),
    ('children', [{},False,0,'',[False],[1],['bad']]),
]:
    for val in values:
        payload=copy.deepcopy(base)
        payload['blockdevices'][0][field]=val
        result=discover(lsblk_payload=payload,mount_sources=['/dev/sdb'],cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})
        assert not result.selectable, (field,val,result.selectable)
        count+=1
# Conflicting live-medium claims must never create a target.
for sources in [ ['/dev/sdb','/dev/sda'], ['/dev/sdb','UUID=missing'], ['/dev/sdb','/dev/loop0'], ['overlay'], ['/dev/missing'] ]:
    result=discover(lsblk_payload=copy.deepcopy(base),mount_sources=sources,cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})
    assert not result.boot_identified and not result.selectable, sources
    count+=1
# Every accepted token must distinguish one path even across awkward serial/size collisions.
identifiers=['SERIAL-1000','SERIAL-0500','SERIAL-sda','sdb','000000','unknown','0x000','ABCD','ZABCD','1000','0500','1234']
for serials in itertools.product(identifiers, repeat=2):
    payload={'blockdevices':[node('sda',serial=serials[0],size=1_000_000_000_000),node('sdc',serial=serials[1],size=500_000_000_000),node('sdb',tran='usb',size=16_000_000_000,mountpoints=['/run/live/medium'])]}
    result=discover(lsblk_payload=payload,mount_sources=['/dev/sdb'],cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})
    specs=[]
    for disk in result.selectable:
        try:
            spec=confirm_spec(disk, result.disks)
        except SafetyError:
            continue
        assert spec.token.casefold() not in {'sda','sdb','sdc'}
        specs.append(spec.token.casefold())
    assert len(specs)==len(set(specs)),serials
    count+=1
print(f'{count} independent fake mutation/token cases passed')
