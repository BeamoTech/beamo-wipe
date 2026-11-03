# SPDX-License-Identifier: GPL-3.0-or-later
"""Language first on the keyboard screen; its usual layout follows (#131).

Before: the language chips sat under seven English layout cards, below an
English title, and choosing French left the keyboard on US QWERTY. Now the
language picker is the first control, each language is in its own name, and
choosing one sets that language's shipped layout unless the person picked a
layout, or a layout change would undo their answers so far. The layout
change is the same transition as picking it by hand, so the confirmation
still has to be typed after it. Fake demo disks; the OS layout call is a
recording stub, so no real keyboard is changed.
"""

from __future__ import annotations

import json
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import keyboard, lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.keyboard import (
    LANGUAGE_ALTERNATIVE_LAYOUTS,
    LANGUAGE_LAYOUTS,
    LAYOUT_ORDER,
    ApplyResult,
)
from beamo_wipe.models import Screen
from beamo_wipe.safety import token_matches

EXPECTED = {"en": "us", "fr": "fr", "de": "de", "es": "es", "it": "it"}


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


class _Apply:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def __call__(self, layout_id, **_):
        self.calls.append(layout_id)
        if self.ok:
            return ApplyResult(True, "", layout_id)
        return ApplyResult(False, keyboard.APPLY_FAILED, layout_id)


def _keyboard_screen(ok=True):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz._apply_keyboard = _Apply(ok)
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    return wiz


def _to_confirm(wiz):
    wiz.accept_keyboard()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM


# --- The mapping uses only shipped, offered layouts -----------------------------


def test_every_language_maps_to_a_shipped_offered_layout():
    assert dict(LANGUAGE_LAYOUTS) == EXPECTED
    assert set(LANGUAGE_LAYOUTS) == set(lang.LANGUAGE_ORDER)
    for code, layout_id in LANGUAGE_LAYOUTS.items():
        assert layout_id in LAYOUT_ORDER and keyboard.is_allowed(layout_id), code
    for code, alt in LANGUAGE_ALTERNATIVE_LAYOUTS.items():
        assert alt in LAYOUT_ORDER and alt != LANGUAGE_LAYOUTS[code], code
    # Only the two well-known alternatives are named; nothing else is guessed.
    assert dict(LANGUAGE_ALTERNATIVE_LAYOUTS) == {"en": "gb", "es": "latam"}


def test_each_language_is_shown_in_its_own_name_under_a_neutral_label():
    assert lang.LANGUAGE_NAMES == {
        "en": "English", "fr": "Français", "de": "Deutsch", "es": "Español", "it": "Italiano"}
    assert lang.LANGUAGE_PICKER_LABEL == "Language · Langue · Sprache · Idioma · Lingua"
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        # Neither the names nor the label change with the active language.
        assert lang.LANGUAGE_PICKER_LABEL == "Language · Langue · Sprache · Idioma · Lingua"
        assert lang.LANGUAGE_NAMES["fr"] == "Français"


# --- Choosing a language sets its layout, visibly ---------------------------------


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_choosing_a_language_sets_its_layout_and_says_so(code):
    wiz = _keyboard_screen()
    assert wiz.choose_language(code)
    assert wiz.language == code and lang.current() == code
    assert wiz.keyboard_layout == EXPECTED[code]
    assert wiz._apply_keyboard.calls == [EXPECTED[code]]
    assert not wiz.layout_chosen and wiz.layout_notice == "auto"
    notice = C.keyboard_layout_notice(wiz)
    assert keyboard.LAYOUTS[EXPECTED[code]].title in notice
    assert lang.LANGUAGE_NAMES[code] in notice
    assert wiz.error is None


def test_back_to_english_returns_to_us_and_names_uk_as_the_alternative():
    wiz = _keyboard_screen()
    wiz.choose_language("fr")
    wiz.choose_language("en")
    assert wiz.keyboard_layout == "us"
    assert C.keyboard_layout_notice(wiz) == (
        "Keyboard set to QWERTY (US) to match English. Using a QWERTY (UK) keyboard? Choose it below.")


