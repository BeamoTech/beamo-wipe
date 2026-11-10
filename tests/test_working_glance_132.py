# SPDX-License-Identifier: GPL-3.0-or-later
"""#132: the Working screen reads at a glance from across the room.

Large percentage, then a cautious time line, then the current step
("Step 1 of 2: Overwriting"). Missing data never shows a "not reported"
placeholder; one calm "Starting…" stands in until the first percentage.
Progress stays conservative (never 100% on this screen), stale progress
stays prominent, and screen readers hear progress at a paced interval.
All disks here are fake demo disks; nothing is erased.
"""

from __future__ import annotations

import re
from unittest.mock import PropertyMock, patch

import pytest

from beamo_wipe import lang
from beamo_wipe import progress as P
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.progress import ProgressAnnouncer, ProgressView, plan_stages
from test_progress_timing import sample

EV = plan_stages(1, True)
QZ = plan_stages(1, False)
EX = plan_stages(3, True)
PLACEHOLDER = re.compile(r"not reported|unavailable", re.IGNORECASE)
# Whole screens also carry unrelated fake-power text ("…is unavailable").
NOT_REPORTED = re.compile(r"not reported", re.IGNORECASE)


@pytest.fixture(autouse=True)
def _english_after():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _shown(view: ProgressView) -> str:
    """Everything the Working screen can show for this view."""
    return "\n".join(
        (*view.glance_lines, view.glance_stale, *view.glance_notes, view.spoken_summary)
    )


# Six acceptance states, shared by the model and rendered tests.
STATES = {
    "starting": (MethodId.EVERYDAY, lambda: ProgressView("Preparing", None, 4, stages=EV)),
    "overwriting": (MethodId.EVERYDAY, lambda: ProgressView(
        "Writing", 23.4, 1500, stages=EV, position=0, step_percent=23.4,
        estimate_state=P.ESTIMATE_LAST_STEP)),
    "verifying": (MethodId.EVERYDAY, lambda: ProgressView(
        "Verifying", 61.2, 5400, 2400, stages=EV, position=1, step_percent=61.2)),
    "stale": (MethodId.EVERYDAY, lambda: ProgressView(
        "Writing", 42.0, 3000, stale_for=130, percent_is_old=True, stages=EV,
        position=0, step_percent=42.0, estimate_state=P.ESTIMATE_PAUSED)),
    "stopping": (MethodId.EVERYDAY, lambda: ProgressView(
        P.PHASE_STOPPING, 42.0, 3010, stages=EV, position=0, step_percent=42.0)),
    "quickzero": (MethodId.QUICK_ZERO, lambda: ProgressView(
        "Writing", 37.0, 900, 1500, stages=QZ, position=0, step_percent=37.0)),
}


# --- Shared model -----------------------------------------------------------


def test_starting_is_one_calm_word_and_no_placeholder():
    view = STATES["starting"][1]()
    assert view.glance_lines == ("Starting…", "Started less than 1 minute ago")  # #167
    assert view.glance_step == "" and view.glance_notes == ()
    assert not PLACEHOLDER.search(_shown(view))


def test_unknown_phase_and_unlocated_step_hide_their_lines():
    view = ProgressView(P.PHASE_UNKNOWN, 12.0, 300, stages=EV, estimate_state=P.ESTIMATE_EARLY)
    assert view.glance_lines == ("12%", "Started 5 minutes ago")  # #167
    assert not PLACEHOLDER.search(_shown(view))
    # The full model text still names the uncertainty for tests and preview.
    assert P.STAGE_NOT_REPORTED in view.timing_text


def test_overwriting_shows_step_1_of_2_and_waits_for_the_estimate():
    view = STATES["overwriting"][1]()
    assert view.glance_lines == ("23%", "Started 25 minutes ago", "Step 1 of 2: Overwriting")
    assert view.glance_notes == (P.GLANCE_TIME_LATER,)
    assert "left" not in view.glance_time


