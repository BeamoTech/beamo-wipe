# SPDX-License-Identifier: GPL-3.0-or-later
"""#142: layout-card number badges show only with keyboard focus.

The 1-7 badges are hidden until a layout card has keyboard focus (or a
layout key was used on this visit); the 1-7 and Up/Down shortcuts always
work, the screen's key hint names them, and GTK's accessible names keep the
number. Fake demo disks only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import keyboard as K
from beamo_wipe.keyboard import LAYOUT_ORDER
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]


def _keyboard_wizard():
    from test_keyboard_layout import _Apply

    wiz = make_demo_wizard()
    wiz._apply_keyboard = _Apply()
    wiz.preview = False
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    return wiz


def test_hint_names_the_digit_shortcut():
    assert "1–7" in C.HINT_KEYBOARD
    assert len(LAYOUT_ORDER) == 7


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_names_it(code):
    from beamo_wipe import lang

    try:
        lang.set_language(code)
        assert "1–7" in C.HINT_KEYBOARD and "Up/Down" in C.HINT_KEYBOARD
    finally:
        lang.set_language("en")


def test_gtk_names_keep_the_number():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert 'f"{index} {spec.title} ({state})"' in src


def test_web_preview_hides_badges_until_the_list_has_focus():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert ".layout-cards .card .row > .kbd { visibility: hidden; }" in html
    assert ".layout-cards:focus-within .card .row > .kbd { visibility: visible; }" in html
    assert '<div class="layout-cards">${layouts}</div>' in html


# --- Rendered Tk -----------------------------------------------------------------------------


@pytest.fixture
def tk_keyboard():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(text_size="standard", size=(800, 600)):
        _needs_display()
        wiz = _keyboard_wizard()
        wiz.text_size = text_size
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _mapped_badges(app):
    return [badge for badge, _text in app._layout_badges if badge.winfo_ismapped()]


class _Key:
    def __init__(self, keysym, char=""):
        self.keysym, self.char = keysym, char or keysym
        self.time = 0
        self.state = 0
        self.widget = None


def test_tk_badges_hidden_by_default(tk_keyboard):
    wiz, app = tk_keyboard()
    assert len(app._layout_badges) == len(LAYOUT_ORDER)
    assert _mapped_badges(app) == []


def test_tk_badges_show_on_card_focus_and_hide_when_focus_leaves(tk_keyboard):
    wiz, app = tk_keyboard()
    card = app._keyboard_layout_cards[LAYOUT_ORDER[2]]
    card.event_generate("<FocusIn>")
    app.root.update()
    assert len(_mapped_badges(app)) == len(LAYOUT_ORDER)
    texts = [str(child.cget("text")) for badge in _mapped_badges(app)
             for child in badge.inner.winfo_children()]
    assert texts == [str(i) for i in range(1, len(LAYOUT_ORDER) + 1)]
    # Focus moves to the check box: badges go away again.
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    entry = next(w for w in walk(app._body) if w.winfo_class() == "Entry")
    app.root.focus_get = lambda: entry  # where Tk reports focus now
    card.event_generate("<FocusOut>")
    app.root.update()
    assert _mapped_badges(app) == []


def test_tk_card_height_does_not_jump_when_badges_appear(tk_keyboard):
    wiz, app = tk_keyboard()
    card = app._keyboard_layout_cards[LAYOUT_ORDER[0]]
    before = card.winfo_height()
    app._show_layout_badges(True)
    app.root.update()
    assert abs(card.winfo_height() - before) <= 2


@pytest.mark.parametrize("index", range(1, len(LAYOUT_ORDER) + 1))
def test_tk_digit_shortcut_always_works_and_reveals_badges(tk_keyboard, index):
    wiz, app = tk_keyboard()
    assert _mapped_badges(app) == []
    app._on_key(_Key(str(index)))
    app.root.update()
    assert wiz.keyboard_layout == LAYOUT_ORDER[index - 1]
    assert len(_mapped_badges(app)) == len(LAYOUT_ORDER)


def test_tk_up_down_also_reveals_badges(tk_keyboard):
    wiz, app = tk_keyboard()
    app._on_key(_Key("Down"))
    app.root.update()
    assert wiz.keyboard_layout == LAYOUT_ORDER[1]
    assert len(_mapped_badges(app)) == len(LAYOUT_ORDER)


def test_tk_badges_reset_on_the_next_visit(tk_keyboard):
    wiz, app = tk_keyboard()
    app._on_key(_Key("3"))
    app.root.update()
    wiz.accept_keyboard()
    app._draw()
    app.root.update()
    wiz.open_keyboard()
    app._draw()
    app.root.update()
    assert wiz.screen == Screen.KEYBOARD
    assert _mapped_badges(app) == []


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_fits_800x600_with_and_without_badges(tk_keyboard, text_size):
    from test_tk_runtime import _clipping_problems

    wiz, app = tk_keyboard(text_size)
    assert _clipping_problems(app) == []
    app._show_layout_badges(True)
    app.root.update()
    assert _clipping_problems(app) == []
    assert K.LAYOUTS  # layouts unchanged
