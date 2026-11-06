# SPDX-License-Identifier: GPL-3.0-or-later
"""#176: one visual style for "selected" across every choice.

Before: a filled radio dot on cards, a filled navy pill in the text-size
switch and an outline only on the language chips. Now one token — brand
edge (2 px), tint fill and a drawn check mark — on layout, disk and method
cards, the size switch and the language chips; GTK and the web preview use
the same token. The check means selection never relies on colour alone.
Fake disks only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import MethodId
from test_ui_system import _contrast


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def test_token_values_and_contrast():
    from beamo_wipe.ui import tk_wizard as tkui

    assert tkui.SELECTED_FILL == tkui.PRIMARY_TINT
    assert tkui.SELECTED_EDGE == tkui.PRIMARY and tkui.SELECTED_EDGE_W == 2
    assert _contrast(tkui.SELECTED_INK, tkui.SELECTED_FILL) >= 7.0  # selected text
    for bg in (tkui.SURFACE, tkui.BG, tkui.TRACK):
        assert _contrast(tkui.SELECTED_EDGE, bg) >= 3.0  # edge and mark vs surroundings
    assert _contrast("#FFFFFF", tkui.SELECTED_EDGE) >= 4.5  # the white check


def _tk(wiz, size=(1280, 820)):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+20+20")
    app._draw()
    for _ in range(8):
        app.root.update()
    return app


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _marks(widget):
    return [w for w in _walk(widget) if hasattr(w, "_beamo_selected_mark")]


def _assert_selected_box(box, tkui):
    assert box._outline == tkui.SELECTED_EDGE and box._ow == tkui.SELECTED_EDGE_W
    assert box._fill == tkui.SELECTED_FILL
    marks = _marks(box)
    assert marks and all(m._beamo_selected_mark for m in marks)
    assert all(m.find_withtag("check") for m in marks)  # not colour alone


def _assert_unselected_box(box, tkui):
    assert box._outline != tkui.SELECTED_EDGE and box._fill != tkui.SELECTED_FILL
    assert not any(m._beamo_selected_mark for m in _marks(box))


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_keyboard_screen_language_size_and_layout_share_the_token(size):
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = make_demo_wizard()
    wiz.skip_splash()
    app = _tk(wiz, size)
    try:
        chips = app._keyboard_language_cards
        _assert_selected_box(chips[wiz.language], tkui)
        for code, chip in chips.items():
            if code != wiz.language:
                _assert_unselected_box(chip, tkui)
        cards = app._keyboard_layout_cards
        _assert_selected_box(cards[wiz.keyboard_layout], tkui)
        for layout_id, card in cards.items():
            if layout_id != wiz.keyboard_layout:
                _assert_unselected_box(card, tkui)
        labels = set(tkui.C.TEXT_SIZE_LABELS.values())
        sizes = [w for w in _walk(app._body)
                 if isinstance(w, tkui._Button) and w.itemcget(w._label, "text") in labels]
        chosen = [b for b in sizes if b._variant == "selected"]
        assert len(chosen) == 1 and chosen[0]._mark > 0
        assert chosen[0].find_withtag("check")
        assert all(b._variant == "segment" and not b._mark for b in sizes if b not in chosen)
    finally:
        app._teardown()


def test_pick_and_method_cards_share_the_token():
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    app = _tk(wiz)
    try:
        _assert_selected_box(app._pick_cards["/dev/sda"], tkui)
    finally:
        app._teardown()
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.set_method(MethodId.EXTRA)
    app = _tk(wiz)
    try:
        boxes = [w for w in _walk(app._body) if isinstance(w, tkui._Box) and _marks(w)
                 and w._ow in (1, tkui.SELECTED_EDGE_W) and w._outline in (tkui.BORDER, tkui.SELECTED_EDGE)]
        selected = [b for b in boxes if b._outline == tkui.SELECTED_EDGE]
        assert len(selected) == 1
        _assert_selected_box(selected[0], tkui)
    finally:
        app._teardown()


def test_gtk_marks_selected_choices_with_the_token():
    import pathlib

    src = (pathlib.Path(__file__).resolve().parents[1]
           / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "button.selected-choice" in src and "border: 2px solid #1C4A73" in src
    assert src.count('add_class("selected-choice")') == 3  # language, text size, layout


def test_web_preview_uses_the_token():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert ".sel .radio::after" in html and "rotate(45deg)" in html
    assert 'class="btn choice sel"' in html and 'class="tick"' in html
    assert ".choice.sel, .textsizes button.btn.choice.sel" in html
