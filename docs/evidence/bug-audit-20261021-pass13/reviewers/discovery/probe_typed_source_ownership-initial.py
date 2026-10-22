"""Finite typed live-source ownership model using synthetic metadata only."""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import os
import posixpath
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from beamo_wipe import discover as discovery
from beamo_wipe import safety

ROOT = Path('/workspace/beamo-wipe')
SOURCES = ['src/beamo_wipe/discover.py', 'src/beamo_wipe/safety.py',
           'src/beamo_wipe/identity.py', 'src/beamo_wipe/inventory.py',
           'src/beamo_wipe/models.py']
KEYS = dict(LABEL='label', PARTLABEL='partlabel', UUID='uuid', PARTUUID='partuuid')
CONDITIONS = ('base', 'peer_same', 'peer_case', 'peer_suffix', 'orphan_same',
              'loop_same', 'same_owner_same', 'same_owner_case', 'bad_parent',
              'malformed_peer')


def state(key, layout, reverse, condition):
    field = KEYS[key]
    value = 'Live é [a]' if key in {'LABEL', 'PARTLABEL'} else 'AbCd-1234'
    boot = dict(name='sdb', path='/dev/sdb', type='disk', size=16_000_000_000,
                tran='usb', serial='BOOT-123', model='Fake boot')
    target = dict(name='sda', path='/dev/sda', type='disk', size=128_000_000_000,
                  tran='sata', serial='TARGET-123', model='Fake target')
    bp = dict(name='sdb1', path='/dev/sdb1', type='part', pkname='sdb',
              size=16_000_000_000, **{field:value})
    tp = dict(name='sda1', path='/dev/sda1', type='part', pkname='sda',
              size=128_000_000_000, **{field:'Other'})
    extra = []
    if condition.startswith('peer_'):
        tp[field] = {'peer_same':value, 'peer_case':value.swapcase(),
                     'peer_suffix':value+'-other'}[condition]
    elif condition == 'orphan_same':
        extra.append(dict(name='sdc1', path='/dev/sdc1', type='part', **{field:value}))
    elif condition == 'loop_same':
        extra.append(dict(name='loop8', path='/dev/loop8', type='loop', **{field:value}))
    elif condition.startswith('same_owner_'):
        extra.append(dict(name='sdb2', path='/dev/sdb2', type='part', pkname='sdb',
                          size=1_000_000, **{field:value if condition.endswith('same') else value.swapcase()}))
    elif condition == 'bad_parent':
        bp['pkname'] = 'sda'
    elif condition == 'malformed_peer':
        tp[field] = ['untrusted-shape']
    if layout == 'tree':
        boot['children'] = [bp] + [p for p in extra if p.get('pkname') == 'sdb']
        target['children'] = [tp]
        nodes = [boot, target] + [p for p in extra if p.get('pkname') != 'sdb']
    else:
        nodes = [boot, bp, target, tp, *extra]
    if reverse:
        nodes.reverse()
        if layout == 'tree': boot['children'].reverse()
    expected = condition in {'base','peer_suffix'}
    if condition in {'peer_case','same_owner_same','same_owner_case'}:
        expected = key in {'LABEL','PARTLABEL'}
    return {'blockdevices':nodes}, value, expected


def main(output):
    records = []
    native = Counter()
    aliases = {}
    realpath, lstat = os.path.realpath, os.lstat
    def fake_realpath(path, *args, **kwargs):
        value = os.fspath(path)
        if value.startswith(('/dev/','/sys/')):
            return aliases.get(value, posixpath.normpath(value))
        return realpath(path, *args, **kwargs)
    def fake_lstat(path, *args, **kwargs):
        if os.fspath(path).startswith(('/dev/','/sys/')):
            raise FileNotFoundError(os.fspath(path))
        return lstat(path, *args, **kwargs)
    def forbidden(name):
        def call(*args, **kwargs):
            native[name] += 1
            raise AssertionError('native acquisition forbidden: '+name)
        return call
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN':'1'}), \
         patch('os.path.realpath',fake_realpath), patch('os.lstat',fake_lstat), \
         patch.object(discovery,'run_lsblk',forbidden('lsblk')), \
         patch.object(discovery,'read_mount_sources',forbidden('mounts')), \
         patch.object(discovery,'read_cmdline',forbidden('cmdline')), \
         patch.object(safety,'assert_local_device_transport',forbidden('transport')), \
         patch('beamo_wipe.diagnostics.log_diag',lambda *a,**kw:None), \
         patch('beamo_wipe.diagnostics.emit_serial_marker',lambda *a,**kw:None):
        for key, layout, reverse, syntax, condition in itertools.product(
                KEYS, ('tree','flat'), (False,True), ('typed','udev'), CONDITIONS):
            payload,value,expected = state(key,layout,reverse,condition)
            aliases.clear()
            if syntax == 'typed':
                source = key+'="'+value+'"'
            else:
                prefix = next(prefix for prefix,k in discovery.UDEV_BY_PREFIXES if k == key)
                source = prefix+value.replace(' ',r'\x20')
                aliases[source] = '/dev/sdb1'
            found = discovery.discover(lsblk_payload=copy.deepcopy(payload), mount_sources=[source], cmdline='', env={})
            actual = bool(found.boot_identified and found.boot and found.boot.path == '/dev/sdb'
                          and {d.path for d in found.selectable} == {'/dev/sda'})
            # Exercise the production link-required identification boundary independently.
            identified = discovery.identify_boot_path(payload['blockdevices'],mount_sources=[source],
                                                       cmdline='',require_device_link=True)
            production_actual = identified == '/dev/sdb'
            records.append(dict(key=key,layout=layout,reverse=reverse,syntax=syntax,
                                condition=condition,expected=expected,actual=actual,
                                production_actual=production_actual))
        for key, link in itertools.product(KEYS, ('missing','target','boot')):
            payload,value,_ = state(key,'tree',False,'base')
            source = next(prefix for prefix,k in discovery.UDEV_BY_PREFIXES if k == key)+value.replace(' ',r'\x20')
            aliases.clear()
            if link != 'missing': aliases[source] = '/dev/sdb1' if link == 'boot' else '/dev/sda1'
            actual = discovery.identify_boot_path(payload['blockdevices'],mount_sources=[source],
                                                  cmdline='',require_device_link=True) == '/dev/sdb'
            records.append(dict(key=key,production_link=link,expected=link=='boot',actual=actual,
                                production_actual=actual))
    mismatches = [r for r in records if r['actual'] != r['expected'] or r['production_actual'] != r['expected']]
    result = dict(states=len(records),positive=sum(r['expected'] for r in records),
                  refusal=sum(not r['expected'] for r in records),mismatches=mismatches,
                  native_callbacks=dict(native),
                  source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    output.with_suffix('.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
    print(json.dumps(result,sort_keys=True))
    return bool(mismatches) or bool(native)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('typed-source-ownership.json'))
    raise SystemExit(main(parser.parse_args().output))
