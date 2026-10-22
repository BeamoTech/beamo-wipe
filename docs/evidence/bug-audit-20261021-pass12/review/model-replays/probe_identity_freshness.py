"""Fake two-snapshot discovery/authorization model; no native inventory/device access."""
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
from beamo_wipe.models import MethodId, WipeRequest

ROOT = Path(__file__).resolve().parents[3] / 'beamo-wipe'
if not (ROOT / 'src/beamo_wipe/discover.py').exists():
    ROOT = Path('/workspace/beamo-wipe')
SOURCES = ['src/beamo_wipe/discover.py', 'src/beamo_wipe/safety.py',
           'src/beamo_wipe/identity.py', 'src/beamo_wipe/inventory.py',
           'src/beamo_wipe/models.py']
CHANGES = ('same', 'reorder', 'target_serial', 'target_wwn', 'target_model',
           'target_vendor', 'target_tran', 'target_rota', 'target_label',
           'part_uuid', 'part_partuuid', 'part_label', 'part_partlabel',
           'part_size', 'part_type', 'part_fstype', 'part_path_swap',
           'target_mounted', 'target_read_only', 'peer_serial', 'peer_added',
           'peer_removed', 'boot_serial', 'boot_label', 'boot_uuid',
           'target_model_control', 'part_uuid_container', 'duplicate_conflict',
           'duplicate_identical')


def machine(family, layout, reverse):
    target_name = {'sd': 'sda', 'nvme': 'nvme0n1', 'mmc': 'mmcblk0'}[family]
    suffix = 'p' if target_name[-1].isdigit() else ''
    names = (target_name + suffix + '1', target_name + suffix + '2')
    boot = dict(name='sdz', path='/dev/sdz', type='disk', size=16_000_000_000,
                model='Fake boot', serial='BOOT-SERIAL', wwn='50014ee200000001',
                tran='usb', rota=False, ro=False, mountpoints=[], label='BOOT')
    target = dict(name=target_name, path='/dev/' + target_name, type='disk',
                  size=128_000_000_000, model='Fake target', vendor='Target vendor',
                  serial='TARGET-SERIAL', wwn='50014ee200000002', tran={
                  'sd': 'sata', 'nvme': 'nvme', 'mmc': 'mmc'}[family],
                  rota=False, ro=False, mountpoints=[], label='Target disk')
    peer = dict(name='sdc', path='/dev/sdc', type='disk', size=512_000_000_000,
                model='Fake peer', serial='PEER-SERIAL', wwn='50014ee200000003',
                tran='sata', rota=False, ro=False, mountpoints=[])
    bp = dict(name='sdz1', path='/dev/sdz1', type='part', pkname='sdz',
              size=16_000_000_000, fstype='iso9660', uuid='boot-uuid',
              partuuid='boot-partuuid', label='BOOT-FS', ro=False, mountpoints=[])
    parts = [dict(name=name, path='/dev/' + name, type='part', pkname=target_name,
                  size=64_000_000_000, fstype='ext4', uuid='target-uuid-' + str(i),
                  partuuid='target-partuuid-' + str(i), label='Target fs ' + str(i),
                  partlabel='Target partition ' + str(i), parttype='linux',
                  ro=False, mountpoints=[]) for i, name in enumerate(names)]
    if layout == 'tree':
        boot['children'] = [bp]
        target['children'] = parts
        nodes = [boot, target, peer]
    else:
        nodes = [boot, target, peer, bp, *parts]
    if reverse:
        nodes.reverse()
        if layout == 'tree':
            target['children'].reverse()
    return dict(blockdevices=nodes)


def flatten(payload):
    return [node for node, _ in discovery.flatten_blockdevices(payload['blockdevices'])]


