# SPDX-License-Identifier: GPL-3.0-or-later
"""Audio must not hold an erase interface. All devices and players are fakes."""

import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from beamo_wipe import audio_jobs, copy as C, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import DEFAULT_METHOD
from beamo_wipe.models import Screen, WipeRequest, WipeResult
from beamo_wipe.ui import console_wizard
from beamo_wipe.ui.sound_dialog import SoundDialog


@pytest.fixture
def audio_worker(monkeypatch):
    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs, "worker", worker)
    monkeypatch.setattr("beamo_wipe.ui.sound_dialog.worker", worker)
    yield worker
    worker.close()


def until(predicate, timeout=2):
    end = time.monotonic() + timeout
    while not predicate() and time.monotonic() < end:
        time.sleep(0.005)
    assert predicate()


def settle(wizard, timeout=2):
    end = time.monotonic() + timeout
    while wizard._audio_request is not None and time.monotonic() < end:
        wizard.tick()
        time.sleep(0.005)
    assert wizard._audio_request is None


def test_slow_discovery_and_playback_leave_progress_and_stop_responsive(monkeypatch, audio_worker):
    # Before the change, 12 x 80 ms _run calls blocked Hear for ~0.998 s.
    calls = []
    monkeypatch.setattr(sound, "_on_live", lambda: True)
    def slow_run(tool, args, timeout):
        calls.append((tool, tuple(args), threading.current_thread().name))
        time.sleep(0.08)
        if args[:3] == ["list", "short", "sinks"]:
            return SimpleNamespace(returncode=0, stdout="0\tspeakers\tmodule\n")
        if args == ["get-default-sink"]:
            return SimpleNamespace(returncode=0, stdout="speakers\n")
        if args == ["get-sink-mute", "speakers"]:
            return SimpleNamespace(returncode=0, stdout="Mute: no\n")
        return SimpleNamespace(returncode=0, stdout="Volume: 50%\n")
    monkeypatch.setattr(sound, "_run", slow_run)
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    wizard._wipe_request = WipeRequest("/dev/fake", DEFAULT_METHOD, "/dev/boot-fake", "/tmp/fake-audio.log")
    polls = []
    wizard.runner.poll = lambda request: polls.append(request) or None
    started = time.perf_counter()
    console_wizard._handle(wizard, ord("h"))
    request_ms = (time.perf_counter() - started) * 1000
    assert request_ms < 60, request_ms
    tick_times = []
    for _ in range(10):
        started = time.perf_counter()
        wizard.tick()
        _ = wizard.progress_view.status_text
        tick_times.append((time.perf_counter() - started) * 1000)
        time.sleep(0.01)
    started = time.perf_counter()
    console_wizard._handle(wizard, 27)  # Escape opens the Stop confirmation.
    stop_ms = (time.perf_counter() - started) * 1000
    assert stop_ms < 60, stop_ms
    assert wizard.stop_confirmation is not None
    assert max(tick_times) < 60, tick_times
    assert polls
    settle(wizard)
    assert wizard.sound_message == C.SOUND_PLAYING_FINISHED + " " + C.SOUND_PLAYING_ATTENTION
    assert len(calls) >= 8
    assert all(name == "beamo-audio" for _, _, name in calls)