def test_verifying_shows_step_2_of_2_checking_and_a_rounded_estimate():
    view = STATES["verifying"][1]()
    # #167: started and time left on one large line; no Elapsed note.
    assert view.glance_lines == (
        "61%", "Started 1 hour 30 minutes ago · about 40 minutes left",
        "Step 2 of 2: Checking (verification)",
    )
    assert P.PHASE_NOTE_VERIFYING in view.glance_notes
    assert not any(note.startswith("Elapsed") for note in view.glance_notes)


def test_quick_zero_has_one_step_and_no_verification():
    spec = METHODS[MethodId.QUICK_ZERO]
    stages = plan_stages(spec.overwrite_passes, bool(spec.verification_passes))
    assert [s.kind for s in stages] == ["overwrite"]
    view = STATES["quickzero"][1]()
    assert view.glance_step == "Step 1 of 1: Overwriting"
    assert "verif" not in _shown(view).lower()


def test_three_overwrites_names_the_pass():
    view = ProgressView("Writing", 37.0, 900, stages=EX, position=1)
    assert view.glance_step == "Step 2 of 4: Overwriting (pass 2 of 3)"
    assert ProgressView("Verifying", 90.0, 9, stages=EX, position=3).glance_step == (
        "Step 4 of 4: Checking (verification)"
    )


def test_mismatch_stays_visible_as_a_warning_not_a_guess():
    view = ProgressView("Verifying", 50.0, 60, stages=QZ, mismatch=True)
    assert view.glance_step == P.STAGE_MISMATCH


def test_stale_progress_stays_prominent():
    view = STATES["stale"][1]()
    assert view.glance_percent == "42% (old)"
    stale = view.glance_stale
    assert "No new progress update for 2 minutes." in stale
    assert P.STALE_MEANING in stale and P.STALE_NEXT in stale
    assert P.STALE_MEANING in view.spoken_summary
    # Stale silence before the first number is shown the same way.
    first = ProgressView("Preparing", None, 95, stale_for=95, stages=EV)
    assert first.glance_headline == "Starting…" and P.STALE_MEANING in first.glance_stale


@pytest.mark.parametrize("pct", [99.0, 99.5, 99.9, 99.95, 100.0])
def test_never_100_percent_on_the_working_screen(pct):
    view = ProgressView("Verifying", pct, 60, stages=EV, position=1)
    assert view.glance_percent == "99%"
    assert "100" not in _shown(view)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (5, "Less than 1 minute left"),
        (59, "Less than 1 minute left"),
        (61, "About 2 minutes left"),
        (599, "About 10 minutes left"),
        (2401, "About 45 minutes left"),
        (3601, "About 2 hours left"),
        (90000, "About 1 day 1 hour left"),
    ],
)
def test_time_left_rounds_up_without_false_precision(seconds, expected):
    assert P.time_left(seconds) == expected
    assert "second" not in P.time_left(seconds)


def test_no_estimate_means_no_time_left_line():
    for state in ("starting", "overwriting", "stale", "stopping"):
        assert "left" not in STATES[state][1]().glance_time, state


def test_stopping_text_has_step_and_elapsed_but_no_estimate():
    view = STATES["stopping"][1]()
    assert view.glance_headline == "42%"
    assert view.stopping_text == "Step 1 of 2: Overwriting\nElapsed: 50 minutes"
    assert ProgressView(P.PHASE_STOPPING, None, 3010).glance_headline == P.GLANCE_STOPPING
    assert ProgressView(P.PHASE_FINALIZING, None, 3010).glance_headline == P.GLANCE_FINISHING


# --- Live wizard (fake runner) ----------------------------------------------


def _live(method):
    """Wizard on Working with an injected clock and fake engine reports.

    Drives the real Wizard.progress_view (throttling, step location, stale
    detection) without launching anything, so it also runs off Linux.
    """
    from beamo_wipe.demo import make_demo_wizard
    from beamo_wipe.progress import ProgressTiming
    from test_progress_timing import Clock

    wiz = make_demo_wizard()
    clock = Clock()
    wiz._clock = clock
    wiz._progress_timing = ProgressTiming(clock, lambda: clock.wall)
    wiz._progress_timing.start(clock())
    wiz.method = method
    wiz.screen = Screen.WORKING
    return wiz, clock


