# SPDX-License-Identifier: GPL-3.0-or-later
"""#133: people can walk away; a sound tells them the result is ready.

During an erase the Working screen offers "Play a sound when it's
finished", on by default for each erase. It is the one session sound
setting (the result screen's "Sounds: on/off"), so its state carries to the
result. The beep is promised only when a sound output is actually found;
otherwise the screen says so and the toggle is greyed with a reason. The
finished sound plays only for a verified erase; every other outcome gets
the attention sound. It repeats every minute, at most five times, until
someone interacts. All audio work runs on the audio worker, never on the
interface thread. Fake demo disks only; nothing is erased.
"""

from __future__ import annotations

import threading
import time

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang, sound
from beamo_wipe import wizard as W
from beamo_wipe.audio_jobs import AudioWorker
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.outcomes import VIEWS
from test_result_presentations import CASES, case_evidence


@pytest.fixture(autouse=True)
def _english_after():
    lang.set_language("en")
    yield
    lang.set_language("en")


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _working(audio=None):
    """Working on a fake disk with the per-erase default applied."""
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.selected = wiz.selectable[0]
    wiz.method = MethodId.EVERYDAY
    wiz.screen = Screen.WORKING
    wiz.begin_finish_sound()
    if audio is not None:
        wiz.set_audio_availability(audio, "" if audio else C.FINISH_SOUND_REASON_NO_OUTPUT)
    return wiz


def _done(code="verified", *, audio=True, clock=None):
    wiz, _ev, _log = case_evidence(next(c for c in CASES if c[0] == code))
    if clock is not None:
        wiz._clock = clock
    wiz.begin_finish_sound()  # the erase that produced this result
    wiz.set_audio_availability(audio, "" if audio else C.FINISH_SOUND_REASON_NO_OUTPUT)
    return wiz


# --- Default, persistence and honest copy -----------------------------------


def test_sounds_start_off_and_each_erase_turns_the_finish_sound_on():
    wiz = make_demo_wizard()
    assert wiz.sounds_enabled is False  # unchanged before any erase
    wiz.begin_finish_sound()
    assert wiz.sounds_enabled is True


def test_an_explicit_choice_before_the_erase_is_kept():
    wiz = make_demo_wizard()
    wiz.set_sounds_enabled(False)
    wiz.begin_finish_sound()
    assert wiz.sounds_enabled is False
    wiz.set_sounds_enabled(True)
    wiz.begin_finish_sound()
    assert wiz.sounds_enabled is True


def test_turning_it_off_during_the_erase_carries_to_the_result():
    wiz = _working(audio=True)
    wiz.set_finish_sound(False)
    assert wiz.walk_away_text == C.WALK_AWAY_QUIET
    wiz.screen = Screen.DONE
    assert wiz.sounds_enabled is False
    assert wiz.sound_toggle_text == C.SOUND_TOGGLE_OFF
    # set_finish_sound leaves no status message: the box shows the state.
    assert wiz.sound_message == ""


def test_the_beep_is_promised_only_when_an_output_was_found():
    wiz = _working()
    assert wiz.audio_available is None
    assert wiz.walk_away_text == C.WALK_AWAY_QUIET  # still checking: no promise
    wiz.set_audio_availability(True)
    assert wiz.walk_away_text == C.WALK_AWAY_BEEP
    assert C.WALK_AWAY_BEEP == "You can leave the computer. It will beep when it's done."
    assert wiz.finish_sound_toggle_enabled and wiz.finish_sound_reason == ""
    wiz.set_audio_availability(False, C.FINISH_SOUND_REASON_MUTED)
    assert wiz.walk_away_text == C.WALK_AWAY_NO_SOUND
    assert "beep" not in wiz.walk_away_text
    assert wiz.finish_sound_reason == C.FINISH_SOUND_REASON_MUTED
    assert not wiz.finish_sound_toggle_enabled


def test_greyed_toggle_cannot_be_changed_while_unavailable():
    wiz = _working(audio=False)
    before = wiz.sounds_enabled
    wiz.set_finish_sound(not before)
    wiz.toggle_sounds()
    assert wiz.sounds_enabled is before


def test_a_new_erase_checks_availability_again():
    wiz = _working(audio=False)
    wiz.begin_finish_sound()
    assert wiz.audio_available is None and wiz.audio_reason == ""


# --- Sound per outcome -------------------------------------------------------


