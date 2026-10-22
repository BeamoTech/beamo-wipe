"""Fake mountinfo only: a block-looking source is not block-backed media."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from beamo_wipe import discover as D
from beamo_wipe import safety as S
import beamo_wipe.app
import beamo_wipe.nwipe_runner


CASES = [
    ('tmpfs', False), ('ramfs', False), ('overlay', False), ('proc', False),
    ('iso9660', True), ('vfat', True), ('ext4', True),
]


def table(filesystem):
    dev = '8:17' if filesystem in {'iso9660', 'vfat', 'ext4'} else '0:48'
    return (
        '1 0 0:1 / / rw - overlay overlay rw\n'
        f'2 1 {dev} / /run/live/medium rw - {filesystem} /dev/sdb1 rw\n'
    )


def forbid_native(monkeypatch):
    effects = []
    def forbidden(*args, **kwargs):
        effects.append((args, kwargs))
        raise AssertionError('Real process, device inventory or power action forbidden')
    for name in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.app._shutdown',
                 'beamo_wipe.nwipe_runner.NwipeRunner.start'):
        monkeypatch.setattr(name, forbidden)
    return effects


@pytest.mark.parametrize('filesystem,expected', CASES)
def test_live_gate_requires_block_backed_filesystem(monkeypatch, filesystem, expected):
    effects = forbid_native(monkeypatch)
    observed = S.is_live_environment(cmdline='boot=live', env={}, mountinfo_text=table(filesystem))
    assert not effects
    assert observed is expected


@pytest.mark.parametrize('filesystem,expected', CASES)
def test_real_nwipe_gate_refuses_non_media_filesystem(monkeypatch, tmp_path, filesystem, expected):
    effects = forbid_native(monkeypatch)
    fake = tmp_path/'mountinfo';fake.write_text(table(filesystem))
    monkeypatch.setattr(D, 'MOUNTINFO_PATH', str(fake))
    monkeypatch.setattr(D, 'read_cmdline', lambda: 'boot=live')
    if expected:
        S.require_real_live_for_nwipe(env={})
    else:
        with pytest.raises(S.SafetyError):
            S.require_real_live_for_nwipe(env={})
    assert not effects


@pytest.mark.parametrize('filesystem,expected', CASES)
def test_production_discovery_does_not_protect_pseudo_source_disk(monkeypatch, tmp_path, filesystem, expected):
    effects = forbid_native(monkeypatch)
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE', raising=False)
    fake = tmp_path/'mountinfo';fake.write_text(table(filesystem))
    monkeypatch.setattr(D, 'MOUNTINFO_PATH', str(fake))
    monkeypatch.setattr(D, 'read_cmdline', lambda: 'boot=live')
    payload = {'blockdevices':[
        {'name':'sdb','path':'/dev/sdb','type':'disk','size':16000000000,
         'tran':'usb','rota':False,'ro':False,'mountpoints':[],
         'serial':'FAKE-BOOT','model':'Fake boot','children':[
             {'name':'sdb1','path':'/dev/sdb1','type':'part','size':15000000000,
              'pkname':'sdb','ro':False,'mountpoints':[],'fstype':filesystem},
         ]},
        {'name':'sda','path':'/dev/sda','type':'disk','size':256000000000,
         'tran':'sata','rota':False,'ro':False,'mountpoints':[],
         'serial':'FAKE-DATA','model':'Fake data'},
    ]}
    monkeypatch.setattr(D, 'run_lsblk', lambda: payload)
    def fake_findmnt(mountpoint):
        return SimpleNamespace(returncode=0 if mountpoint=='/run/live/medium' else 1,
                               stdout='/dev/sdb1\n' if mountpoint=='/run/live/medium' else '',stderr='')
    monkeypatch.setattr(D, '_run_findmnt', fake_findmnt)
    result = D.discover(env={})
    assert not effects
    if expected:
        assert result.boot_identified and result.boot.path=='/dev/sdb'
        assert [disk.path for disk in result.selectable]==['/dev/sda']
    else:
        assert not result.boot_identified and not result.selectable
