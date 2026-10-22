"""Independent public entry proof using owned proc-file substitutes only."""
import builtins

import pytest

from beamo_wipe import app, discover, safety, session_recovery


@pytest.mark.parametrize('owned', [False, True], ids=['initial-io-failure', 'owned-live'])
@pytest.mark.parametrize('location', ['cmdline', 'mountinfo'])
def test_later_undecodable_metadata_has_blocked_public_exit(monkeypatch, tmp_path, owned, location, capsys):
    command = tmp_path / 'command'
    command.write_bytes(b'boot=live quiet')
    bad_command = tmp_path / 'bad-command'
    bad_command.write_bytes(b'boot=live label=\xff')
    mount = tmp_path / 'mount'
    live_mount = b'1 0 8:241 / /run/live/medium ro - iso9660 /dev/sdz1 ro\n'
    mount.write_bytes(live_mount)
    bad_mount = tmp_path / 'bad-mount'
    bad_mount.write_bytes(live_mount + b'2 0 8:1 / /media/\xff rw - ext4 /dev/sda1 rw\n')
    original_open = builtins.open
    reads = []
    calls = []
    monkeypatch.setattr(safety.sys, 'platform', 'linux')
    monkeypatch.setattr(app, 'running_on_live_usb', safety.running_on_live_usb)

    def proc(path, *args, **kwargs):
        if str(path) == '/proc/cmdline':
            reads.append('cmdline')
            if len(reads) == 1 and not owned:
                raise OSError('fake transient first proc read failure')
            bad = len(reads) > 1 and location == 'cmdline'
            return original_open(bad_command if bad else command, *args, **kwargs)
        if str(path) == discover.MOUNTINFO_PATH:
            bad = len(reads) > 1 and location == 'mountinfo'
            return original_open(bad_mount if bad else mount, *args, **kwargs)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', proc)
    monkeypatch.setattr('beamo_wipe.diagnostics.log_diag', lambda *a, **kw: None)
    monkeypatch.setattr('beamo_wipe.diagnostics.emit_serial_marker', lambda *a, **kw: None)

    class Store:
        def open(self): calls.append('open')
        def close(self): calls.append('close')

    monkeypatch.setattr(session_recovery, 'SessionStore', Store)
    monkeypatch.setattr(app, '_run_session', lambda *a, **kw: pytest.fail('Session dispatch forbidden'))
    monkeypatch.setattr(app.signal, 'signal', lambda *a: None)
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: pytest.fail('Native process forbidden'))
    monkeypatch.setattr('subprocess.Popen', lambda *a, **kw: pytest.fail('Native process forbidden'))
    escaped = None
    code = None
    try:
        code = app.main(['--demo'])
    except UnicodeError as exc:
        escaped = type(exc).__name__
    assert escaped is None, (escaped, reads, calls)
    assert code == 3
    assert capsys.readouterr().err.strip() == app.RECOVERY_UNAVAILABLE
    assert calls == (['open', 'close'] if owned else [])