def test_spanish_names_latin_american_as_the_alternative():
    wiz = _keyboard_screen()
    wiz.choose_language("es")
    assert keyboard.LAYOUTS["latam"].title in C.keyboard_layout_notice(wiz)


def test_a_layout_the_person_picked_is_kept():
    wiz = _keyboard_screen()
    assert wiz.set_keyboard_layout("gb")
    for code in ("fr", "de", "en"):
        wiz.choose_language(code)
        assert wiz.keyboard_layout == "gb", code
        assert wiz.layout_notice == "kept"
    assert wiz._apply_keyboard.calls == ["gb"]
    assert C.keyboard_layout_notice(wiz) == "Keyboard stays QWERTY (UK), the layout you chose."
    # Picking the already-selected layout also counts as a choice.
    other = _keyboard_screen()
    assert other.set_keyboard_layout("us")
    other.choose_language("de")
    assert other.keyboard_layout == "us" and other.layout_notice == "kept"


def test_language_change_after_answers_keeps_the_layout_and_the_answers():
    wiz = _keyboard_screen()
    wiz.accept_keyboard()
    wiz.set_owner(True)
    wiz.open_keyboard()
    assert wiz.screen == Screen.KEYBOARD
    wiz.choose_language("fr")
    assert wiz.language == "fr"
    assert wiz.keyboard_layout == "us" and wiz.owner_ok
    assert wiz._apply_keyboard.calls == []
    assert wiz.layout_notice == "stays"
    assert "QWERTY" in C.keyboard_layout_notice(wiz)


def test_language_choice_off_the_keyboard_screen_never_touches_the_layout():
    wiz = _keyboard_screen()
    wiz.accept_keyboard()
    assert wiz.screen == Screen.OWNER
    wiz.choose_language("de")
    assert wiz.language == "de" and wiz.keyboard_layout == "us"
    assert wiz._apply_keyboard.calls == []
    # The programmatic language switch (session restore, tests) never does.
    wiz2 = _keyboard_screen()
    wiz2.set_language("fr")
    assert wiz2.keyboard_layout == "us" and wiz2._apply_keyboard.calls == []


def test_failed_auto_layout_keeps_the_old_layout_and_reports_it():
    wiz = _keyboard_screen(ok=False)
    assert wiz.choose_language("fr")
    assert wiz.language == "fr"
    assert wiz.keyboard_layout == "us"
    assert wiz.error == keyboard.APPLY_FAILED
    assert wiz.layout_notice is None and C.keyboard_layout_notice(wiz) == ""


def test_preview_restart_forgets_the_layout_choice():
    wiz = _keyboard_screen()
    wiz.set_keyboard_layout("gb")
    wiz.preview = True
    wiz.reset_for_preview()
    assert not wiz.layout_chosen and wiz.layout_notice is None
    assert wiz.keyboard_layout == keyboard.DEFAULT_LAYOUT


# --- The confirmation after each auto-picked layout ------------------------------


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_confirmation_typed_after_each_auto_layout_still_compares_exactly(code):
    wiz = _keyboard_screen()
    wiz.choose_language(code)
    assert wiz.keyboard_layout == EXPECTED[code]
    _to_confirm(wiz)
    spec = wiz.confirm
    # Partial, padded-inside and another disk's characters are refused...
    for wrong in (spec.token[:-1], spec.token[0] + " " + spec.token[1:], "", "ZZZZ"):
        wiz.set_confirm_input(wrong)
        assert not wiz.token_ok, (code, wrong)
    # ...the exact characters, any case, outer spaces trimmed, are accepted.
    for typed in (spec.token, spec.token.lower(), f" {spec.token} "):
        wiz.set_confirm_input(typed)
        assert wiz.token_ok and token_matches(typed, spec), (code, typed)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD


def test_a_later_layout_change_still_clears_a_typed_confirmation():
    wiz = _keyboard_screen()
    wiz.choose_language("fr")
    _to_confirm(wiz)
    wiz.set_confirm_input(wiz.confirm.token)
    assert wiz.token_ok
    wiz.open_keyboard()
    assert wiz.set_keyboard_layout("us")
    assert wiz.confirm_input == "" and wiz.selected is None and not wiz.owner_ok
    assert wiz.screen == Screen.KEYBOARD


# --- Console ------------------------------------------------------------------


def test_curses_shows_languages_first_and_f2_picks_the_layout(monkeypatch):
    from test_console_parity import _draw

    from beamo_wipe.ui import console_wizard as console

    wiz = _keyboard_screen()
    english_lead = C.KEYBOARD_LEAD.split(".")[0]
    _shown, _packed, term = _draw(monkeypatch, wiz, h=24, w=80, keys=[console.curses.KEY_F2])
    first = term.frames[0]
    rows = [first[y] for y in sorted(first)]
    label_at = next(i for i, row in enumerate(rows) if lang.LANGUAGE_PICKER_LABEL in row)
    # Right under the one header line, before any instruction.
    lead_at = next(i for i, row in enumerate(rows) if english_lead in row)
    assert label_at == 1 < lead_at
    assert all(name in " ".join(rows) for name in lang.LANGUAGE_NAMES.values())
    assert wiz.language == "fr" and wiz.keyboard_layout == "fr"
    last = term.frames[-1]
    shown = " ".join(last[y] for y in sorted(last))
    # The notice (in French now) names the picked layout.
    assert keyboard.LAYOUTS["fr"].title in shown


