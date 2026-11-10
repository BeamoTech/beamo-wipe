# SPDX-License-Identifier: GPL-3.0-or-later
"""#140: a guided keyboard check instead of a silent typing box.

The person presses the key printed Z; the active layout turns that physical
key into a character. Z sits in a different place on QWERTY, QWERTZ and
AZERTY keyboards, so the produced character tells the families apart.
Advisory only: it never blocks Continue. Simulated key events only.
"""

from __future__ import annotations

import json
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import keyboard as K
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

# Where the key printed Z physically sits, named by the US key there.
Z_POSITION = {"qwerty": "z", "qwertz": "y", "azerty": "w"}
FAMILY_LAYOUT = {"qwertz": "de", "azerty": "fr"}


def _produced(active_layout: str, physical_family: str) -> str:
    """What the active layout types for the physical Z key."""
    return K._FAMILY_LETTERS[K.LAYOUTS[active_layout].family][Z_POSITION[physical_family]]


@pytest.mark.parametrize("active", K.LAYOUT_ORDER)
@pytest.mark.parametrize("physical", ["qwerty", "qwertz", "azerty"])
def test_every_shipped_layout_against_every_keyboard_family(active, physical):
    result = K.check_key(active, _produced(active, physical))
    if K.LAYOUTS[active].family == physical:
        assert (result.kind, result.layout_id) == ("match", active)
    else:
        assert result.kind == "other"
        assert K.LAYOUTS[result.layout_id].family == physical
        if physical in FAMILY_LAYOUT:
            assert result.layout_id == FAMILY_LAYOUT[physical]


@pytest.mark.parametrize(("language", "expected"), [
    ("en", "us"), ("es", "es"), ("it", "it"), ("fr", "us"), ("de", "us"),
])
def test_a_qwerty_keyboard_is_offered_the_languages_usual_qwerty(language, expected):
    # A QWERTY keyboard while QWERTZ is active: the produced letter is "y".
    result = K.check_key("de", "y", language=language)
    assert (result.kind, result.layout_id) == ("other", expected)


def test_uppercase_and_shift_count_the_same():
    assert K.check_key("us", "Z").kind == "match"


@pytest.mark.parametrize("typed", ["", "Shift_L", "Return", "1", " ", "zz", None])
def test_keys_that_are_not_one_letter_are_not_an_answer(typed):
    assert K.check_key("us", typed) is None


@pytest.mark.parametrize("typed", ["a", "k", "é"])
def test_another_letter_asks_for_z_again(typed):
    result = K.check_key("us", typed)
    assert result.kind == "unclear" and result.typed == typed.lower()


# --- Wizard: advisory, one-click switch ----------------------------------------------


def _keyboard_wizard(layout="us"):
    from test_keyboard_layout import _Apply

    wiz = make_demo_wizard()
    wiz._apply_keyboard = _Apply()  # no setxkbmap/loadkeys in tests
    wiz.preview = False
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    if layout != wiz.keyboard_layout:
        wiz.set_keyboard_layout(layout)
    return wiz


def test_match_result_in_words():
    wiz = _keyboard_wizard("us")
    assert wiz.check_keyboard_key("z").kind == "match"
    assert wiz.keyboard_check_text == "✓ Letters and numbers match QWERTY (US)."
    assert wiz.keyboard_check_switch == ""


def test_a_failed_switch_keeps_the_layout_and_the_result():
    from test_keyboard_layout import _Apply

    wiz = _keyboard_wizard("us")
    wiz._apply_keyboard = _Apply(ok=False)
    wiz.check_keyboard_key("y")
    assert wiz.accept_keyboard_suggestion() is False
    assert wiz.keyboard_layout == "us"
    assert wiz.keyboard_message  # the existing failure message explains it


def test_mismatch_offers_a_one_click_switch_that_clears_the_result():
    wiz = _keyboard_wizard("us")
    wiz.check_keyboard_key("y")  # a QWERTZ keyboard
    assert wiz.keyboard_check_text == "That looks like QWERTZ (German). Switch to it?"
    assert wiz.keyboard_check_switch == "Switch to QWERTZ (German)"
    assert wiz.accept_keyboard_suggestion()
    assert wiz.keyboard_layout == "de"
    assert wiz.keyboard_check is None
    # Pressing Z again now matches.
    assert wiz.check_keyboard_key("z").kind == "match"


