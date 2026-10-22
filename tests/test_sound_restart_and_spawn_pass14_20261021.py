"""Audio preparation and cancellation stay bound to the owned request.

All processes, tickets and output probes are fakes. No host audio, device or
native subprocess is touched.
"""

import pytest

from beamo_wipe import audio_jobs, copy as C, sound


@pytest.mark.parametrize("ensure_ok", [False, True])
@pytest.mark.parametrize("available", [False, True])
def test_ready_restarts_audio_before_probe_and_keeps_probe_authoritative(
    monkeypatch, ensure_ok, available
):
    events = []
    state = sound.SoundState(
        available=available,
        message="" if available else C.SOUND_NO_OUTPUT,
        outputs=(sound.SoundOutput("owned", "Speakers", "owned", True),)
        if available
        else (),
        volume_percent=50 if available else None,
        muted=False if available else None,
    )
    monkeypatch.setattr(sound, "_on_live", lambda: True)
    monkeypatch.setattr(
        sound, "ensure_audio", lambda: events.append("ensure") or ensure_ok
    )
    monkeypatch.setattr(
        sound, "list_outputs", lambda: events.append("probe") or state
    )

    ready, message = sound._ready(sound.KIND_FINISHED)

    assert events == ["ensure", "probe"]
    assert ready is available
    assert message == ("" if available else C.SOUND_NO_OUTPUT_PLAY)


@pytest.mark.parametrize("protected", [False, True])
@pytest.mark.parametrize("wait_hangs", [False, True])
def test_cancel_during_popen_construction_terminates_and_reaps_child(
    monkeypatch, protected, wait_hangs
):
    ticket = audio_jobs.AudioTicket(protected=protected)
    monkeypatch.setattr(sound._audio_context, "ticket", ticket, raising=False)
    threads = []

    class Process:
        def __init__(self):
            self.calls = []
            self.first_wait = True

        def terminate(self):
            self.calls.append("terminate")

        def kill(self):
            self.calls.append("kill")

        def wait(self, timeout):
            self.calls.append(("wait", timeout))
            if wait_hangs and self.first_wait:
                self.first_wait = False
                raise sound.subprocess.TimeoutExpired("paplay", timeout)
            return -15

    process = Process()

    def spawn(*_args, **_kwargs):
        ticket.cancel()
        return process

    class ForbiddenThread:
        def __init__(self, **_kwargs):
            threads.append(True)

        def start(self):
            raise AssertionError("cancelled child received a reaper thread")

    monkeypatch.setattr(sound.subprocess, "Popen", spawn)
    monkeypatch.setattr(sound.threading, "Thread", ForbiddenThread)
    monkeypatch.setattr(
        "beamo_wipe.safety.resolve_system_binary", lambda _tool: "/fake/paplay"
    )
    monkeypatch.setattr("beamo_wipe.safety.session_exec_env", lambda: {})

    assert sound._popen("paplay", ["owned.wav"]) is None
    assert threads == []
    expected = ["terminate", ("wait", 1)]
    if wait_hangs:
        expected.extend(["kill", ("wait", 1)])
    assert process.calls == expected


@pytest.mark.parametrize("protected", [False, True])
def test_uncancelled_child_keeps_one_existing_reaper(monkeypatch, protected):
    ticket = audio_jobs.AudioTicket(protected=protected)
    monkeypatch.setattr(sound._audio_context, "ticket", ticket, raising=False)
    reapers = []

    class Process:
        def __init__(self):
            self.calls = []

        def wait(self, timeout):
            self.calls.append(("wait", timeout))
            return 0

    process = Process()

    class Reaper:
        def __init__(self, *, target, daemon):
            assert daemon
            self.target = target
            reapers.append(self)

        def start(self):
            pass

    monkeypatch.setattr(sound.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(sound.threading, "Thread", Reaper)
    monkeypatch.setattr(
        "beamo_wipe.safety.resolve_system_binary", lambda _tool: "/fake/paplay"
    )
    monkeypatch.setattr("beamo_wipe.safety.session_exec_env", lambda: {})

    assert sound._popen("paplay", ["owned.wav"]) is process
    assert len(reapers) == 1
    reapers[0].target()
    assert process.calls == [("wait", sound._PLAY_TIMEOUT)]
