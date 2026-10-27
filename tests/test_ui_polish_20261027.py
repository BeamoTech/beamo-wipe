# SPDX-License-Identifier: GPL-3.0-or-later
"""Rendered Tk polish: method time guide, header, glyphs, empty and splash.

Fake disks and DryRunRunner only; no engine, no real device. Each case pins
a defect seen in 72 DPI screenshots of the real wizard.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
import tkinter as tk

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.methods import METHODS
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as tkui
from beamo_wipe.ui.layout import LARGE_SIZE, LAPTOP_SIZE, MIN_SIZE, NETBOOK_SIZE
from test_adaptive_layout import _assert_actions_on_window, _texts
from test_tk_runtime import _drive_to, ui  # noqa: F401

GUIDE_SIZES = (MIN_SIZE, NETBOOK_SIZE, LAPTOP_SIZE, LARGE_SIZE)


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


def _at_method(wiz, app, path="/dev/sda"):
    """Method screen for one disk (default: the 1 TB hard disk, longest guide)."""
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    app._draw()
    app.root.update_idletasks()
    app.root.update()


def _clocks(app) -> int:
    found = 0

    def visit(node):
        nonlocal found
        if isinstance(node, tk.Canvas) and int(node.cget("width")) == 16 and len(node.find_all()) == 3:
            found += 1
        for child in node.winfo_children():
            visit(child)

    visit(app.root)
    return found


@pytest.mark.parametrize("size", GUIDE_SIZES)
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_method_cards_show_the_time_guide_without_clipping(ui, size, code):  # noqa: F811
    wiz, app = ui(size=size)
    wiz.set_language(code)
    app.root.geometry(f"{size[0]}x{size[1]}+40+40")
    _at_method(wiz, app)
    shown = _texts(app.root)
    for method in METHODS:
        guide = C.method_time_guide(method, wiz.selected)
        assert guide, (code, method)
        assert guide in shown, (code, method)
    # One clock per card, beside the guide line.
    assert _clocks(app) == len(METHODS)
    _assert_actions_on_window(app)


def test_method_guide_hidden_when_size_is_unknown(ui):  # noqa: F811
    wiz, app = ui(size=LAPTOP_SIZE)
    _at_method(wiz, app)
    wiz.selected = replace(wiz.selected, size_gb_label="", size_bytes=0)
    app._draw()
    app.root.update()
    shown = _texts(app.root)
    assert "Rough guide" not in shown
    for spec in METHODS.values():
        assert spec.verification_description in shown
    # Without a guide the clock stays beside the check sentence, as before.
    checks = sum(1 for spec in METHODS.values() if spec.verification_passes)
    assert _clocks(app) == checks
    _assert_actions_on_window(app)


def _header_texts(app):
    header = app._header
    return [
        (str(header.itemcget(item, "text")), header.bbox(item))
        for item in header.find_all()
        if header.type(item) == "text"
    ]


@pytest.mark.parametrize("code", ["fr", "de", "es"])
def test_header_stage_caption_follows_the_language(ui, code):  # noqa: F811
    wiz, app = ui(size=MIN_SIZE)
    wiz.set_language(code)
    _drive_to(wiz, app, Screen.CONFIRM)
    texts = [text for text, _ in _header_texts(app)]
    assert C.JOURNEY_LABELS[0] in texts
    assert "Preparation" not in texts


def test_wide_header_names_the_stage_once(ui):  # noqa: F811
    wiz, app = ui(size=(1280, 820))
    _drive_to(wiz, app, Screen.CONFIRM)
    texts = [text for text, _ in _header_texts(app)]
    assert texts.count("Preparation") == 1
    for label in C.JOURNEY_LABELS:
        assert label in texts
    # Without the stepper (narrow windows) the caption remains the one label.
    narrow_wiz, narrow = ui(size=MIN_SIZE)
    _drive_to(narrow_wiz, narrow, Screen.CONFIRM)
    assert [text for text, _ in _header_texts(narrow)].count("Preparation") == 1


@pytest.mark.parametrize("size", [LAPTOP_SIZE, NETBOOK_SIZE, (1280, 820)])
def test_stepper_labels_clear_the_header_hairline(ui, size):  # noqa: F811
    wiz, app = ui(size=size)
    _drive_to(wiz, app, Screen.METHOD)
    height = app._header.winfo_height()
    labels = [box for text, box in _header_texts(app) if text in C.JOURNEY_LABELS]
    assert len(labels) == len(C.JOURNEY_LABELS)
    for _x0, y0, _x1, y1 in labels:
        assert y0 >= 0 and y1 <= height - 1


@pytest.mark.parametrize("size", [MIN_SIZE, LAPTOP_SIZE, (1280, 820), LARGE_SIZE])
@pytest.mark.parametrize("screen", [Screen.OWNER, Screen.CONFIRM, Screen.METHOD])
def test_back_is_centred_beside_the_primary(ui, size, screen):  # noqa: F811
    wiz, app = ui(size=size)
    _drive_to(wiz, app, screen)
    app.root.update()
    back = next(
        b for b in _buttons_in(app._footer)
        if b.itemcget(b._label, "text") == C.BTN_BACK
    )
    primary = app._primary

    def middle(widget):
        return widget.winfo_rooty() + widget.winfo_height() / 2.0

    assert abs(middle(back) - middle(primary)) <= 2


def _buttons_in(widget):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, tkui._Button):
            found.append(child)
        found.extend(_buttons_in(child))
    return found


class _Stub:
    def __init__(self):
        self.calls = []

    def create_oval(self, *args, **kwargs):
        self.calls.append(("oval", args, kwargs))

    def create_line(self, *args, **kwargs):
        self.calls.append(("line", args, kwargs))


# Rendered info sizes: empty badge 40, panels 28, result badges 64/72, 88.
@pytest.mark.parametrize("size", [40 * 0.58, 28.0, 64 * 0.58, 72 * 0.58, 88 * 0.58])
def test_info_glyph_dot_and_stem_stay_apart(size):
    stub = _Stub()
    tkui._draw_alert_glyph(stub, 0, 0, size, "info")
    (_, ring, _), (_, dot, _), (_, stem, stem_kw) = stub.calls
    dot_bottom = dot[3]
    stem_top = stem[1] - stem_kw["width"] / 2.0  # round cap
    assert stem_top - dot_bottom >= 1.0
    assert dot[1] >= ring[1] + 1 and stem[3] + stem_kw["width"] / 2.0 <= ring[3]


@pytest.mark.parametrize("size", [MIN_SIZE, LAPTOP_SIZE, LARGE_SIZE])
def test_empty_screen_badge_and_reasons_use_the_page(ui, size):  # noqa: F811
    wiz, app = ui(scenario="empty", size=size)
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    app._draw()
    app.root.update()
    assert wiz.screen == Screen.PICK_EMPTY
    assert app._body_canvas is None
    canvases = []

    def visit(node):
        if isinstance(node, tk.Canvas):
            canvases.append(node)
        for child in node.winfo_children():
            visit(child)

    visit(app._body)
    badge = canvases[0]
    assert int(badge.cget("width")) == 40
    assert badge.cget("bg") == tkui.BG
    # The reasons scroller reaches down to the footer instead of stopping at
    # the default canvas height above empty space.
    region = max(canvases, key=lambda c: c.winfo_height())
    bottom = region.winfo_rooty() + region.winfo_height()
    footer_top = app._footer.winfo_rooty()
    assert footer_top - bottom <= 24
    _assert_actions_on_window(app)


@pytest.mark.parametrize("size", [MIN_SIZE, NETBOOK_SIZE, LAPTOP_SIZE, (1280, 820)])
@pytest.mark.parametrize("text_size", ["standard", "extra"])
def test_splash_is_vertically_centred(ui, size, text_size):  # noqa: F811
    wiz, app = ui(size=size)
    wiz.set_text_size(text_size)
    app._draw()
    app.root.update()
    assert wiz.screen == Screen.SPLASH
    assert app._body_canvas is None
    mapped = []

    def visit(node):
        if node.winfo_ismapped() and node.winfo_class() in {"Label", "Canvas"}:
            mapped.append(node)
        for child in node.winfo_children():
            visit(child)

    visit(app._body)
    top = min(w.winfo_rooty() for w in mapped) - app._body.winfo_rooty()
    bottom = app._body.winfo_height() - max(
        w.winfo_rooty() + w.winfo_height() for w in mapped
    ) + app._body.winfo_rooty()
    assert top >= 16 and bottom >= 16
    assert abs(top - bottom) <= 48
    _assert_actions_on_window(app)