def mutation(payload, change, family):
    nodes = flatten(payload)
    target_name = {'sd': 'sda', 'nvme': 'nvme0n1', 'mmc': 'mmcblk0'}[family]
    target = next(n for n in nodes if n['name'] == target_name)
    boot = next(n for n in nodes if n['name'] == 'sdz')
    peer = next(n for n in nodes if n['name'] == 'sdc')
    parts = sorted((n for n in nodes if n.get('pkname') == target_name), key=lambda n:n['name'])
    bp = next(n for n in nodes if n['name'] == 'sdz1')
    if change == 'same': return
    if change == 'reorder':
        payload['blockdevices'].reverse()
        for node in nodes:
            if node.get('children'): node['children'].reverse()
        return
    changes = {
        'target_serial': (target, 'serial', 'TARGET-CHANGED'),
        'target_wwn': (target, 'wwn', '50014ee200000009'),
        'target_model': (target, 'model', 'Changed target'),
        'target_vendor': (target, 'vendor', 'Changed vendor'),
        'target_tran': (target, 'tran', 'usb'),
        'target_rota': (target, 'rota', True),
        'target_label': (target, 'label', 'Changed disk label'),
        'part_uuid': (parts[0], 'uuid', 'changed-uuid'),
        'part_partuuid': (parts[0], 'partuuid', 'changed-partuuid'),
        'part_label': (parts[0], 'label', 'Changed fs label'),
        'part_partlabel': (parts[0], 'partlabel', 'Changed partition label'),
        'part_size': (parts[0], 'size', 63_000_000_000),
        'part_type': (parts[0], 'parttype', 'windows'),
        'part_fstype': (parts[0], 'fstype', 'ntfs'),
        'target_mounted': (parts[0], 'mountpoints', ['/media/owned-fake']),
        'target_read_only': (target, 'ro', True),
        'peer_serial': (peer, 'serial', 'PEER-CHANGED'),
        'boot_serial': (boot, 'serial', 'BOOT-CHANGED'),
        'boot_label': (boot, 'label', 'Changed boot label'),
        'boot_uuid': (bp, 'uuid', 'boot-uuid-changed'),
        'target_model_control': (target, 'model', 'Fake\ntarget'),
        'part_uuid_container': (parts[0], 'uuid', ['bad']),
    }
    if change in changes:
        node, field, value = changes[change]; node[field] = value; return
    if change == 'part_path_swap':
        for key in ('uuid', 'partuuid', 'label', 'partlabel'):
            parts[0][key], parts[1][key] = parts[1][key], parts[0][key]
    elif change == 'peer_added':
        new = copy.deepcopy(peer)
        new.update(name='sde', path='/dev/sde', serial='NEW-PEER', wwn='50014ee200000004')
        payload['blockdevices'].append(new)
    elif change == 'peer_removed':
        payload['blockdevices'] = [n for n in payload['blockdevices'] if n is not peer]
    elif change.startswith('duplicate_'):
        new = copy.deepcopy(target)
        if change == 'duplicate_conflict': new['ro'] = True
        payload['blockdevices'].append(new)
    else: raise AssertionError(change)


def request(result, family):
    path = '/dev/' + {'sd': 'sda', 'nvme': 'nvme0n1', 'mmc': 'mmcblk0'}[family]
    target = next(d for d in result.selectable if d.path == path)
    return WipeRequest(device=path, boot_device=result.boot.path,
                       method=MethodId.EVERYDAY, logfile='/tmp/fake-only.log',
                       device_identity=safety.disk_identity(target),
                       boot_identity=safety.disk_identity(result.boot),
                       inventory_identity=tuple(sorted(safety.disk_identity(d) for d in safety.listed_disks(result))))


