# SPDX-License-Identifier: GPL-3.0-or-later
"""BW-155B: the hidden Confirm layout hint holds no unmapped Change button.

#155 built the hint's sentence and Change button up front and only packed
the row after a wrong entry, so a hidden, unmapped control sat on Confirm
(test_ui_rework canvas controls [confirm]). The row's contents are now
built while it shows and removed while it is hidden. Fake disks only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.models import Screen
from test_confirm_layout_hint_155 import _confirm, _wrong


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _controls(widget):
    from beamo_wipe.ui.tk_wizard import _Button

    found = []

    def visit(w):
        if isinstance(w, _Button):
            found.append(w)
        for child in w.winfo_children():
            visit(child)

    visit(widget)
    return found


def _settle(app):
    for _ in range(6):
        app.root.update()


@pytest.mark.parametrize("size", [(1024, 740), (800, 600)])
def test_hidden_hint_has_no_controls_and_shown_hint_has_a_mapped_change(size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _confirm()
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        _settle(app)
        hint = app._layout_hint
        assert hint is not None and not hint.winfo_children()
        assert all(b.winfo_ismapped() for b in _controls(app._body))
        wiz.set_confirm_input(_wrong(wiz.confirm.token))
        app._sync_layout_hint()
        _settle(app)
        (change,) = [b for b in _controls(hint)]
        assert getattr(change, "_beamo_layout_change", False)
        assert str(change.itemcget(change._label, "text")) == C.CONFIRM_LAYOUT_CHANGE
        assert change.winfo_ismapped()
        change._command()
        _settle(app)
        assert wiz.screen == Screen.KEYBOARD
    finally:
        app._teardown()


def test_hint_contents_go_away_when_it_hides_again():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _confirm()
    app = TkWizard(wiz)
    try:
        app.root.geometry("1024x740+20+20")
        app._draw()
        _settle(app)
        wiz.set_confirm_input(_wrong(wiz.confirm.token))
        app._sync_layout_hint()
        _settle(app)
        assert app._layout_hint.winfo_children()
        wiz.set_confirm_input(wiz.confirm.token)  # matches: the hint hides
        app._sync_layout_hint()
        _settle(app)
        assert not app._layout_hint.winfo_children() and app._layout_sentence is None
    finally:
        app._teardown()