def test_unclear_result_never_suggests():
    wiz = _keyboard_wizard("us")
    wiz.check_keyboard_key("a")
    assert "“a”" in wiz.keyboard_check_text
    assert wiz.keyboard_check_switch == ""
    assert wiz.accept_keyboard_suggestion() is False


@pytest.mark.parametrize("answer", [None, "z", "y", "a"])
def test_continue_never_waits_for_the_check(answer):
    wiz = _keyboard_wizard("us")
    if answer:
        wiz.check_keyboard_key(answer)
    wiz.accept_keyboard()
    assert wiz.screen != Screen.KEYBOARD
    assert wiz.keyboard_layout == "us"  # a mismatch never switches by itself


def test_check_only_on_the_keyboard_screen():
    wiz = _keyboard_wizard("us")
    wiz.accept_keyboard()
    assert wiz.check_keyboard_key("y") is None


def test_changing_layout_clears_the_old_result():
    wiz = _keyboard_wizard("us")
    wiz.check_keyboard_key("z")
    wiz.set_keyboard_layout("fr")
    assert wiz.keyboard_check is None and wiz.keyboard_check_text == ""


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_the_check(code):
    from beamo_wipe import lang

    names = ("KEYBOARD_CHECK_LABEL", "KEYBOARD_CHECK_HINT", "KEYBOARD_CHECK_MATCH",
             "KEYBOARD_CHECK_OTHER", "KEYBOARD_CHECK_SWITCH", "KEYBOARD_CHECK_UNCLEAR",
             "CON_KEYBOARD_CHECK_SWITCH", "CON_KEYBOARD_CHECK_SWITCH_WORD")
    english = {n: getattr(C, n) for n in names}
    try:
        lang.set_language(code)
        for name, value in english.items():
            assert getattr(C, name) != value, (code, name)
        assert " Z" in C.KEYBOARD_CHECK_LABEL and " Z" in C.KEYBOARD_CHECK_HINT
        for name in ("KEYBOARD_CHECK_MATCH", "KEYBOARD_CHECK_OTHER", "KEYBOARD_CHECK_SWITCH"):
            assert "{layout}" in getattr(C, name)
        assert "{typed}" in C.KEYBOARD_CHECK_UNCLEAR
        assert "SWITCH" in C.CON_KEYBOARD_CHECK_SWITCH_WORD
    finally:
        lang.set_language("en")


def test_check_copy_stays_within_the_claims():
    text = " ".join(str(getattr(C, n)) for n in dir(C) if n.startswith("KEYBOARD_CHECK"))
    assert "password" not in text.lower() or "not" in text.lower()
    for banned in ("certif", "guarantee", "plug and play"):
        assert banned not in text.lower()


# --- Consoles -----------------------------------------------------------------------------


def test_curses_compares_the_produced_character_and_f3_switches():
    import curses

    from beamo_wipe.ui import console_wizard as console

    wiz = _keyboard_wizard("us")
    console._handle(wiz, ord("y"))
    footer = console._primary_footer(wiz, False)
    assert wiz.keyboard_check_text in footer
    assert C.CON_KEYBOARD_CHECK_SWITCH.format(layout=K.LAYOUTS["de"].title) in footer
    console._handle(wiz, curses.KEY_F3)
    assert wiz.keyboard_layout == "de" and wiz.keyboard_check is None
    console._handle(wiz, ord("z"))
    assert wiz.keyboard_check.kind == "match"
    assert C.KEYBOARD_CHECK_MATCH.format(layout=K.LAYOUTS["de"].title) in console._primary_footer(wiz, False)