def test_audio_exception_is_visible_and_never_changes_erase_status(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    monkeypatch.setattr(sound, "play_test", lambda kind: (_ for _ in ()).throw(RuntimeError("fake player failed")))
    started = time.perf_counter()
    wizard.request_hear_both_sounds()
    assert time.perf_counter() - started < 0.06
    settle(wizard)
    assert wizard.sound_message == C.SOUND_ACTION_FAILED
    assert wizard.error is None
    assert wizard.wipe_result is None


def test_superseded_and_stale_audio_cannot_overwrite_new_state(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    entered = threading.Event()
    release = threading.Event()
    calls = []
    def player(kind):
        calls.append(kind)
        if len(calls) == 1:
            entered.set()
            release.wait(timeout=2)
            return sound.SoundResult(False, "old result")
        return sound.SoundResult(False, "new result")
    monkeypatch.setattr(sound, "play_test", player)
    first = wizard.request_hear_both_sounds()
    until(entered.is_set)
    second = wizard.request_hear_both_sounds()
    third = wizard.request_hear_both_sounds()
    assert first.cancelled.is_set() and second.cancelled.is_set()
    assert not third.cancelled.is_set()
    release.set()
    settle(wizard)
    assert calls == [sound.KIND_FINISHED, sound.KIND_FINISHED]
    assert wizard.sound_message == "new result"
    wizard.request_hear_both_sounds()
    wizard.screen = Screen.DONE
    wizard.screen = Screen.WORKING
    wizard.tick()
    assert wizard.sound_message != C.SOUND_CHECKING
    assert wizard._audio_request is None


def test_stop_confirm_during_slow_audio_and_late_result_is_ignored(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    request = WipeRequest("/dev/fake", DEFAULT_METHOD, "/dev/boot-fake", "/tmp/fake-audio-stop.log")
    wizard._wipe_request = request
    class FakeRunner:
        progress = 42.0
        result = WipeResult(False, 143, "interrupted", request.logfile)
        def poll(self, _request):
            return None
        def cancel(self):
            return None
    wizard.runner = FakeRunner()
    monkeypatch.setattr(wizard, "_write_evidence", lambda **kwargs: None)
    entered = threading.Event()
    release = threading.Event()
    def slow_player(_kind):
        entered.set()
        release.wait(timeout=2)
        return sound.SoundResult(False, "late audio result")
    monkeypatch.setattr(sound, "play_test", slow_player)
    console_wizard._handle(wizard, ord("h"))
    until(entered.is_set)
    started = time.perf_counter()
    console_wizard._handle(wizard, 27)
    console_wizard._handle(wizard, ord("s"))
    assert time.perf_counter() - started < 0.06
    until(lambda: wizard.screen == Screen.DONE)
    wizard.tick()
    release.set()
    time.sleep(0.02)
    wizard.tick()
    assert wizard.sound_message != "late audio result"
    assert wizard.result_view.code != "verified"


def test_hung_python_substitute_uses_one_worker_and_times_out(audio_worker):
    release = threading.Event()
    entered = threading.Event()
    def hung():
        entered.set()
        release.wait(timeout=2)
    first = audio_worker.submit(hung, seconds=0.05)
    until(entered.is_set)
    until(lambda: first.poll()[0])
    assert isinstance(first.poll()[1], TimeoutError)
    for _ in range(100):
        audio_worker.submit(lambda: sound.SoundResult(True, "later"), seconds=0.05)
    assert audio_worker._pending is not None
    assert audio_worker._thread is not None
    assert len([t for t in threading.enumerate() if t is audio_worker._thread]) == 1
    started = time.perf_counter()
    audio_worker.close()
    assert time.perf_counter() - started < 0.8
    release.set()
    audio_worker._thread.join(timeout=1)
    assert not audio_worker._thread.is_alive()


def test_cancel_reaps_owned_audio_subprocess(monkeypatch):
    worker = audio_jobs.AudioWorker()
    real_popen = subprocess.Popen
    processes = []
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: sys.executable)
    monkeypatch.setattr(sound.subprocess, "Popen", lambda *args, **kwargs: processes.append(real_popen(*args, **kwargs)) or processes[-1])
    ticket = worker.submit(lambda: sound._run("pactl", ["-c", "import time; time.sleep(30)"], 20))
    until(lambda: bool(processes))
    ticket.cancel()
    until(lambda: processes[0].poll() is not None)
    assert processes[0].returncode is not None
    worker.close()


def test_audio_subprocess_output_is_capped_and_reaped(monkeypatch):
    worker = audio_jobs.AudioWorker()
    real_popen = subprocess.Popen
    processes = []
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: sys.executable)
    monkeypatch.setattr(sound.subprocess, "Popen", lambda *args, **kwargs: processes.append(real_popen(*args, **kwargs)) or processes[-1])
    command = "import sys,time;sys.stdout.write('x'*70000);sys.stdout.flush();time.sleep(30)"
    ticket = worker.submit(lambda: sound._run("pactl", ["-c", command], 20))
    until(lambda: ticket.poll()[0])
    assert ticket.poll()[1] is None
    assert len(processes) == 1
    assert processes[0].poll() is not None
    worker.close()


@pytest.mark.parametrize("failure", ["create", "register", "close"])
def test_audio_selector_failures_reap_child_and_close_pipe(monkeypatch, failure):
    real_popen = subprocess.Popen
    real_selector = sound.selectors.DefaultSelector
    processes = []
    selectors_created = []

    def launch(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        processes.append(proc)
        return proc

    class BrokenSelector:
        def __init__(self):
            if failure == "create":
                raise OSError("controlled selector creation failure")
            self.inner = real_selector()
            selectors_created.append(self.inner)

        def register(self, *args):
            if failure == "register":
                raise OSError("controlled selector registration failure")
            return self.inner.register(*args)

        def close(self):
            self.inner.close()
            if failure == "close":
                raise OSError("controlled selector close failure")

    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: sys.executable)
    monkeypatch.setattr(sound.subprocess, "Popen", launch)
    monkeypatch.setattr(sound.selectors, "DefaultSelector", BrokenSelector)
    # An expired ticket reaches cleanup immediately in the close-failure case.
    monkeypatch.setattr(sound._audio_context, "ticket", audio_jobs.AudioTicket(seconds=0), raising=False)
    try:
        assert sound._run("pactl", ["-c", "import time; time.sleep(30)"], 20) is None
        assert len(processes) == 1
        assert processes[0].returncode is not None, "owned audio child was not reaped"
        assert processes[0].stdout.closed
    finally:
        # Regressions in the production cleanup must not leak the test child.
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=2)
            proc.stdout.close()
        for selector in selectors_created:
            selector.close()


