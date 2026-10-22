"""Protected aliases in an otherwise authorized inventory must remain journalable."""
from dataclasses import replace

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import assert_boot_excluded
from beamo_wipe.session_recovery import SessionStore
from test_discovery_observation_fallback_pass16 import _boot, _disk, fake_machine  # noqa: F401

ROUTES = ('direct', 'injected', 'production-metadata-stub')
BOOT = '00000000-0000-0000-0000-000000000001'
BUILD = 'a' * 64


def scan(fake_machine, route, mode):
    boot = _boot()
    alias = _disk('sdc', tran='usb')
    if mode == 'wwn':
        alias['wwn'] = boot['wwn']
    if mode == 'serial':
        boot['wwn'] = alias['wwn'] = ''
        alias['serial'] = boot['serial']
    if mode == 'distinct-wwn':
        alias['serial'] = boot['serial']
    return fake_machine({'blockdevices': [boot, _disk('sda'), alias]}, route)


def request(discovery, directory):
    return WipeRequest('/dev/sda', MethodId.QUICK_ZERO, discovery.boot.path,
                       str(directory / 'nwipe-fake.log'))


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('mode', ('wwn', 'serial'))
def test_protected_boot_alias_does_not_block_unrelated_target_journal(fake_machine, tmp_path, route, mode):
    discovery = scan(fake_machine, route, mode)
    assert_boot_excluded(discovery)
    assert [d.path for d in discovery.selectable] == ['/dev/sda']
    assert {d.path for d in discovery.disks if d.is_boot} == {'/dev/sdz', '/dev/sdc'}
    store = SessionStore(tmp_path / 'private', boot=BOOT, build=BUILD).open()
    try:
        store.arm(discovery, request(discovery, store.directory))
        assert store.record['phase'] == 'armed'
    finally:
        store.close()


@pytest.mark.parametrize('route', ROUTES)
def test_distinct_wwn_reused_serial_control_still_arms(fake_machine, tmp_path, route):
    discovery = scan(fake_machine, route, 'distinct-wwn')
    assert_boot_excluded(discovery)
    assert {d.path for d in discovery.disks if d.is_boot} == {'/dev/sdz'}
    store = SessionStore(tmp_path / 'private', boot=BOOT, build=BUILD).open()
    try:
        store.arm(discovery, request(discovery, store.directory))
        assert store.record['phase'] == 'armed'
    finally:
        store.close()
