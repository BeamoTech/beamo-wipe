"""Public startup blocks unreadable live-state encoding without native effects."""
import builtins
import json
from pathlib import Path

import pytest

import beamo_wipe.app as app
import beamo_wipe.nwipe_runner as runner
from beamo_wipe import discover as D
from beamo_wipe import safety as S


@pytest.mark.parametrize('case', ['normal-desktop', 'normal-live', 'bad-cmdline', 'bad-unrelated-mountpoint'])
def test_startup_decoding_failure_returns_blocked_status(tmp_path, monkeypatch, request, case):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE', raising=False)
    monkeypatch.setattr(S.sys, 'platform', 'linux')
    command = tmp_path/'cmdline'
    command.write_bytes(b'quiet' if case=='normal-desktop' else b'boot=live quiet')
    if case=='bad-cmdline':command.write_bytes(b'boot=live label=\xff')
    mounts = tmp_path/'mountinfo'
    data=(b'1 0 0:1 / / rw - overlay overlay rw\n'
          b'2 1 8:241 / /run/live/medium rw - iso9660 /dev/sdz1 rw\n')
    if case=='bad-unrelated-mountpoint':data+=b'3 1 8:33 / /media/\xff rw - ext4 /dev/sdc1 rw\n'
    mounts.write_bytes(data)
    monkeypatch.setattr(D, 'MOUNTINFO_PATH', str(mounts))
    real_open=builtins.open
    def proc_file(path, *args, **kwargs):
        if str(path)=='/proc/cmdline':return real_open(command, *args, **kwargs)
        return real_open(path, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', proc_file)
    forbidden=[]
    def no_native(*_args, **_kwargs):
        forbidden.append(True)
        raise AssertionError('Native device/process/power callback forbidden')
    for name in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk', 'beamo_wipe.discover._run_findmnt'):
        monkeypatch.setattr(name, no_native)
    monkeypatch.setattr(runner.NwipeRunner, 'start', no_native)
    monkeypatch.setattr(app, '_shutdown', no_native)
    calls=[]
    class FakeStore:
        def open(self):calls.append('store-open')
        def close(self):calls.append('store-close')
    monkeypatch.setattr('beamo_wipe.session_recovery.SessionStore', FakeStore)
    def main(*_args, **_kwargs):calls.append('main');return 17
    monkeypatch.setattr(app, '_main', main)
    code=app.main([])
    request.node.user_properties.append(('startup_trace', json.dumps({'case':case, 'code':code, 'calls':calls, 'native_calls':len(forbidden)})))
    assert not forbidden
    if case.startswith('bad-'):
        assert code==3
        assert calls==[]
    else:
        assert code==17
        assert calls==(['main'] if case=='normal-desktop' else ['store-open','main','store-close'])