class FakeWidget:
    """Headless GTK stand-in that rejects worker-thread widget mutations."""

    def __init__(self, label="", **kwargs):
        self.label = label
        self.children = []
        self.signals = {}
        self.active = False
        self.sensitive = True
        self.content = None

    def __getattr__(self, name):
        def ui_method(*args, **kwargs):
            assert threading.current_thread() is threading.main_thread(), name
            if name == "get_content_area":
                if self.content is None:
                    self.content = FakeWidget()
                return self.content
            if name in {"get_accessible", "get_child"}:
                return self
            if name == "get_active":
                return self.active
            if name == "set_active":
                self.active = args[0]
            if name in {"set_text", "set_label"}:
                self.label = args[0]
            if name == "set_sensitive":
                self.sensitive = args[0]
            if name == "pack_start":
                self.children.append(args[0])
            if name == "connect":
                self.signals.setdefault(args[0], []).append((args[1], args[2:]))
            if name == "destroy":
                for callback, extra in self.signals.get("destroy", []):
                    callback(self, *extra)
            return None
        return ui_method


class FakeGtk:
    class Orientation:
        HORIZONTAL = 0
        VERTICAL = 1
    class ResponseType:
        CLOSE = 0
    Dialog = FakeWidget
    Label = FakeWidget
    Box = FakeWidget
    class Button:
        @staticmethod
        def new_with_label(label):
            return FakeWidget(label)
    class RadioButton:
        @staticmethod
        def new_with_label_from_widget(group, label):
            return FakeWidget(label)


