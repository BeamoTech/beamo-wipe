"""PASS11: protected alias closure across ineligible rows and capacity edges.

Every inventory is synthetic. Public injected and production-metadata routes
exercise actual parser/eligibility/identity guards; the production acquisition
is replaced with the same fake payload and all native I/O is forbidden.
"""
from pathlib import Path
import builtins
import copy
import hashlib
import io
import itertools
import json
import os
import sys

from pytest import MonkeyPatch

sys.path.insert(0, '/workspace/beamo-wipe/src')
from beamo_wipe import discover as D, safety as S

ROOT = Path(__file__).parent
REPO = Path('/workspace/beamo-wipe')
X, Y = '50014ee20aa00001', '50014ee20aa00002'
# Explicit semantic oracle: the leaf can or cannot be an alias of the anchor.
# Distinct known WWNs defeat a shared serial, even through a missing-WWN row.
CHAINS = {
    'serial-to-wwn': ((('FAKE-A', ''), ('FAKE-A', X), ('FAKE-B', X)), True),
    'wwn-to-serial': ((('FAKE-A', X), ('FAKE-B', X), ('FAKE-B', '')), True),
    'contrary-through-missing': ((('FAKE-A', X), ('FAKE-A', ''), ('FAKE-A', Y)), False),
    'unconnected': ((('FAKE-A', X), ('FAKE-B', Y), ('FAKE-C', Y)), False),
    'placeholder-is-not-id': ((('UNKNOWN', ''), ('UNKNOWN', X), ('FAKE-C', X)), False),
    'direct-prefixed-wwn': ((('FAKE-A', X), ('FAKE-B', Y), ('FAKE-C', '0x'+X)), True),
    'reused-serial-distinct-wwn': ((('FAKE-A', X), ('FAKE-A', Y), ('FAKE-A', Y)), False),
    'serial-only-chain': ((('FAKE-A', ''), ('FAKE-A', ''), ('FAKE-A', '')), True),
}
TARGETS = {
    'under-half-gb': (499_999_999, False, '0', 'under 1 GB'),
    'half-gb': (500_000_000, False, '1', '1 GB'),
    'half-up-2.5gb': (2_500_000_000, False, '3', '3 GB'),
    'read-only': (1_500_000_000, True, '2', '2 GB'),
    'zero': (0, False, '0', '0 GB'),
}
metrics = {'states': 0, 'calls': 0, 'direct_calls': 0, 'injected_calls': 0,
           'production_metadata_calls': 0, 'positive_leaf_observations': 0,
           'protected_leaf_refusals': 0, 'capacity_or_readonly_refusals': 0,
           'capacity_boundary_checks': 0, 'unique_target_identity_checks': 0,
           'boot_guard_checks': 0, 'native_callbacks': 0, 'mismatches': []}


def disk(name, serial, wwn, **changes):
    row = dict(name=name, path='/dev/'+name, type='disk', tran='sata',
               size=128_000_000_000, model='Fake '+name, vendor='Fake vendor',
               serial=serial, wwn=wwn, ro=False, mountpoints=[], rota=False)
    row.update(changes)
    return row


def inventory(chain, kind, layout, bridge_kind, target_kind, reverse):
    identifiers, protected = CHAINS[chain]
    rows = [disk(name, *ids) for name, ids in zip(('sdb', 'sdc', 'sdd'), identifiers)]
    rows[0]['mountpoints'] = ['/run/live/medium' if kind == 'boot' else '/media/fake-owner-data']
    if kind == 'boot':
        rows[0].update(tran='usb', size=16_000_000_000)
    if bridge_kind == 'read-only':
        rows[1]['ro'] = True
    elif bridge_kind == 'zero-capacity':
        rows[1]['size'] = 0
    elif bridge_kind == 'hidden-rom':
        rows[1]['type'] = 'rom'
    elif bridge_kind == 'malformed-model':
        rows[1]['model'] = 'M'*129
    elif bridge_kind == 'pathless':
        rows[1].update(name='', path='')
    size, locked, label, phrase = TARGETS[target_kind]
    rows[2].update(size=size, ro=locked)
    anchor = rows[0]
    if layout != 'whole':
        mounts = anchor['mountpoints']
        anchor['mountpoints'] = []
        part = dict(name='sdb1', path='/dev/sdb1', type='part', pkname='sdb',
                    size=8_000_000_000, fstype='ext4', ro=False, mountpoints=mounts)
        if layout == 'tree-partition':
            anchor['children'] = [part]
        else:
            rows.append(part)
    if kind == 'boot':
        boot = anchor
    else:
        boot = disk('sdz', 'FAKE-UNRELATED-BOOT', '50014ee20aa00009',
                    tran='usb', size=16_000_000_000, mountpoints=['/run/live/medium'])
        rows.append(boot)
    if reverse:
        rows.reverse()
    source = '/dev/sdb1' if kind == 'boot' and layout != 'whole' else boot['path']
    return {'blockdevices': rows}, boot['path'], source, protected, (size, locked, label, phrase)