def main(output):
    native = Counter()
    realpath = os.path.realpath
    lstat = os.lstat
    def fake_realpath(path, *args, **kwargs):
        value = os.fspath(path)
        if value.startswith(('/dev/', '/sys/')):
            return posixpath.normpath(value)
        return realpath(path, *args, **kwargs)
    def fake_lstat(path, *args, **kwargs):
        if os.fspath(path).startswith(('/dev/', '/sys/')):
            native['fake_stat'] += 1
            raise FileNotFoundError(os.fspath(path))
        return lstat(path, *args, **kwargs)
    def forbidden(name):
        def call(*args, **kwargs):
            native[name] += 1
            raise AssertionError('native boundary called: ' + name)
        return call
    records = []
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN':'1'}), \
         patch('os.path.realpath', fake_realpath), patch('os.lstat', fake_lstat), \
         patch.object(discovery, 'run_lsblk', forbidden('lsblk')), \
         patch.object(discovery, 'read_mount_sources', forbidden('mount_sources')), \
         patch.object(discovery, 'read_cmdline', forbidden('cmdline')), \
         patch.object(safety, 'assert_local_device_transport', forbidden('transport')), \
         patch('beamo_wipe.diagnostics.log_diag', lambda *a, **k: None), \
         patch('beamo_wipe.diagnostics.emit_serial_marker', lambda *a, **k: None):
        for family, layout, reverse, source, change in itertools.product(
                ('sd', 'nvme', 'mmc'), ('tree','flat'), (False,True),
                ('/dev/sdz1','PARTUUID=boot-partuuid'), CHANGES):
            initial_payload = machine(family, layout, reverse)
            initial = discovery.discover(lsblk_payload=initial_payload, mount_sources=[source], cmdline='', env={})
            assert initial.boot_identified and len(initial.selectable) == 2, (family, layout, initial)
            confirmed = request(initial, family)
            fresh_payload = copy.deepcopy(initial_payload)
            mutation(fresh_payload, change, family)
            fresh = discovery.discover(lsblk_payload=fresh_payload, mount_sources=[source], cmdline='', env={})
            accepted = True
            try: safety.assert_rediscovered_identity(confirmed, fresh)
            except safety.SafetyError: accepted = False
            expected = change in {'same', 'reorder'}
            # ROTA is not an identity distinction when an NVMe transport fixes kind.
            if family == 'nvme' and change == 'target_rota': expected = True
            records.append(dict(family=family, layout=layout, reverse=reverse,
                                source=source, change=change, expected=expected,
                                accepted=accepted, fresh_boot=fresh.boot_identified,
                                selectable=[d.path for d in fresh.selectable]))
        precedence = (
            ('mount_over_cmdline', ['/dev/sdz1'], 'live-media=/dev/sda1', None, True),
            ('agreeing_override', ['/dev/sdz1'], '', '/dev/sdz', True),
            ('conflicting_override', ['/dev/sdz1'], '', '/dev/sda', False),
            ('unresolved_source', ['/dev/sdz1','UUID=unknown'], '', None, False),
            ('two_owners', ['/dev/sdz1','/dev/sda1'], '', None, False),
            ('duplicate_same_source', ['/dev/sdz1','/dev/sdz1'], '', None, True),
        )
        for layout, reverse, (name, sources, cmdline, override, expected) in itertools.product(
                ('tree','flat'), (False,True), precedence):
            result = discovery.discover(lsblk_payload=machine('sd', layout, reverse),
                                        mount_sources=sources, cmdline=cmdline,
                                        boot_path=override, env={})
            accepted = bool(result.boot_identified and result.boot and result.boot.path == '/dev/sdz'
                            and {d.path for d in result.selectable} == {'/dev/sda','/dev/sdc'})
            records.append(dict(precedence=name, layout=layout, reverse=reverse,
                                expected=expected, accepted=accepted))
    mismatches = [row for row in records if row['accepted'] != row['expected']]
    result = dict(states=len(records), initial_scans=3*2*2*2*len(CHANGES),
                  fresh_scans=3*2*2*2*len(CHANGES), precedence_scans=24,
                  positive=sum(row['expected'] for row in records),
                  refusal=sum(not row['expected'] for row in records),
                  mismatches=mismatches, native_callbacks=dict(native),
                  source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    output.with_suffix('.jsonl').write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in records))
    print(json.dumps(result, sort_keys=True))
    return bool(mismatches) or any(value for key, value in native.items() if key != 'fake_stat')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('identity-freshness.json'))
    raise SystemExit(main(parser.parse_args().output))
