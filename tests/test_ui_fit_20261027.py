# SPDX-License-Identifier: GPL-3.0-or-later
"""Rendered Tk fit at short heights and around the scrolling body.

Fake disks and DryRunRunner only; no engine, no real device. Each case pins
a defect seen in 72 DPI screenshots of the real wizard: titles sliced by the
opening focus scroll, an empty progress block, method cards and disks below
the fold at 800x600, a half-visible countdown ring, stale body offsets after
content shrinks, an English-only preview stripe and pick rows that did not
say what each disk holds.
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import PropertyMock, patch

import pytest
import tkinter as tk

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe import progress
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import (
    CONTENTS_DATA,
    CONTENTS_SYSTEM,
    CONTENTS_UNKNOWN,
    CONTENTS_WINDOWS,
    MethodId,
    Screen,
)
from beamo_wipe.progress import ProgressView
from beamo_wipe.ui import tk_wizard as tkui
from beamo_wipe.ui.layout import LARGE_SIZE, LAPTOP_SIZE, MIN_SIZE, NETBOOK_SIZE
from beamo_wipe.wizard import Wizard
from test_adaptive_layout import _assert_actions_on_window
from test_tk_runtime import _clipping_problems, _drive_to, _needs_display

SHORT = (MIN_SIZE, NETBOOK_SIZE)
SIZES = (MIN_SIZE, NETBOOK_SIZE, LAPTOP_SIZE, LARGE_SIZE)
MODES = pytest.mark.parametrize("preview", [False, True], ids=["live", "preview"])
# Demo paths with each observed classification; the boot USB stays as found.
CONTENTS = {
    "/dev/nvme0n1": CONTENTS_WINDOWS,
    "/dev/sda": CONTENTS_DATA,
    "/dev/sdd": CONTENTS_SYSTEM,
}


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


@pytest.fixture
def tk_app():
    created = []

    def build(*, size=MIN_SIZE, code="en", preview=False, contents=None):
        _needs_display()
        lang.set_language("en")
        wiz = make_demo_wizard()
        # The live kiosk has no preview stripe; ./preview adds one above the header.
        wiz.preview = preview
        wiz.set_language(code)
        if contents:
            def tag(disk):
                if disk.is_boot:
                    return disk
                return replace(disk, contents=contents.get(disk.path, disk.contents))

            wiz.discovery = replace(
                wiz.discovery,
                disks=tuple(map(tag, wiz.discovery.disks)),
                selectable=tuple(map(tag, wiz.discovery.selectable)),
            )
        app = tkui.TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app.root.update_idletasks()
        app.root.focus_force()
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _settle(app, ms=250):
    """Let wrapping, focus reveals and picker restore timers finish."""
    app.root.update_idletasks()
    app.root.update()
    app.root.after(ms, app.root.quit)
    app.root.mainloop()
    app.root.update_idletasks()
    app.root.update()


def _descendants(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _descendants(child)


def _extent(widget, view):
    top = widget.winfo_rooty() - view.winfo_rooty()
    return top, top + widget.winfo_height()


def _label(root, text):
    found = [
        w for w in _descendants(root)
        if w.winfo_class() == "Label" and str(w.cget("text")) == text and w.winfo_ismapped()
    ]
    assert found, text
    return found[0]


def _box_of(widget):
    node = widget
    while node is not None and not isinstance(node, tkui._Box):
        node = node.master
    assert node is not None
    return node


def _between_lines(label, top) -> bool:
    """True when the view edge falls exactly between two wrapped lines."""
    line = float(label.tk.call("font", "metrics", label.cget("font"), "-linespace"))
    inset = sum(float(label.cget(o)) for o in ("borderwidth", "highlightthickness", "pady"))
    lines = int(round((label.winfo_reqheight() - 2 * inset) / line))
    first = top + (label.winfo_height() - lines * line) / 2.0
    return any(abs(first + k * line) <= 1 for k in range(1, lines))


def _sliced_at_top(app):
    """Text, entries, icons and buttons cut by the body's top edge."""
    canvas = app._body_canvas
    origin = canvas.winfo_rooty()
    sliced = []
    for widget in _descendants(app._body_inner):
        cls = widget.winfo_class()
        if not widget.winfo_ismapped() or isinstance(widget, tkui._Box) or cls == "Frame":
            continue
        top = widget.winfo_rooty() - origin
        bottom = top + widget.winfo_height()
        if top >= -1 or bottom <= 1:
            continue
        text = str(widget.cget("text")) if cls == "Label" else ""
        if text and _between_lines(widget, top):
            continue
        sliced.append((cls, top, bottom, text[:40]))
    return sliced


# -- 1. Opening focus never slices a title or a line --------------------------