def test_plain_console_letter_checks_and_switch_word(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _keyboard_wizard("us")
    answers = iter(["w", "SWITCH", "z"])

    def fake_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    assert C.KEYBOARD_CHECK_OTHER.format(layout=K.LAYOUTS["fr"].title) in out
    assert C.CON_KEYBOARD_CHECK_SWITCH_WORD.format(layout=K.LAYOUTS["fr"].title) in out
    assert wiz.keyboard_layout == "fr"
    assert C.KEYBOARD_CHECK_MATCH.format(layout=K.LAYOUTS["fr"].title) in out


# --- GTK (source) and web preview ---------------------------------------------------------


def test_gtk_reads_the_keysym_and_announces_the_result():
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert '"key-press-event"' in src and "Gdk.keyval_name(event.keyval)" in src
    block = src[src.index("result = self.w.keyboard_check_text"):]
    block = block[:block.index("self.button(C.primary_action(Screen.KEYBOARD)")]
    assert "Atk.Role.ALERT" in block and "arrival = result_label" in block
    assert "set_name(C.KEYBOARD_CHECK_LABEL)" in src


def test_web_preview_uses_the_same_rules():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    check = payload["keyCheck"]
    assert check["families"] == {k: dict(v) for k, v in K._FAMILY_LETTERS.items()}
    assert check["layoutFamily"] == {lid: K.LAYOUTS[lid].family for lid in K.LAYOUT_ORDER}
    assert check["familyLayout"]["qwertz"] == "de" and check["familyLayout"]["azerty"] == "fr"
    assert "function keyCheck(active, typed)" in html
    assert 'id="kbresult" role="status" aria-live="polite"' in html


# --- Rendered Tk: simulated key events -------------------------------------------------------


class _Key:
    def __init__(self, keysym, char=""):
        self.keysym, self.char = keysym, char


@pytest.fixture
def tk_keyboard():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(layout="us", size=(800, 600)):
        _needs_display()
        wiz = _keyboard_wizard(layout)
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _shown(app):
    labels = [str(w.cget("text")) for w in _walk(app.root)
              if w.winfo_class() == "Label" and w.winfo_ismapped()]
    buttons = [str(w.itemcget(w._label, "text")) for w in _walk(app.root)
               if hasattr(w, "_label") and w.winfo_ismapped()]
    return labels, buttons


@pytest.mark.parametrize(("active", "keysym", "kind"), [
    ("us", "z", "match"), ("us", "y", "other"), ("us", "w", "other"),
    ("fr", "z", "match"), ("fr", "w", "other"), ("de", "z", "match"), ("de", "y", "other"),
    ("gb", "Z", "match"), ("it", "a", "unclear"),
])
def test_tk_key_event_shows_the_result(tk_keyboard, active, keysym, kind):
    wiz, app = tk_keyboard(active)
    entry = next(w for w in _walk(app._body) if w.winfo_class() == "Entry")
    assert "_keyboard_check_key" in entry.bind("<KeyPress>")
    app._keyboard_check_key(_Key(keysym))
    app.root.update()
    labels, buttons = _shown(app)
    assert wiz.keyboard_check.kind == kind
    assert wiz.keyboard_check_text in labels
    assert (wiz.keyboard_check_switch in buttons) is (kind == "other")
    assert app.root.focus_lastfor().winfo_class() == "Entry"  # keep checking


def test_tk_switch_button_switches_and_ignores_modifiers(tk_keyboard):
    wiz, app = tk_keyboard("us")
    app._keyboard_check_key(_Key("Shift_L"))
    app.root.update()
    assert wiz.keyboard_check is None
    app._keyboard_check_key(_Key("y"))
    app.root.update()
    switch = next(w for w in _walk(app.root) if hasattr(w, "_label")
                  and str(w.itemcget(w._label, "text")) == wiz.keyboard_check_switch)
    switch._command()
    app.root.update()
    assert wiz.keyboard_layout == "de" and wiz.keyboard_check is None
    labels, _ = _shown(app)
    assert C.KEYBOARD_CHECK_LABEL in labels


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_result_fits_800x600(tk_keyboard, text_size):
    from test_tk_runtime import _clipping_problems

    wiz, app = tk_keyboard("us")
    wiz.text_size = text_size
    app._keyboard_check_key(_Key("y"))
    app.root.update()
    assert _clipping_problems(app) == []
    assert app._primary.winfo_ismapped() and app._primary._enabled
