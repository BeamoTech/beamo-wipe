# SPDX-License-Identifier: GPL-3.0-or-later
"""#150: double-click or Enter on a disk opens Review this disk.

The activation is exactly the footer's Review this disk (wizard.continue_pick):
it only opens the Confirm step. The token is always empty there, so the owner
still types it, picks a method, waits out the five-second review and presses
Erase now. A disk that cannot be confirmed stays on Pick with the reason. A
double-click is recognised by disk identity (path), and the rest of it cannot
press a control on the next screen. Parity: Tk, GTK (a disk button's
activation is its row-activated), curses and the plain console (Enter /
number), and the web preview. Fake lsblk data and fake disks only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from beamo_wipe import copy as C, lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.discover import discover
from beamo_wipe.identity import AMBIGUOUS_IDENTITY
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at_pick(wiz):
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def _demo_pick():
    return _at_pick(make_demo_wizard())


def _ambiguous_pick():
    payload = json.loads((FIXTURES / "lsblk_identical_missing_serial.json").read_text(encoding="utf-8"))
    result = discover(lsblk_payload=payload, boot_path="/dev/sdb", mount_sources=[], cmdline="",
                      env={"BEAMO_WIPE_DRY_RUN": "1"})
    wiz = _at_pick(Wizard(result, DryRunRunner(), dry_run=True))
    assert len(wiz.selectable) == 2
    assert not any(wiz.disk_view(d).confirmable for d in wiz.selectable)
    return wiz


def _assert_only_review(wiz, path):
    """Confirm is open for that disk and nothing after it was granted."""
    assert wiz.screen == Screen.CONFIRM
    assert wiz.selected is not None and wiz.selected.path == path
    assert wiz.confirm_input == ""
    assert not wiz.token_ok
    assert wiz._authorized_operation is None
    assert not wiz.erase_enabled
    assert not wiz.runner.started
    # The next gate still holds: no token, no Method screen.
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM


# -- Tk ------------------------------------------------------------------


@pytest.fixture
def tk_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(wiz=None, size=(800, 600)):
        _needs_display()
        wiz = wiz or _demo_pick()
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        _settle(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _settle(app):
    for _ in range(6):
        app.root.update()


def _press(app, path, when, root=(300, 200)):
    """A mouse press on that disk's row (on its current widget)."""
    card = app._pick_cards[path]
    card.inner.event_generate(
        "<ButtonPress-1>", x=5, y=5, rootx=root[0], rooty=root[1], time=when,
    )
    _settle(app)


def _click_button(app, button, when):
    button.event_generate("<ButtonPress-1>", x=4, y=4, time=when)
    button.event_generate("<ButtonRelease-1>", x=4, y=4, time=when + 40)
    _settle(app)


def _button_named(app, text):
    from beamo_wipe.ui.tk_wizard import _Button

    found = []

    def visit(widget):
        if isinstance(widget, _Button) and widget.itemcget(widget._label, "text") == text:
            found.append(widget)
        for child in widget.winfo_children():
            visit(child)

    visit(app.root)
    assert len(found) == 1, (text, len(found))
    return found[0]


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_double_click_on_a_disk_opens_review_only(tk_app, size):
    wiz, app = tk_app(size=size)
    path = sorted(d.path for d in wiz.selectable)[1]
    assert getattr(app._pick_cards[path], "_beamo_compact_row", False)
    _press(app, path, 10_000)
    assert wiz.screen == Screen.PICK and wiz.selected.path == path  # first press selects
    _press(app, path, 10_180)  # same disk, now its expanded card
    _assert_only_review(wiz, path)


def test_tk_double_click_never_carries_a_typed_token_forward(tk_app):
    wiz, app = tk_app()
    path = wiz.selectable[0].path
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    assert wiz.token_ok
    wiz.back()
    assert wiz.screen == Screen.PICK
    app._draw()
    _settle(app)
    _press(app, path, 20_000)
    _press(app, path, 20_150)
    _assert_only_review(wiz, path)


def test_tk_second_press_on_another_disk_only_selects_it(tk_app):
    # Rows move when the chosen one expands: the second press of a quick
    # pair can land on a different disk. That is a click on that disk.
    wiz, app = tk_app()
    first, second = sorted(d.path for d in wiz.selectable)[:2]
    _press(app, first, 30_000)
    _press(app, second, 30_120)
    assert wiz.screen == Screen.PICK
    assert wiz.selected.path == second