def test_only_a_verified_erase_gets_the_finished_sound():
    assert sound.kind_for_code("verified") == sound.KIND_FINISHED
    for code in VIEWS:
        if code != "verified":
            assert sound.kind_for_code(code) == sound.KIND_ATTENTION, code


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_each_outcome_queues_its_sound_and_quick_zero_is_never_success(case, monkeypatch):
    wiz = _done(case[0])
    queued = []
    monkeypatch.setattr(wiz, "_queue_audio", lambda action, **kw: queued.append((action, kw)))
    played = []
    monkeypatch.setattr(sound, "play_test", lambda kind: played.append(kind))
    wiz.request_auto_outcome_sound()
    assert len(queued) == 1 and queued[0][1]["auto"] is True
    queued[0][0]()
    expected = sound.KIND_FINISHED if wiz.result_view.code == "verified" else sound.KIND_ATTENTION
    assert played == [expected]
    if case[1] == MethodId.QUICK_ZERO or case[0] in {"cancelled", "interrupted"}:
        assert played == [sound.KIND_ATTENTION]


def test_preview_never_plays():
    wiz = _done()
    wiz.preview = True
    assert wiz.request_auto_outcome_sound() is None


# --- Repeats -----------------------------------------------------------------


def _repeating(code="verified", audio=True):
    clock = Clock()
    wiz = _done(code, audio=audio, clock=clock)
    queued = []
    wiz._queue_audio = lambda action, **kw: queued.append(action)  # type: ignore[method-assign]
    wiz.request_auto_outcome_sound()
    return wiz, clock, queued


def test_repeats_every_minute_up_to_five_plays():
    wiz, clock, queued = _repeating()
    assert len(queued) == 1
    clock.t += W.FINISH_REPEAT_S - 1
    wiz._tick_finish_sound()
    assert len(queued) == 1
    for n in range(2, 8):
        clock.t += W.FINISH_REPEAT_S
        wiz._tick_finish_sound()
        assert len(queued) == min(n, W.FINISH_PLAYS_MAX)
    assert W.FINISH_PLAYS_MAX == 5 and W.FINISH_REPEAT_S == 60.0


def test_any_interaction_stops_the_repeats():
    wiz, clock, queued = _repeating()
    wiz.acknowledge_finish_sound()
    for _ in range(5):
        clock.t += W.FINISH_REPEAT_S
        wiz._tick_finish_sound()
    assert len(queued) == 1


def test_turning_sounds_off_or_leaving_the_result_stops_the_repeats():
    wiz, clock, queued = _repeating()
    wiz.toggle_sounds()  # result screen's Sounds: on -> off
    clock.t += W.FINISH_REPEAT_S
    wiz._tick_finish_sound()
    assert len(queued) == 1
    wiz, clock, queued = _repeating()
    wiz.screen = Screen.SHUTDOWN_CONFIRM
    clock.t += W.FINISH_REPEAT_S
    wiz._tick_finish_sound()
    assert len(queued) == 1


def test_repeats_keep_the_attention_sound_for_a_failure(monkeypatch):
    wiz, clock, queued = _repeating("verification_failed")
    clock.t += W.FINISH_REPEAT_S
    wiz._tick_finish_sound()
    played = []
    monkeypatch.setattr(sound, "play_test", lambda kind: played.append(kind))
    for action in queued:
        action()
    assert played == [sound.KIND_ATTENTION, sound.KIND_ATTENTION]


def test_without_an_output_alerts_are_counted_for_the_bell_but_not_played():
    wiz, clock, queued = _repeating(audio=False)
    first = wiz.finish_alert_serial
    clock.t += W.FINISH_REPEAT_S
    wiz._tick_finish_sound()
    assert wiz.finish_alert_serial == first + 1
    assert len(queued) == 1  # only the first (truthful failure message)


# --- Never on the interface thread ------------------------------------------


def test_availability_check_runs_on_the_worker_and_never_blocks_tick(monkeypatch):
    release = threading.Event()
    started = threading.Event()

    def slow_status():
        started.set()
        release.wait(5)
        return sound.SoundResult(True, "")

    monkeypatch.setattr(sound, "output_status", slow_status)
    wiz = _working()
    t0 = time.monotonic()
    wiz.tick()
    assert time.monotonic() - t0 < 0.5
    assert started.wait(2)
    assert wiz.audio_available is None
    release.set()
    deadline = time.monotonic() + 3
    while wiz.audio_available is None and time.monotonic() < deadline:
        wiz.tick()
        time.sleep(0.02)
    assert wiz.audio_available is True
    assert wiz.walk_away_text == C.WALK_AWAY_BEEP


