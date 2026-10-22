"""Cancelled audio tickets cannot launch a new fire-and-forget player.

Only fake process and reaper callbacks run. The daemon-helper boundary uses
real outcome preparation; no audio, device, OS thread or subprocess executes.
"""

from types import SimpleNamespace

import pytest

from beamo_wipe import audio_jobs, sound


@pytest.fixture
def fake_playback(monkeypatch):
    processes, reapers, resolutions = [], [], []

    class Process:
        def __init__(self, argv):
            self.argv = argv
            self.waits = []
            self.stops = []

        def wait(self, timeout):
            self.waits.append(timeout)
            return 0

        def terminate(self):
            self.stops.append("terminate")

        def kill(self):
            self.stops.append("kill")

    def spawn(argv, **kwargs):
        assert kwargs["shell"] is False and kwargs["start_new_session"] is True
        process = Process(argv)
        processes.append(process)
        return process

    class Reaper:
        def __init__(self, *, target, daemon):
            assert daemon
            self.target = target
            reapers.append(self)

        def start(self):
            pass

    def resolve(tool):
        resolutions.append(tool)
        return "/fake/" + tool

    monkeypatch.setattr(sound.subprocess, "Popen", spawn)
    monkeypatch.setattr(sound.threading, "Thread", Reaper)
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", resolve)
    monkeypatch.setattr("beamo_wipe.safety.session_exec_env", lambda: {})
    monkeypatch.delattr(sound._audio_context, "ticket", raising=False)
    return SimpleNamespace(processes=processes, reapers=reapers, resolutions=resolutions)


def assert_playback(fixture, allowed):
    assert len(fixture.processes) == len(fixture.reapers) == int(allowed)
    for reaper in fixture.reapers:
        reaper.target()
    for process in fixture.processes:
        assert process.waits == [sound._PLAY_TIMEOUT]
        assert process.stops == []


@pytest.mark.parametrize("boundary", ["entry", "resolver"])
@pytest.mark.parametrize("protected", [False, True])
@pytest.mark.parametrize("cancelled", [False, True])
def test_spawn_rechecks_ticket_at_both_admission_boundaries(
    monkeypatch, fake_playback, boundary, protected, cancelled
):
    ticket = audio_jobs.AudioTicket(protected=protected)
    monkeypatch.setattr(sound._audio_context, "ticket", ticket, raising=False)
    if boundary == "entry" and cancelled:
        ticket.cancel()
    if boundary == "resolver":
        def resolve(tool):
            fake_playback.resolutions.append(tool)
            if cancelled:
                ticket.cancel()
            return "/fake/" + tool

        monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", resolve)
    result = sound._popen("paplay", ["owned-fake.wav"])
    assert_playback(fake_playback, not cancelled)
    assert (result is not None) is (not cancelled)
    if boundary == "entry" and cancelled:
        assert fake_playback.resolutions == []


@pytest.mark.parametrize("kind", [sound.KIND_FINISHED, sound.KIND_ATTENTION])
@pytest.mark.parametrize("protected", [False, True])
@pytest.mark.parametrize("cancelled", [False, True])
def test_outcome_cancelled_during_daemon_helper_cannot_start_player(
    monkeypatch, fake_playback, kind, protected, cancelled
):
    ticket = audio_jobs.AudioTicket(protected=protected)
    monkeypatch.setattr(sound._audio_context, "ticket", ticket, raising=False)
    monkeypatch.setattr(sound, "_on_live", lambda: True)
    helpers = []

    def helper(tool, args, timeout):
        helpers.append((tool, args, timeout))
        if tool == "pulseaudio":
            if cancelled:
                ticket.cancel()
                return None
            return SimpleNamespace(returncode=0, stdout="")
        if args == ["list", "short", "sinks"]:
            text = "0\tfake-speakers\tmodule\n"
        elif args == ["get-default-sink"]:
            text = "fake-speakers\n"
        elif args[0] == "get-sink-mute":
            text = "Mute: no\n"
        else:
            text = "Volume: 50%\n"
        return SimpleNamespace(returncode=0, stdout=text)

    monkeypatch.setattr(sound, "_run", helper)
    result = sound.play_outcome(kind)
    assert helpers[-1][0] == "pulseaudio"
    assert result.ok is (not cancelled)
    assert_playback(fake_playback, not cancelled)
    if not cancelled:
        assert fake_playback.processes[0].argv == ["/fake/paplay", sound.asset_path(kind)]


@pytest.mark.parametrize("tool", ["paplay", "pactl", "unlisted-player", ""])
def test_no_ticket_preserves_allowlist_and_single_reaper(fake_playback, tool):
    allowed = tool in sound._ALLOWED_BINARIES
    result = sound._popen(tool, ["owned-fake-argument"])
    assert_playback(fake_playback, allowed)
    assert (result is not None) is allowed
    assert fake_playback.resolutions == ([tool] if allowed else [])