@pytest.mark.parametrize(
    "gap,moved",
    [(700, (0, 0)), (120, (40, 0)), (120, (0, 30))],
    ids=["too-slow", "moved-sideways", "moved-down"],
)
def test_tk_slow_or_distant_presses_are_two_clicks(tk_app, gap, moved):
    wiz, app = tk_app()
    path = wiz.selectable[0].path
    _press(app, path, 40_000, root=(300, 200))
    _press(app, path, 40_000 + gap, root=(300 + moved[0], 200 + moved[1]))
    assert wiz.screen == Screen.PICK
    assert wiz.selected.path == path


def test_tk_double_click_is_the_footer_review_action(tk_app):
    # The double-click presses Review this disk itself: when that button
    # is not available nothing happens.
    wiz, app = tk_app()
    path = wiz.selectable[0].path
    _press(app, path, 50_000)
    review = _button_named(app, C.BTN_REVIEW_DISK)
    assert app._primary is review and review._enabled
    review.set_enabled(False)
    _press(app, path, 50_100)
    assert wiz.screen == Screen.PICK


def test_tk_rest_of_the_double_click_cannot_press_a_confirm_control(tk_app):
    wiz, app = tk_app()
    path = wiz.selectable[0].path
    _press(app, path, 60_000)
    _press(app, path, 60_150)
    assert wiz.screen == Screen.CONFIRM
    back = _button_named(app, C.BTN_BACK)
    more = _button_named(app, C.BTN_MORE)
    # The tail of the double-click and a quick third click land on Confirm.
    _click_button(app, back, 60_200)
    _click_button(app, more, 60_400)
    assert wiz.screen == Screen.CONFIRM
    assert not app._show_more
    # After the double-click window the controls work as before.
    _click_button(app, back, 60_800)
    assert wiz.screen == Screen.PICK


def test_tk_double_click_on_an_unconfirmable_disk_shows_the_reason(tk_app):
    wiz, app = tk_app(_ambiguous_pick())
    path = sorted(d.path for d in wiz.selectable)[0]
    _press(app, path, 70_000)
    _press(app, path, 70_100)
    assert wiz.screen == Screen.PICK
    assert wiz.error == AMBIGUOUS_IDENTITY
    assert wiz.confirm_input == "" and not wiz.runner.started
    # And the next pointer press is not swallowed: nothing advanced.
    assert app._pointer_quiet_until is None


def test_tk_protected_usb_card_is_never_chosen(tk_app):
    wiz, app = tk_app()
    boot = wiz.protected_boot
    assert boot is not None

    def find(widget):
        if getattr(widget, "_beamo_protected_boot", False):
            return widget
        for child in widget.winfo_children():
            hit = find(child)
            if hit is not None:
                return hit
        return None

    card = find(app.root)
    assert card is not None
    for when in (80_000, 80_100, 80_200):
        card.inner.event_generate("<ButtonPress-1>", x=5, y=5, rootx=300, rooty=200, time=when)
        card.inner.event_generate("<ButtonRelease-1>", x=5, y=5, rootx=300, rooty=200, time=when + 30)
        _settle(app)
    assert wiz.screen == Screen.PICK
    assert wiz.selected is None


def test_tk_enter_on_the_selected_disk_opens_review_once(tk_app):
    wiz, app = tk_app()
    app.root.focus_force()
    _settle(app)
    app.root.event_generate("<Down>")
    _settle(app)
    path = wiz.selected.path
    target = app.root.focus_get() or app.root
    target.event_generate("<Return>", time=90_000)
    _settle(app)
    _assert_only_review(wiz, path)
    # X11 autorepeat: a release/press pair with one timestamp, still held.
    app.root.event_generate("<KeyRelease-Return>", time=90_050)
    (app.root.focus_get() or app.root).event_generate("<Return>", time=90_050)
    _settle(app)
    assert wiz.screen == Screen.CONFIRM and wiz.confirm_input == ""


def test_tk_enter_on_an_unconfirmable_disk_shows_the_reason(tk_app):
    wiz, app = tk_app(_ambiguous_pick())
    app.root.focus_force()
    _settle(app)
    app.root.event_generate("<Down>")
    _settle(app)
    (app.root.focus_get() or app.root).event_generate("<Return>", time=95_000)
    _settle(app)
    assert wiz.screen == Screen.PICK
    assert wiz.error == AMBIGUOUS_IDENTITY


