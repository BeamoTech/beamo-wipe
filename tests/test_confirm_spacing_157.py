# SPDX-License-Identifier: GPL-3.0-or-later
"""#157: Confirm is balanced, and its card and warning stay in view.

Roomy windows centre Confirm's block vertically, measured as if the
wrong-entry help were showing, so nothing moves when that help appears; the
space under the status line is where it appears. Short windows and larger
text trim Confirm's gaps, show the #156 feedback in the status line right
under the entry, and the #155 reveal never scrolls the disk card or the #128
warning out of view. Fake disks only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import lang
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

ROOMY = [((1024, 768), "standard"), ((1280, 720), "standard"), ((1280, 820), "standard"),
         ((1280, 1024), "standard"), ((1920, 1080), "standard"), ((1280, 820), "large")]
TIGHT = [((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
         ((1024, 600), "standard"), ((1280, 820), "extra")]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


@pytest.fixture
def confirm_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size, text_size):
        _needs_display()
        wiz = make_demo_wizard()
        wiz.preview = False
        wiz.text_size = text_size
        wiz.skip_intro()
        wiz.set_owner(True)
        wiz.continue_owner()
        wiz.select_disk(wiz.selectable[0].path)
        wiz.continue_pick()
        assert wiz.screen == Screen.CONFIRM
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        _settle(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _settle(app, n=10):
    for _ in range(n):
        app.root.update()


def _walk(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(_walk(child))
    return out


def _spacer(app):
    found = [w for w in _walk(app._body) if getattr(w, "_beamo_confirm_spacer", False)]
    assert len(found) == 1
    return found[0]


def _warning(app):
    labels = [w for w in _walk(app._body) if w.winfo_class() == "Label"
              and "will be erased" in str(w.cget("text"))]
    assert labels
    return labels[0]


def _in_view(app, widget):
    top = widget.winfo_rooty()
    return (widget.winfo_ismapped() and top >= app._body.winfo_rooty() - 1
            and top + widget.winfo_height() <= app._footer.winfo_rooty() + 1)


def _wrong(app, wiz):
    token = wiz.confirm.token
    app._confirm_var.set(("Z" if token[0].upper() != "Z" else "Y") + token[1:])
    _settle(app)


@pytest.mark.parametrize("size,text_size", ROOMY)
def test_roomy_confirm_is_balanced_and_does_not_move_when_help_appears(confirm_app, size, text_size):
    wiz, app = confirm_app(size, text_size)
    spacer = _spacer(app)
    assert int(spacer.winfo_height()) > 10  # space above, not only below
    entry_y = app._match_pill.winfo_rooty()
    card_y = app._confirm_card.winfo_rooty()
    gap_above = card_y - app._body.winfo_rooty()
    gap_below = app._footer.winfo_rooty() - (app._match_pill.winfo_rooty() + app._match_pill.winfo_height())
    assert gap_below > 0
    assert gap_above > 40
    _wrong(app, wiz)
    # Nothing above the status line moved, and the help fits in the space.
    assert app._match_pill.winfo_rooty() == entry_y
    assert app._confirm_card.winfo_rooty() == card_y
    assert app._layout_hint.winfo_manager() == "pack"
    assert _in_view(app, app._layout_hint)
    assert _in_view(app, app._match_pill)


@pytest.mark.parametrize("size,text_size", TIGHT)
def test_tight_confirm_keeps_card_warning_entry_and_status_in_view(confirm_app, size, text_size):
    wiz, app = confirm_app(size, text_size)
    for state in ("empty", "wrong"):
        if state == "wrong":
            _wrong(app, wiz)
        assert _in_view(app, app._confirm_card), (state, size, text_size)
        assert _in_view(app, _warning(app)), (state, size, text_size)
        assert _in_view(app, app._match_pill), (state, size, text_size)
    # The feedback is in the status line, right under the entry.
    text = str(app._match_label.cget("text"))
    assert text.startswith("You typed: ") and "Character 1 doesn't match." in text


def test_the_status_line_follows_the_entry(confirm_app):
    wiz, app = confirm_app((1280, 820), "standard")
    from beamo_wipe import copy as C

    assert str(app._match_label.cget("text")) == C.CONFIRM_MATCH_WAIT
    _wrong(app, wiz)
    assert str(app._match_label.cget("text")).count("\n") == 1
    app._confirm_var.set(wiz.confirm.token)
    _settle(app)
    assert wiz.token_ok
    assert str(app._match_label.cget("text")) == C.CONFIRM_MATCH_OK
    assert not app._layout_hint.winfo_manager()


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((1280, 820), "standard")])
def test_confirm_has_no_clipping_or_off_window_controls(confirm_app, size, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    wiz, app = confirm_app(size, text_size)
    for state in ("empty", "wrong"):
        if state == "wrong":
            _wrong(app, wiz)
        assert _clipping_problems(app) == [], state
        assert not _off_window_problems(app), state


def test_gates_are_unchanged(confirm_app):
    wiz, app = confirm_app((1280, 820), "standard")
    _wrong(app, wiz)
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM and wiz._authorized_operation is None
    app._confirm_var.set(wiz.confirm.token)
    _settle(app)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE and not wiz.erase_enabled and not wiz.runner.started
