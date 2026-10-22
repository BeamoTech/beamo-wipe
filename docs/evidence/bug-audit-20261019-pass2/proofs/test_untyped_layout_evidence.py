"""Unrecognized root-level device types cannot discard a candidate's layout evidence."""
import copy
from dataclasses import replace

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import assert_rediscovered_identity, disk_identity
from test_discovery_observation_fallback_pass16 import _boot, _disk, fake_machine  # noqa: F401

ROUTES = ('direct', 'injected', 'production-metadata-stub')


def payload(kind, uuid, *, bound=False):
    part = dict(name='sda1', path='/dev/sda1', type=kind, size=120_000_000_000,
                fstype='ext4', uuid=uuid, model='', ro=False, mountpoints=[])
    if bound:
        part['pkname'] = 'sda'
    return {'blockdevices': [_boot(), _disk('sda'), part]}


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('kind', (None, '', 'unknown', 'unexpected-volume'))
def test_unknown_type_cannot_hide_unbound_filesystem_identity(fake_machine, route, kind):
    old_payload = payload(kind, 'VOLUME-A')
    new_payload = payload(kind, 'VOLUME-B')
    try:
        old = fake_machine(old_payload, route)
        new = fake_machine(new_payload, route)
    except ValueError:
        assert route == 'direct'
        return
    before = next((d for d in old.selectable if d.path == '/dev/sda'), None)
    after = next((d for d in new.selectable if d.path == '/dev/sda'), None)
    assert before is None or after is None or disk_identity(before) != disk_identity(after)


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('kind', ('part', 'crypt', 'dm', 'lvm'))
def test_existing_recognized_unbound_type_is_refused(fake_machine, route, kind):
    try:
        result = fake_machine(payload(kind, 'VOLUME-A'), route)
    except ValueError:
        assert route == 'direct'
        return
    assert not result.selectable


@pytest.mark.parametrize('route', ROUTES)
def test_valid_bound_partition_retains_uuid_change(fake_machine, route):
    old = fake_machine(payload('part', 'VOLUME-A', bound=True), route)
    new = fake_machine(payload('part', 'VOLUME-B', bound=True), route)
    assert disk_identity(old.selectable[0]) != disk_identity(new.selectable[0])