def test_tk_enter_in_other_devices_never_advances(tk_app):
    wiz, app = tk_app()
    assert wiz.other_devices
    wiz.select_disk(wiz.selectable[0].path)
    app._draw()
    _settle(app)

    def find(widget):
        if getattr(widget, "_beamo_inventory", False):
            return widget
        for child in widget.winfo_children():
            hit = find(child)
            if hit is not None:
                return hit
        return None

    reader = find(app.root)
    assert reader is not None
    reader.focus_force()
    _settle(app)
    reader.event_generate("<Return>", time=96_000)
    _settle(app)
    assert wiz.screen == Screen.PICK


# -- GTK (fake gi in a subprocess; the real AccessibleWizard methods) ------

_GTK_SCRIPT = r'''
import json, sys
from types import ModuleType, SimpleNamespace

class Widget:
    def __init__(self, text=""):
        self.text = text
        self.sensitive = True
        self.handlers = {}
    def get_child(self): return self
    def get_children(self): return []
    def get_accessible(self): return self
    def get_style_context(self): return self
    def get_sensitive(self): return self.sensitive
    def set_sensitive(self, value): self.sensitive = value
    def connect(self, name, fn): self.handlers[name] = fn
    def click(self): self.handlers["clicked"](self)
    def __getattr__(self, _name): return lambda *_a, **_k: None

current = [None]
gtk = SimpleNamespace(
    Button=SimpleNamespace(new_with_label=lambda text: Widget(text)),
    get_current_event=lambda: current[0],
)
EV = SimpleNamespace(BUTTON_PRESS=4, _2BUTTON_PRESS=5, BUTTON_RELEASE=7, KEY_PRESS=8)
repo = ModuleType("gi.repository")
repo.Gtk = gtk
repo.Gdk = SimpleNamespace(CURRENT_TIME=0, EventType=EV)
repo.GLib = SimpleNamespace()
repo.Pango = SimpleNamespace(WrapMode=SimpleNamespace(WORD=1, WORD_CHAR=2))
repo.Atk = SimpleNamespace(Role=SimpleNamespace(PANEL=1, ALERT=2))
gi = ModuleType("gi")
gi.require_version = lambda *_a: None
gi.repository = repo
sys.modules["gi"] = gi
sys.modules["gi.repository"] = repo

import json as _json
from beamo_wipe import copy as C
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.discover import discover
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard
from beamo_wipe.ui import accessible_wizard as accessible

def pointer(t): return SimpleNamespace(type=EV.BUTTON_RELEASE, get_time=lambda: t)
def key(t): return SimpleNamespace(type=EV.KEY_PRESS, get_time=lambda: t)

def at_pick(wiz):
    wiz.preview = False
    wiz.skip_intro(); wiz.set_owner(True); wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz

def ui_for(wiz):
    ui = object.__new__(accessible.AccessibleWizard)
    ui.w = wiz
    ui.generation = 0
    ui.closed = False
    ui.actions = {}
    ui.body = Widget()
    ui.navigation = Widget()
    ui.utilities = Widget()
    ui._utility_count = 0
    ui.render = lambda: None
    return ui

out = {}
# Pointer: one click on a disk button opens Review; the rest of a
# double-click cannot press a Confirm control; later clicks work.
wiz = at_pick(make_demo_wizard())
ui = ui_for(wiz)
path = sorted(d.path for d in wiz.selectable)[0]
disk = ui.button("disk", lambda: ui._select(path), in_body=True)
current[0] = pointer(1000)
disk.click()
out["pointer_screen"] = wiz.screen.name
out["pointer_token"] = wiz.confirm_input
out["quiet_until"] = ui._pointer_quiet_until
back = ui.button(C.BTN_BACK, wiz.back)
current[0] = pointer(1300)
back.click()
out["tail_screen"] = wiz.screen.name
current[0] = key(1350)
back.click()
out["key_back_screen"] = wiz.screen.name
# Keyboard (Enter/Space on the button) or Orca's press: no guard is set.
wiz.select_disk(path)
current[0] = key(2000)
ui._pointer_quiet_until = None
disk2 = ui.button("disk2", lambda: ui._select(path), in_body=True)
disk2.click()
out["key_screen"] = wiz.screen.name
out["key_quiet"] = ui._pointer_quiet_until
current[0] = None
back2 = ui.button(C.BTN_BACK + " ", wiz.back)
back2.click()
out["atspi_back_screen"] = wiz.screen.name
# After the window, pointer clicks work again.
current[0] = pointer(3000)
disk3 = ui.button("disk3", lambda: ui._select(path), in_body=True)
disk3.click()
current[0] = pointer(3600)
back3 = ui.button(C.BTN_BACK + "  ", wiz.back)
back3.click()
out["late_back_screen"] = wiz.screen.name
# A typed token never survives Back + reactivation.
wiz.select_disk(path); wiz.continue_pick(); wiz.set_confirm_input(wiz.confirm.token)
assert wiz.token_ok
wiz.back()
current[0] = key(4000)
ui._select(path)
out["retoken_screen"] = wiz.screen.name
out["retoken_input"] = wiz.confirm_input
# A disk that cannot be confirmed stays on Pick with the reason.
payload = _json.loads(open(sys.argv[1], encoding="utf-8").read())
result = discover(lsblk_payload=payload, boot_path="/dev/sdb", mount_sources=[], cmdline="",
                  env={"BEAMO_WIPE_DRY_RUN": "1"})
amb = at_pick(Wizard(result, DryRunRunner(), dry_run=True))
ui2 = ui_for(amb)
current[0] = pointer(5000)
ui2._select(sorted(d.path for d in amb.selectable)[0])
out["ambiguous_screen"] = amb.screen.name
out["ambiguous_error"] = amb.error
out["ambiguous_quiet"] = getattr(ui2, "_pointer_quiet_until", None)
out["started"] = wiz.runner.started or amb.runner.started
print(json.dumps(out))
'''


