"""Owned-file and callback probes, independent of reviewer injection points."""
import importlib.util
import os
from pathlib import Path

import pytest

from beamo_wipe import audio_jobs, evidence, sound
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize('mutation', ['normal', 'bytes', 'mode', 'link'])
def test_evidence_final_sync_is_bound(tmp_path, monkeypatch, mutation):
    target = tmp_path / 'owned.json'
    real_sync = os.fsync
    touched = False
    def sync(fd):
        nonlocal touched
        result = real_sync(fd)
        import stat
        if not touched and stat.S_ISREG(os.fstat(fd).st_mode):
            touched = True
            if mutation == 'bytes':
                os.pwrite(fd, b'changed!', 0)
            elif mutation == 'mode':
                os.fchmod(fd, 0o644)
            elif mutation == 'link':
                temp = next(tmp_path.glob('.owned.json.tmp.*'))
                os.link(temp, tmp_path / 'another')
        return result
    monkeypatch.setattr(os, 'fsync', sync)
    if mutation == 'normal':
        evidence._atomic_write_bytes(target, b'original')
        assert target.read_bytes() == b'original'
    else:
        with pytest.raises((SafetyError, OSError)):
            evidence._atomic_write_bytes(target, b'original')
    assert touched


@pytest.mark.parametrize('cancel_at', ['none', 'prepare', 'resolve'])
def test_outcome_cancellation_before_spawn(monkeypatch, cancel_at):
    ticket = audio_jobs.AudioTicket()
    monkeypatch.setattr(sound._audio_context, 'ticket', ticket, raising=False)
    monkeypatch.setattr(sound, '_ready', lambda _kind: (True, ''))
    def prepare():
        if cancel_at == 'prepare': ticket.cancel()
        return True
    def resolve(_tool):
        if cancel_at == 'resolve': ticket.cancel()
        return '/fake/player'
    monkeypatch.setattr(sound, 'ensure_audio', prepare)
    monkeypatch.setattr('beamo_wipe.safety.resolve_system_binary', resolve)
    launches = []
    class Process:
        def wait(self, timeout): return 0
        def terminate(self): return None
    monkeypatch.setattr(sound.subprocess, 'Popen', lambda *a, **kw: launches.append(a) or Process())
    class Thread:
        def __init__(self, **kwargs): pass
        def start(self): pass
    monkeypatch.setattr(sound.threading, 'Thread', Thread)
    result = sound.play_outcome(sound.KIND_ATTENTION)
    assert len(launches) == int(cancel_at == 'none')
    assert result.ok is (cancel_at == 'none')


@pytest.mark.parametrize('failure', [RuntimeError, KeyboardInterrupt, SystemExit])
def test_interrupted_builder_retires_receipt(tmp_path, monkeypatch, failure):
    from test_desktop_output_replacement_pass2_20261019 import _setup
    path = Path('/workspace/beamo-wipe/scripts/build_desktop.py')
    spec = importlib.util.spec_from_file_location('pass13_root_builder', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    output = _setup(builder, tmp_path, monkeypatch, 'posix', False)
    real_check = builder._require_unchanged_launcher_outputs
    injected = False
    def check(*args):
        nonlocal injected
        result = real_check(*args)
        if (output / 'desktop-build.json').exists():
            injected = True
            (output / builder.LAUNCHERS[0]).write_bytes(b'changed during final check')
            raise failure('owned injected interrupt')
        return result
    monkeypatch.setattr(builder, '_require_unchanged_launcher_outputs', check)
    with pytest.raises(failure): builder.build(output)
    assert injected
    assert not (output / '.build.lock').exists()
    assert not (output / 'desktop-build.json').exists()