def test_wizard_view_follows_the_engine_without_100_before_the_result():
    wiz, clock = _live(MethodId.EVERYDAY)
    view = wiz.progress_view
    assert view.glance_headline == "Starting…"
    assert not PLACEHOLDER.search(_shown(view))
    wiz.runner.progress = 40.0
    wiz.runner.progress_observation = sample(40)
    assert wiz.progress_view.glance_lines[0] == "40%"
    assert wiz.progress_view.glance_step == "Step 1 of 2: Overwriting"
    clock.advance(6)
    wiz.runner.progress = 99.9
    wiz.runner.progress_observation = sample(100, phase="verifying")
    view = wiz.progress_view
    assert view.glance_step == "Step 2 of 2: Checking (verification)"
    assert view.glance_percent == "99%"
    assert "100" not in _shown(view)


def test_wizard_quick_zero_never_shows_a_verification_step():
    wiz, _clock = _live(MethodId.QUICK_ZERO)
    wiz.runner.progress = 50.0
    wiz.runner.progress_observation = sample(50)
    assert wiz.progress_view.glance_step == "Step 1 of 1: Overwriting"
    wiz.runner.progress_observation = sample(60, phase="verifying")
    assert wiz.progress_view.glance_step == P.STAGE_MISMATCH


def test_wizard_stale_after_quiet_engine():
    wiz, clock = _live(MethodId.EVERYDAY)
    wiz.runner.progress = 30.0
    wiz.runner.progress_observation = sample(30)
    assert wiz.progress_view.glance_stale == ""
    clock.advance(P.STALE_PROGRESS_S + 1)
    view = wiz.progress_view
    assert view.glance_percent == "30% (old)"
    assert P.STALE_MEANING in view.glance_stale


# --- Paced announcements ----------------------------------------------------


def _view(pct, *, position=0, stale_for=None, elapsed=600, phase="Writing"):
    return ProgressView(
        phase, pct, elapsed, stages=EV, position=position,
        stale_for=stale_for, percent_is_old=stale_for is not None and pct is not None,
    )


def test_announcer_speaks_first_then_at_most_once_a_minute():
    a = ProgressAnnouncer()
    assert a.update(_view(10.0), 0.0) == "10%. Started 10 minutes ago. Step 1 of 2: Overwriting."  # #167
    assert a.update(_view(10.0), 1.0) is None  # nothing changed
    for t, pct in ((5.0, 11.0), (30.0, 15.0), (59.0, 19.0)):
        assert a.update(_view(pct), t) is None  # changed, but within the minute
    assert a.update(_view(20.0), 60.0) is not None
    assert a.update(_view(21.0), 61.0) is None


def test_announcer_speaks_new_steps_and_stale_promptly_but_not_in_bursts():
    a = ProgressAnnouncer()
    assert a.update(_view(48.0), 0.0) is not None
    assert a.update(_view(50.0, position=1, phase="Verifying"), 3.0) is None  # within 5 s
    spoken = a.update(_view(50.0, position=1, phase="Verifying"), 6.0)
    assert spoken is not None and "Step 2 of 2: Checking (verification)" in spoken
    stale = a.update(_view(50.0, position=1, phase="Verifying", stale_for=11), 20.0)
    assert stale is not None and P.STALE_MEANING in stale
    assert a.update(_view(50.0, position=1, phase="Verifying", stale_for=40), 50.0) is None
    resumed = a.update(_view(55.0, position=1, phase="Verifying"), 56.0)
    assert resumed is not None and P.STALE_MEANING not in resumed


def test_announcer_over_a_long_erase_is_bounded():
    a = ProgressAnnouncer()
    spoken = 0
    for tick in range(0, 3600 * 10, 2):  # ten hours of 2-second polls
        pct = min(99.0, tick / 360.0)
        position = 0 if pct < 50 else 1
        if a.update(_view(pct, position=position, elapsed=tick), float(tick)) is not None:
            spoken += 1
    assert spoken <= 10 * 60 + 2


# --- Translations -----------------------------------------------------------


