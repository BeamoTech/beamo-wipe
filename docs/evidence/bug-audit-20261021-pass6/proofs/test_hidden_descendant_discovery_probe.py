"""Production discovery must not list targets from a hidden live-mount row."""
import pytest
from beamo_wipe import discover as discovery
from beamo_wipe import safety


def _disk(name, serial, tran):
    return dict(name=name, path='/dev/'+name, type='disk', serial=serial,
                tran=tran, size=16_000_000_000 if tran=='usb' else 128_000_000_000,
                ro=False, mountpoints=[], model='Fake disk', rota=False)

@pytest.mark.parametrize('cover', [False,True], ids=['normal','ancestor-cover'])
def test_production_discovery_refuses_hidden_live_mount(tmp_path, monkeypatch, cover):
    boot=_disk('sdz','FAKE-BOOT','usb')
    boot['children']=[dict(name='sdz1',path='/dev/sdz1',type='part',pkname='sdz',
                          size=16_000_000_000,ro=False,mountpoints=[],fstype='iso9660')]
    payload={'blockdevices':[boot,_disk('sda','FAKE-TARGET','sata')]}
    mountinfo=tmp_path/'mountinfo'
    mountinfo.write_text('1 0 0:1 / / rw - overlay overlay rw\n'
                        '3 1 8:1 / /run/live/medium rw - iso9660 /dev/sdz1 ro\n'
                        + ('4 1 0:4 / /run/live rw - tmpfs tmpfs rw\n' if cover else ''))
    monkeypatch.setattr(discovery,'MOUNTINFO_PATH',str(mountinfo))
    monkeypatch.setattr(discovery,'run_lsblk',lambda:payload)
    monkeypatch.setattr(discovery,'_run_findmnt',lambda path:None)
    monkeypatch.setattr(discovery,'read_cmdline',lambda:'boot=live')
    monkeypatch.setattr(safety,'assert_local_device_transport',lambda path:None)
    result=discovery.discover(env={})
    assert [disk.path for disk in result.selectable] == ([] if cover else ['/dev/sda'])
    assert result.boot_identified is (not cover)