def test_plain_console_lists_languages_first_and_l_codes_choose(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _keyboard_screen()
    answers = iter(["L3"])

    def fake_input(*_):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError() from None

    monkeypatch.setattr("builtins.input", fake_input)
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert out.index(lang.LANGUAGE_PICKER_LABEL) < out.index("Choose the layout that matches")
    assert "L2 Français" in out and "L3 Deutsch" in out
    assert wiz.language == "de" and wiz.keyboard_layout == "de"


# --- Web preview --------------------------------------------------------------


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_web_preview_starts_on_the_language_layout(code):
    from beamo_wipe.gallery import gallery_html

    html = gallery_html(code)
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    assert payload["languageLayout"] == EXPECTED[code]
    assert payload["languagePicker"] == lang.LANGUAGE_PICKER_LABEL
    lang.set_language(code)
    assert keyboard.LAYOUTS[EXPECTED[code]].title in payload["layoutNotice"]
    lang.set_language("en")
    assert "let keyboardLayout = P.languageLayout;" in html
    assert html.index('class="language-first"') < html.index("${P.titles.keyboard}</h1>")


# --- Rendered Tk ----------------------------------------------------------------


def _focus_chain(app):
    first = app.root.focus_get()
    chain, widget = [], first
    for _ in range(40):
        chain.append(widget)
        widget = widget.tk_focusNext()
        if widget is None or widget is first:
            break
    return chain


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_language_is_first_on_screen_and_in_focus(ui, size, text_size):  # noqa: F811
    wiz, app = ui(size=size)
    wiz._apply_keyboard = _Apply()
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
        app._sync_layout()
    wiz.skip_splash()
    app._draw()
    app.root.update()
    chips = app._keyboard_language_cards
    assert list(chips) == list(lang.LANGUAGE_ORDER)
    # First arrival: the chosen language, and it is the first control.
    assert app.root.focus_get() is chips["en"]
    controls = [w for w in _focus_chain(app) if w.winfo_ismapped()]
    first_layout = app._keyboard_layout_cards[LAYOUT_ORDER[0]]
    assert controls.index(chips["en"]) < controls.index(first_layout)
    # On screen: the picker sits above the title and the layout cards.
    title = next(w for w in _descendants(app._body)
                 if w.winfo_class() == "Label" and str(w.cget("text")) == C.TITLE_KEYBOARD)
    assert chips["en"].winfo_rooty() < title.winfo_rooty() < first_layout.winfo_rooty()
    texts = [str(w.cget("text")) for w in _descendants(app._body) if w.winfo_class() == "Label"]
    assert lang.LANGUAGE_PICKER_LABEL in texts
    for name in lang.LANGUAGE_NAMES.values():
        assert name in texts


def test_tk_choosing_french_rerenders_everything_and_picks_azerty(ui):  # noqa: F811
    wiz, app = ui(size=(800, 600))
    wiz._apply_keyboard = _Apply()
    wiz.skip_splash()
    app._draw()
    app.root.update()
    app.choose_language("fr")
    app.root.update()
    assert wiz.language == "fr" and wiz.keyboard_layout == "fr"
    texts = [str(w.cget("text")) for w in _descendants(app.root) if w.winfo_class() == "Label"]
    lang.set_language("fr")
    assert C.TITLE_KEYBOARD in texts and C.keyboard_layout_notice(wiz) in texts
    header = [str(app._header.itemcget(i, "text")) for i in app._header.find_all()
              if app._header.type(i) == "text"]
    assert C.journey_step_caption(wiz) in header
    assert app._primary.itemcget(app._primary._label, "text") == C.primary_action(Screen.KEYBOARD)
    # Focus stays on the chosen language, now Français.
    assert app.root.focus_get() is app._keyboard_language_cards["fr"]


def test_tk_arrow_keys_move_the_language_and_enter_continues(ui):  # noqa: F811
    wiz, app = ui(size=(1280, 820))
    wiz._apply_keyboard = _Apply()
    wiz.skip_splash()
    app._draw()
    app.root.update()
    chip = app._keyboard_language_cards["en"]
    chip.focus_set()
    app.root.update()
    chip.event_generate("<Right>", when="tail")
    app.root.update()
    assert wiz.language == "fr" and wiz.keyboard_layout == "fr"
    assert app.root.focus_get() is app._keyboard_language_cards["fr"]
    app._keyboard_language_cards["fr"].event_generate("<Left>", when="tail")
    app.root.update()
    assert wiz.language == "en" and wiz.keyboard_layout == "us"
    focused = app.root.focus_get()
    focused.event_generate("<KeyPress-Return>", when="tail")
    focused.event_generate("<KeyRelease-Return>", when="tail")
    app.root.update()
    assert wiz.screen == Screen.OWNER


def test_tk_layout_click_keeps_focus_on_the_layout(ui):  # noqa: F811
    wiz, app = ui(size=(1280, 820))
    wiz._apply_keyboard = _Apply()
    wiz.skip_splash()
    app._draw()
    app.root.update()
    card = app._keyboard_layout_cards["de"]
    card.event_generate("<Button-1>", x=10, y=10)
    app.root.update()
    assert wiz.keyboard_layout == "de" and wiz.layout_chosen
    assert app.root.focus_get() is app._keyboard_layout_cards["de"]
    app.choose_language("fr")
    app.root.update()
    assert wiz.keyboard_layout == "de"  # the person's choice stays


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_tk_token_typed_in_the_confirm_box_after_each_auto_layout(ui, code):  # noqa: F811
    from test_tk_runtime import _drive_to

    wiz, app = ui(size=(1280, 820))
    wiz._apply_keyboard = _Apply()
    wiz.skip_splash()
    app._draw()
    app.choose_language(code)
    assert wiz.keyboard_layout == EXPECTED[code]
    wiz.accept_keyboard()
    _drive_to(wiz, app, Screen.PICK, size=(1280, 820))
    assert wiz.screen == Screen.PICK
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    app._draw()
    app.root.update()
    token = wiz.confirm.token
    app._confirm_var.set(token[:-1])
    app.root.update()
    assert not wiz.token_ok
    app._confirm_var.set(token)
    app.root.update()
    assert wiz.token_ok and not wiz.runner.started


def _descendants(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _descendants(child)


from test_tk_runtime import ui  # noqa: E402,F401  (fixture)