with MonkeyPatch.context() as patch:
    patch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    patch.delenv('BEAMO_WIPE_LIVE', raising=False)
    original_realpath = os.path.realpath

    def realpath(path, *args, **kwargs):
        value = os.fsdecode(path)
        if value.startswith(('/dev/', '/sys/', '/proc/')):
            return value
        return original_realpath(path, *args, **kwargs)

    patch.setattr(os.path, 'realpath', realpath)

    def forbidden(*_a, **_k):
        metrics['native_callbacks'] += 1
        raise AssertionError('Native acquisition forbidden in fake matrix')

    def guarded(original):
        def checked(path, *args, **kwargs):
            if not isinstance(path, int):
                text = os.fsdecode(path)
                if text in {'/dev', '/sys', '/proc'} or text.startswith(('/dev/', '/sys/', '/proc/')):
                    forbidden()
            return original(path, *args, **kwargs)
        return checked

    for name in ('run_lsblk', 'read_mount_sources', 'read_cmdline', '_run_findmnt'):
        patch.setattr(D, name, forbidden)
    for name in ('run', 'Popen'):
        patch.setattr(D.subprocess, name, forbidden)
    patch.setattr(builtins, 'open', guarded(builtins.open))
    patch.setattr(io, 'open', guarded(io.open))
    patch.setattr(os, 'open', guarded(os.open))
    patch.setattr(os, 'lstat', guarded(os.lstat))
    patch.setattr('beamo_wipe.diagnostics.log_diag', lambda *_a, **_k: None)
    patch.setattr('beamo_wipe.diagnostics.emit_serial_marker', lambda *_a, **_k: None)
    for values in itertools.product(CHAINS, ('boot', 'mounted'),
                                   ('whole', 'tree-partition', 'flat-partition'),
                                   ('visible', 'read-only', 'zero-capacity', 'hidden-rom', 'malformed-model', 'pathless'),
                                   TARGETS, (False, True)):
        payload, boot, source, protected, target = inventory(*values)
        size, locked, label, phrase = target
        eligible = not protected and size > 0 and not locked
        metrics['states'] += 1
        for route in ('direct', 'injected', 'production_metadata'):
            try:
                if route == 'direct':
                    result = D.parse_lsblk_json(copy.deepcopy(payload), boot_path=boot)
                elif route == 'injected':
                    result = D.discover(lsblk_payload=copy.deepcopy(payload), mount_sources=[source], cmdline='', env={})
                else:
                    with patch.context() as local:
                        local.setattr(D, 'run_lsblk', lambda: copy.deepcopy(payload))
                        result = D.discover(mount_sources=[source], cmdline='', env={})
                metrics['calls'] += 1
                metrics[route+'_calls'] += 1
                assert result.boot_identified and result.boot.path == boot and not result.error
                S.assert_boot_excluded(result)
                metrics['boot_guard_checks'] += 1
                leaf = next(item for item in result.disks if item.path == '/dev/sdd')
                assert (leaf.size_bytes, leaf.size_gb_label, leaf.size_phrase) == (size, label, phrase)
                metrics['capacity_boundary_checks'] += 1
                observed = leaf.path in {item.path for item in S.selectable_disks(result)}
                assert observed is eligible, (values, route, observed, eligible)
                if eligible:
                    S.assert_disk_identity(leaf, result)
                    metrics['unique_target_identity_checks'] += 1
                    metrics['positive_leaf_observations'] += 1
                else:
                    try:
                        S.assert_disk_identity(leaf, result)
                    except S.SafetyError:
                        pass
                    else:
                        raise AssertionError('Ineligible leaf passed identity boundary')
                    metrics['protected_leaf_refusals' if protected else 'capacity_or_readonly_refusals'] += 1
                if protected:
                    assert leaf.mountpoints
                    if values[1] == 'boot':
                        assert leaf.is_boot
            except Exception as exc:
                metrics['mismatches'].append({'state': values, 'route': route, 'error': type(exc).__name__, 'detail': str(exc)})

metrics['source_sha256'] = {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest()
                           for name in ('src/beamo_wipe/discover.py', 'src/beamo_wipe/safety.py',
                                        'src/beamo_wipe/models.py', 'src/beamo_wipe/inventory.py',
                                        'src/beamo_wipe/identity.py')}
(ROOT/'protected-alias-capacity-matrix.json').write_text(json.dumps(metrics, indent=2)+'\n')
print(json.dumps(metrics))
assert not metrics['mismatches'] and metrics['native_callbacks'] == 0
