"""Fresh fake-only rediscovery fingerprint, boot and token boundary review."""
from __future__ import annotations
import builtins
import copy
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from unittest.mock import patch

os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe.discover import discover
from beamo_wipe.models import Disk, DiskKind
from beamo_wipe.safety import SafetyError, assert_disk_identity, confirm_spec, disk_identity, listed_disks, token_matches
import beamo_wipe.diagnostics as diagnostics

observations = []
native_attempts = []
def forbidden(*args, **kwargs):
    native_attempts.append(str(args[:1]))
    raise AssertionError('Forbidden native acquisition')
original_builtin_open, original_io_open = builtins.open, io.open
def guard_open(original):
    def guarded(path, *args, **kwargs):
        value = str(path)
        if value.startswith(('/proc/', '/sys/', '/dev/')):
            native_attempts.append(value)
            raise AssertionError('Forbidden machine read: ' + value)
        return original(path, *args, **kwargs)
    return guarded

subprocess.run = forbidden
subprocess.Popen = forbidden
builtins.open = guard_open(original_builtin_open)
io.open = guard_open(original_io_open)
diagnostics.log_diag = lambda *args, **kwargs: None
diagnostics.emit_serial_marker = lambda *args, **kwargs: None

def disk(name, transport, serial):
    return dict(name=name, path='/dev/' + name, type='disk', tran=transport,
                serial=serial, wwn='wwn-' + serial, model='Fake ' + name,
                vendor='FakeVendor', size=512_000_000_000, rota=False, ro=False,
                mountpoints=[])

def machine(target_name='sda', transport='sata', shape='tree'):
    boot = disk('sdb', 'usb', 'BOOT')
    boot.update(size=16_000_000_000)
    boot['children'] = [dict(name='sdb1', path='/dev/sdb1', type='part', pkname='sdb',
                            size=15_000_000_000, label='BEAMO_WIPE', uuid='BOOT-UUID',
                            partuuid='BOOT-PARTUUID', partlabel='boot partition', mountpoints=[])]
    target = disk(target_name, transport, 'TARGET')
    partname = target_name + ('p1' if target_name[-1].isdigit() else '1')
    part = dict(name=partname, path='/dev/' + partname, type='part', pkname=target_name,
                size=500_000_000_000, fstype='ext4', uuid='TARGET-UUID', partuuid='PART-UUID',
                label='OwnerData', partlabel='OwnerPartition', parttype='linux-data',
                parttypename='Linux filesystem', mountpoints=[])
    payload = dict(blockdevices=[boot, target])
    if shape == 'tree':
        target['children'] = [part]
    else:
        payload['blockdevices'].append(part)
    return payload, target, part

def scan(payload, sources=None, **kwargs):
    return discover(lsblk_payload=payload, mount_sources=['/dev/sdb1'] if sources is None else sources,
                    cmdline=kwargs.pop('cmdline', ''), env={'BEAMO_WIPE_DRY_RUN': '1'}, **kwargs)

def record(label, result):
    targets = tuple(sorted(d.path for d in result.selectable))
    assert not any(d.is_boot for d in result.selectable), label
    assert result.boot is None or result.boot.path not in targets, label
    observations.append(dict(case=label, targets=targets, boot_identified=result.boot_identified,
                             refused=bool(result.error)))

