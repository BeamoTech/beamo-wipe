# SPDX-License-Identifier: GPL-3.0-or-later
"""#144: power status is a persistent header badge.

States from the existing power reading: Plugged in (✓), On battery — plug in
(amber), Power: unknown (neutral), Mains power (desktop, no battery). Never
"Plugged in" unless wall power is reported online. Live through the existing
non-blocking monitor. Text always carries the state. The long sentence left
the Owner screen; erase-time power warnings are unchanged. Fake data only.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import power as Pw
from beamo_wipe.models import Screen
from beamo_wipe.power import PowerMonitor, PowerStatus
from beamo_wipe.wizard import make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]

STATES = {
    "plugged": (PowerStatus(ac=True, batteries=(80,), complete=True), "ok", Pw.BADGE_PLUGGED),
    "plugged_low": (PowerStatus(ac=True, batteries=(5,), complete=True), "ok", Pw.BADGE_PLUGGED),
    "battery": (PowerStatus(ac=False, batteries=(55,), complete=True), "warn", Pw.BADGE_BATTERY),
    "battery_low": (PowerStatus(ac=False, batteries=(12,), complete=True), "warn", Pw.BADGE_BATTERY),
    "unknown": (PowerStatus(), "neutral", Pw.BADGE_UNKNOWN),
    "battery_ac_unknown": (PowerStatus(ac=None, batteries=(70,), complete=True), "neutral", Pw.BADGE_UNKNOWN),
    "incomplete": (PowerStatus(ac=None, batteries=(), complete=False), "neutral", Pw.BADGE_UNKNOWN),
    "ac_off_no_battery": (PowerStatus(ac=False, batteries=(), complete=True), "neutral", Pw.BADGE_UNKNOWN),
    "desktop": (PowerStatus(complete=True), "neutral", Pw.BADGE_MAINS),
}


@pytest.mark.parametrize("name", list(STATES))
def test_badge_for_every_power_state(name):
    status, kind, text = STATES[name]
    badge = status.badge
    assert (badge.kind, badge.text) == (kind, text)


def test_never_plugged_in_unless_reported_online():
    for status, _kind, _text in STATES.values():
        if status.ac is not True:
            assert status.badge.text != Pw.BADGE_PLUGGED
            assert "✓" not in status.badge.display


def test_text_carries_the_state_not_colour_or_symbol_alone():
    plugged = STATES["plugged"][0].badge
    assert plugged.display == "Plugged in ✓"
    assert plugged.spoken == "Power: Plugged in"
    assert STATES["battery"][0].badge.display == "On battery — plug in"
    assert STATES["unknown"][0].badge.spoken == "Power: unknown"
    assert STATES["desktop"][0].badge.spoken == "Power: Mains power"


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_the_badge(code):
    from beamo_wipe import lang

    english = {n: getattr(Pw, n) for n in ("BADGE_PLUGGED", "BADGE_BATTERY", "BADGE_UNKNOWN",
                                            "BADGE_MAINS", "BADGE_SPOKEN")}
    try:
        lang.set_language(code)
        for name, value in english.items():
            assert getattr(Pw, name) != value, (code, name)
        assert "{state}" in Pw.BADGE_SPOKEN
        assert PowerStatus(ac=True).badge.text == Pw.BADGE_PLUGGED
    finally:
        lang.set_language("en")


# --- Live and non-blocking ------------------------------------------------------------------


def test_unplugging_shows_on_the_next_reading_without_blocking():
    readings = iter([STATES["plugged"][0], STATES["battery"][0], STATES["plugged"][0]])
    gate = threading.Event()
    calls = []

    def reader():
        calls.append(1)
        if len(calls) == 2:
            gate.wait(5)  # a slow driver on the second reading
        return next(readings)

    monitor = PowerMonitor(reader)
    now = 0.0
    monitor.tick(now)
    _wait(lambda: not monitor._results.empty())
    monitor.tick(now)
    assert monitor.status.badge.kind == "ok"
    now += Pw.REFRESH_SECONDS
    started = time.monotonic()
    monitor.tick(now)  # starts the slow read on a worker
    assert time.monotonic() - started < 0.5  # never waits for the driver
    assert monitor.status.badge.kind == "ok"
    gate.set()
    _wait(lambda: not monitor._results.empty())
    monitor.tick(now + 0.1)
    assert monitor.status.badge.kind == "warn"  # unplugged
    assert monitor.status.badge.text == Pw.BADGE_BATTERY


def _wait(predicate, timeout=5.0):
    end = time.monotonic() + timeout
    while not predicate() and time.monotonic() < end:
        time.sleep(0.01)
    assert predicate()


def test_a_stuck_reading_turns_unknown_never_stays_plugged_in():
    monitor = PowerMonitor(lambda: STATES["plugged"][0])
    monitor.tick(0.0)
    _wait(lambda: not monitor._results.empty())
    monitor.tick(0.0)
    assert monitor.status.badge.kind == "ok"
    monitor.tick(Pw.STALE_SECONDS + 1)  # sampled too long ago
    assert monitor.status.badge.text == Pw.BADGE_UNKNOWN


def test_wizard_badge_follows_the_monitor():
    wiz = make_demo_wizard()
    for status, kind, text in STATES.values():
        wiz.power.status = status
        assert (wiz.power_badge.kind, wiz.power_badge.text) == (kind, text)


# --- Consoles, GTK (source), web preview ------------------------------------------------------


def _owner_wizard(status):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.power.status = status
    return wiz


@pytest.mark.parametrize("name", ["plugged", "battery", "unknown", "desktop"])
def test_curses_header_carries_the_badge_on_80_columns(name):
    from beamo_wipe.ui import console_wizard as console

    status, _kind, text = STATES[name]
    for screen in (Screen.OWNER, Screen.PICK):
        wiz = _owner_wizard(status)
        if screen == Screen.PICK:
            wiz.set_owner(True)
            wiz.continue_owner()
        lines = console._chrome_lines(wiz, 80)
        assert f"[{text}]" in lines[0]
        assert all(len(line) <= 80 for line in lines)
        assert len(lines) <= 2  # never a second header row (plus preview banner)


def test_curses_owner_body_drops_the_sentence(monkeypatch):
    from test_plain_result_134 import _curses_lines

    wiz = _owner_wizard(STATES["unknown"][0])
    body = "\n".join(_curses_lines(monkeypatch, wiz, h=80))
    assert wiz.power_text not in body
    assert C.POWER_REMINDER[:30] in body


def test_plain_console_owner_prints_the_badge_not_the_sentence(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _owner_wizard(STATES["battery"][0])

    def stop(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    assert wiz.power_badge.spoken in out
    assert wiz.power_text not in out


def test_gtk_badge_on_every_screen_named_and_live():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    render = src[src.index("    def render(self):"):]
    render = render[:render.index("\n    def ")]
    assert "self.power_badge_label = Gtk.Label(label=badge.display)" in render
    assert "get_accessible().set_name(badge.spoken)" in render
    status = src[src.index("    def update_status(self):"):]
    status = status[:status.index("\n    def ")]
    assert "label.set_text(badge.display)" in status and "set_name(badge.spoken)" in status
    # Owner no longer carries the sentence; erase screens keep it.
    assert "if screen in {Screen.LAST_CHANCE, Screen.CHECKING, Screen.WORKING, Screen.STOPPING}:" in src


def test_web_preview_header_badge():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert 'id="power-badge" role="status" aria-live="polite"' in html
    assert "function renderPowerBadge()" in html
    import json
    import re

    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    badges = payload["powerBadges"]
    assert badges["ac"] == {"kind": "ok", "display": "Plugged in ✓", "spoken": "Power: Plugged in"}
    assert badges["battery"]["kind"] == "warn" and badges["unknown"]["display"] == Pw.BADGE_UNKNOWN
    assert badges["desktop"]["display"] == Pw.BADGE_MAINS


# --- Rendered Tk ------------------------------------------------------------------------------


@pytest.fixture
def tk_app():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(wiz, size=(800, 600)):
        _needs_display()
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return app

    yield build
    for app in created:
        app._teardown()


def _header_texts(app):
    cv = app._header
    return [cv.itemcget(item, "text") for item in cv.find_all() if cv.type(item) == "text"]


@pytest.mark.parametrize("name", ["plugged", "battery", "unknown", "desktop"])
def test_tk_header_badge_per_state(tk_app, name):
    status, _kind, _text = STATES[name]
    app = tk_app(_owner_wizard(status))
    assert status.badge.display in _header_texts(app)
    assert status.badge.display != "" and app._header.find_withtag("power_badge")


@pytest.mark.parametrize("screen", [Screen.PICK, Screen.CONFIRM, Screen.METHOD, Screen.LAST_CHANCE])
def test_tk_badge_on_every_screen_with_a_header(tk_app, screen):
    from test_tk_runtime import _drive_to

    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.power.status = STATES["battery"][0]
    app = tk_app(wiz)
    _drive_to(wiz, app, screen)
    app._draw()
    app.root.update()
    assert Pw.BADGE_BATTERY in _header_texts(app)


def test_tk_unplugging_updates_the_badge_live(tk_app):
    wiz = _owner_wizard(STATES["plugged"][0])
    app = tk_app(wiz)
    assert "Plugged in ✓" in _header_texts(app)
    wiz.power.status = STATES["battery"][0]
    app._tick()
    app.root.update()
    texts = _header_texts(app)
    assert Pw.BADGE_BATTERY in texts and "Plugged in ✓" not in texts


def test_tk_owner_drops_the_sentence_but_review_keeps_its_warning(tk_app):
    from test_tk_runtime import _drive_to

    wiz = _owner_wizard(STATES["unknown"][0])
    app = tk_app(wiz)

    def labels():
        def walk(widget):
            yield widget
            for child in widget.winfo_children():
                yield from walk(child)
        return [str(w.cget("text")) for w in walk(app._body) if w.winfo_class() == "Label"]

    assert wiz.power_text not in labels()
    assert C.POWER_REMINDER in labels()
    _drive_to(wiz, app, Screen.LAST_CHANCE)
    app._draw()
    app.root.update()
    assert wiz.power_text in labels()  # erase-time warnings unchanged (#165/#183)


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_header_fits_800x600(tk_app, text_size):
    from test_tk_runtime import _off_window_problems

    wiz = _owner_wizard(STATES["battery"][0])
    wiz.text_size = text_size
    app = tk_app(wiz)
    cv = app._header
    x0, _y0, x1, _y1 = cv.bbox("power_badge")
    assert 0 <= x0 and x1 <= cv.winfo_width()
    assert _off_window_problems(app) == []