GLANCE_NAMES = [n for n in dir(P) if n.startswith("GLANCE_")]


@pytest.mark.parametrize("code", [c for c in lang.LANGUAGE_ORDER if c != "en"])
def test_every_language_translates_the_glance(code):
    english = {n: getattr(P, n) for n in GLANCE_NAMES}
    lang.set_language(code)
    for name, text in english.items():
        translated = getattr(P, name)
        assert translated and translated != text, (code, name)
        assert set(re.findall(r"\{\w+\}", translated)) == set(re.findall(r"\{\w+\}", text))
    for state, (_m, make) in STATES.items():
        assert not PLACEHOLDER.search(_shown(make())), (code, state)


# --- Curses and plain console -----------------------------------------------


def _fake_working(method=MethodId.EVERYDAY):
    """Working screen on a fake demo disk, with no erase process at all."""
    from beamo_wipe.demo import make_demo_wizard

    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.selected = wiz.selectable[0]
    wiz.method = method
    wiz.screen = Screen.WORKING
    return wiz


def _curses_frame(monkeypatch, wiz, view, h=24):
    from beamo_wipe.ui import console_wizard as console
    from beamo_wipe.wizard import Wizard
    from test_console_parity import Terminal

    class Stop(BaseException):
        pass

    class Once(Terminal):
        def getch(self):
            self.frames.append(dict(self.rows))
            raise Stop

    for name in ("curs_set", "use_default_colors", "echo", "noecho"):
        monkeypatch.setattr(console.curses, name, lambda *a, **k: None)
    term = Once(wiz, h=h, w=80)
    with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=view):
        with pytest.raises(Stop):
            console._loop(term, wiz)
    last = term.frames[-1]
    return [last.get(y, "") for y in range(h)]


@pytest.mark.parametrize("state", ["starting", "overwriting", "verifying", "stale", "quickzero"])
def test_curses_shows_the_same_three_lines_first(monkeypatch, state):
    method, make = STATES[state]
    view = make()
    rows = _curses_frame(monkeypatch, _fake_working(method), view)
    body = [r for r in rows[1:] if r.strip()]
    assert body[: len(view.glance_lines)] == list(view.glance_lines)
    assert not NOT_REPORTED.search("\n".join(rows))


