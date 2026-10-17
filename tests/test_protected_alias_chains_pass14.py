"""Boot and mounted aliases remain protected through mixed hardware evidence."""
from dataclasses import replace
import importlib
import itertools

import pytest

from beamo_wipe.safety import (
    SafetyError, assert_boot_excluded, assert_disk_identity, confirm_spec, listed_disks,
)

discovery = importlib.import_module('beamo_wipe.discover')
X = '50014ee20aa00001'
Y = '50014ee20aa00002'
CHAINS = {
    'root_missing': [('FAKE-A', ''), ('FAKE-A', '0x' + X), ('FAKE-C', X)],
    'leaf_missing': [('FAKE-A', X), ('FAKE-B', '0x' + X), ('FAKE-B', '')],
    'distinct': [('FAKE-A', X), ('FAKE-A', Y), ('FAKE-C', Y)],
    'contrary_through_missing': [('FAKE-A', X), ('FAKE-A', ''), ('FAKE-A', Y)],
    'placeholder': [('UNKNOWN', ''), ('UNKNOWN', X), ('FAKE-C', X)],
    'unrelated': [('FAKE-A', ''), ('FAKE-B', X), ('FAKE-C', X)],
}


def _scan(monkeypatch, kind, chain, layout, order):
    def forbidden(*_a, **_k):
        raise AssertionError('Injected discovery reached native acquisition')
    for name in ('run_lsblk', 'read_mount_sources', 'read_cmdline'):
        monkeypatch.setattr(discovery, name, forbidden)
    rows = []
    for i, (name, (serial, wwn)) in enumerate(zip(('sdb', 'sdc', 'sdd'), CHAINS[chain])):
        mounts = ['/run/live/medium' if kind == 'boot' else '/media/fake-data'] if i == 0 else []
        row = dict(name=name, path='/dev/' + name, type='disk', tran='usb' if i == 0 and kind == 'boot' else 'sata',
                   size=128_000_000_000, serial=serial, wwn=wwn, ro=False, mountpoints=[])
        if layout == 'whole':
            row['mountpoints'] = mounts
        else:
            row['children'] = [dict(name=name+'1', path='/dev/'+name+'1', type='part', pkname=name,
                                    size=64_000_000_000, fstype='ext4', mountpoints=mounts)]
        rows.append(row)
    boot = rows[0]
    ordered = [rows[i] for i in order]
    if kind == 'mounted':
        boot = dict(name='sdz', path='/dev/sdz', type='disk', tran='usb', size=16_000_000_000,
                    serial='FAKE-BOOT', wwn='50014ee20aa00009', ro=False, mountpoints=['/run/live/medium'])
        ordered.append(boot)
    source = boot['path'] + ('1' if kind == 'boot' and layout == 'partition' else '')
    result = discovery.discover(lsblk_payload={'blockdevices': ordered}, mount_sources=[source], cmdline='', env={})
    assert result.boot_identified and result.boot.path == boot['path']
    assert result.boot.path not in {d.path for d in result.selectable}
    return result


@pytest.mark.parametrize('order', list(itertools.permutations(range(3))))
@pytest.mark.parametrize('layout', ['whole', 'partition'])
@pytest.mark.parametrize('kind', ['boot', 'mounted'])
@pytest.mark.parametrize('chain', list(CHAINS))
def test_composed_protection_preserves_stronger_contrary_wwns(monkeypatch, chain, kind, layout, order):
    result = _scan(monkeypatch, kind, chain, layout, order)
    leaf = next(d for d in result.disks if d.path == '/dev/sdd')
    protected = chain in {'root_missing', 'leaf_missing'}
    assert (leaf.path in {d.path for d in result.selectable}) is not protected
    if protected:
        assert leaf.mountpoints
        if kind == 'boot':
            assert leaf.is_boot
        with pytest.raises(SafetyError):
            assert_disk_identity(leaf, result)
    else:
        assert not leaf.is_boot and not leaf.mountpoints
        assert_disk_identity(leaf, result)
        assert confirm_spec(leaf, listed_disks(result)).token
    assert_boot_excluded(result)


@pytest.mark.parametrize('order', list(itertools.permutations(range(3))))
@pytest.mark.parametrize('layout', ['whole', 'partition'])
@pytest.mark.parametrize('chain', ['root_missing', 'leaf_missing'])
def test_final_boot_guard_rechecks_complete_alias_context(monkeypatch, chain, layout, order):
    result = _scan(monkeypatch, 'boot', chain, layout, order)
    leaf = next(d for d in result.disks if d.path == '/dev/sdd')
    unsafe = replace(leaf, is_boot=False, mountpoints=())
    observations = tuple(unsafe if d.path == unsafe.path else d for d in result.disks)
    injected = replace(result, disks=observations, selectable=(unsafe,))
    with pytest.raises(SafetyError, match='Boot USB appeared'):
        assert_boot_excluded(injected)
