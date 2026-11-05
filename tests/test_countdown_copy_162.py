# SPDX-License-Identifier: GPL-3.0-or-later
"""#162: the review lead says what starts the erase.

"The countdown never starts erasure." becomes "Erasing starts only when you
press Erase now." on every surface (Tk, GTK, curses, plain console, web
preview). Behaviour is unchanged: the five-second countdown only enables
Erase now, and nothing starts until that separate action. Fake disks only;
the runner is the dry-run fake.
"""

from __future__ import annotations

import json
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard

OLD = {
    "en": "The countdown never starts erasure.",
    "fr": "Le compte à rebours ne déclenche jamais l’effacement.",
    "de": "Der Countdown startet nie das Löschen.",
    "es": "La cuenta regresiva nunca inicia el borrado.",
    "it": "Il conto alla rovescia non avvia mai la cancellazione.",
}


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _last_chance():
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


def test_english_lead():
    assert C.LAST_LEAD == (
        "Check the selected disk and method. Erasing starts only when you press Erase now."
    )
    assert C.BTN_ERASE in C.LAST_LEAD


@pytest.mark.parametrize("code", ["en", "fr", "de", "es", "it"])
def test_every_language_names_its_own_erase_button(code):
    lang.set_language(code)
    assert OLD[code] not in C.LAST_LEAD
    # The lead names the button exactly as that language labels it.
    assert C.BTN_ERASE in C.LAST_LEAD
    assert C.LAST_LEAD.endswith(".")


def test_gate_is_unchanged_zero_only_enables_erase_now():
    wiz = _last_chance()
    assert not wiz.erase_enabled and not wiz.runner.started
    wiz._erase_until = 0  # the five-second review has passed
    assert wiz.erase_enabled
    # Reaching zero starts nothing and leaves the review screen in place.
    assert not wiz.runner.started and wiz.screen == Screen.LAST_CHANCE


def test_plain_console_prints_the_lead(monkeypatch, capsys):
    wiz = _last_chance()

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out
    assert C.LAST_LEAD in out and OLD["en"] not in out
    assert not wiz.runner.started


def test_curses_shows_the_lead(monkeypatch):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _last_chance()
    text = " ".join(_curses_text(wiz, 40, 120).split())
    assert C.LAST_LEAD in text and OLD["en"] not in text
    assert not wiz.runner.started


def test_gtk_and_preview_read_the_same_copy():
    import pathlib

    from beamo_wipe.gallery import gallery_html

    src = (pathlib.Path(__file__).resolve().parents[1] / "src" / "beamo_wipe" / "ui"
           / "accessible_wizard.py").read_text(encoding="utf-8")
    assert "self.label(C.LAST_LEAD)" in src
    for code in ("en", "de"):
        html = gallery_html(code)
        payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
        lang.set_language(code)
        assert payload["lastLead"] == C.LAST_LEAD
        assert OLD[code] not in html


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "large"),
                                            ((1280, 820), "extra")])
def test_tk_review_shows_the_lead_and_keeps_the_gate(size, text_size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _last_chance()
    wiz.text_size = text_size
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        found = []

        def visit(w):
            if w.winfo_class() == "Label" and str(w.cget("text")) == C.LAST_LEAD:
                found.append(w)
            for child in w.winfo_children():
                visit(child)

        visit(app._body)
        (lead,) = found
        assert lead.winfo_ismapped()
        assert lead.winfo_reqwidth() <= lead.winfo_width() + 2
        wiz._erase_until = 0
        app._refresh_last_chance()
        for _ in range(4):
            app.root.update()
        assert wiz.erase_enabled and not wiz.runner.started
        assert wiz.screen == Screen.LAST_CHANCE
    finally:
        app._teardown()
