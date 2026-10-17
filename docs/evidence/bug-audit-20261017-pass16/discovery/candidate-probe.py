"""Pass16 fake-only public discovery numeric/duplicate probes. Root admission required."""
from __future__ import annotations
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path('/root/dev/Beamo Wipe')
sys.path.insert(0, str(ROOT/'src'))
d = importlib.import_module('beamo_wipe.discover')
s = importlib.import_module('beamo_wipe.safety')
OUT = Path('/tmp/pass16-discovery')

def disk(name, **extra):
    row = dict(name=name, path='/dev/'+name, size=128000000000, type='disk', tran='sata',
               rota=False, model='Fake disk', vendor='Fake vendor', serial='FAKE-'+name,
               wwn='50014ee20'+name, ro=False, mountpoints=[])
    row.update(extra)
    return row

def boot():
    return disk('sdz', size=16000000000, tran='usb', mountpoints=['/run/live/medium'])

native_attempts=[]
def forbidden(*args, **kwargs):
    native_attempts.append('native effect')
    raise AssertionError('Probe reached a native effect')

realpath=os.path.realpath

def safe_realpath(path,*args,**kwargs):
    text=os.fspath(path)
    if text.startswith(('/dev/','/sys/')):
        return text
    return realpath(path,*args,**kwargs)

def scan(payload, route):
    if route == 'direct-parser':
        return d.parse_lsblk_json(payload, boot_path='/dev/sdz')
    if route == 'injected-public':
        return d.discover(lsblk_payload=payload, mount_sources=['/dev/sdz'],cmdline='',env={})
    if route == 'production-metadata-stub':
        with patch.object(d,'run_lsblk',return_value=payload):
            return d.discover(mount_sources=['/dev/sdz'],cmdline='',env={})
    raise AssertionError(route)


def inspect_result(result):
    out={'error': bool(result.error), 'boot_identified':result.boot_identified,
         'selectable':[item.path for item in result.selectable]}
    if '/dev/sda' in out['selectable']:
        target=next(item for item in result.selectable if item.path=='/dev/sda')
        s.assert_boot_excluded(result)
        s.assert_disk_identity(target,result)
        out.update(token=s.confirm_spec(target,s.listed_disks(result)).token,
                   identity=s.disk_identity(target))
    return out

numeric=[]
duplicates=[]
with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN':'1'}, clear=True), \
     patch.object(os.path,'realpath',safe_realpath), \
     patch.object(d,'run_lsblk',forbidden), \
     patch.object(d,'read_mount_sources',forbidden), \
     patch.object(d,'read_cmdline',forbidden), \
     patch.object(subprocess,'run',forbidden), \
     patch.object(subprocess,'Popen',forbidden), \
     patch('beamo_wipe.diagnostics.log_diag',lambda *_a,**_k:None), \
     patch('beamo_wipe.diagnostics.emit_serial_marker',lambda *_a,**_k:None):
    for spelling in ('1e999','-1e999','Infinity','-Infinity','NaN','128000000000','0','-1',
                     '128000000000.0','"1e999"','"Infinity"','null'):
        original={'blockdevices':[boot(),disk('sda')]}
        raw=json.dumps(original).replace('"size": 128000000000','"size": '+spelling)
        payload=d.load_lsblk_json_text(raw)
        for route in ('injected-public','production-metadata-stub','direct-parser'):
            row={'spelling':spelling,'route':route,'native_metadata_gate':route=='production-metadata-stub'}
            try:
                row.update(inspect_result(scan(copy.deepcopy(payload),route)))
                row['escaped']=None
            except Exception as exc:
                row.update(escaped=type(exc).__name__,exception=str(exc))
            numeric.append(row)
    for field,value in (
        ('vendor','Another vendor'),('model','Another model'),
        ('uuid','another-uuid'),('partuuid','another-partuuid'),
        ('label','another-label'),('partlabel','another-partlabel'),
        ('fstype','ext4'),('parttype','another-parttype'),
    ):
        for omission in ('valid','overlong-model','overlong-vendor','overlong-label'):
            first=disk('sda',fstype='ntfs',uuid='original-uuid',partuuid='original-partuuid',
                       label='original-label',partlabel='original-partlabel',parttype='original-parttype')
            second=copy.deepcopy(first)
            second[field]=value
            if omission=='overlong-model': second['model']='M'*129
            if omission=='overlong-vendor': second['vendor']='V'*129
            if omission=='overlong-label': second['label']='L'*129
            for order in ((first,second),(second,first)):
                payload={'blockdevices':[boot(),*copy.deepcopy(order)]}
                row={'field':field,'omission':omission,'valid_first':order[0] is first}
                result=scan(payload,'injected-public')
                row.update(inspect_result(result))
                duplicates.append(row)
output={'numeric':numeric,'duplicates':duplicates,'native_attempts':native_attempts,
        'hashes':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (ROOT/'src/beamo_wipe/discover.py',ROOT/'src/beamo_wipe/safety.py',ROOT/'src/beamo_wipe/models.py')}}
(OUT/'candidate-probe.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
print(json.dumps({'numeric_cases':len(numeric),'numeric_escaped':sum(bool(x['escaped']) for x in numeric),
                  'duplicates':len(duplicates),'duplicates_target_selectable':sum('/dev/sda' in x['selectable'] for x in duplicates),
                  'native_attempts':native_attempts},sort_keys=True))
assert not native_attempts