mutations = {
    'serial': ('REPLACEMENT', '', 'X\nY', 'X' * 129, 4),
    'wwn': ('wwn-REPLACEMENT', '', 'X\nY', 'X' * 129, 4),
    'model': ('Replacement model', '', 'X\nY', 'X' * 129, None),
    'vendor': ('Replacement vendor', '', 'X\nY', 'X' * 129, None),
    'size': (512_000_000_001, 0, -1, 'not-a-size', float('nan')),
    'tran': ('usb', 'iscsi', None, 'unknown-remote', 4),
    'ro': (True,),
    'mountpoints': (['/media/owned'], '/media/owned', ['\n'], {'bad': 1}),
}
part_mutations = {
    'uuid': ('REPLACEMENT', '', 'X\nY', 'X' * 129, 4),
    'partuuid': ('REPLACEMENT', '', 'X\nY', 'X' * 129, 4),
    'label': ('Replacement', '', 'X\nY', 'X' * 129, 4),
    'partlabel': ('Replacement', '', 'X\nY', 'X' * 129, 4),
    'parttype': ('windows-recovery', '', 'X\nY', 'X' * 129, 4),
    'parttypename': ('Windows recovery', '', 'X\nY', 'X' * 129, None),
    'fstype': ('ntfs', '', 'X\nY', 'X' * 129, 4),
    'size': (500_000_000_001, 0, -1, 'not-a-size', float('nan')),
    'mountpoints': (['/media/owned'], '/media/owned', ['\n'], {'bad': 1}),
    'pkname': ('sdb', '', 'missing-parent'),
    'path': ('/dev/sdb1', '/dev/not-target-part', '/dev/' + 'x' * 129),
}
for (name, transport), shape in itertools.product((('sda', 'sata'), ('nvme0n1', 'nvme'), ('vda', 'virtio')), ('tree', 'flat')):
    old_payload, _, _ = machine(name, transport, shape)
    old = scan(old_payload)
    assert len(old.selectable) == 1
    before = old.selectable[0]
    for location, changes in (('disk', mutations), ('part', part_mutations)):
        for key, values in changes.items():
            for value in values:
                payload, root, part = machine(name, transport, shape)
                node = root if location == 'disk' else part
                if node.get(key) == value:
                    continue
                node[key] = value
                result = scan(payload)
                label = f'identity/{name}/{shape}/{location}/{key}/{value!r}'
                # A changed observed identity or a newly mounted/RO/invalid node
                # may no longer satisfy the exact old selected disk snapshot.
                redundant_parent = location == 'part' and key == 'pkname' and value == '' and shape == 'tree'
                if redundant_parent:
                    assert_disk_identity(before, result)
                else:
                    try:
                        assert_disk_identity(before, result)
                    except SafetyError:
                        pass
                    else:
                        raise AssertionError(('old snapshot accepted', label, result))
                record(label, result)

# Boot mounts outrank stale cmdline, and every conflicting/unresolved mount
# closes the inventory across ordering and duplicates.
boot_sources = ('/dev/sdb', '/dev/sdb1', 'UUID=BOOT-UUID', 'PARTUUID=BOOT-PARTUUID',
                'LABEL=BEAMO_WIPE', 'PARTLABEL=boot partition')
for source, other, order, cmdline in itertools.product(
    boot_sources, (None, '/dev/sda', 'UUID=MISSING', 'overlay', '/dev/loop99'),
    ('first', 'last', 'duplicate'), ('', 'boot=live live-media=/dev/sda')):
    payload, _, _ = machine()
    sources = [source] if other is None else ([other, source] if order == 'first' else [source, other])
    if order == 'duplicate':
        sources.append(source)
    result = scan(payload, sources, cmdline=cmdline)
    label = f'boot/{source}/{other}/{order}/{cmdline}'
    assert tuple(d.path for d in result.selectable) == (() if other else ('/dev/sda',)), label
    record(label, result)

# Equivalent tree/flat representations and inventory order preserve bound
# identity (pure representation changes must not be invented hot-swaps).
for (name, transport), permutation in itertools.product((('sda', 'sata'), ('nvme0n1', 'nvme'), ('vda', 'virtio')), range(12)):
    tree, _, _ = machine(name, transport, 'tree')
    flat, _, _ = machine(name, transport, 'flat')
    random.Random(permutation).shuffle(flat['blockdevices'])
    left, right = scan(tree), scan(flat)
    assert disk_identity(left.selectable[0]) == disk_identity(right.selectable[0])
    assert_disk_identity(left.selectable[0], right)
    record(f'equivalent/{name}/{permutation}', right)

# Exhaustive adversarial three-disk token alphabet: any available token is
# unique across every other disk's confirmation token and accepted spelling.
alphabet = ('', 'AAAA1234', 'BBBB1234', '1234', '500', '1000', 'sda', 'WWN-0001', '0000')
for serials in itertools.product(alphabet, repeat=3):
    peers = tuple(Disk(path='/dev/' + name, name=name, model='Fake', serial=serial,
                       wwn='', size_bytes=size*1_000_000_000, size_gb_label=str(size),
                       kind=DiskKind.SSD, bus='SATA', label='')
                  for name, serial, size in zip(('sda', 'sdc', 'sdd'), serials, (500,500,1000)))
    specs = []
    for peer in peers:
        try:
            spec = confirm_spec(peer, peers)
        except SafetyError:
            specs.append(None)
        else:
            assert spec.token.casefold() not in {'sda','sdc','sdd'}
            assert token_matches(spec.token, spec)
            specs.append(spec)
    for a,b in itertools.combinations(specs,2):
        if a is not None and b is not None:
            assert not token_matches(a.token,b), (serials,a,b)
    observations.append(dict(case='tokens/'+repr(serials), available=[s.token if s else None for s in specs]))

assert not native_attempts, native_attempts
out = dict(cases=len(observations), native_attempts=native_attempts,
           cases_sha256=hashlib.sha256(json.dumps(observations,sort_keys=True).encode()).hexdigest(),
           observations=observations)
Path('/tmp/pass12-discovery/matrix.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='observations'},indent=2))
