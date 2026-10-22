"""Fake-only proof: cancellation during final audio helper must prevent playback."""
from types import SimpleNamespace
import pytest
from beamo_wipe import audio_jobs, sound

@pytest.mark.parametrize('cancelled', [True, False])
def test_cancelled_final_helper_does_not_launch_player(monkeypatch, cancelled):
    ticket = audio_jobs.AudioTicket()
    monkeypatch.setattr(sound._audio_context, 'ticket', ticket, raising=False)
    monkeypatch.setattr(sound, '_ready', lambda kind: (True, ''))
    calls = []
    def prepare():
        if cancelled:
            ticket.cancel()
        return not cancelled
    monkeypatch.setattr(sound, 'ensure_audio', prepare)
    monkeypatch.setattr('beamo_wipe.safety.resolve_system_binary', lambda name: '/fake/paplay')
    class Process:
        def wait(self, timeout): return 0
        def terminate(self): pass
    monkeypatch.setattr(sound.subprocess, 'Popen', lambda *a, **kw: calls.append((a, kw)) or Process())
    class Thread:
        def __init__(self, *, target, daemon): self.target = target
        def start(self): pass
    monkeypatch.setattr(sound.threading, 'Thread', Thread)
    result = sound.play_outcome(sound.KIND_FINISHED)
    assert len(calls) == (0 if cancelled else 1), 'Cancelled audio request launched a new player'
    assert result.ok is (not cancelled)
