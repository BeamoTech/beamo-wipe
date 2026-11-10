# SPDX-License-Identifier: GPL-3.0-or-later
"""#161: Three overwrites is labelled "Rarely needed", with the reason under Show more.

The chip replaces "More overwrites" (which only repeated the title) on every
surface. Its Show more explanation says it takes longer, that extra passes
do not reach hidden storage, that Everyday is the usual choice, and keeps
"This is not a DoD certificate." (docs/ADVANCED.md). The method mapping is
unchanged. Fake disks only; nothing starts the engine.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.ui import console_wizard

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTRA = METHODS[MethodId.EXTRA]
# "certificado/certificato DoD" read as "DoD certified" in ES/IT (test_language_selection).
FORBIDDEN = ("dod certified", "certified dod", "dod 5220", "nist", "guarantee", "unrecoverable",
             "sanitiz", "military", "certificado dod", "certificato dod", "certificación dod",
             "certificazione dod", "dod-zertifiziert", "certifié dod")


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _method_wizard(path="/dev/sda"):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    return wiz


def test_tag_and_explanation_wording():
    assert EXTRA.comparison_mark == "Rarely needed"
    assert C.METHOD_CARDS[MethodId.EXTRA]["mark"] == "Rarely needed"
    assert METHODS[MethodId.EVERYDAY].comparison_mark == ""
    assert METHODS[MethodId.QUICK_ZERO].comparison_mark == "No check"
    assert EXTRA.extra_work == (
        "Three times the overwrites of Everyday, so it takes longer. Extra passes do "
        "not reach hidden storage. Everyday is the usual choice. This is not a DoD "
        "certificate."
    )


def test_wording_stays_within_the_claims():
    advanced = (ROOT / "docs" / "ADVANCED.md").read_text(encoding="utf-8")
    assert "This is not a DoD certificate." in advanced
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        text = f"{EXTRA.comparison_mark} {EXTRA.extra_work}"
        assert EXTRA.comparison_mark and "{" not in text
        assert "DoD" in EXTRA.extra_work, code
        assert METHODS[MethodId.EVERYDAY].title in EXTRA.extra_work, code
        for word in FORBIDDEN:
            assert word not in text.lower(), (code, word)
    lang.set_language("en")


def test_method_mapping_is_unchanged():
    assert (EXTRA.nwipe_method, EXTRA.rounds, EXTRA.verify, EXTRA.noblank) == ("dodshort", 1, "last", True)
    assert (EXTRA.overwrite_passes, EXTRA.verification_passes) == (3, 1)
    assert EXTRA.title == "Three overwrites"


def test_plain_console_tags_the_choice_and_explains_after_the_choices(monkeypatch, capsys):
    wiz = _method_wizard()

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    lines = capsys.readouterr().out.splitlines()
    (choice,) = [ln for ln in lines if ln.startswith("2 Three overwrites")]
    assert choice.startswith("2 Three overwrites [Rarely needed]: ")
    assert EXTRA.extra_work not in choice
    (note,) = [ln for ln in lines if EXTRA.extra_work in ln]
    assert note == f"Three overwrites: {EXTRA.extra_work}"
    assert lines.index(note) > lines.index(choice)


def test_curses_tags_on_the_first_page_and_pages_the_explanation(monkeypatch):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _method_wizard()
    first = " ".join(_curses_text(wiz, 25, 80).split())
    assert "Three overwrites [Rarely needed]" in first
    wiz.wants_shutdown = False
    tall = " ".join(_curses_text(wiz, 80, 120).split())
    assert f"Three overwrites: {EXTRA.extra_work}" in tall


def test_gtk_source_keeps_the_explanation_out_of_the_radio_label():
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    radio = src[src.index("label = spec.summary"):src.index("choice = Gtk.RadioButton")]
    assert "card['mark']" in radio and 'card["extra"]' not in radio
    block = src[src.index("# #160:"):src.index("self.button(storage_limits.BUTTON")]
    assert 'more_card["extra"]' in block and "Gtk.Expander.new(C.BTN_MORE)" in block


def test_preview_payload_and_card_show_the_tag():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    extra = payload["methods"]["extra"]
    assert extra["mark"] == "Rarely needed" and extra["checks"] is True
    assert extra["extra"] == EXTRA.extra_work


@pytest.fixture
def method_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size, text_size="standard", code="en"):
        _needs_display()
        lang.set_language(code)
        wiz = _method_wizard("/dev/nvme0n1")
        wiz.set_language(code)
        wiz.text_size = text_size
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _card_labels(app, method):
    box = app._method_more_buttons[method]
    while not hasattr(box, "inner"):
        box = box.master
    out = []

    def visit(w):
        if w.winfo_class() == "Label" and w.winfo_ismapped():
            out.append(w)
        for child in w.winfo_children():
            visit(child)

    visit(box)
    return out


@pytest.mark.parametrize("size,text_size,code,tag", [((800, 600), "standard", "en", "Rarely needed"),
                                                     ((800, 600), "extra", "en", "Rarely needed"),
                                                     ((800, 600), "standard", "de", "Selten nötig")])
def test_tk_tag_is_visible_and_the_reason_is_under_show_more(method_app, size, text_size, code, tag):
    from test_tk_runtime import _clipping_problems

    from beamo_wipe.ui import tk_wizard as tkui

    wiz, app = method_app(size, text_size, code)
    labels = _card_labels(app, MethodId.EXTRA)
    assert EXTRA.comparison_mark == tag
    (chip,) = [w for w in labels if str(w.cget("text")) == tag]
    # A neutral chip (the method checks its result), not the warning colour.
    assert str(chip.cget("fg")).lower() == tkui.MUTED.lower()
    assert chip.winfo_rooty() + chip.winfo_height() <= app._footer.winfo_rooty() + 1
    assert EXTRA.extra_work not in [str(w.cget("text")) for w in labels]
    app._method_more_buttons[MethodId.EXTRA]._command()
    for _ in range(10):
        app.root.update()
    assert EXTRA.extra_work in [str(w.cget("text")) for w in _card_labels(app, MethodId.EXTRA)]
    assert wiz.method == MethodId.EVERYDAY
    assert _clipping_problems(app) == []
