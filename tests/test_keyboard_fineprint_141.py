# SPDX-License-Identifier: GPL-3.0-or-later
"""#141: the keyboard-layout fine print sits behind Show more.

"Only the layouts listed here are offered... does not change firmware or
BIOS keyboards" is no longer in the keyboard screen's main view; the shared
Show more control (Tk, web preview) or a native expander (GTK) reveals it,
by keyboard and screen reader. The consoles have no disclosure control, so
it follows the layout list instead of leading it. Fake demo disks only.
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
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    return wiz


def test_the_information_is_unchanged():
    assert C.KEYBOARD_LIMITS == (
        "Only the layouts listed here are offered. The change lasts until this "
        "USB restarts. It does not change firmware or BIOS keyboards."
    )


# --- Consoles: after the layouts, not leading them -------------------------------------


def test_plain_console_prints_it_after_the_layouts(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _keyboard_wizard()

    def stop(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    last_layout = K.LAYOUTS[LAYOUT_ORDER[-1]].note
    assert out.index(last_layout) < out.index(C.KEYBOARD_LIMITS) < out.index(C.KEYBOARD_CHECK_LABEL)


def test_curses_first_page_leaves_it_out_and_paging_reaches_it(monkeypatch):
    from test_plain_result_134 import _curses_lines

    wiz = _keyboard_wizard()
    first = "\n".join(_curses_lines(monkeypatch, wiz, h=24))
    assert C.KEYBOARD_LIMITS[:30] not in first
    tall = "\n".join(_curses_lines(monkeypatch, wiz, h=80))
    assert C.KEYBOARD_LIMITS[:30] in tall
    assert tall.index(K.LAYOUTS[LAYOUT_ORDER[-1]].title) < tall.index(C.KEYBOARD_LIMITS[:30])


# --- GTK (source) and web preview ------------------------------------------------------


def test_gtk_puts_it_in_a_collapsed_expander():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("elif screen == Screen.KEYBOARD:"):]
    block = block[:block.index("elif screen in (Screen.WHAT, Screen.OWNER):")]
    assert "self.label(C.KEYBOARD_LIMITS)" not in block
    assert "Gtk.Expander.new(C.BTN_MORE)" in block and "set_expanded(False)" in block
    assert "limits_text.set_can_focus(True)" in block


def test_web_preview_uses_the_shared_show_more():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    block = html[html.index('} else if (screen === "keyboard") {'):]
    block = block[:block.index('} else if (screen === "owner")')]
    assert '${moreLink("keyboard-limits")}' in block
    assert "${showMore ? `<p class=\"small muted\">${P.keyboardLimits}</p>` : \"\"}" in block
    assert "bindMore();" in block


# --- Rendered Tk ---------------------------------------------------------------------------


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
        app._show_more = False
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _labels(app):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [str(w.cget("text")) for w in walk(app.root)
            if w.winfo_class() == "Label" and w.winfo_ismapped()]


def test_tk_main_view_hides_it_and_show_more_reveals_it(tk_keyboard):
    wiz, app = tk_keyboard()
    assert C.KEYBOARD_LIMITS not in _labels(app)
    more = app._more_button
    assert more.itemcget(more._label, "text") == C.BTN_MORE
    more._command()
    app.root.update()
    assert C.KEYBOARD_LIMITS in _labels(app)
    assert app._more_button.itemcget(app._more_button._label, "text") == C.BTN_LESS
    # Keyboard users stay on the disclosure after it toggles.
    assert app.root.focus_lastfor() is app._more_button
    app._more_button._command()
    app.root.update()
    assert C.KEYBOARD_LIMITS not in _labels(app)


def test_tk_show_more_is_in_the_tab_order_between_layouts_and_check(tk_keyboard):
    wiz, app = tk_keyboard()
    last_layout = app._keyboard_layout_cards[LAYOUT_ORDER[-1]]
    assert last_layout.tk_focusNext() is app._more_button
    assert app._more_button.tk_focusNext().winfo_class() == "Entry"


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_fits_800x600_open_and_closed(tk_keyboard, text_size):
    from test_tk_runtime import _clipping_problems

    wiz, app = tk_keyboard(text_size)
    assert _clipping_problems(app) == []
    app._more_button._command()
    app.root.update()
    assert _clipping_problems(app) == []
    assert app._primary.winfo_ismapped()
