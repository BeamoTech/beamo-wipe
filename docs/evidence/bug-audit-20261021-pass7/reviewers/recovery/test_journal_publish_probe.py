"""Fake journal temp replacement must not silently discard its armed phase."""
import json
import os
import sys
from pathlib import Path

import pytest
sys.path.insert(0, '/workspace/beamo-wipe/tests')
from test_session_recovery import armed, BOOT, BUILD
from beamo_wipe.session_recovery import SessionStore, NAME
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize('swap', [False, True], ids=['normal-control','swapped-temporary'])
def test_arm_cannot_return_with_preflight_still_persisted(tmp_path, monkeypatch, swap, request):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    directory=tmp_path/'private'
    store=SessionStore(directory,boot=BOOT,build=BUILD).open()
    old=(directory/NAME).read_bytes()
    original_sync=os.fsync
    changed=[]
    def sync(fd):
        original_sync(fd)
        for path in directory.glob('.recovery-*'):
            if os.fstat(fd).st_ino==path.stat().st_ino and swap and not changed:
                changed.append(path.name)
                path.rename(directory/'retired-owned-temporary')
                path.write_bytes(old);path.chmod(0o600)
    monkeypatch.setattr(os,'fsync',sync)
    error=None
    try:
        try:
            armed(store)
        except SafetyError as exc:
            error=str(exc)
        disk_record=json.loads((directory/NAME).read_bytes())['payload']
        trace={'swap':swap,'changed':changed,'save_error':error,
               'memory_phase':store.record['phase'],'persisted_phase':disk_record['phase']}
        request.node.user_properties.append(('trace',json.dumps(trace)));print(json.dumps(trace))
        assert error is not None or disk_record['phase']=='armed',trace
        if not swap:assert error is None and store.record['phase']=='armed'
    finally:
        monkeypatch.setattr(os,'fsync',original_sync)
        store.close()
