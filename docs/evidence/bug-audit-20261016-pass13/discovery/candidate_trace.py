"""Trace EFI-looking substrings using fake metadata only."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
sys.path.insert(0, str(Path.cwd() / 'src'))
discovery = importlib.import_module('beamo_wipe.discover')
import beamo_wipe.diagnostics as diagnostics

def forbidden(*args, **kwargs):
    raise AssertionError('Native acquisition forbidden')
subprocess.run = subprocess.Popen = forbidden
discovery.run_lsblk = discovery.read_mount_sources = discovery.read_cmdline = forbidden
diagnostics.log_diag = diagnostics.emit_serial_marker = lambda *args, **kwargs: None

records = []
for fstype in ('ntfs', 'ext4'):
    for field in ('partlabel', 'parttypename'):
        for name in ('Benefits', 'Definitions', 'EFI system partition', 'UEFI System'):
            part = dict(name='sda1', path='/dev/sda1', type='part', pkname='sda',
                        size=100_000_000_000, fstype=fstype, mountpoints=[], **{field:name})
            target = dict(name='sda', path='/dev/sda', type='disk', tran='sata',
                          size=128_000_000_000, serial='TARGET', ro=False,
                          children=[part], mountpoints=[])
            boot = dict(name='sdb', path='/dev/sdb', type='disk', tran='usb',
                        size=16_000_000_000, serial='BOOT', ro=False, mountpoints=[])
            result = discovery.discover(lsblk_payload={'blockdevices':[target,boot]},
                                        mount_sources=['/dev/sdb'], cmdline='',
                                        env={'BEAMO_WIPE_DRY_RUN':'1'})
            assert result.boot_identified and len(result.selectable)==1
            observed = result.selectable[0].contents
            records.append(dict(fstype=fstype,field=field,name=name,
                                contents=observed, selectable=[d.path for d in result.selectable]))
Path('/tmp/pass13-discovery/candidate-trace.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
