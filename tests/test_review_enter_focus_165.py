# SPDX-License-Identifier: GPL-3.0-or-later
"""#165: on Review, Enter presses only the focused button, on every surface.

Before: Tk and GTK erased only from a focused, enabled Erase now (focus
starts on Back), but the curses fallback erased on a bare Enter once the
ready frame was painted. Now curses has the same two buttons: focus starts
on Back, Tab / Shift-Tab / Left / Right move it, Erase now takes focus only
once it is enabled on a painted frame, and Enter presses the highlighted
button. A countdown restart returns focus to Back, and _handle never erases
on a bare Enter (fail closed). The plain console still requires typing
ERASE. Fake disks; erase starts are recorded, never run.
"""

from __future__ import annotations

import time as real_time
from types import SimpleNamespace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console

ENTER, TAB = 10, 9


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at_last():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


def _ready(wiz):
    wiz._erase_until = 0


def _restart(wiz):
    wiz._erase_until = wiz.now + 60


def _run_curses(monkeypatch, wiz, steps):
    """Drive the curses loop: ints are keys; callables run on an idle read.

    Two idle reads follow every key so the next Enter is a new press (curses
    has no key-up; the loop needs a quiet interval). Returns erase starts.
    """
    starts = []
    monkeypatch.setattr(wiz, "confirm_erase", lambda: starts.append(wiz.screen))
    clock = {"t": 1000.0}

    def mono():
        clock["t"] += 0.6
        return clock["t"]

    monkeypatch.setattr(console, "time", SimpleNamespace(
        monotonic=mono, sleep=lambda *_: None, time=real_time.time))
    monkeypatch.setattr(console.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console.curses, "use_default_colors", lambda: None, raising=False)
    queue = [-1, -1]
    for step in steps:
        queue.append(step)
        if isinstance(step, int):
            queue.extend([-1, -1, -1])
    footers = []

    class Terminal:
        def getmaxyx(self):
            return (60, 120)

        def addstr(self, y, x, text, attr=0):
            if "Back" in text and "Erase now" in text:
                footers.append(text)

        def getch(self):
            if not queue:
                wiz.wants_shutdown = True
                return -1
            step = queue.pop(0)
            if callable(step):
                step(wiz)
                return -1
            return step

        def __getattr__(self, name):
            return lambda *args: None

    console._loop(Terminal(), wiz)
    return starts, footers


def test_curses_enter_during_countdown_presses_back(monkeypatch):
    wiz = _at_last()
    starts, footers = _run_curses(monkeypatch, wiz, [ENTER])
    assert starts == [] and wiz.screen == Screen.METHOD
    assert any(f.startswith(f"[> {C.BTN_BACK} <]") for f in footers)


def test_curses_enter_right_after_the_countdown_still_presses_back(monkeypatch):
    wiz = _at_last()
    starts, _ = _run_curses(monkeypatch, wiz, [_ready, ENTER])
    assert starts == [] and wiz.screen == Screen.METHOD


def test_curses_tab_to_erase_now_then_enter_erases_once(monkeypatch):
    wiz = _at_last()
    starts, footers = _run_curses(monkeypatch, wiz, [_ready, TAB, ENTER])
    assert starts == [Screen.LAST_CHANCE]
    assert any(f.endswith(f"[> {C.BTN_ERASE} <]") for f in footers)


@pytest.mark.parametrize("key", ["KEY_BTAB", "KEY_LEFT", "KEY_RIGHT"])
def test_curses_other_focus_keys_move_to_erase_now(monkeypatch, key):
    wiz = _at_last()
    starts, _ = _run_curses(monkeypatch, wiz, [_ready, getattr(console.curses, key), ENTER])
    assert starts == [Screen.LAST_CHANCE]


def test_curses_tab_twice_returns_to_back(monkeypatch):
    wiz = _at_last()
    starts, _ = _run_curses(monkeypatch, wiz, [_ready, TAB, TAB, ENTER])
    assert starts == [] and wiz.screen == Screen.METHOD


def test_curses_erase_now_cannot_take_focus_during_the_countdown(monkeypatch):
    wiz = _at_last()
    # Tab while counting keeps focus on Back; the countdown then ends.
    starts, _ = _run_curses(monkeypatch, wiz, [TAB, _ready, ENTER])
    assert starts == [] and wiz.screen == Screen.METHOD


def test_curses_restarted_countdown_returns_focus_to_back(monkeypatch):
    wiz = _at_last()
    starts, _ = _run_curses(monkeypatch, wiz, [_ready, TAB, _restart, ENTER])
    assert starts == [] and wiz.screen == Screen.METHOD


def test_handle_never_erases_on_a_bare_enter(monkeypatch):
    wiz = _at_last()
    _ready(wiz)
    assert wiz.erase_enabled
    starts = []
    monkeypatch.setattr(wiz, "confirm_erase", lambda: starts.append(True))
    for key in (10, 13, console.curses.KEY_ENTER):
        console._handle(wiz, key)
    assert starts == []
    assert wiz.screen == Screen.LAST_CHANCE and not wiz.runner.started