def test_auto_finish_sound_returns_while_playback_blocks(monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(sound, "play_test", lambda kind: release.wait(5) or sound.SoundResult(True, ""))
    wiz = _done()
    t0 = time.monotonic()
    ticket = wiz.request_auto_outcome_sound()
    assert ticket is not None and time.monotonic() - t0 < 0.5
    release.set()


def test_background_check_never_displaces_a_running_request():
    worker = AudioWorker()
    gate = threading.Event()
    running = threading.Event()
    try:
        def held():
            running.set()
            gate.wait(5)
            return "done"

        first = worker.submit(held)
        assert running.wait(2)
        probe = worker.submit(lambda: "probe", background=True)
        assert probe.cancelled.is_set()
        assert not first.cancelled.is_set()
        gate.set()
        deadline = time.monotonic() + 3
        while not first.poll()[0] and time.monotonic() < deadline:
            time.sleep(0.01)
        assert first.poll() == (True, "done")
    finally:
        gate.set()
        worker.close()


def test_output_status_reasons(monkeypatch):
    monkeypatch.setattr(sound, "_on_live", lambda: False)
    assert sound.output_status() == sound.SoundResult(False, C.FINISH_SOUND_REASON_PREVIEW)
    monkeypatch.setattr(sound, "_on_live", lambda: True)
    monkeypatch.setattr(sound, "ensure_audio", lambda: True)
    for state, expected in (
        (sound.SoundState(False, "", ()), sound.SoundResult(False, C.FINISH_SOUND_REASON_NO_OUTPUT)),
        (sound.SoundState(True, "", (), muted=True), sound.SoundResult(False, C.FINISH_SOUND_REASON_MUTED)),
        (sound.SoundState(True, "", (), muted=False), sound.SoundResult(True, "")),
    ):
        monkeypatch.setattr(sound, "list_outputs", lambda s=state: s)
        assert sound.output_status() == expected


# --- Translations --------------------------------------------------------------


NAMES = (
    "FINISH_SOUND_TOGGLE", "WALK_AWAY_BEEP", "WALK_AWAY_QUIET", "WALK_AWAY_NO_SOUND",
    "FINISH_SOUND_REASON_NO_OUTPUT", "FINISH_SOUND_REASON_MUTED",
    "FINISH_SOUND_REASON_PREVIEW", "FINISH_SOUND_STATE_ON", "FINISH_SOUND_STATE_OFF",
    "FINISH_SOUND_STATE_UNAVAILABLE",
)


@pytest.mark.parametrize("code", [c for c in lang.LANGUAGE_ORDER if c != "en"])
def test_every_language_translates_the_finish_sound(code):
    english = {n: getattr(C, n) for n in NAMES}
    lang.set_language(code)
    for name, text in english.items():
        assert getattr(C, name) and getattr(C, name) != text, (code, name)
    for name in ("FINISH_SOUND_STATE_ON", "FINISH_SOUND_STATE_OFF", "FINISH_SOUND_STATE_UNAVAILABLE"):
        assert getattr(C, name).startswith(C.FINISH_SOUND_TOGGLE), (code, name)


# --- Curses and plain console --------------------------------------------------


def test_bell_rings_once_per_alert_only_without_an_output():
    from beamo_wipe.ui.console_wizard import _ring_finish_bell

    rings = []
    wiz = _working(audio=False)
    rung = _ring_finish_bell(wiz, wiz.finish_alert_serial, lambda: rings.append(1))
    assert rings == []
    wiz.finish_alert_serial += 1
    rung = _ring_finish_bell(wiz, rung, lambda: rings.append(1))
    rung = _ring_finish_bell(wiz, rung, lambda: rings.append(1))
    assert rings == [1]
    wiz.set_audio_availability(True)
    wiz.finish_alert_serial += 1
    _ring_finish_bell(wiz, rung, lambda: rings.append(1))
    assert rings == [1]


def _curses_rows(monkeypatch, wiz, h=24):
    from unittest.mock import PropertyMock, patch

    from beamo_wipe.progress import ProgressView
    from beamo_wipe.ui import console_wizard as console
    from beamo_wipe.wizard import Wizard
    from test_console_parity import Terminal

    class Stop(BaseException):
        pass

    class Once(Terminal):
        def getch(self):
            self.frames.append(dict(self.rows))
            raise Stop

    for name in ("curs_set", "use_default_colors", "echo", "noecho", "beep"):
        monkeypatch.setattr(console.curses, name, lambda *a, **k: None)
    monkeypatch.setattr(wiz, "tick", lambda: None)
    term = Once(wiz, h=h, w=80)
    view = ProgressView("Writing", 40.0, 600)
    with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=view):
        with pytest.raises(Stop):
            console._loop(term, wiz)
    last = term.frames[-1]
    return [last.get(y, "") for y in range(h)]