def test_gtk_disk_activation_opens_review_and_guards_the_double_click():
    result = subprocess.run(
        [sys.executable, "-c", _GTK_SCRIPT, str(FIXTURES / "lsblk_identical_missing_serial.json")],
        cwd=ROOT,
        env={**os.environ, "BEAMO_WIPE_DRY_RUN": "1",
             "PYTHONPATH": os.pathsep.join(filter(None, [str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]))},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip().splitlines()[-1])
    assert out["pointer_screen"] == "CONFIRM" and out["pointer_token"] == ""
    assert out["quiet_until"] == 1500
    assert out["tail_screen"] == "CONFIRM"  # second click of the double-click
    assert out["key_back_screen"] == "PICK"  # a key press is never swallowed
    assert out["key_screen"] == "CONFIRM" and out["key_quiet"] is None
    assert out["atspi_back_screen"] == "PICK"
    assert out["late_back_screen"] == "PICK"
    assert out["retoken_screen"] == "CONFIRM" and out["retoken_input"] == ""
    assert out["ambiguous_screen"] == "PICK"
    assert out["ambiguous_error"] == AMBIGUOUS_IDENTITY
    assert out["ambiguous_quiet"] is None
    assert out["started"] is False


def test_gtk_source_disk_button_is_review_and_clicks_check_the_guard():
    source = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    select = source[source.index("    def _select(self, path):"):]
    select = select[:select.index("\n    def _owner(")]
    assert "self.w.select_disk(path)" in select and "self.w.continue_pick()" in select
    clicked = source[source.index("        def clicked(_button):"):]
    clicked = clicked[:clicked.index('widget.connect("clicked", clicked)')]
    assert clicked.index("_pointer_quiet(") < clicked.index("action()")


# -- curses and plain console ---------------------------------------------


def _curses_run(monkeypatch, wiz, events):
    from beamo_wipe.ui import console_wizard as console

    def forbidden(*_args, **_kwargs):
        raise AssertionError("A device or application action was reached")

    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    keys = iter(events)

    class Terminal:
        def getmaxyx(self):
            return 24, 80

        def keypad(self, *_args):
            pass

        def nodelay(self, *_args):
            pass

        def timeout(self, *_args):
            pass

        def erase(self):
            pass

        def addstr(self, *_args):
            pass

        def refresh(self):
            pass

        def getch(self):
            try:
                return next(keys)
            except StopIteration:
                wiz.wants_shutdown = True
                return -1

    now = [0.0]

    def monotonic():
        now[0] += 1.0
        return now[0]

    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda *_args: None)
    monkeypatch.setattr(console.time, "monotonic", monotonic)
    assert console._loop(Terminal(), wiz) == 0


