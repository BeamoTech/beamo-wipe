# SPDX-License-Identifier: GPL-3.0-or-later
"""#139: the setup screen reads language, then text size, then keyboard.

One screen, three labelled parts in that order, on screen and in Tab order,
on every surface; it still fits at 800x600 at every text size. Fake demo
disks only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe.keyboard import LAYOUT_ORDER
from beamo_wipe.lang import LANGUAGE_PICKER_LABEL
from beamo_wipe import keyboard as K
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard


def _at_keyboard(text_size="standard"):
    wiz = make_demo_wizard()
    wiz.preview = False
    if text_size != "standard":
        wiz.text_size = text_size
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    return wiz


# --- Consoles and web preview -----------------------------------------------------------


def test_plain_console_order(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _at_keyboard()

    def stop(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    first_layout = K.LAYOUTS[LAYOUT_ORDER[0]].title
    language = out.index(LANGUAGE_PICKER_LABEL)
    size = out.index(C.TEXT_SIZE_CONSOLE)
    # The page title also heads the console; the keyboard part's own heading
    # comes after the size part.
    positions = [language, size, out.index(C.TITLE_KEYBOARD, size),
                 out.index(first_layout), out.index(C.KEYBOARD_CHECK_LABEL)]
    assert positions == sorted(positions)


def test_curses_order(monkeypatch):
    from test_plain_result_134 import _curses_lines

    wiz = _at_keyboard()
    rows = _curses_lines(monkeypatch, wiz, h=60)
    text = "\n".join(rows)

    def at(fragment):
        return text.index(fragment)

    assert at(LANGUAGE_PICKER_LABEL[:20]) < at(C.TEXT_SIZE_CONSOLE[:30]) < at(C.KEYBOARD_LEAD[:30])
    assert at(C.KEYBOARD_LEAD[:30]) < at(K.LAYOUTS[LAYOUT_ORDER[0]].title)


def test_web_preview_order():
    import re

    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    block = html[html.index('} else if (screen === "keyboard") {'):]
    block = block[:block.index("main.querySelectorAll")]
    order = [block.index(token) for token in (
        "${P.languagePicker}", "${P.textSizeUtility}", "${P.titles.keyboard}",
        "${layouts}", "${P.keyboardCheck}")]
    assert order == sorted(order)
    assert re.search(r'class="text-size"', block)


def test_gtk_source_order():
    """GTK cannot run on every host; its build order is the reading order."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("elif screen == Screen.KEYBOARD:"):]
    block = block[:block.index("elif screen in (Screen.WHAT, Screen.OWNER):")]
    order = [block.index(token) for token in (
        "LANGUAGE_PICKER_LABEL", "C.TEXT_SIZE_UTILITY", "C.TEXT_SIZE_LABELS",
        "C.KEYBOARD_LEAD", "LAYOUT_ORDER", "C.KEYBOARD_CHECK_LABEL")]
    assert order == sorted(order)


# --- Rendered Tk ----------------------------------------------------------------------------


@pytest.fixture
def tk_keyboard():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(text_size="standard", size=(800, 600)):
        _needs_display()
        wiz = _at_keyboard(text_size)
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(3):
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


def _label_y(app, text):
    for w in _walk(app._body):
        if w.winfo_class() == "Label" and str(w.cget("text")) == text:
            return w.winfo_rooty()
    raise AssertionError(f"label not shown: {text!r}")


def test_tk_sections_are_language_then_size_then_keyboard(tk_keyboard):
    wiz, app = tk_keyboard()
    language = _label_y(app, LANGUAGE_PICKER_LABEL)
    size = _label_y(app, C.TEXT_SIZE_UTILITY)
    keyboard = _label_y(app, C.TITLE_KEYBOARD)
    first_layout = app._keyboard_layout_cards[LAYOUT_ORDER[0]].winfo_rooty()
    check = _label_y(app, C.KEYBOARD_CHECK_LABEL)
    assert language < size < keyboard < first_layout < check
    # Every size choice sits between the size label and the keyboard heading.
    from beamo_wipe.ui.tk_wizard import _Button

    sizes = [b for b in _walk(app._body) if isinstance(b, _Button)
             and str(b.itemcget(b._label, "text")) in C.TEXT_SIZE_LABELS.values()]
    assert len(sizes) == 3
    assert all(size < b.winfo_rooty() < keyboard for b in sizes)


def test_tk_tab_order_follows_the_screen(tk_keyboard):
    from beamo_wipe.ui.tk_wizard import _Button

    wiz, app = tk_keyboard()
    start = app._keyboard_language_cards[wiz.language]
    kinds, current = [], start
    for _ in range(40):
        if current in app._keyboard_language_cards.values():
            kinds.append("language")
        elif isinstance(current, _Button) and str(current.itemcget(current._label, "text")) in C.TEXT_SIZE_LABELS.values():
            kinds.append("size")
        elif current in app._keyboard_layout_cards.values():
            kinds.append("layout")
        elif current.winfo_class() == "Entry":
            kinds.append("check")
        elif current is app._primary:
            kinds.append("continue")
            break
        current = current.tk_focusNext()
    collapsed = [k for i, k in enumerate(kinds) if i == 0 or kinds[i - 1] != k]
    assert collapsed[:5] == ["language", "size", "layout", "check", "continue"]


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_fits_800x600_at_every_text_size(tk_keyboard, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    wiz, app = tk_keyboard(text_size)
    assert _clipping_problems(app) == []
    assert _off_window_problems(app) == []
    assert app._primary.winfo_ismapped()
    # The language and size parts are both in the first view.
    canvas_bottom = app._body_canvas.winfo_rooty() + app._body_canvas.winfo_height()
    assert _label_y(app, C.TEXT_SIZE_UTILITY) < canvas_bottom