@MODES
@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("screen", [Screen.KEYBOARD, Screen.OWNER, Screen.CONFIRM])
def test_opening_focus_never_slices_a_title_or_line(tk_app, screen, code, size, preview):
    wiz, app = tk_app(size=size, code=code, preview=preview)
    _drive_to(wiz, app, screen)
    _settle(app)
    assert wiz.screen == screen
    canvas = app._body_canvas
    if canvas is None:
        # Tall windows show Confirm without a scrolling body.
        assert screen == Screen.CONFIRM and not app.lay.short
        return
    view = canvas.winfo_height()
    assert _sliced_at_top(app) == []
    focus = app.root.focus_get()
    assert focus is not None
    if str(focus).startswith(str(canvas)):
        top, bottom = _extent(focus, canvas)
        assert 0 <= top and bottom <= view, (top, bottom, view)
        offset = focus.winfo_rooty() - app._body_inner.winfo_rooty()
        if offset + focus.winfo_height() <= view:
            # It fits with the body at the top: the screen opens at the top.
            assert canvas.canvasy(0) == 0


@pytest.mark.parametrize("size", (MIN_SIZE, LAPTOP_SIZE), ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("screen", [Screen.OWNER, Screen.CONFIRM])
def test_show_more_round_trip_keeps_toggle_visible_and_lines_whole(tk_app, screen, size):
    wiz, app = tk_app(size=size)
    _drive_to(wiz, app, screen)
    _settle(app)
    for expected in (C.BTN_LESS, C.BTN_MORE):
        app._more_button._command()
        _settle(app)
        assert app._more_button.itemcget(app._more_button._label, "text") == expected
        focus = app.root.focus_get()
        if screen == Screen.CONFIRM:
            # Confirm hands focus back to its typing field after a redraw.
            assert isinstance(focus, tk.Entry)
        else:
            assert focus is app._more_button
        canvas = app._body_canvas
        top, bottom = _extent(focus, canvas)
        assert 0 <= top and bottom <= canvas.winfo_height()
        assert _sliced_at_top(app) == []
        region = [float(v) for v in str(canvas.cget("scrollregion")).split()]
        assert 0 <= canvas.canvasy(0) <= max(0.0, region[3] - canvas.winfo_height())
    assert not wiz.runner.started


# -- 2. Working: an honest starting state, no empty block, no jump ------------


def _progress_slot_texts(app):
    heading = _label(app._body, C.ERASE_PROGRESS_LABEL)
    bar = app._progress_bar
    upper = heading.winfo_rooty() + heading.winfo_height()
    lower = bar.winfo_rooty()
    return [
        str(w.cget("text"))
        for w in _descendants(app._body)
        if w.winfo_class() == "Label" and w.winfo_ismapped() and str(w.cget("text"))
        and upper <= w.winfo_rooty() and w.winfo_rooty() + w.winfo_height() <= lower
    ]


@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_working_opens_with_not_reported_line_in_a_stable_slot(tk_app, code, size):
    wiz, app = tk_app(size=size, code=code)
    wiz.screen = Screen.WORKING
    wiz.selected = wiz.selectable[0]
    waiting = ProgressView("Preparing", None, 1)
    with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=waiting):
        app._draw()
        _settle(app, 50)
        # Between "Erase progress" and the bar: the same honest state the
        # screen-reader and console views speak, never an empty block or a number.
        assert _progress_slot_texts(app) == [progress.PROGRESS_UNKNOWN]
        assert not any(ch.isdigit() for ch in progress.PROGRESS_UNKNOWN)
        bar_top = app._progress_bar.winfo_rooty()
    reported = ProgressView("Writing", 42, 60)
    with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=reported):
        app._refresh_working()
        _settle(app, 50)
        assert _progress_slot_texts(app) == ["42%"]
        # The first number replaces the line in place: nothing below moves.
        assert app._progress_bar.winfo_rooty() == bar_top
    stale = ProgressView("Writing", 42, 60, stale_for=900, percent_is_old=True)
    with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=stale):
        app._refresh_working()
        _settle(app, 50)
        # An old number is marked in the owner's language, in the same slot.
        assert _progress_slot_texts(app) == [progress.OLD_PERCENT.format(percent="42%")]
        assert ("(old)" in _progress_slot_texts(app)[0]) == (code == "en")
        assert app._progress_bar.winfo_rooty() == bar_top
    assert not wiz.runner.started


# -- 3. The first option starts above the fold at short heights --------------