def test_curses_enter_on_the_highlighted_disk_opens_review_once(monkeypatch):
    import curses

    wiz = _demo_pick()
    # Down highlights the first disk; Enter reviews it; the held Enter
    # (no key-up yet) cannot do anything on Confirm.
    _curses_run(monkeypatch, wiz, [curses.KEY_DOWN, 10, 10, 10])
    first = sorted(d.path for d in wiz.selectable)[0]
    assert wiz.screen == Screen.CONFIRM
    assert wiz.selected.path == first
    assert wiz.confirm_input == "" and not wiz.token_ok
    assert not wiz.runner.started


def test_curses_enter_on_an_unconfirmable_disk_shows_the_reason(monkeypatch):
    import curses

    wiz = _ambiguous_pick()
    _curses_run(monkeypatch, wiz, [curses.KEY_DOWN, 10])
    assert wiz.screen == Screen.PICK
    assert wiz.error == AMBIGUOUS_IDENTITY


def test_plain_console_number_is_review_this_disk(monkeypatch):
    from beamo_wipe.ui.console_wizard import _plain_loop

    wiz = _demo_pick()
    answers = iter(["1"])
    screens = []

    def fake_input(_prompt=""):
        screens.append(wiz.screen)
        try:
            return next(answers)
        except StopIteration:
            wiz.shutdown()
            return ""

    monkeypatch.setattr("builtins.input", fake_input)
    _plain_loop(wiz)
    assert screens[:2] == [Screen.PICK, Screen.CONFIRM]
    assert wiz.confirm_input == "" and not wiz.runner.started


# -- web preview ----------------------------------------------------------


def _gallery_source():
    from beamo_wipe.gallery import gallery_html

    return gallery_html()


def test_preview_source_enter_reviews_space_selects_double_click_by_disk():
    html = _gallery_source()
    review = html[html.index("function reviewDisk(pointer)"):]
    review = review[:review.index("\n}\n")]
    # The same condition as the footer button; Confirm starts with no token.
    assert 'if (screen !== "pick" || !selected || selected.isBoot) return;' in review
    assert 'screen = "confirm"; token = "";' in review
    assert "btn(P.buttons.reviewDisk, () => reviewDisk(false)" in html
    cards = html[html.index('main.querySelectorAll(".card.pickable").forEach'):]
    cards = cards[:cards.index("renderHint(P.hints.pick)")]
    assert 'if (e.key === " ") { e.preventDefault(); pick(); }' in cards
    assert 'e.key === "Enter"' in cards and "if (!e.repeat) { pick(); reviewDisk(false); }" in cards
    assert "last.path === path" in cards and "selected.path === path" in cards
    assert "reviewDisk(true)" in cards
    # The rest of a double-click is swallowed before any control sees it.
    assert 'for (const type of ["mousedown", "mouseup", "click", "dblclick"])' in html
    guard = html[html.index('for (const type of ["mousedown"'):]
    guard = guard[:guard.index("}, true);")]
    assert "e.timeStamp <= pointerQuietUntil" in guard and "e.stopPropagation()" in guard


@pytest.mark.parametrize("size", [(1024, 740), (1280, 820)])
def test_preview_browser_enter_and_double_click_open_review(tmp_path, size):
    import shutil

    api = pytest.importorskip("playwright.sync_api")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        pytest.skip("Chrome unavailable")
    html = tmp_path / "index.html"
    html.write_text(_gallery_source(), encoding="utf-8")
    with api.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(html.as_uri() + "#s=pick&owner=1")
        card = page.locator(".card.pickable").first
        card.focus()
        page.keyboard.press("Space")
        assert page.evaluate("screen") == "pick"
        page.locator(".card.pickable").first.focus()
        page.keyboard.press("Enter")
        assert page.evaluate("screen") == "confirm"
        assert page.evaluate("token") == ""
        page.keyboard.press("Escape")
        page.goto(html.as_uri() + "#s=pick&owner=1")
        page.reload()
        box = page.locator(".card.pickable").nth(1).bounding_box()
        page.mouse.dblclick(box["x"] + 20, box["y"] + 12)
        assert page.evaluate("screen") == "confirm"
        assert page.evaluate("token") == ""
        assert not errors
        browser.close()
