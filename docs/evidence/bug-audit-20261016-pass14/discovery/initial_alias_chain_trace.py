"""Concrete fake-only trace of composed boot/mounted hardware aliases."""
from __future__ import annotations
import builtins
import hashlib
import importlib
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
sys.path.insert(0, str(Path.cwd() / 'src'))
d = importlib.import_module('beamo_wipe.discover')
import beamo_wipe.safety as s
import beamo_wipe.diagnostics as diagnostics
attempts = []
def forbidden(*args, **kwargs):
    attempts.append(repr(args[:1]))
    raise AssertionError('Native acquisition forbidden')
subprocess.run = subprocess.Popen = forbidden
d.run_lsblk = d.read_mount_sources = d.read_cmdline = forbidden
s.assert_local_device_transport = forbidden
original_open = builtins.open
original_io_open = io.open
original_lstat = os.lstat
def guarded_open(original):
    def wrapped(path, *args, **kwargs):
        if str(path).startswith(('/dev/', '/proc/', '/sys/')):
            return forbidden(path)
        return original(path, *args, **kwargs)
    return wrapped
builtins.open = guarded_open(original_open)
io.open = guarded_open(original_io_open)
def guarded_lstat(path, *args, **kwargs):
    if str(path).startswith(('/dev/', '/proc/', '/sys/')):
        return forbidden(path)
    return original_lstat(path, *args, **kwargs)
os.lstat = guarded_lstat
os.path.realpath = lambda value, *args, **kwargs: str(value)
diagnostics.log_diag = diagnostics.emit_serial_marker = lambda *args, **kwargs: None

def node(name, serial, wwn, mounts=()):
    return dict(name=name, path='/dev/' + name, type='disk', tran='sata',
                size=128_000_000_000, serial=serial, wwn=wwn,
                model='Fixture ' + name, mountpoints=list(mounts), ro=False)

records = []
# Missing root WWN with a serial leg followed by a stronger WWN leg;
# known root WWN with a WWN leg followed by a missing-WWN serial leg.
for kind, chain in itertools.product(('boot', 'mounted'), ('root-missing-wwn', 'leaf-missing-wwn', 'distinct-wwn-control', 'placeholder-control', 'no-chain-control')):
    if chain == 'root-missing-wwn':
        ids = [('ROOT-SERIAL', ''), ('ROOT-SERIAL', '0x50014ee20aa00001'), ('OTHER-SERIAL', '50014ee20aa00001')]
    elif chain == 'leaf-missing-wwn':
        ids = [('ROOT-SERIAL', '0x50014ee20aa00001'), ('OTHER-SERIAL', '50014ee20aa00001'), ('OTHER-SERIAL', '')]
    elif chain == 'distinct-wwn-control':
        ids = [('ROOT-SERIAL', 'wwn-root'), ('ROOT-SERIAL', 'wwn-other'), ('OTHER-SERIAL', 'wwn-other')]
    elif chain == 'no-chain-control':
        ids = [('ROOT-SERIAL', ''), ('BRIDGE-SERIAL', 'wwn-other'), ('OTHER-SERIAL', 'wwn-other')]
    else:
        ids = [('UNKNOWN', ''), ('UNKNOWN', 'wwn-other'), ('OTHER-SERIAL', 'wwn-other')]
    mounts = ['/run/live/medium'] if kind == 'boot' else ['/media/data']
    a, b, c = [node(name, serial, wwn, mounts if index == 0 else ())
               for index, (name, (serial, wwn)) in enumerate(zip(('sdb', 'sdc', 'sdd'), ids))]
    boot = a if kind == 'boot' else node('sdz', 'BOOT-UNRELATED', 'wwn-boot', ['/run/live/medium'])
    all_rows = [a, b, c] if kind == 'boot' else [a, b, c, boot]
    for order in itertools.permutations(range(3)):
        rows = [all_rows[index] for index in order]
        if kind == 'mounted':
            rows.append(boot)
        result = d.discover(lsblk_payload={'blockdevices': rows}, mount_sources=[boot['path']], cmdline='', env={})
        assert result.boot_identified and result.boot is not None
        mapped = {disk.path: disk for disk in result.disks}
        root, bridge, leaf = [mapped['/dev/' + name] for name in ('sdb', 'sdc', 'sdd')]
        controls = chain.endswith('control')
        expected_leaf_selectable = controls
        leaf_selectable = leaf.path in [disk.path for disk in result.selectable]
        try:
            token = s.confirm_spec(leaf, s.listed_disks(result)).token
        except s.SafetyError as exc:
            token = {'refused': str(exc)}
        try:
            s.assert_boot_excluded(result)
            full_boot_gate = 'accepts'
        except s.SafetyError as exc:
            full_boot_gate = {'refused': str(exc)}
        try:
            s.assert_disk_identity(leaf, result)
            leaf_identity_gate = 'accepts'
        except s.SafetyError as exc:
            leaf_identity_gate = {'refused': str(exc)}
        records.append(dict(payload={'blockdevices': rows}, kind=kind, chain=chain, order=order,
                            root_bridge_alias=s.possible_hardware_alias(root, bridge),
                            bridge_leaf_alias=s.possible_hardware_alias(bridge, leaf),
                            root_leaf_alias=s.possible_hardware_alias(root, leaf),
                            expected_leaf_selectable=expected_leaf_selectable,
                            actual_leaf_selectable=leaf_selectable,
                            violation=leaf_selectable != expected_leaf_selectable,
                            confirm_token=token, boot_exclusion_gate=full_boot_gate,
                            leaf_identity_gate=leaf_identity_gate,
                            boot_path=result.boot.path,
                            targets=[disk.path for disk in result.selectable],
                            disks=[dict(path=x.path, serial=x.serial, wwn=x.wwn,
                                        is_boot=x.is_boot, mounts=x.mountpoints) for x in result.disks]))
assert not attempts
out = dict(cases=len(records), violations=sum(record['violation'] for record in records),
           controls=sum(not record['violation'] for record in records),
           native_attempts=attempts,
           source_sha256={name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                          for name in ('src/beamo_wipe/discover.py', 'src/beamo_wipe/safety.py')},
           observations=records)
Path('/tmp/pass14-discovery/alias-chain-trace.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({key: value for key, value in out.items() if key != 'observations'}, indent=2))