@MODES
@pytest.mark.parametrize("size", SHORT, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_first_method_card_is_visible_without_scrolling(tk_app, code, size, preview):
    wiz, app = tk_app(size=size, code=code, preview=preview)
    _drive_to(wiz, app, Screen.METHOD)
    _settle(app)
    canvas = app._body_canvas
    view = canvas.winfo_height()
    assert canvas.canvasy(0) == 0
    card_copy = C.METHOD_CARDS[MethodId.EVERYDAY]
    card = _box_of(_label(app._body_inner, str(card_copy["title"])))
    top, bottom = _extent(card, canvas)
    assert top >= 0
    if preview:
        # The preview stripe costs a row: the card's name and lead still show.
        lead = _label(card, str(card_copy["lead"]))
        assert _extent(lead, canvas)[1] <= view, (_extent(lead, canvas), view)
    else:
        assert bottom <= view, (top, bottom, view)
    # Limits stay on the screen, after the choices; each card keeps its own note.
    shown = [str(w.cget("text")) for w in _descendants(app._body_inner) if w.winfo_class() == "Label"]
    assert wiz.storage_notice in shown
    _assert_actions_on_window(app)
    assert not wiz.runner.started


@MODES
@pytest.mark.parametrize("selected", [False, True], ids=["arrival", "ssd-selected"])
@pytest.mark.parametrize("size", SHORT, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_first_disk_starts_visibly_on_the_picker(tk_app, code, size, selected, preview):
    wiz, app = tk_app(size=size, code=code, preview=preview, contents=CONTENTS)
    if selected:
        _drive_to(wiz, app, Screen.PICK)
    else:
        wiz.skip_intro()
        wiz.accept_what()
        wiz.set_owner(True)
        wiz.continue_owner()
        app._draw()
    _settle(app)
    assert wiz.screen == Screen.PICK
    canvas = app._pick_canvas
    view = canvas.winfo_height()
    first = sorted(wiz.selectable, key=lambda d: d.path)[0]
    card = app._pick_cards[first.path]
    disk_view = wiz.disk_view(first)
    assert _extent(card, canvas)[0] >= 0
    # Its name, capacity and identifier are readable without scrolling.
    for text in (disk_view.title, disk_view.capacity, disk_view.marked_id):
        top, bottom = _extent(_label(card, text), canvas)
        assert 0 <= top and bottom <= view, (text, top, bottom, view)
    # The protected boot USB is still listed, never selectable.
    boot = [w for w in _descendants(canvas) if getattr(w, "_beamo_protected_boot", False)]
    assert len(boot) == 1 and wiz.discovery.boot.path not in app._pick_cards
    _assert_actions_on_window(app)
    assert not wiz.runner.started


# -- 4. The countdown ring is whole at 800x600 and 1024x600 ------------------


@MODES
@pytest.mark.parametrize("ready", [False, True], ids=["counting", "ready"])
@pytest.mark.parametrize("size", SHORT, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_countdown_ring_and_erase_warning_fit_short_windows(tk_app, code, size, ready, preview):
    wiz, app = tk_app(size=size, code=code, preview=preview)
    _drive_to(wiz, app, Screen.LAST_CHANCE)
    _settle(app, 50)
    if ready:
        wiz._erase_until = 0.0
        app._refresh_last_chance()
        _settle(app, 50)
    canvas = app._body_canvas
    view = canvas.winfo_height()
    assert canvas.canvasy(0) == 0
    warning = _label(app._body_inner, f"{C.SEVERITY_WARNING}: {wiz.erase_label()}")
    for widget in (warning, app._countdown_ring, app._countdown_label):
        top, bottom = _extent(widget, canvas)
        assert 0 <= top and bottom <= view, (widget.winfo_class(), top, bottom, view)
    expected = C.COUNTDOWN_READY if ready else C.COUNTDOWN_CAPTION
    assert app._countdown_label.cget("text") == expected
    _assert_actions_on_window(app)
    assert not wiz.runner.started


# -- 5. Body offsets never go stale when content shrinks ---------------------


def _scroll_state(canvas):
    bounds = canvas.bbox("all")
    region = [float(v) for v in str(canvas.cget("scrollregion")).split()]
    return float(canvas.canvasy(0)), float(bounds[3] - bounds[1]), region, float(canvas.winfo_height())


def test_body_offset_follows_content_that_shrank_out_of_view(tk_app):
    wiz, app = tk_app(size=MIN_SIZE)
    _drive_to(wiz, app, Screen.OWNER)
    _settle(app)
    canvas = app._body_canvas
    extra = tk.Frame(app._body_inner, height=900, bg=tkui.BG)
    extra.pack(fill=tk.X)
    _settle(app, 50)
    canvas.yview_moveto(1.0)
    _settle(app, 50)
    # The grown part collapses while the owner is scrolled past the old
    # content: Tk configures no window lying wholly outside the view.
    extra.destroy()
    app.root.update_idletasks()
    app.root.update()
    app._tick()
    app.root.update_idletasks()
    app.root.update()
    top, content, region, view = _scroll_state(canvas)
    assert region[3] - region[1] <= content + view / 3.0
    assert 0 <= top <= max(0.0, region[3] - region[1] - view)
    assert top < content  # some of the screen is in view, not a blank body
    assert not wiz.runner.started


def test_short_content_is_never_bottom_aligned_with_blank_space_above(tk_app):
    wiz, app = tk_app(size=LARGE_SIZE)
    _drive_to(wiz, app, Screen.OWNER)
    _settle(app)
    canvas = app._body_canvas
    _top, content, _region, view = _scroll_state(canvas)
    assert content < view  # precondition: the whole screen fits
    # A reveal measured against transient geometry asked for a negative offset.
    canvas.yview_moveto(-0.2)
    app._tick()
    app.root.update_idletasks()
    app.root.update()
    assert canvas.canvasy(0) == 0


def test_manual_scroll_survives_later_layout_changes(tk_app):
    wiz, app = tk_app(size=MIN_SIZE)
    _drive_to(wiz, app, Screen.OWNER)
    _settle(app)
    canvas = app._body_canvas
    canvas.yview_moveto(0)
    _settle(app, 50)
    canvas.event_generate("<Button-5>")  # owner scrolls; focus stays put
    _settle(app, 50)
    moved = canvas.canvasy(0)
    assert moved > 0
    # Late wrapping elsewhere in the body must not yank the view back.
    tk.Frame(app._body_inner, height=40, bg=tkui.BG).pack(fill=tk.X)
    _settle(app, 50)
    assert canvas.canvasy(0) == moved


# -- 6. The preview stripe follows the chosen language -----------------------


def _stripe_texts(app):
    return [
        str(w.cget("text"))
        for w in _descendants(app.root)
        if w.winfo_class() == "Label" and w.cget("bg") == tkui.PREVIEW_BG
    ]


@pytest.mark.parametrize("code", [c for c in lang.LANGUAGE_ORDER if c != "en"])
def test_preview_stripe_and_title_follow_the_language_choice(tk_app, code):
    wiz, app = tk_app(size=LAPTOP_SIZE, preview=True)
    _drive_to(wiz, app, Screen.KEYBOARD)
    _settle(app, 50)
    assert _stripe_texts(app) == [C.PREVIEW_BANNER]
    for chosen in (code, "en"):
        chip = app._keyboard_language_cards[chosen]
        chip.event_generate("<Button-1>", x=4, y=4)
        _settle(app, 50)
        assert wiz.language == chosen
        assert _stripe_texts(app) == [C.PREVIEW_BANNER]
        assert C.PREVIEW_BANNER in app.root.title()
    assert lang.current() == "en"


# -- 8. Pick rows say what each disk holds (factual, never advice) ----------


@pytest.mark.parametrize("size", (MIN_SIZE, LAPTOP_SIZE), ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_pick_rows_show_what_each_disk_holds(tk_app, code, size):
    wiz, app = tk_app(size=size, code=code, contents=CONTENTS)
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    app._draw()
    _settle(app)
    hints = {
        CONTENTS_WINDOWS: C.CONTENTS_HINT_WINDOWS,
        CONTENTS_SYSTEM: C.CONTENTS_HINT_SYSTEM,
        CONTENTS_DATA: "",
    }
    named = set(hints.values()) - {""}
    assert len(named) == 2
    for disk in wiz.selectable:
        card = app._pick_cards[disk.path]
        shown = [str(w.cget("text")) for w in _descendants(card) if w.winfo_class() == "Label"]
        expected = hints[CONTENTS[disk.path]]
        if expected:
            assert shown.count(expected) == 1, (disk.path, shown)
        assert not (named - {expected}) & set(shown)
    boot = next(w for w in _descendants(app._pick_canvas) if getattr(w, "_beamo_protected_boot", False))
    boot_text = [str(w.cget("text")) for w in _descendants(boot) if w.winfo_class() == "Label"]
    assert not named & set(boot_text)
    assert _clipping_problems(app) == []
    _assert_actions_on_window(app)
    assert wiz.selected is None and not wiz.runner.started


def test_unknown_contents_add_no_hint(tk_app):
    wiz, app = tk_app(contents={path: CONTENTS_UNKNOWN for path in CONTENTS})
    _drive_to(wiz, app, Screen.PICK)
    _settle(app, 50)
    hints = {C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM}
    shown = {str(w.cget("text")) for w in _descendants(app._pick_canvas) if w.winfo_class() == "Label"}
    assert not hints & shown