@pytest.mark.parametrize("audio", [True, False])
def test_curses_working_shows_the_toggle_and_walk_away_line(monkeypatch, audio):
    wiz = _working(audio=audio)
    rows = _curses_rows(monkeypatch, wiz, h=40)
    text = "\n".join(rows)
    if audio:
        assert C.WALK_AWAY_BEEP in text
        assert f"O: {C.FINISH_SOUND_STATE_ON}" in text
    else:
        assert C.WALK_AWAY_NO_SOUND in text and C.FINISH_SOUND_REASON_NO_OUTPUT in text
        assert C.FINISH_SOUND_STATE_UNAVAILABLE in text and "O: " + C.FINISH_SOUND_STATE_UNAVAILABLE not in text
    # Walk-away advice sits right before the laptop power advice, said once.
    walk = next(i for i, r in enumerate(rows) if r.startswith(wiz.walk_away_text[:20]))
    power = next(i for i, r in enumerate(rows) if r.startswith(C.POWER_KEEP[:20]))
    assert walk < power and text.count(C.POWER_KEEP) == 1


def test_plain_console_typed_answer_counts_as_interaction(monkeypatch):
    from beamo_wipe.ui import console_wizard as console

    wiz = _done()
    wiz.request_auto_outcome_sound = lambda: None  # type: ignore[method-assign]
    wiz._finish_plays = 1
    monkeypatch.setattr("builtins.input", lambda *_: "")
    console._answer(wiz, "?")
    assert wiz._finish_ack is True


# --- Rendered Tk -----------------------------------------------------------------


@pytest.fixture
def live_ui():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(wiz, size=(800, 600)):
        _needs_display()
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app.root.update_idletasks()
        app.root.focus_force()
        created.append(app)
        return app

    yield build
    for app in created:
        app._teardown()


def _tk_working(live_ui, audio, text_size="standard"):
    from unittest.mock import PropertyMock, patch

    from beamo_wipe.progress import ProgressView, plan_stages
    from beamo_wipe.wizard import Wizard

    wiz = _working(audio=audio)
    wiz._audio_probe_at = wiz.now + 3600  # no live availability check here
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
    view = ProgressView("Writing", 23.0, 1500, stages=plan_stages(1, True), position=0)
    patcher = patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=view)
    patcher.start()
    app = live_ui(wiz)
    app._draw()
    app.root.update_idletasks()
    app.root.update()
    return wiz, app, patcher


def _labels(app):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [str(w.cget("text")) for w in walk(app.root)
            if w.winfo_class() == "Label" and w.winfo_ismapped()]


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_toggle_is_visible_and_on_by_default(live_ui, text_size):
    wiz, app, patcher = _tk_working(live_ui, True, text_size)
    try:
        toggle = app._finish_toggle
        assert toggle is not None and toggle.winfo_ismapped()
        assert toggle.cget("text") == C.FINISH_SOUND_TOGGLE
        assert bool(toggle._variable.get()) is True
        bottom = toggle.winfo_rooty() + toggle.winfo_height()
        assert bottom <= app.root.winfo_rooty() + app.root.winfo_height()
        texts = _labels(app)
        assert C.WALK_AWAY_BEEP in texts
        assert texts.count(C.POWER_KEEP) == 1
    finally:
        patcher.stop()


def test_tk_toggle_space_turns_it_off_and_keeps_focus(live_ui):
    wiz, app, patcher = _tk_working(live_ui, True)
    try:
        app._finish_toggle.focus_set()
        app.root.update()
        app._finish_toggle._activate(None)
        app.root.update()
        assert wiz.sounds_enabled is False
        assert bool(app._finish_toggle._variable.get()) is False
        assert app.root.focus_get() is app._finish_toggle
        assert C.WALK_AWAY_QUIET in _labels(app)
    finally:
        patcher.stop()


def test_tk_toggle_is_greyed_with_a_reason_without_an_output(live_ui):
    wiz, app, patcher = _tk_working(live_ui, False)
    try:
        toggle = app._finish_toggle
        assert str(toggle.cget("takefocus")) == "0"
        before = wiz.sounds_enabled
        toggle.invoke()
        assert wiz.sounds_enabled is before
        texts = _labels(app)
        assert C.WALK_AWAY_NO_SOUND in texts and C.FINISH_SOUND_REASON_NO_OUTPUT in texts
        assert not any("beep" in t for t in texts)
    finally:
        patcher.stop()


def test_tk_key_or_click_on_the_result_stops_repeats(live_ui):
    wiz = _done()
    wiz._queue_audio = lambda action, **kw: None  # type: ignore[method-assign]
    app = live_ui(wiz)
    app._draw()
    app.root.update()
    assert wiz._finish_plays == 1 and not wiz._finish_ack
    app._on_key(type("E", (), {"keysym": "a", "state": 0, "char": "a"})())
    assert wiz._finish_ack is True
