# SPDX-License-Identifier: GPL-3.0-or-later
"""#173: the footer's key hint starts where the footer link text starts.

The quiet footer links draw their text inside a hover pill (3 px pill
inset + 12 px padding), so the hint under them sat 11-14 px to the left.
The shared footer now indents the hint by that inset, measured from the
hint's own first glyph or key-cap, at every window and text size.
"""

from __future__ import annotations

import pytest

from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at(name, text_size):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.text_size = text_size
    wiz.skip_intro()
    if name == "owner":
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if name == "pick":
        return wiz
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    return wiz


def _link_text_x(app, tkui):
    found = []

    def visit(w):
        if isinstance(w, tkui._Button) and w._variant == "quiet" and w.winfo_ismapped():
            found.append(w)
        for child in w.winfo_children():
            visit(child)

    visit(app._footer)
    first = min(found, key=lambda w: (w.winfo_rooty(), w.winfo_rootx()))
    return first.winfo_rootx() + first.bbox(first._label)[0]


def _hint_x(app, tkui):
    return app._hint.winfo_rootx() + tkui._text_start(app._hint)


@pytest.mark.parametrize("name", ["owner", "pick", "method"])
@pytest.mark.parametrize("size,text_size", [
    ((800, 600), "standard"), ((800, 600), "extra"),
    ((1280, 820), "standard"), ((1280, 820), "large"),
])
def test_hint_starts_under_the_link_text(name, size, text_size):
    from test_tk_runtime import _clipping_problems, _needs_display
    from beamo_wipe.ui import tk_wizard as tkui

    _needs_display()
    app = tkui.TkWizard(_at(name, text_size))
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        assert abs(_hint_x(app, tkui) - _link_text_x(app, tkui)) <= 2
        assert not _clipping_problems(app)
    finally:
        app._teardown()


def test_text_inset_matches_the_drawn_quiet_link():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui import tk_wizard as tkui

    _needs_display()
    app = tkui.TkWizard(_at("pick", "standard"))
    try:
        app._draw()
        app.root.update()
        links = []

        def visit(w):
            if isinstance(w, tkui._Button) and w._variant == "quiet":
                links.append(w)
            for child in w.winfo_children():
                visit(child)

        visit(app._footer)
        button = links[0]
        assert abs(button.bbox(button._label)[0] - tkui._Button.text_inset(compact=True)) <= 1
    finally:
        app._teardown()


def test_web_preview_hint_has_the_link_inset():
    import re

    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    ghost = re.search(r"button\.btn\.ghost \{[^}]*padding: 8px 16px", html)
    hint = re.search(r"\.fhint \{[^}]*padding: 4px 0 8px 17px", html)
    assert ghost and hint  # 16 px ghost padding + 1 px border