def test_curses_footer_matches_the_behaviour():
    wiz = _at_last()
    counting = console._primary_footer(wiz, False, False, "erase")
    # Erase now cannot hold focus while it is not enabled.
    assert counting[1] == f"[> {C.BTN_BACK} <]    [ {C.BTN_ERASE} ]"
    assert C.HINT_LAST_CHANCE_TK in counting
    assert not any("Enter to erase" in line for line in counting)
    _ready(wiz)
    ready = console._primary_footer(wiz, False, False, "erase")
    assert ready[0] == f"{C.COUNTDOWN_READY_WORD}. {C.COUNTDOWN_AVAILABLE}"
    assert ready[1] == f"[ {C.BTN_BACK} ]    [> {C.BTN_ERASE} <]"


def test_plain_console_still_requires_typing_erase(monkeypatch, capsys):
    wiz = _at_last()
    _ready(wiz)
    starts = []
    monkeypatch.setattr(wiz, "confirm_erase", lambda: starts.append(True))
    answers = iter(["", "erase now", "ERAS"])

    def answer(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", answer)
    console._plain_loop(wiz)
    assert starts == []


# --- Tk ------------------------------------------------------------------


@pytest.fixture
def tk_last():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build():
        _needs_display()
        wiz = _at_last()
        starts = []
        wiz.begin_erase = lambda: starts.append(wiz.screen)  # type: ignore[method-assign]
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry("1280x820+20+20")
        # The kiosk window holds the focus; take it first, as test_tk_runtime's
        # ui fixture does, so Review's own Back focus is what key events reach.
        app.root.focus_force()
        app.root.update()
        app._draw()
        for _ in range(8):
            app.root.update()
        return wiz, app, starts

    yield build
    for app in created:
        app._teardown()


def _press(app, key, t):
    target = app.root.focus_get() or app.root
    target.event_generate(f"<{key}>", time=t)
    app.root.event_generate(f"<KeyRelease-{key}>", time=t + 50)
    for _ in range(4):
        app.root.update()


def test_tk_enter_during_countdown_presses_back(tk_last):
    from test_tk_runtime import _button_named

    wiz, app, starts = tk_last()
    assert app.root.focus_get() is _button_named(app, C.BTN_BACK)
    assert not int(app._primary.cget("takefocus") or 0)  # Erase now not reachable yet
    _press(app, "Return", 10_000)
    assert starts == [] and wiz.screen == Screen.METHOD


def test_tk_enter_right_after_countdown_presses_back(tk_last):
    wiz, app, starts = tk_last()
    _ready(wiz)
    app._refresh_last_chance()
    app.root.update()
    _press(app, "Return", 20_000)
    assert starts == [] and wiz.screen == Screen.METHOD


def test_tk_tab_to_erase_now_then_enter_erases(tk_last):
    wiz, app, starts = tk_last()
    _ready(wiz)
    app._refresh_last_chance()
    app.root.update()
    app._primary.focus_set()
    app.root.update()
    _press(app, "Return", 30_000)
    assert starts == [Screen.LAST_CHANCE]


# --- GTK -----------------------------------------------------------------


def test_gtk_enter_presses_only_a_focused_enabled_action():
    pytest.importorskip("gi")
    from test_accessible_runtime import drain

    from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk

    wiz = _at_last()
    starts = []
    wiz.begin_erase = lambda: starts.append(wiz.screen)  # type: ignore[method-assign]
    app = AccessibleWizard(wiz)
    try:
        def enter(t):
            event = SimpleNamespace(keyval=Gdk.KEY_Return, time=t)
            app._key_press(app.window, event)
            app._key_release(app.window, SimpleNamespace(keyval=Gdk.KEY_Return, time=t + 50))

        def focus():
            drain()
            return app.window.get_focus()

        enter(1000)  # arrival focus is the warning, not a button
        assert starts == [] and wiz.screen == Screen.LAST_CHANCE
        assert focus() is not app.primary
        # During the countdown Erase now is insensitive. GTK never gives an
        # insensitive widget focus, so a grab cannot put Enter on it.
        assert not app.primary.get_sensitive()
        app.primary.grab_focus()
        assert focus() is not app.primary
        enter(2000)
        assert starts == [] and wiz.screen == Screen.LAST_CHANCE
        # The countdown ending enables Erase now but never moves focus to it.
        _ready(wiz)
        app.update_status()
        assert app.primary.get_sensitive() and focus() is not app.primary
        enter(3000)
        assert starts == [] and wiz.screen == Screen.LAST_CHANCE
        # Focused, then made insensitive again (a restarted review period):
        # the sensitivity check refuses it even if GTK keeps the focus there.
        app.primary.grab_focus()
        assert focus() is app.primary
        _restart(wiz)
        app.update_status()
        assert not app.primary.get_sensitive()
        enter(4000)
        assert starts == [] and wiz.screen == Screen.LAST_CHANCE
        # Only a deliberate move to the enabled Erase now, then a new Enter.
        _ready(wiz)
        app.update_status()
        app.primary.grab_focus()
        assert focus() is app.primary and app.primary.get_sensitive()
        enter(5000)
        assert starts == [Screen.LAST_CHANCE]
    finally:
        app.close()
        drain()
