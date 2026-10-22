"""Fake inventory: presentation fallback must not erase changes in raw MODEL."""
import copy
import importlib
import os
from unittest.mock import patch

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError, assert_rediscovered_identity, disk_identity

d = importlib.import_module('beamo_wipe.discover')


def payload(model, label):
    return {'blockdevices': [
        {'name': 'sdz', 'path': '/dev/sdz', 'type': 'disk', 'size': 16_000_000_000,
         'tran': 'usb', 'serial': 'FAKE-BOOT', 'model': 'Fake boot', 'ro': False,
         'mountpoints': ['/run/live/medium']},
        {'name': 'sda', 'path': '/dev/sda', 'type': 'disk', 'size': 128_000_000_000,
         'tran': 'sata', 'serial': '', 'model': model, 'label': label,
         'ro': False, 'mountpoints': []},
    ]}


def scan(data, route):
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN': '1'}):
        if route == 'direct':
            return d.parse_lsblk_json(data, boot_path='/dev/sdz')
        if route == 'injected':
            return d.discover(lsblk_payload=data, mount_sources=['/dev/sdz'], env={})
        with patch.object(d, 'run_lsblk', return_value=data):
            return d.discover(mount_sources=['/dev/sdz'], cmdline='', env={})


def request(result):
    target = result.selectable[0]
    return WipeRequest(device=target.path, method=MethodId.EVERYDAY,
        boot_device=result.boot.path, logfile='/tmp/beamo-wipe/fake.log',
        device_identity=disk_identity(target), boot_identity=disk_identity(result.boot))


@pytest.mark.parametrize('route', ('direct', 'injected', 'production-metadata-stub'))
@pytest.mark.parametrize('label,fallback', (('Owner Data', 'Owner Data'), ('', 'Unknown model')))
def test_raw_model_change_hidden_by_presentation_is_refused(route, label, fallback):
    old = scan(payload('', label), route)
    new = scan(payload(fallback, label), route)
    assert old.boot_identified and new.boot_identified
    before, after = old.selectable[0], new.selectable[0]
    assert before.model == after.model == fallback
    assert before.raw_model == '' and after.raw_model == fallback
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN': '1'}):
        with pytest.raises(SafetyError, match='identity changed'):
            assert_rediscovered_identity(request(old), new)


@pytest.mark.parametrize('route', ('direct', 'injected', 'production-metadata-stub'))
def test_controls_preserve_accept_and_refuse_model_change(route):
    old = scan(payload('Original model', 'Owner Data'), route)
    same = scan(payload('Original model', 'Owner Data'), route)
    changed = scan(payload('Different model', 'Owner Data'), route)
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN': '1'}):
        assert_rediscovered_identity(request(old), same)
        with pytest.raises(SafetyError, match='identity changed'):
            assert_rediscovered_identity(request(old), changed)