def test_gtk_dialog_discovery_and_playback_are_polled_on_ui_thread(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    discovered = threading.Event()
    release_discovery = threading.Event()
    played = threading.Event()
    release_playback = threading.Event()
    output = sound.SoundOutput("speaker", "Speakers", "speaker", True)
    state = sound.SoundState(True, "", (output,), 50, False)
    def slow_outputs():
        discovered.set()
        release_discovery.wait(timeout=2)
        return state
    def slow_speech():
        played.set()
        release_playback.wait(timeout=2)
        return sound.SoundResult(True, C.SOUND_TEST_PLAYED)
    monkeypatch.setattr(sound, "list_outputs", slow_outputs)
    monkeypatch.setattr(sound, "orca_running", lambda: True)
    monkeypatch.setattr(sound, "set_output", lambda sink: sound.SoundResult(True, ""))
    monkeypatch.setattr(sound, "play_speech_test", slow_speech)
    started = time.perf_counter()
    dialog = SoundDialog(FakeGtk, FakeWidget(), wizard)
    assert time.perf_counter() - started < 0.06
    until(discovered.is_set)
    started = time.perf_counter()
    dialog.poll()
    assert time.perf_counter() - started < 0.06
    release_discovery.set()
    until(lambda: dialog.ticket is not None and dialog.ticket.poll()[0])
    dialog.poll()
    assert dialog.chosen == output
    started = time.perf_counter()
    dialog._play_speech(None)
    assert time.perf_counter() - started < 0.06
    until(played.is_set)
    dialog.poll()
    release_playback.set()
    until(lambda: dialog.ticket is not None and dialog.ticket.poll()[0])
    dialog.poll()
    assert dialog.status.label == C.SOUND_TEST_PLAYED
    dialog.close()


def test_gtk_dialog_close_drops_late_discovery(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    entered = threading.Event()
    release = threading.Event()
    def slow_outputs():
        entered.set()
        release.wait(timeout=2)
        return sound.SoundState(False, C.SOUND_NO_OUTPUT, ())
    monkeypatch.setattr(sound, "list_outputs", slow_outputs)
    monkeypatch.setattr(sound, "orca_running", lambda: None)
    dialog = SoundDialog(FakeGtk, FakeWidget(), wizard)
    until(entered.is_set)
    dialog.close()
    assert dialog.ticket is None
    release.set()
    time.sleep(0.02)
    dialog.poll()
    assert dialog.status.label == C.SOUND_CHECKING


def test_gtk_dialog_same_screen_revisit_is_stale(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    entered = threading.Event()
    release = threading.Event()
    def slow_outputs():
        entered.set()
        release.wait(timeout=2)
        return sound.SoundState(False, C.SOUND_NO_OUTPUT, ())
    monkeypatch.setattr(sound, "list_outputs", slow_outputs)
    monkeypatch.setattr(sound, "orca_running", lambda: None)
    dialog = SoundDialog(FakeGtk, FakeWidget(), wizard)
    until(entered.is_set)
    wizard.screen = Screen.DONE
    wizard.screen = Screen.WORKING
    dialog.poll()
    assert dialog.dialog is None
    release.set()


def test_gtk_sound_dialog_stop_stays_available_during_hung_discovery(monkeypatch, audio_worker):
    wizard = make_demo_wizard()
    wizard.screen = Screen.WORKING
    wizard._wipe_request = WipeRequest("/dev/fake", DEFAULT_METHOD, "/dev/boot-fake", "/tmp/fake-dialog-stop.log")
    entered = threading.Event()
    release = threading.Event()
    def slow_outputs():
        entered.set()
        release.wait(timeout=2)
        return sound.SoundState(False, C.SOUND_NO_OUTPUT, ())
    monkeypatch.setattr(sound, "list_outputs", slow_outputs)
    monkeypatch.setattr(sound, "orca_running", lambda: None)
    rendered = []
    dialog = SoundDialog(FakeGtk, FakeWidget(), wizard, on_stop=lambda: rendered.append(True))
    until(entered.is_set)
    started = time.perf_counter()
    dialog._request_stop(None)
    assert time.perf_counter() - started < 0.06
    assert wizard.stop_confirmation is not None
    assert dialog.dialog is None and dialog.ticket is None
    assert rendered == [True]
    release.set()


@pytest.mark.parametrize("queued", [False, True])
def test_sound_dialog_cannot_cancel_automatic_outcome(monkeypatch, audio_worker, queued):
    """Protect a queued or running notification without blocking GTK discovery."""
    blocker_entered = threading.Event()
    unblock = threading.Event()
    playing = threading.Event()
    finish_sound = threading.Event()
    calls = []

    def blocker():
        blocker_entered.set()
        unblock.wait(timeout=3)

    def play(kind):
        calls.append(kind)
        playing.set()
        finish_sound.wait(timeout=3)
        return sound.SoundResult(True, "")

    monkeypatch.setattr(sound, "play_test", play)
    monkeypatch.setattr(sound, "list_outputs", lambda: sound.SoundState(False, C.SOUND_NO_OUTPUT, ()))
    monkeypatch.setattr(sound, "orca_running", lambda: None)
    wizard = make_demo_wizard()
    wizard.preview = False
    wizard.screen = Screen.DONE
    wizard.wipe_result = WipeResult(True, 0, "Erase completed", "/tmp/fake-audio-result.log")
    wizard.set_sounds_enabled(True)
    dialog = None
    try:
        if queued:
            audio_worker.submit(blocker)
            until(blocker_entered.is_set)
        ticket = wizard.request_auto_outcome_sound()
        assert ticket is not None
        if not queued:
            until(playing.is_set)
        dialog = SoundDialog(FakeGtk, FakeWidget(), wizard)
        assert not ticket.cancelled.is_set()
        assert wizard.request_auto_outcome_sound() is None
        unblock.set()
        until(playing.is_set)
        assert not ticket.cancelled.is_set()
        finish_sound.set()
        settle(wizard)
        until(lambda: dialog.ticket.poll()[0])
        dialog.poll()
        assert dialog.status.label == C.SOUND_NO_OUTPUT
        assert len(calls) == 1
        assert wizard.request_auto_outcome_sound() is None
        assert wizard.sound_message == ""
    finally:
        unblock.set()
        finish_sound.set()
        if dialog is not None:
            dialog.close()


def test_audio_eof_uses_cancellable_wait_not_empty_selector(monkeypatch):
    real_selector = sound.selectors.DefaultSelector
    selections_after_eof = []
    waits = []
    ticket = audio_jobs.AudioTicket(seconds=1)
    real_wait = ticket.cancelled.wait

    def wait(timeout):
        waits.append(timeout)
        return real_wait(timeout)

    class Selector:
        def __init__(self):
            self.inner = real_selector()
            self.eof = False

        def register(self, *args):
            return self.inner.register(*args)

        def unregister(self, *args):
            self.eof = True
            return self.inner.unregister(*args)

        def select(self, **kwargs):
            if self.eof:
                selections_after_eof.append(True)
                raise AssertionError("empty selector must not be polled after EOF")
            return self.inner.select(**kwargs)

        def close(self):
            self.inner.close()

    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: sys.executable)
    monkeypatch.setattr(sound.selectors, "DefaultSelector", Selector)
    monkeypatch.setattr(sound._audio_context, "ticket", ticket, raising=False)
    monkeypatch.setattr(ticket.cancelled, "wait", wait)
    assert sound._run("pactl", ["-c", "import os,time; os.close(1); time.sleep(30)"], 20) is None
    assert waits and all(0 < timeout <= 0.1 for timeout in waits)
    assert not selections_after_eof
