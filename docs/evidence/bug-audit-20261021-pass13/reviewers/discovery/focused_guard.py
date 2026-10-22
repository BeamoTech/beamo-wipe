"""Guard all focused cases from native inventory and physical metadata I/O."""
import json
import os
import posixpath
from pathlib import Path
from collections import Counter

import pytest

COUNTS = Counter()


@pytest.fixture(autouse=True)
def only_synthetic_machine(monkeypatch):
    from beamo_wipe import discover, safety
    realpath, lstat = os.path.realpath, os.lstat
    def fake_realpath(path, *args, **kwargs):
        value = os.fspath(path)
        if value.startswith(('/dev/', '/sys/')):
            COUNTS['synthetic_realpath'] += 1
            return posixpath.normpath(value)
        return realpath(path, *args, **kwargs)
    def fake_lstat(path, *args, **kwargs):
        if os.fspath(path).startswith(('/dev/', '/sys/')):
            COUNTS['synthetic_lstat'] += 1
            raise FileNotFoundError(os.fspath(path))
        return lstat(path, *args, **kwargs)
    def forbidden(name):
        def call(*args, **kwargs):
            COUNTS['forbidden_'+name] += 1
            raise AssertionError('native acquisition forbidden: '+name)
        return call
    monkeypatch.setattr(os.path, 'realpath', fake_realpath)
    monkeypatch.setattr(os, 'lstat', fake_lstat)
    for name in ('run_lsblk','read_mount_sources','read_cmdline'):
        monkeypatch.setattr(discover, name, forbidden(name))
    monkeypatch.setattr(safety, 'assert_local_device_transport', forbidden('transport'))
    monkeypatch.setattr('beamo_wipe.diagnostics.log_diag',lambda *a,**kw:None)
    monkeypatch.setattr('beamo_wipe.diagnostics.emit_serial_marker',lambda *a,**kw:None)


def pytest_sessionfinish(session, exitstatus):
    Path('/workspace/beamo-tools/audit-pass13-20261021/discovery/focused-native-guard.json').write_text(
        json.dumps(dict(COUNTS),indent=2,sort_keys=True)+'\n')
