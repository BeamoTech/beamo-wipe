"""A development preflight must refuse unknown Linux markers cleanly."""
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('pass7_dev_probe', '/workspace/beamo-wipe/dev.py')
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


@pytest.mark.parametrize('case,expected', [
    ('normal', False), ('live', True), ('denied', True), ('bad-utf8', True),
])
def test_linux_runtime_marker_is_a_boolean_refusal(case, expected, monkeypatch, tmp_path):
    monkeypatch.delenv('BEAMO_WIPE_LIVE', raising=False)
    monkeypatch.setattr(dev.sys, 'platform', 'linux')
    marker = tmp_path / 'cmdline'
    marker.write_bytes({'normal': b'quiet splash', 'live': b'boot=live quiet',
                        'denied': b'', 'bad-utf8': b'boot=live label=\xff'}[case])
    original_read = Path.read_text
    calls = []

    def read(path, *args, **kwargs):
        if str(path) != '/proc/cmdline':
            raise AssertionError('Unexpected native read')
        calls.append('read-marker')
        if case == 'denied':
            raise PermissionError('fake denied marker')
        return original_read(marker, *args, **kwargs)

    def mounted(path):
        assert str(path) == '/run/live/medium'
        calls.append('fake-mount-check')
        return False

    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(Path, 'is_mount', mounted)
    assert dev.live_environment() is expected
    assert calls[0] == 'read-marker'
