"""Fake-only source ordering, typed identity and rediscovery invariants."""
from __future__ import annotations
import builtins
import copy
import hashlib
import importlib
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import replace

os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
sys.path.insert(0, str(Path.cwd() / 'src'))
d = importlib.import_module('beamo_wipe.discover')
import beamo_wipe.safety as s
import beamo_wipe.diagnostics as diagnostics
from beamo_wipe.models import MethodId, WipeRequest

records = []
native_attempts = []

def forbidden(*args, **kwargs):
    native_attempts.append(repr(args[:1]))
    raise AssertionError('Native acquisition forbidden')

subprocess.run = subprocess.Popen = forbidden
d.run_lsblk = d.read_mount_sources = d.read_cmdline = forbidden
s.assert_local_device_transport = forbidden

def guard_open(original):
    def wrapped(path, *args, **kwargs):
        if str(path).startswith(('/proc/', '/sys/', '/dev/')):
            native_attempts.append(str(path))
            raise AssertionError('Machine read forbidden')
        return original(path, *args, **kwargs)
    return wrapped

builtins.open = guard_open(builtins.open)
io.open = guard_open(io.open)
original_lstat = os.lstat

def lstat(path, *args, **kwargs):
    if str(path).startswith(('/proc/', '/sys/', '/dev/')):
        return forbidden(path)
    return original_lstat(path, *args, **kwargs)

os.lstat = lstat
aliases = {
    '/dev/disk/by-label/Beamo\\x20Wipe': '/dev/sdb1',
    '/dev/disk/by-uuid/BOOT-UUID': '/dev/sdb1',
    '/dev/disk/by-partuuid/BOOT-PART-UUID': '/dev/sdb1',
    '/dev/disk/by-partlabel/Live\\x20Medium': '/dev/sdb1',
}
# All node names are inert strings: no operating-system device lookup occurs.
os.path.realpath = lambda path, *args, **kwargs: aliases.get(str(path), str(path))
diagnostics.log_diag = diagnostics.emit_serial_marker = lambda *args, **kwargs: None

families = [('sda', 'sata'), ('nvme0n11', 'nvme'), ('mmcblk0', '')]
shapes = ['tree', 'flat']

def machine(name, tran, shape):
    suffix = 'p1' if name[-1].isdigit() else '1'
    part = dict(name=name + suffix, path='/dev/' + name + suffix,
                type='part', pkname=name, size=100_000_000_000,
                fstype='ntfs', uuid='TARGET-FS', partuuid='TARGET-PART',
                partlabel='Definitions', mountpoints=[])
    target = dict(name=name, path='/dev/' + name, type='disk', tran=tran,
                  size=128_000_000_000, serial='FAKE-TARGET', wwn='wwn-target',
                  model='Fixture disk', ro=False, mountpoints=[])
    bootpart = dict(name='sdb1', path='/dev/sdb1', type='part', pkname='sdb',
                    size=16_000_000_000, fstype='vfat', uuid='BOOT-UUID',
                    partuuid='BOOT-PART-UUID', label='Beamo Wipe',
                    partlabel='Live Medium', mountpoints=[])
    boot = dict(name='sdb', path='/dev/sdb', type='disk', tran='usb',
                size=16_000_000_000, serial='FAKE-BOOT', wwn='wwn-boot',
                model='Fixture boot', ro=False, mountpoints=[])
    rows = [target, boot]
    if shape == 'tree':
        target['children'] = [part]
        boot['children'] = [bootpart]
    else:
        rows.extend([part, bootpart])
    return {'blockdevices': rows}, target, part, boot, bootpart

sources = [
    ('direct-part', ['/dev/sdb1'], True),
    ('direct-disk', ['/dev/sdb'], True),
    ('label', ['LABEL=Beamo Wipe'], True),
    ('quoted-label', ['LABEL="Beamo Wipe"'], True),
    ('uuid', ['UUID=boot-uuid'], True),
    ('partuuid', ['PARTUUID=boot-part-uuid'], True),
    ('partlabel', ['PARTLABEL=Live Medium'], True),
    ('udev-label', ['/dev/disk/by-label/Beamo\\x20Wipe'], True),
    ('udev-uuid', ['/dev/disk/by-uuid/BOOT-UUID'], True),
    ('udev-partuuid', ['/dev/disk/by-partuuid/BOOT-PART-UUID'], True),
    ('udev-partlabel', ['/dev/disk/by-partlabel/Live\\x20Medium'], True),
    ('equivalent-triple', ['/dev/sdb1', 'UUID=BOOT-UUID', 'LABEL=Beamo Wipe'], True),
    ('repeated', ['/dev/sdb1', '/dev/sdb1'], True),
    ('wrong-case-label', ['LABEL=beamo wipe'], False),
    ('unknown-competing', ['/dev/sdb1', 'UUID=MISSING'], False),
    ('conflicting-target', ['/dev/sdb1', 'UUID=TARGET-FS'], False),
]

def scan(payload, observations):
    return d.discover(lsblk_payload=payload, mount_sources=observations,
                      cmdline='', env={})