def test_plain_console_prints_progress_at_the_paced_interval(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console
    from beamo_wipe.wizard import Wizard

    wiz = _fake_working()
    now = [0.0]
    monkeypatch.setattr(console.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(console.select, "select", lambda *a: ([], [], []))
    polls = iter(range(40))

    def tick():
        try:
            n = next(polls)
        except StopIteration:
            wiz.wants_shutdown = True
            return
        now[0] = n * 2.0

    monkeypatch.setattr(wiz, "tick", tick)
    # A percentage that moves on every 2-second poll.
    live = PropertyMock(side_effect=lambda: _view(10.0 + now[0] / 2.0, elapsed=600 + now[0]))
    with patch.object(Wizard, "progress_view", new_callable=lambda: live):
        console._plain_loop_body(wiz)
    out = capsys.readouterr().out
    printed = [line for line in out.splitlines() if "Step 1 of 2: Overwriting." in line]
    # 80 seconds of 2-second polls: the first summary and one a minute later.
    assert len(printed) == 2, printed
    assert "not reported" not in out.lower()


# --- Rendered Tk ------------------------------------------------------------


@pytest.fixture
def live_ui():
    """Like test_tk_runtime's ui fixture, but the live-USB window: built
    with preview off, so no preview banner takes height (the 800x600 fit
    is about the shipped screen)."""
    from beamo_wipe.demo import make_demo_wizard
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(size=(1280, 720)):
        _needs_display()
        wiz = make_demo_wizard()
        wiz.preview = False
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app.root.update_idletasks()
        app.root.focus_force()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _tk_working(live_ui, state, size, text_size="standard"):
    from beamo_wipe.wizard import Wizard

    method, make = STATES[state]
    wiz, app = live_ui(size=size)
    wiz.selected = wiz.selectable[0]
    wiz.method = method
    wiz.screen = Screen.STOPPING if state == "stopping" else Screen.WORKING
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
        app._sync_layout()
    view = make()
    patcher = patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=view)
    patcher.start()
    app._draw()
    app.root.update_idletasks()
    app.root.update()
    return wiz, app, view, patcher


def _labels(app):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [w for w in walk(app.root) if w.winfo_class() == "Label" and w.winfo_ismapped()]


def _inside_body(app, widget):
    view = app._body_canvas or app._body
    top = view.winfo_rooty()
    return top <= widget.winfo_rooty() and (
        widget.winfo_rooty() + widget.winfo_height() <= top + view.winfo_height()
    )


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("state", ["starting", "overwriting", "verifying", "stale", "quickzero"])
def test_tk_glance_reads_in_order_at_800x600(live_ui, state, text_size):
    _wiz, app, view, patcher = _tk_working(live_ui, state, (800, 600), text_size)
    try:
        big = app._progress_pct if view.glance_percent else app._progress_wait
        assert big.winfo_ismapped() and big.cget("text") == view.glance_headline
        assert app._progress_time.cget("text") == view.glance_time
        assert app._progress_time.winfo_ismapped()
        order = [big, app._progress_time]
        if view.glance_step:
            assert app._progress_step.cget("text") == view.glance_step
            order.append(app._progress_step)
        else:
            assert not app._progress_step.winfo_ismapped()
        ys = [w.winfo_rooty() for w in order]
        assert ys == sorted(ys)
        # Readable without scrolling at every text size.
        for widget in order:
            assert _inside_body(app, widget), (state, text_size, widget.cget("text"))
        texts = "\n".join(str(w.cget("text")) for w in _labels(app))
        assert not NOT_REPORTED.search(texts)
        assert "100%" not in texts
        assert app._progress_stale.winfo_ismapped() == (state == "stale")
        if state == "stale":
            assert P.STALE_MEANING in app._progress_stale.cget("text")
    finally:
        patcher.stop()


def test_tk_stop_stays_available_on_every_state(live_ui):
    from beamo_wipe.ui.tk_wizard import _Button

    for state in ("starting", "overwriting", "verifying", "stale", "quickzero"):
        _wiz, app, _view, patcher = _tk_working(live_ui, state, (800, 600), "extra")
        try:
            def walk(widget):
                yield widget
                for child in widget.winfo_children():
                    yield from walk(child)

            stop = [b for b in walk(app.root) if isinstance(b, _Button)
                    and b.itemcget(b._label, "text") == "Stop erase"]
            assert len(stop) == 1 and stop[0].winfo_ismapped(), state
            bottom = stop[0].winfo_rooty() + stop[0].winfo_height()
            assert bottom <= app.root.winfo_rooty() + app.root.winfo_height()
        finally:
            patcher.stop()


def test_tk_stopping_screen_shows_step_and_elapsed(live_ui):
    _wiz, app, view, patcher = _tk_working(live_ui, "stopping", (800, 600))
    try:
        assert app._progress_label.cget("text") == view.stopping_text
        app._refresh_working()
        assert app._progress_label.cget("text") == "Step 1 of 2: Overwriting\nElapsed: 50 minutes"
        assert "left" not in app._progress_label.cget("text")
    finally:
        patcher.stop()


def test_tk_lines_appear_and_hide_with_real_data(live_ui):
    from beamo_wipe.wizard import Wizard

    _wiz, app, _view, patcher = _tk_working(live_ui, "starting", (800, 600))
    patcher.stop()
    assert not app._progress_step.winfo_ismapped()
    for make, step_shown, stale_shown in (
        (STATES["overwriting"][1], True, False),
        (STATES["stale"][1], True, True),
        (STATES["starting"][1], False, False),
    ):
        with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=make()):
            app._refresh_working()
            app.root.update_idletasks()
            assert bool(app._progress_step.winfo_ismapped()) == step_shown
            assert bool(app._progress_stale.winfo_ismapped()) == stale_shown
    # Hidden slots collapse back instead of keeping their old height.
    assert app._progress_stale_slot.winfo_reqheight() <= 1

