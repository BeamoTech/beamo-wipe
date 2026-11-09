# SPDX-License-Identifier: GPL-3.0-or-later
"""#169: result-screen key hints say exactly what will happen.

The preview result showed "Enter continues. Esc goes back." although Esc does
nothing on a result and Enter runs the preview again. Now: preview "Enter
runs the preview again." (Tk and the web preview, where Enter now does the
same as Run again); live "Enter requests shutdown." (unchanged). No result
screen offers Esc or going back into a completed erase. Fake disks only.
"""

from __future__ import annotations


import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard
from preview_page import inline_script


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at_done(preview):
    wiz = make_demo_wizard()
    wiz.preview = preview
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    wiz.screen = Screen.DONE  # result screen only; nothing starts
    return wiz


def test_hint_copy_names_the_action_and_never_esc():
    assert C.HINT_DONE_PREVIEW == "Enter runs the preview again."
    assert C.HINT_DONE == "Enter requests shutdown."
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for hint in (C.HINT_DONE, C.HINT_DONE_PREVIEW):
            assert hint.startswith("Enter ") and "Esc" not in hint, (code, hint)


@pytest.mark.parametrize("preview", [True, False])
def test_result_has_no_back(preview):
    wiz = _at_done(preview)
    wiz.back()
    assert wiz.screen == Screen.DONE


def test_preview_enter_runs_again_and_live_enter_requests_shutdown():
    wiz = _at_done(True)
    wiz.arm_done_keyboard()
    wiz.accept_done_keyboard()
    assert wiz.screen != Screen.DONE and not wiz.wants_shutdown
    live = _at_done(False)
    live.arm_done_keyboard()
    live.accept_done_keyboard()
    assert live.screen != Screen.DONE or live.wants_shutdown


def test_curses_result_footer_matches():
    for preview, expected in ((True, C.CON_DONE_PREVIEW), (False, C.CON_DONE_SHUTDOWN)):
        lines = " ".join(console_wizard._primary_footer(_at_done(preview), False))
        assert expected in lines and "Esc" not in lines


def test_web_preview_result_hint_and_enter():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    script = inline_script(html)
    done = script[script.index('} else if (screen === "done")'):]
    done = done[:6000]
    assert "renderHint(P.hints.donePreview)" in done
    assert C.HINT_DONE_PREVIEW in html
    keys = script[script.index('(screen === "done" || screen === "stopped") && e.key === "Enter"'):]
    keys = keys[: keys.index("return;") + 7]
    assert "requestAnotherPreview()" in keys and "Escape" not in keys
    # Enter on a focused control keeps its own meaning.
    assert 'closest?.("button, a, input, textarea, select, summary")' in keys


@pytest.mark.parametrize("preview,expected", [(True, "HINT_DONE_PREVIEW"), (False, "HINT_DONE")])
def test_tk_result_hint(preview, expected):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _at_done(preview)
    app = TkWizard(wiz)
    try:
        app.root.geometry("1280x820+20+20")
        app._draw()
        for _ in range(6):
            app.root.update()
        texts = []

        def visit(w):
            if w.winfo_class() == "Label":
                texts.append(str(w.cget("text")))
            for child in w.winfo_children():
                visit(child)

        visit(_shown_hint(app))  # #174: on the Keyboard shortcuts page
        joined = " ".join(" ".join(texts).split())
        want = " ".join(getattr(C, expected).split())
        # Key names render as key caps; the words around them must all be there.
        for word in want.replace(".", "").split():
            assert word in joined
        assert "Esc" not in joined and "goes back" not in joined
    finally:
        app._teardown()


def _shown_hint(app):
    """#174: the screen's key hint, on the Keyboard shortcuts page."""
    app._open_shortcuts()
    for _ in range(4):
        app.root.update()
    found = []

    def walk(node):
        if getattr(node, "_beamo_shortcuts_hint", False):
            found.append(node)
        for child in node.winfo_children():
            walk(child)

    walk(app._help_popup)
    (hint,) = found
    return hint