def order_rows(payload, mode):
    rows = payload['blockdevices']
    if mode == 'reverse':
        rows.reverse()
    elif mode == 'rotate':
        rows[:] = rows[1:] + rows[:1]

for (name, tran), shape in itertools.product(families, shapes):
    baseline_payload, *_ = machine(name, tran, shape)
    baseline = scan(baseline_payload, ['/dev/sdb1'])
    assert baseline.boot_identified and baseline.boot.path == '/dev/sdb'
    assert [disk.path for disk in baseline.selectable] == ['/dev/' + name]
    target = baseline.selectable[0]
    initial_identity = s.disk_identity(target)
    assert target.contents == 'data'
    assert s.confirm_spec(target, s.listed_disks(baseline)).token == '128'
    request = WipeRequest(target.path, MethodId.EVERYDAY, baseline.boot.path,
                          '/tmp/pass14-discovery/inert.log',
                          device_identity=initial_identity,
                          boot_identity=s.disk_identity(baseline.boot))
    for mode, (source_id, observations, expected) in itertools.product(
        ('normal', 'reverse', 'rotate'), sources
    ):
        payload, *_ = machine(name, tran, shape)
        order_rows(payload, mode)
        if mode == 'reverse':
            observations = list(reversed(observations))
        result = scan(payload, observations)
        assert '/dev/sdb' not in [disk.path for disk in result.selectable]
        assert result.boot_identified is expected, (name, shape, mode, source_id, result)
        if expected:
            assert result.boot.path == '/dev/sdb'
            assert [disk.path for disk in result.selectable] == [target.path]
            assert s.disk_identity(result.selectable[0]) == initial_identity
            assert s.confirm_spec(result.selectable[0], s.listed_disks(result)).token == '128'
            s.assert_rediscovered_identity(request, result)
        else:
            assert result.selectable == () and result.error
        records.append(dict(case=f'source/{name}/{shape}/{mode}/{source_id}',
                            boot=result.boot_identified,
                            targets=[disk.path for disk in result.selectable]))

    mutations = [
        'normal', 'target-ro', 'target-mounted', 'partition-mounted',
        'serial-changed', 'wwn-changed', 'layout-changed', 'boot-serial-changed',
        'boot-wwn-changed', 'duplicate-equal', 'duplicate-ro', 'duplicate-mounted',
        'partition-parent-contradiction', 'shared-boot-wwn', 'shared-mounted-serial',
    ]
    for mode, change in itertools.product(('normal', 'reverse', 'rotate'), mutations):
        payload, root, part, boot, bootpart = machine(name, tran, shape)
        if change == 'target-ro': root['ro'] = True
        elif change == 'target-mounted': root['mountpoints'] = ['/mnt/data']
        elif change == 'partition-mounted': part['mountpoints'] = ['/mnt/data']
        elif change == 'serial-changed': root['serial'] = 'REPLACEMENT'
        elif change == 'wwn-changed': root['wwn'] = 'wwn-replacement'
        elif change == 'layout-changed': part['label'] = 'Replacement data'
        elif change == 'boot-serial-changed': boot['serial'] = 'REPLACEMENT-BOOT'
        elif change == 'boot-wwn-changed': boot['wwn'] = 'wwn-replacement-boot'
        elif change.startswith('duplicate-'):
            extra = copy.deepcopy(root)
            if change == 'duplicate-ro': extra['ro'] = True
            if change == 'duplicate-mounted': extra['mountpoints'] = ['/mnt/data']
            payload['blockdevices'].append(extra)
        elif change == 'partition-parent-contradiction': part['pkname'] = 'sdb'
        elif change == 'shared-boot-wwn': root['wwn'] = boot['wwn']
        elif change == 'shared-mounted-serial':
            root['wwn'] = ''
            other = dict(name='sdc', path='/dev/sdc', type='disk', tran='sata',
                         size=256_000_000_000, serial=root['serial'], wwn='',
                         ro=False, mountpoints=['/mnt/other'])
            payload['blockdevices'].append(other)
        order_rows(payload, mode)
        result = scan(payload, ['/dev/sdb1'])
        accepted = True
        try:
            s.assert_rediscovered_identity(request, result)
        except s.SafetyError:
            accepted = False
        assert accepted is (change == 'normal'), (name, shape, mode, change, result)
        assert '/dev/sdb' not in [disk.path for disk in result.selectable]
        records.append(dict(case=f'rediscovery/{name}/{shape}/{mode}/{change}',
                            accepted=accepted, boot=result.boot_identified,
                            targets=[disk.path for disk in result.selectable]))

assert not native_attempts
out = dict(cases=len(records), native_attempts=native_attempts,
           source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [Path('src/beamo_wipe/discover.py'),
                                       Path('src/beamo_wipe/safety.py'),
                                       Path('src/beamo_wipe/wizard.py')]},
           observations_sha256=hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(),
           observations=records)
Path('/tmp/pass14-discovery/permutation-matrix.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({key: value for key, value in out.items() if key != 'observations'}, indent=2))
