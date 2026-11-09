# SPDX-License-Identifier: GPL-3.0-or-later
"""#175: one fixed Help & settings menu instead of changing footer links.

Every screen offers the same menu in the same place: Text size, Language
and keyboard, Sounds, High contrast, Report help, Advanced and Keyboard
shortcuts. An item that does not apply is disabled with a reason instead of
disappearing; Advanced keeps its limit (Method only). Opening the menu
changes nothing, Esc closes it and focus returns to its button, and no key
pressed while it is open reaches the screen behind it. Fake disks only;
erase starts are recorded, never run.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import time as real_time
from types import SimpleNamespace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import help_menu as M
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console
from preview_page import inline_script

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTER, ESC, TAB = 10, 27, 9
OLD_FOOTER_LINKS = (C.KEYBOARD_UTILITY, C.REPORT_HELP_TITLE, C.BTN_ADVANCED, C.TEXT_SIZE_UTILITY,
                    C.SOUND_TOGGLE_ON, C.SOUND_TOGGLE_OFF)


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _wizard_at(name: str):
    wiz = make_demo_wizard()
    wiz.preview = False
    if name == "splash":
        return wiz
    wiz.skip_splash()
    if name == "keyboard":
        return wiz
    wiz.skip_intro()
    if name == "owner":
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if name == "pick":
        return wiz
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    if name == "confirm":
        return wiz
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    if name == "method":
        return wiz
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


def _state(wiz):
    return (wiz.screen, wiz.text_size, wiz.sounds_enabled, wiz.owner_ok, wiz.confirm_input,
            wiz.method, wiz.language, wiz.keyboard_layout, wiz.runner.started)


# --- the shared model --------------------------------------------------------


@pytest.mark.parametrize("screen", list(Screen), ids=lambda s: s.name)
def test_every_screen_lists_every_item_in_the_same_order(screen):
    wiz = _wizard_at("method")
    wiz.screen = screen
    menu = wiz.help_menu()
    assert tuple(item.key for item in menu) == M.ORDER
    for item in menu:
        assert item.label and "{" not in item.label
        assert item.enabled or item.reason, item.key  # never disabled without a reason
    assert M.find(menu, M.HIGH_CONTRAST).enabled is True  # #179: a working setting
    assert M.find(menu, M.SHORTCUTS).enabled is True
    # Advanced keeps its existing limit: the method step only.
    assert M.find(menu, M.ADVANCED).enabled is (screen == Screen.METHOD)
    assert M.find(menu, M.TEXT_SIZE).enabled is (screen not in M.TEXT_SIZE_LOCKED)


@pytest.mark.parametrize("name", ["splash", "keyboard", "owner", "pick", "confirm", "method", "last"])
def test_reading_the_menu_changes_nothing(name):
    wiz = _wizard_at(name)
    before = _state(wiz)
    for _ in range(3):
        wiz.help_menu()
        wiz.help_menu(text_size_supported=False)
    assert _state(wiz) == before


def test_items_never_start_an_erase_on_a_ready_review():
    for key in M.ORDER:
        wiz = _wizard_at("last")
        wiz._erase_until = 0
        assert wiz.erase_enabled
        starts = []
        wiz.begin_erase = lambda: starts.append(key)  # type: ignore[method-assign]
        wiz.confirm_erase = lambda: starts.append(key)  # type: ignore[method-assign]
        wiz.activate_help_item(key)
        assert starts == [] and not wiz.runner.started
        assert wiz.screen in (Screen.LAST_CHANCE, Screen.KEYBOARD)


def test_advanced_opens_only_from_the_method_step():
    wiz = _wizard_at("pick")
    assert not wiz.activate_help_item(M.ADVANCED)
    assert wiz.screen == Screen.PICK
    assert M.find(wiz.help_menu(), M.ADVANCED).reason == C.MENU_REASON_ADVANCED
    wiz = _wizard_at("method")
    assert wiz.activate_help_item(M.ADVANCED)
    assert wiz.screen == Screen.ADVANCED
    assert M.find(wiz.help_menu(), M.ADVANCED).reason == C.MENU_REASON_HERE


def test_disabled_items_do_nothing_and_say_why():
    wiz = _wizard_at("last")
    size = M.find(wiz.help_menu(), M.TEXT_SIZE)
    assert not size.enabled and size.reason == C.MENU_REASON_FINAL_CHECK
    assert not wiz.activate_help_item(M.TEXT_SIZE)
    assert wiz.text_size == "standard"
    assert wiz.activate_help_item(M.HIGH_CONTRAST) and wiz.high_contrast  # #179
    assert wiz.screen == Screen.LAST_CHANCE and wiz.text_size == "standard"
    assert not wiz.activate_help_item("no-such-item")
    wiz.screen = Screen.WORKING
    wiz.audio_available = False
    sounds = M.find(wiz.help_menu(), M.SOUNDS)
    assert not sounds.enabled and sounds.reason == C.MENU_REASON_NO_SOUND
    language = M.find(wiz.help_menu(), M.LANGUAGE)
    assert not language.enabled and language.reason == C.MENU_REASON_LANGUAGE_BEFORE


def test_settings_change_and_the_keyboard_returns_to_its_screen():
    wiz = _wizard_at("pick")
    assert wiz.activate_help_item(M.TEXT_SIZE) and wiz.text_size == "large"
    sounds = wiz.sounds_enabled
    assert wiz.activate_help_item(M.SOUNDS) and wiz.sounds_enabled is not sounds
    assert wiz.activate_help_item(M.LANGUAGE) and wiz.screen == Screen.KEYBOARD
    wiz.accept_keyboard()
    assert wiz.screen == Screen.PICK
    wiz = _wizard_at("owner")
    assert wiz.activate_help_item(M.REPORT_HELP) and wiz.screen == Screen.REPORT_HELP


def test_console_text_size_is_disabled_with_the_console_reason():
    wiz = _wizard_at("pick")
    size = M.find(wiz.help_menu(text_size_supported=False), M.TEXT_SIZE)
    assert not size.enabled and size.reason == C.TEXT_SIZE_CONSOLE
    assert not wiz.activate_help_item(M.TEXT_SIZE, text_size_supported=False)


def test_every_language_has_the_menu_words():
    names = [n for n in dir(C) if n.startswith(("MENU_", "CON_MENU_"))]
    assert len(names) >= 20
    english = {n: getattr(C, n) for n in names}
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for name in names:
            value = getattr(C, name)
            assert value and "{" not in value, (code, name)
            if code != "en" and name not in {"MENU_SHORTCUTS_REFRESH"}:
                assert value != english[name] or name == "MENU_KEY", (code, name)
        menu = _wizard_at("pick").help_menu()
        assert [item.key for item in menu] == list(M.ORDER)


# --- Tk ------------------------------------------------------------------------


@pytest.fixture
def tk_at():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(name, size=(1280, 820), wiz=None):
        _needs_display()
        wiz = wiz or _wizard_at(name)
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app.root.focus_force()
        app.root.update()
        app._draw()
        for _ in range(8):
            app.root.update()
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _press(app, key, t):
    target = app.root.focus_get() or app.root
    target.event_generate(f"<{key}>", time=t)
    app.root.event_generate(f"<KeyRelease-{key}>", time=t + 50)
    for _ in range(4):
        app.root.update()


def _buttons(widget):
    from beamo_wipe.ui.tk_wizard import _Button

    found = []

    def visit(w):
        if isinstance(w, _Button) and w.winfo_ismapped():
            found.append(w)
        for child in w.winfo_children():
            visit(child)

    visit(widget)
    return found


def _text(button):
    return str(button.itemcget(button._label, "text"))


@pytest.mark.parametrize("name", ["splash", "keyboard", "owner", "pick", "confirm", "method", "last"])
def test_tk_menu_button_is_first_in_the_footer_on_every_screen(tk_at, name):
    _wiz, app = tk_at(name)
    footer = _buttons(app._footer)
    assert footer and _text(footer[0]) == C.MENU_TITLE
    assert getattr(footer[0], "_beamo_help_menu", False)
    texts = [_text(b) for b in footer]
    for old in OLD_FOOTER_LINKS:
        assert not any(t.startswith(old) for t in texts), (name, old, texts)


def test_tk_f10_opens_esc_closes_and_focus_returns(tk_at):
    wiz, app = tk_at("pick")
    before = _state(wiz)
    _press(app, "F10", 1000)
    assert app._help_open and app._help_popup is not None
    assert app._in_help_menu(app.root.focus_get())
    assert _state(wiz) == before  # opening changed nothing
    _press(app, "Escape", 2000)
    assert not app._help_open and app._help_popup is None
    assert wiz.screen == Screen.PICK  # Esc closed the menu; it did not go back
    assert getattr(app.root.focus_get(), "_beamo_help_menu", False)


def test_tk_disabled_items_show_their_reasons(tk_at):
    _wiz, app = tk_at("pick")
    app._open_help_menu()
    app.root.update()
    reasons = {}

    def visit(w):
        key = getattr(w, "_beamo_help_reason", None)
        if key:
            reasons[key] = str(w.cget("text"))
        for child in w.winfo_children():
            visit(child)

    visit(app._help_popup)
    disabled = [b._beamo_help_item for b in _buttons(app._help_popup) if not b._enabled]
    assert set(disabled) == {M.REPORT_HELP, M.ADVANCED}  # #179: High contrast works
    assert reasons == {
        M.REPORT_HELP: C.MENU_REASON_REPORT_HELP,
        M.ADVANCED: C.MENU_REASON_ADVANCED,
    }


def test_tk_tab_stays_inside_the_open_menu(tk_at):
    _wiz, app = tk_at("method")
    app._open_help_menu()
    for _ in range(4):
        app.root.update()
    for step in range(12):
        _press(app, "Tab", 3000 + step * 200)
        assert app._in_help_menu(app.root.focus_get()), step


def test_tk_enter_and_esc_on_a_ready_review_never_erase(tk_at):
    wiz, app = tk_at("last")
    starts = []
    wiz.begin_erase = lambda: starts.append(wiz.screen)  # type: ignore[method-assign]
    wiz._erase_until = 0
    app._refresh_last_chance()
    app.root.update()
    app._primary.focus_set()  # Erase now has focus before the menu opens
    app.root.update()
    _press(app, "F10", 4000)
    assert app._help_open
    # Text size is locked on the final check; focus starts on the next item.
    assert app.root.focus_get()._beamo_help_item == M.LANGUAGE
    close = next(b for b in _buttons(app._help_popup) if b._beamo_help_item == "close")
    close.focus_set()
    app.root.update()
    _press(app, "Return", 5000)
    assert not app._help_open and starts == []
    assert wiz.screen == Screen.LAST_CHANCE
    _press(app, "F10", 6000)
    _press(app, "Escape", 7000)
    assert starts == [] and wiz.screen == Screen.LAST_CHANCE


def test_tk_esc_with_the_menu_open_does_not_ask_to_stop(tk_at):
    wiz = _wizard_at("last")
    wiz.screen = Screen.WORKING
    wiz, app = tk_at("working", wiz=wiz)
    _press(app, "F10", 8000)
    _press(app, "Escape", 9000)
    assert wiz.stop_confirmation is None and wiz.screen == Screen.WORKING


def test_tk_text_size_keeps_the_menu_open_on_its_item(tk_at):
    wiz, app = tk_at("pick")
    app._open_help_menu(M.TEXT_SIZE)
    app.root.update()
    _press(app, "Return", 10_000)
    for _ in range(6):
        app.root.update()
    assert wiz.text_size == "large" and app._help_open
    assert app.root.focus_get()._beamo_help_item == M.TEXT_SIZE


def test_tk_shortcuts_page_lists_the_screen_keys_and_esc_returns(tk_at):
    wiz, app = tk_at("pick")
    app._open_help_menu(M.SHORTCUTS)
    app.root.update()
    _press(app, "Return", 11_000)
    texts = []

    def visit(w):
        if w.winfo_class() == "Label":
            texts.append(str(w.cget("text")))
        for child in w.winfo_children():
            visit(child)

    visit(app._help_popup)
    assert C.MENU_SHORTCUTS_MENU in texts and C.MENU_SHORTCUTS_REFRESH in texts
    # #174: the screen's hint is drawn with key-caps (#153 draws the arrow
    # keys), so its words are split around the keys; all of them are there.
    from beamo_wipe.ui.tk_wizard import _Box

    hint = []

    def find(w):
        if getattr(w, "_beamo_shortcuts_hint", False):
            hint.append(w)
        for child in w.winfo_children():
            find(child)

    find(app._help_popup)
    (box,) = hint
    words = []

    def collect(w):
        if w.winfo_class() == "Label":
            words.append(str(w.cget("text")))
        for child in w.winfo_children():
            collect(child)

    collect(box)
    shown = " ".join(" ".join(words).split())
    assert shown == " ".join(C.HINT_PICK.replace("Up/Down", " ").split())
    caps = []

    def boxes(w):
        if isinstance(w, _Box):
            caps.append(w)
        for child in w.winfo_children():
            boxes(child)

    boxes(box)
    assert caps  # key-caps
    _press(app, "Escape", 12_000)
    assert app._help_open and app._help_view == "menu"
    assert app.root.focus_get()._beamo_help_item == M.SHORTCUTS
    assert wiz.screen == Screen.PICK


@pytest.mark.parametrize("size,text", [((800, 600), "standard"), ((800, 600), "extra"),
                                       ((1280, 820), "large")])
def test_tk_open_menu_fits_the_window(tk_at, size, text):
    wiz = _wizard_at("pick")
    wiz.text_size = text
    _wiz, app = tk_at("pick", size=size, wiz=wiz)
    app._open_help_menu()
    for _ in range(8):
        app.root.update()
    popup = app._help_popup
    x, y = popup.winfo_x(), popup.winfo_y()
    assert x >= 0 and y >= 0
    assert x + popup.winfo_width() <= app.root.winfo_width()
    assert y + popup.winfo_height() <= app.root.winfo_height()


def test_tk_screen_change_closes_the_menu(tk_at):
    wiz, app = tk_at("method")
    app._open_help_menu(M.ADVANCED)
    app.root.update()
    _press(app, "Return", 13_000)
    assert wiz.screen == Screen.ADVANCED and not app._help_open


# --- curses and the line console ----------------------------------------------


def _run_curses(monkeypatch, wiz, steps):
    """Drive the curses loop (ints are keys, callables run on an idle read)."""
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
    painted = []

    class Terminal:
        def getmaxyx(self):
            return (60, 120)

        def addstr(self, y, x, text, attr=0):
            painted.append(text)

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
    return starts, painted


@pytest.mark.parametrize("name", ["splash", "keyboard", "owner", "pick", "confirm", "method", "last"])
def test_curses_footer_names_f10_on_every_screen(name):
    wiz = _wizard_at(name)
    lines = console._footer_lines(wiz, False, 120, 60)
    assert any(C.MENU_KEY in line for line in lines), lines
    joined = " ".join(lines)
    assert C.CON_KEYBOARD not in joined and C.CON_REPORT_HELP not in joined


def test_curses_f10_lists_items_with_reasons_and_esc_keeps_the_screen(monkeypatch):
    wiz = _wizard_at("pick")
    starts, painted = _run_curses(monkeypatch, wiz, [console.curses.KEY_F10, ESC])
    text = "\n".join(painted)
    assert C.MENU_TITLE in text and C.TEXT_SIZE_CONSOLE in text and C.MENU_REASON_ADVANCED in text
    assert starts == [] and wiz.screen == Screen.PICK


def test_curses_menu_opens_advanced_from_method(monkeypatch):
    wiz = _wizard_at("method")
    _run_curses(monkeypatch, wiz, [console.curses.KEY_F10, ord("6")])
    assert wiz.screen == Screen.ADVANCED


def test_curses_menu_on_a_ready_review_never_erases(monkeypatch):
    wiz = _wizard_at("last")
    ready = lambda w: setattr(w, "_erase_until", 0)  # noqa: E731
    # Erase now has focus, then the menu opens; Enter on the locked text
    # size and Esc to close must not press Erase now.
    starts, _ = _run_curses(monkeypatch, wiz, [ready, TAB, console.curses.KEY_F10, ENTER, ESC])
    assert starts == [] and wiz.screen == Screen.LAST_CHANCE


def test_curses_confirm_typing_is_untouched_by_the_menu(monkeypatch):
    wiz = _wizard_at("confirm")
    _run_curses(monkeypatch, wiz, [ord("a"), console.curses.KEY_F10, ESC, ord("b")])
    assert wiz.screen == Screen.CONFIRM and wiz.confirm_input == "ab"


def test_plain_console_menu(monkeypatch, capsys):
    wiz = _wizard_at("method")
    answers = iter(["6"])
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    console._plain_help_menu(wiz)
    out = capsys.readouterr().out
    assert C.MENU_TITLE in out and f"4. {C.MENU_HIGH_CONTRAST_OFF}" in out  # #179
    assert wiz.screen == Screen.ADVANCED
    wiz = _wizard_at("pick")
    answers = iter(["6"])
    console._plain_help_menu(wiz)
    assert wiz.screen == Screen.PICK and C.MENU_REASON_ADVANCED in capsys.readouterr().out


# --- GTK / Orca (source; the runtime check needs Linux GTK) --------------------


def test_gtk_menu_is_first_and_owns_esc():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    render = src[src.index("    def render(self):"):src.index("    def _help_menu_button(self)")]
    assert render.index("self._help_menu_button()") < render.index("self.button(")
    for old in ("C.KEYBOARD_UTILITY", "C.REPORT_HELP_TITLE, self.w.open_report_help",
                "C.BTN_ADVANCED, self.w.open_advanced", "self.w.cycle_text_size"):
        assert old not in render, old
    block = src[src.index("    def _help_menu_button(self)"):src.index("    def _help_shortcut_lines")]
    assert "Gtk.MenuButton" in block and "set_can_focus(True)" in block and "item.spoken" in block
    keys = src[src.index("    def _key_press(self, _window, event):"):]
    keys = keys[:keys.index("    def _key_release")]
    # Esc while the popover is open closes it before any back() or stop.
    assert keys.index("popover.popdown()") < keys.index("self.w.back()")
    assert keys.index("Gdk.KEY_F10") < keys.index("Gdk.KEY_Return, Gdk.KEY_KP_Enter")


def test_gtk_runtime_menu():
    pytest.importorskip("gi")
    from test_accessible_runtime import drain

    from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk

    wiz = _wizard_at("pick")
    app = AccessibleWizard(wiz)
    try:
        assert app.utilities.get_child_at(0, 0) is app.help_button
        app._key_press(app.window, SimpleNamespace(keyval=Gdk.KEY_F10, time=100))
        assert app.help_popover.get_visible()
        app._key_press(app.window, SimpleNamespace(keyval=Gdk.KEY_Escape, time=200))
        assert not app.help_popover.get_visible() and wiz.screen == Screen.PICK
    finally:
        app.close()
        drain()


# --- web preview ---------------------------------------------------------------


def test_preview_payload_follows_the_wizard_rules():
    from beamo_wipe.gallery import _HELP_MENU_SCREENS, _help_menu_payload

    payload = _help_menu_payload()
    assert payload["title"] == C.MENU_TITLE
    for name, screen in _HELP_MENU_SCREENS.items():
        states = payload["states"][name]
        assert [s["key"] for s in states] == list(M.ORDER)
        advanced = next(s for s in states if s["key"] == M.ADVANCED)
        assert advanced["enabled"] is (screen == Screen.METHOD)
        assert all(s["enabled"] or s["reason"] for s in states)


def test_preview_footer_has_one_fixed_menu():
    from beamo_wipe.gallery import gallery_html

    script = inline_script(gallery_html())
    assert "renderHelpTrigger(utilities);" in script
    assert 'btn(P.reportHelpTitle' not in script and "text-size-utility" not in script
    assert "P.buttons.advanced" not in script
    handler = script[script.index('document.addEventListener("keydown"'):]
    # F10 and the open menu come before every screen's own keys.
    assert handler.index('e.key === "F10"') < handler.index('screen === "splash"')
    assert handler.index("if (helpOpen)") < handler.index('["working", "stop_confirm"]')


def test_preview_menu_logic_in_node():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    from beamo_wipe.gallery import gallery_html

    script = inline_script(gallery_html())
    payload = re.search(r"const P = (\{.*?\});\n", script, re.S)
    start = script.index("let helpOpen = false")
    end = script.index("function renderHelpTrigger")
    program = ("const P = " + payload.group(1) + ";\n"
               + "let screen = 'pick', textSize = 'standard', soundsOn = false;\n"
               + "let keyboardFrom = null, reportHelpFrom = 'owner', draws = 0, highContrast = false;\n"
               + "function draw() { draws += 1; }\n"
               + script[start:end]
               + """
openHelp();
if (!helpOpen || screen !== 'pick') throw Error('open changed the screen');
const keys = helpItems().map(i => i.key).join(',');
if (keys !== 'text_size,language,sounds,high_contrast,report_help,advanced,shortcuts') throw Error(keys);
activateHelp('advanced');
if (screen !== 'pick' || !helpOpen) throw Error('disabled Advanced acted');
activateHelp('text_size');
if (textSize !== 'large' || !helpOpen) throw Error('text size');
activateHelp('language');
if (screen !== 'keyboard' || keyboardFrom !== 'pick' || helpOpen) throw Error('language');
screen = 'method'; openHelp(); activateHelp('advanced');
if (screen !== 'advanced') throw Error('advanced from method');
""")
    # On stdin: the payload is longer than a Windows command line allows.
    result = subprocess.run([node], input=program, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
