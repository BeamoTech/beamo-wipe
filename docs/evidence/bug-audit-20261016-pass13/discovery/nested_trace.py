"""Record bounded nested fake disk topology; no inference of a defect."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
sys.path.insert(0,str(Path.cwd()/'src'))
d=importlib.import_module('beamo_wipe.discover')
import beamo_wipe.diagnostics as diagnostics
def forbidden(*args,**kwargs):
    raise AssertionError('Native acquisition forbidden')
subprocess.run=subprocess.Popen=forbidden
d.run_lsblk=d.read_mount_sources=d.read_cmdline=forbidden
diagnostics.log_diag=diagnostics.emit_serial_marker=lambda *args,**kwargs:None
def disk(name,**kwargs):
    row=dict(name=name,path='/dev/'+name,type='disk',size=128_000_000_000,
             serial=name,tran='sata',ro=False,mountpoints=[])
    row.update(kwargs)
    return row
records=[]
for childname in ('sdc','bcache0'):
    for mounts in ([],['/mnt/data']):
        rows=[disk('sdb',tran='usb'),disk('sda',children=[disk(childname,pkname='sda',mountpoints=mounts)])]
        result=d.discover(lsblk_payload={'blockdevices':rows},mount_sources=['/dev/sdb'],cmdline='',env={})
        records.append(dict(child=childname,mounts=mounts,boot=result.boot_identified,
                            targets=[item.path for item in result.selectable],error=result.error))
Path('/tmp/pass13-discovery/nested-trace.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
