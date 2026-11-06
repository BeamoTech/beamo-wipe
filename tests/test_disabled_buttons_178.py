# SPDX-License-Identifier: GPL-3.0-or-later
"""#178: disabled buttons are legible and come with a reason.

The shared button draws a disabled filled button (primary, danger,
secondary) as a faded brand pill with a dashed edge: label #4A6684 on
#F0F5FA (5.4:1), edge #6A84A1 on white (3.9:1). Before, a grey pill on the
white footer barely showed (1.19:1) with a 3.7:1 label. The shared
_primary_btn puts the reason on the same row, just before the button, on
every screen where it can be disabled (Owner, Pick, Confirm, Review,
Diagnostic), and keeps it in step when the button turns on without a
redraw. Fake disks only; erase starts are recorded, never run.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from test_ui_system import _contrast


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def test_disabled_token_contrast():
    from beamo_wipe.ui import tk_wizard as tkui

    assert _contrast(tkui.DISABLED_INK, tkui.DISABLED_FILL) >= 4.5  # >= 3:1 required
    assert _contrast(tkui.DISABLED_EDGE, tkui.SURFACE) >= 3.0
    assert _contrast(tkui.DISABLED_EDGE, tkui.FOOTER_BG) >= 3.0
    # Never mistaken for the #176 selected style.
    assert tkui.DISABLED_EDGE != tkui.SELECTED_EDGE


def _wizard(name):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    if name == "owner":
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if name == "pick":
        wiz.selected = None
        return wiz
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    if name == "confirm":
        return wiz
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    return wiz


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


def _dash(button):
    (pill,) = [i for i in button.find_withtag("rr") if button.type(i) == "polygon"
               and button.itemcget(i, "outline")]
    return str(button.itemcget(pill, "dash"))


REASONS = {
    "owner": "OWNER_CONTINUE_REASON",
    "pick": "PICK_CONTINUE_REASON",
    "confirm": "CONFIRM_CONTINUE_REASON",
    "last": "REVIEW_ERASE_REASON",
}


@pytest.mark.parametrize("name", list(REASONS))
@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_disabled_primary_is_readable_and_has_its_reason(name, size):
    from test_tk_runtime import _clipping_problems
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = _wizard(name)
    app = _tk(wiz, size)
    try:
        primary = app._primary
        assert not primary._enabled
        fill, fg, outline = primary._state_colors()
        assert (fill, fg, outline) == (tkui.DISABLED_FILL, tkui.DISABLED_INK, tkui.DISABLED_EDGE)
        assert _dash(primary)  # dashed edge
        reason = app._disabled_reason
        assert reason is not None and reason.winfo_ismapped()
        assert str(reason.cget("text")) == getattr(C, REASONS[name])
        # Same row, just before the button.
        assert reason.winfo_rootx() + reason.winfo_width() <= primary.winfo_rootx()
        assert reason.winfo_rooty() < primary.winfo_rooty() + primary.winfo_height()
        assert not _clipping_problems(app)
    finally:
        app._teardown()


def test_reason_follows_the_button_without_a_redraw():
    wiz = _wizard("confirm")
    app = _tk(wiz)
    try:
        assert app._disabled_reason.winfo_ismapped()
        app._confirm_var.set(wiz.confirm.token)
        for _ in range(4):
            app.root.update()
        assert app._primary._enabled and not app._disabled_reason.winfo_ismapped()
        app._confirm_var.set("")
        for _ in range(4):
            app.root.update()
        assert not app._primary._enabled and app._disabled_reason.winfo_ismapped()
    finally:
        app._teardown()


def test_review_reason_goes_when_erase_now_turns_on_and_nothing_erases():
    wiz = _wizard("last")
    starts = []
    wiz.begin_erase = lambda: starts.append(wiz.screen)  # type: ignore[method-assign]
    app = _tk(wiz)
    try:
        assert not app._primary._enabled and app._disabled_reason.winfo_ismapped()
        wiz._erase_until = 0
        app._refresh_last_chance()
        for _ in range(4):
            app.root.update()
        assert app._primary._enabled and not app._disabled_reason.winfo_ismapped()
        assert starts == [] and not wiz.runner.started  # enabling never starts it
    finally:
        app._teardown()


def test_enabled_buttons_are_unchanged():
    from beamo_wipe.ui import tk_wizard as tkui

    wiz = _wizard("pick")
    wiz.select_disk("/dev/sda")
    app = _tk(wiz)
    try:
        fill, fg, outline = app._primary._state_colors()
        assert app._primary._enabled
        assert (fill, fg, outline) == (tkui.PRIMARY, "#FFFFFF", None)  # solid navy, no dashed edge
        assert app._disabled_reason is None or not app._disabled_reason.winfo_ismapped()
    finally:
        app._teardown()


def test_gtk_and_web_use_the_same_disabled_style():
    import pathlib

    from beamo_wipe.gallery import gallery_html

    root = pathlib.Path(__file__).resolve().parents[1]
    gtk = (root / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "button:disabled {{ background-image: none; background-color: #F0F5FA; color: #4A6684; border: 1px dashed #6A84A1; }}" in gtk
    html = gallery_html()
    assert "button.btn:disabled { background: #F0F5FA; color: #4A6684; border: 1px dashed #6A84A1;" in html


def test_every_language_has_the_reasons():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for key in ("PICK_CONTINUE_REASON", "CONFIRM_CONTINUE_REASON", "REVIEW_ERASE_REASON",
                    "DISABLED_BUSY"):
            value = getattr(C, key)
            assert value and "{" not in value
