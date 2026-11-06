# SPDX-License-Identifier: GPL-3.0-or-later
"""#179: a high-contrast theme for people with low vision.

One session setting (Wizard.high_contrast, carried to the next session
like the text size; BEAMO_WIPE_HIGH_CONTRAST=1 starts with it on), chosen
on the first screen or in Help & settings. Tk swaps every colour token to
a high-contrast palette (text 7:1 or more on every surface, black edges,
thick black focus rings; states keep their checks, dashes, icons and
words), GTK switches to its built-in HighContrast theme plus matching
overrides (and starts in high contrast when the session already uses a
high-contrast theme), curses draws bold white on black, and the web
preview swaps its CSS tokens. Colours only: no answer or gate changes.
Fake disks only.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import help_menu as M
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console
from test_ui_system import _contrast

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _english_and_standard_palette():
    from beamo_wipe.ui import tk_wizard as tkui

    lang.set_language("en")
    yield
    lang.set_language("en")
    tkui.apply_palette(False)
    console._sync_contrast(SimpleNamespace(bkgd=lambda *a: None), SimpleNamespace(high_contrast=False))


# --- the palette --------------------------------------------------------------


def test_palette_contrast():
    from beamo_wipe.ui.tk_wizard import _HIGH_CONTRAST_PALETTE as P

    text_pairs = [
        ("INK", "BG"), ("INK", "SURFACE"), ("INK", "SURFACE_ALT"), ("INK", "PRIMARY_TINT"),
        ("MUTED", "SURFACE"), ("MUTED", "TRACK"), ("WARN", "WARN_BG"), ("DANGER", "DANGER_TINT"),
        ("OK", "OK_TINT"), ("DISABLED_INK", "DISABLED_FILL"), ("SELECTED_INK", "SELECTED_FILL"),
        ("PREVIEW_FG", "PREVIEW_BG"), ("PRIMARY", "SURFACE"),
    ]
    for fg, bg in text_pairs:
        assert _contrast(P[fg], P[bg]) >= 7.0, (fg, bg)
    for fill in ("PRIMARY", "DANGER", "PRIMARY_DARK", "DANGER_DARK"):
        assert _contrast("#FFFFFF", P[fill]) >= 7.0, fill  # labels on filled buttons
    for edge in ("BORDER", "FOCUS", "SELECTED_EDGE", "DISABLED_EDGE", "BORDER_STRONG"):
        assert _contrast(P[edge], P["BG"]) >= 3.0, edge
    assert P["SELECTED_EDGE_W"] >= 3


def test_apply_palette_switches_every_token_and_restores_them():
    from beamo_wipe.ui import tk_wizard as tkui

    standard = {name: getattr(tkui, name) for name in tkui._HIGH_CONTRAST_PALETTE}
    variants = dict(tkui._Button._VARIANTS)
    assert tkui.apply_palette(True) and tkui.HIGH_CONTRAST
    for name, value in tkui._HIGH_CONTRAST_PALETTE.items():
        assert getattr(tkui, name) == value, name
    assert tkui._Button._VARIANTS["primary"][0] == tkui._HIGH_CONTRAST_PALETTE["PRIMARY"]
    assert not tkui.apply_palette(True)  # no change, no redraw needed
    assert tkui.apply_palette(False) and not tkui.HIGH_CONTRAST
    assert {name: getattr(tkui, name) for name in standard} == standard
    assert tkui._Button._VARIANTS == variants


# --- the setting -----------------------------------------------------------------


def test_setting_is_colours_only_and_in_help_and_settings():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    item = M.find(wiz.help_menu(), M.HIGH_CONTRAST)
    assert item.enabled and item.label == C.MENU_HIGH_CONTRAST_OFF and item.stays_open
    before = (wiz.screen, wiz.owner_ok, wiz.selected, wiz.text_size, wiz.language)
    assert wiz.activate_help_item(M.HIGH_CONTRAST) and wiz.high_contrast
    assert M.find(wiz.help_menu(), M.HIGH_CONTRAST).label == C.MENU_HIGH_CONTRAST_ON
    assert (wiz.screen, wiz.owner_ok, wiz.selected, wiz.text_size, wiz.language) == before
    assert not wiz.set_high_contrast("yes")  # type: ignore[arg-type]
    assert wiz.set_high_contrast(False) and not wiz.high_contrast


def test_starts_on_from_the_environment(monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_HIGH_CONTRAST", "1")
    assert make_demo_wizard().high_contrast is True
    monkeypatch.setenv("BEAMO_WIPE_HIGH_CONTRAST", "0")
    assert make_demo_wizard().high_contrast is False


def test_setting_carries_to_the_next_session():
    src = (ROOT / "src/beamo_wipe/app.py").read_text(encoding="utf-8")
    assert "high_contrast = code.high_contrast" in src
    assert "wizard.set_high_contrast(high_contrast)" in src
    assert "text_size=text_size, high_contrast=high_contrast)" in src


def test_every_language_has_the_contrast_words():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for key in ("MENU_HIGH_CONTRAST_ON", "MENU_HIGH_CONTRAST_OFF", "CONTRAST_TITLE",
                    "CONTRAST_STANDARD", "CONTRAST_HIGH", "CONTRAST_LEAD", "CON_CONTRAST_KEY"):
            value = getattr(C, key)
            assert value and value.count("{") == value.count("{state}"), (code, key)
        # The contrast choices never share a name with a text-size choice.
        sizes = set(C.TEXT_SIZE_LABELS.values())
        assert C.CONTRAST_STANDARD not in sizes and C.CONTRAST_HIGH not in sizes, code
    lang.set_language("en")


# --- Tk -------------------------------------------------------------------------


def _wizard_at(name, high=False):
    from test_result_presentations import CASES, case_evidence

    if name == "done":
        wiz, _ev, _log = case_evidence(next(c for c in CASES if c[0] == "verified"))
    else:
        wiz = make_demo_wizard()
        wiz.preview = False
        wiz.skip_splash()
        if name != "keyboard":
            wiz.skip_intro()
            if name != "owner":
                wiz.set_owner(True)
                wiz.continue_owner()
                if name != "pick":
                    wiz.select_disk("/dev/sda")
                    wiz.continue_pick()
                    if name != "confirm":
                        wiz.set_confirm_input(wiz.confirm.token)
                        wiz.continue_confirm()
                        if name == "last":
                            wiz.continue_method()
    wiz.high_contrast = high
    return wiz


def _tk(wiz, size=(1280, 820)):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+20+20")
    app.root.focus_force()
    app._draw()
    for _ in range(8):
        app.root.update()
    return app


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


@pytest.mark.parametrize("name", ["keyboard", "owner", "pick", "confirm", "method", "last", "done"])
@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_every_screen_applies_the_theme_without_clipping(name, size):
    from test_tk_runtime import _clipping_problems
    from beamo_wipe.ui import tk_wizard as tkui

    app = _tk(_wizard_at(name, high=True), size)
    try:
        assert tkui.HIGH_CONTRAST
        hc = tkui._HIGH_CONTRAST_PALETTE
        assert str(app._body.cget("bg")).upper() == hc["BG"]
        assert str(app._footer.cget("bg")).upper() == hc["FOOTER_BG"]
        labels = [w for w in _walk(app._body) if w.winfo_class() == "Label" and w.winfo_ismapped()]
        # Text colours on the page come from the palette (no grey from the old one).
        old_greys = {tkui._STANDARD_PALETTE["MUTED"].upper(), tkui._STANDARD_PALETTE["INK"].upper()}
        assert not [w for w in labels if str(w.cget("fg")).upper() in old_greys]
        assert not _clipping_problems(app)
    finally:
        app._teardown()


def test_first_screen_choice_switches_and_returns():
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = _wizard_at("keyboard")
    app = _tk(wiz)
    try:
        choices = {w._beamo_contrast: w for w in _walk(app._body) if hasattr(w, "_beamo_contrast")}
        assert set(choices) == {False, True}
        assert choices[False]._variant == "selected" and choices[True]._variant == "segment"
        choices[True]._command()
        for _ in range(4):
            app.root.update()
        assert wiz.high_contrast and tkui.HIGH_CONTRAST
        assert str(app._body.cget("bg")).upper() == "#FFFFFF"
        choices = {w._beamo_contrast: w for w in _walk(app._body) if hasattr(w, "_beamo_contrast")}
        assert choices[True]._variant == "selected" and choices[True]._mark
        choices[False]._command()
        for _ in range(4):
            app.root.update()
        assert not wiz.high_contrast and not tkui.HIGH_CONTRAST
        assert str(app._body.cget("bg")).upper() == tkui.BG.upper()
    finally:
        app._teardown()


def test_help_and_settings_toggle_keeps_the_menu_open():
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = _wizard_at("pick")
    app = _tk(wiz)
    try:
        app._open_help_menu(M.HIGH_CONTRAST)
        app.root.update()
        app._help_activate(M.HIGH_CONTRAST)
        for _ in range(6):
            app.root.update()
        assert wiz.high_contrast and tkui.HIGH_CONTRAST and app._help_open
        assert app._help_focused_key() == M.HIGH_CONTRAST
        assert str(app._help_popup.cget("bg")).upper() == "#FFFFFF"
    finally:
        app._teardown()


def test_focus_ring_is_thick_in_high_contrast():
    from beamo_wipe.ui import tk_wizard as tkui

    app = _tk(_wizard_at("pick", high=True))
    try:
        button = app._help_button
        button._focus_in()
        rings = [i for i in button.find_withtag("rr") if button.type(i) == "polygon"
                 and button.itemcget(i, "outline").upper() == tkui._HIGH_CONTRAST_PALETTE["FOCUS"]
                 and float(button.itemcget(i, "width")) >= 3]
        assert rings
    finally:
        app._teardown()


# --- GTK, curses, web -----------------------------------------------------------


def test_gtk_follows_and_honours_the_high_contrast_theme():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert 'HIGH_CONTRAST_THEME = "HighContrast"' in src
    assert "css += HIGH_CONTRAST_CSS" in src and "self._sync_gtk_theme()" in src
    assert '"contrast" in theme.lower()' in src  # a high-contrast session starts in it
    assert "*:focus { outline: 4px solid #000000" in src
    assert src.count("button:disabled") == 2  # #178 rule no longer overridden; HC rule
    keyboard = src[src.index("contrast_heading = self.label(C.CONTRAST_TITLE"):]
    assert "self.w.set_high_contrast(value)" in keyboard[:900]


def test_curses_f4_on_the_first_screen_and_bold_text(monkeypatch):
    wiz = make_demo_wizard()
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    lines = console._primary_footer(wiz, False)
    assert C.CON_CONTRAST_KEY.format(state=C.MENU_HIGH_CONTRAST_OFF) in lines
    console._handle(wiz, console.curses.KEY_F4)
    assert wiz.high_contrast and wiz.screen == Screen.KEYBOARD
    written = []
    terminal = SimpleNamespace(getmaxyx=lambda: (24, 80), bkgd=lambda *a: None,
                               addstr=lambda y, x, text, attr=0: written.append(attr))
    console._sync_contrast(terminal, wiz)
    console._add(terminal, 0, 0, "Serial number")
    assert written[-1] & console.curses.A_BOLD
    wiz.toggle_high_contrast()
    console._sync_contrast(terminal, wiz)
    console._add(terminal, 0, 0, "Serial number")
    assert not written[-1] & console.curses.A_BOLD


def test_web_preview_contrast():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert ".shell.hc {" in html and "--ink: #000000" in html
    assert 'shell.classList.toggle("hc", highContrast)' in html
    assert "data-contrast" in html
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    (script,) = re.findall(r"<script>(.*?)</script>", html, re.S)
    payload = re.search(r"const P = (\{.*?\});\n", script, re.S)
    start = script.index("let helpOpen = false")
    end = script.index("function renderHelpTrigger", start)
    program = ("const P = " + payload.group(1) + ";\n"
               + "let screen = 'pick', textSize = 'standard', soundsOn = false, highContrast = false;\n"
               + "let keyboardFrom = null, reportHelpFrom = 'owner';\nfunction draw() {}\n"
               + script[start:end] + """
openHelp();
if (helpItems().find(i => i.key === 'high_contrast').label !== P.helpMenu.contrastOff) throw Error('off');
activateHelp('high_contrast');
if (!highContrast || !helpOpen || helpFocus !== 'high_contrast') throw Error('toggle');
if (helpItems().find(i => i.key === 'high_contrast').label !== P.helpMenu.contrastOn) throw Error('on');
""")
    result = subprocess.run([node], input=program, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
