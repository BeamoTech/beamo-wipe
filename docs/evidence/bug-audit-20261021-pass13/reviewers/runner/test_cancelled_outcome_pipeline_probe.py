"""Cancellation through real outcome preparation, with process callbacks only."""
from types import SimpleNamespace
import pytest
from beamo_wipe import audio_jobs, sound

@pytest.mark.parametrize('cancelled', [True, False])
@pytest.mark.parametrize('kind', [sound.KIND_FINISHED, sound.KIND_ATTENTION])
def test_pipeline_cancelled_during_daemon_check_has_no_player(monkeypatch, cancelled, kind):
    ticket = audio_jobs.AudioTicket()
    monkeypatch.setattr(sound._audio_context, 'ticket', ticket, raising=False)
    monkeypatch.setattr(sound, '_on_live', lambda: True)
    calls = []
    helper_calls = []
    def helper(tool, args, timeout):
        helper_calls.append((tool, args))
        if tool == 'pulseaudio':
            if cancelled:
                ticket.cancel()
                return None
            return SimpleNamespace(returncode=0, stdout='')
        if args == ['list', 'short', 'sinks']:
            text = '0\tfake-speakers\tmodule\n'
        elif args == ['get-default-sink']:
            text = 'fake-speakers\n'
        elif args[0] == 'get-sink-mute':
            text = 'Mute: no\n'
        else:
            text = 'Volume: 50%\n'
        return SimpleNamespace(returncode=0, stdout=text)
    monkeypatch.setattr(sound, '_run', helper)
    monkeypatch.setattr('beamo_wipe.safety.resolve_system_binary', lambda name: '/fake/paplay')
    class Process:
        def wait(self, timeout): return 0
        def terminate(self): pass
    monkeypatch.setattr(sound.subprocess, 'Popen', lambda *a, **kw: calls.append(a) or Process())
    class Thread:
        def __init__(self, *, target, daemon): self.target = target
        def start(self): pass
    monkeypatch.setattr(sound.threading, 'Thread', Thread)
    result = sound.play_outcome(kind)
    assert helper_calls[-1][0] == 'pulseaudio'
    assert len(calls) == (0 if cancelled else 1), 'Cancelled outcome launched playback after daemon helper returned'
    assert result.ok is (not cancelled)
