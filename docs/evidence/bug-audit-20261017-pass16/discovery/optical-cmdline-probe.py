"""Prepared fake-only ambiguous optical cmdline fallback proof. Root admission required."""
import copy
import hashlib
import importlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
ROOT=Path('/root/dev/Beamo Wipe')
sys.path.insert(0,str(ROOT/'src'))
d=importlib.import_module('beamo_wipe.discover')
s=importlib.import_module('beamo_wipe.safety')
OUT=Path('/tmp/pass16-discovery')
records=[]
native_attempts=[]
def forbidden(*_a,**_k):
    native_attempts.append('native')
    raise AssertionError('Native effect reached')
realpath=os.path.realpath
def safe_realpath(path,*args,**kwargs):
    text=os.fspath(path)
    return text if text.startswith(('/dev/','/sys/')) else realpath(path,*args,**kwargs)
def disk(name,**extra):
    row=dict(name=name,path='/dev/'+name,type='disk',size=128000000000,tran='sata',
             serial='FAKE-'+name,wwn='50014ee20'+name,ro=False,model='Fake '+name,mountpoints=[])
    row.update(extra)
    return row
with patch.dict(os.environ,{'BEAMO_WIPE_DRY_RUN':'1'},clear=True), \
     patch.object(os.path,'realpath',safe_realpath), \
     patch.object(d,'run_lsblk',forbidden),patch.object(d,'read_mount_sources',forbidden), \
     patch.object(d,'read_cmdline',forbidden),patch.object(subprocess,'run',forbidden), \
     patch.object(subprocess,'Popen',forbidden), \
     patch('beamo_wipe.diagnostics.log_diag',lambda *_a,**_k:None), \
     patch('beamo_wipe.diagnostics.emit_serial_marker',lambda *_a,**_k:None):
    for candidate_bus in ('usb','sata','nvme','sas','virtio',''):
        for optical_size in (0,4000000000):
            for source in ('/dev/sr0','LABEL=FAKE-OPTICAL','UUID=optical-uuid'):
                for mounted in (False,True):
                    for reverse in (False,True):
                        optical=disk('sr0',type='rom',tran='usb',ro=True,size=optical_size,
                                     label='FAKE-OPTICAL',uuid='optical-uuid')
                        candidate=disk('sda',tran=candidate_bus)
                        rows=[optical,candidate]
                        if reverse:rows.reverse()
                        result=d.discover(lsblk_payload={'blockdevices':copy.deepcopy(rows)},
                            mount_sources=['/dev/sr0'] if mounted else [],cmdline='boot=live live-media='+source,env={})
                        item={'candidate_bus':candidate_bus,'optical_size':optical_size,'source':source,
                              'mounted':mounted,'reverse':reverse,'boot_identified':result.boot_identified,
                              'boot':result.boot.path if result.boot else None,'error':bool(result.error),
                              'selectable':[disk.path for disk in result.selectable]}
                        if result.selectable:
                            target=result.selectable[0]
                            s.assert_boot_excluded(result)
                            s.assert_disk_identity(target,result)
                            item['token']=s.confirm_spec(target,s.listed_disks(result)).token
                        records.append(item)
output={'cases':records,'native_attempts':native_attempts,'source_sha256':hashlib.sha256((ROOT/'src/beamo_wipe/discover.py').read_bytes()).hexdigest()}
(OUT/'optical-cmdline-probe.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
print(json.dumps({'cases':len(records),'unmounted_identified':sum(not x['mounted'] and x['boot_identified'] for x in records),
                  'unmounted_selectable':sum(not x['mounted'] and bool(x['selectable']) for x in records),
                  'native_attempts':native_attempts},sort_keys=True))
assert not native_attempts
