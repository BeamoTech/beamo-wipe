# SPDX-License-Identifier: GPL-3.0-or-later
"""Second modernisation pass: lighter chrome, fewer stray rows, one review flow.

- Secondary buttons have a light decorative edge; low-emphasis footer
  actions (sounds, erase another disk) are links.
- No rule separates the footer's assist strip from its navigation row.
- The selected-disk summary has a soft edge and carries its own Show more
  toggle, so no stray link row follows it.
- Pick puts "I'm not sure which disk" and Show more on the inventory row.
- Text size is a segmented control.
- Review: the erase warning (same words) is a red callout, and the countdown
  ring sits beside its caption directly under it at every size.

Fake disks and DryRunRunner only; nothing is erased.
"""

from __future__ import annotations

import time

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.gallery import gallery_html
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as tkui
from beamo_wipe.ui.layout import MIN_SIZE
from test_tk_runtime import _drive_to
from test_ui_fit_20261027 import _descendants, _settle, tk_app  # noqa: F401


def _boxes_above(widget):
    fills = []
    node = widget
    while node is not None:
        if isinstance(node, tkui._Box):
            fills.append(node._fill)
        node = node.master
    return fills


def _label(app, text):
    return next(
        w for w in _descendants(app.root)
        if w.winfo_class() == "Label" and str(w.cget("text")).replace("\n", "") == text
    )


def test_light_secondary_edge_and_summary_edge_are_shared_with_the_gallery():
    assert tkui._Button._VARIANTS["secondary"][4] == tkui.BUTTON_EDGE
    # The edge is decorative; keyboard focus still draws the focus ring.
    assert tkui._Button._VARIANTS["secondary"][5] == tkui.FOCUS
    html = gallery_html().lower()
    for token in ("BUTTON_EDGE", "SUMMARY_EDGE"):
        assert getattr(tkui, token).lower() in html
    assert "border: 1px solid var(--button-edge)" in html
    assert "border-color: var(--summary-edge)" in html


@pytest.mark.parametrize("screen", [Screen.CONFIRM, Screen.METHOD])
@pytest.mark.parametrize("size", [MIN_SIZE, (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
def test_show_more_lives_in_the_selected_disk_summary(tk_app, screen, size):  # noqa: F811
    wiz, app = tk_app(size=size)
    _drive_to(wiz, app, screen, size=size)
    _settle(app)
    fills = _boxes_above(app._more_button)
    assert fills and fills[0] == tkui.PRIMARY_TINT
    summary = app._more_button
    while not isinstance(summary, tkui._Box):
        summary = summary.master
    assert summary._outline == tkui.SUMMARY_EDGE
    assert not wiz.runner.started


@pytest.mark.parametrize("size", [MIN_SIZE, (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_pick_links_share_the_inventory_row(tk_app, code, size):  # noqa: F811
    wiz, app = tk_app(size=size, code=code)
    _drive_to(wiz, app, Screen.PICK, size=size)
    _settle(app)
    unsure = next(
        w for w in _descendants(app._body)
        if isinstance(w, tkui._Button) and w.itemcget(w._label, "text") == C.DISK_HELP_BUTTON
    )
    count = next(w for w in _descendants(app._body) if getattr(w, "_beamo_inventory_count", False))
    assert unsure.master is app._more_button.master
    assert unsure.master.master is count.master
    # Same tab order as before: the help link, then Show more.
    assert unsure.tk_focusNext() is app._more_button
    # The count wraps beside the links, never under or over them.
    assert count.winfo_rootx() + count.winfo_width() <= unsure.winfo_rootx()
    assert count.winfo_reqwidth() <= count.winfo_width() + 2
    assert not wiz.runner.started


def test_footer_has_no_rule_between_assist_and_navigation(tk_app):  # noqa: F811
    wiz, app = tk_app(size=(1280, 820))
    _drive_to(wiz, app, Screen.PICK, size=(1280, 820))
    _settle(app)
    rules = [
        w for w in _descendants(app._footer)
        if w.winfo_class() == "Frame" and str(w.cget("bg")).upper() == tkui.BORDER
    ]
    assert rules == []
    assert "footrow { max-width: 940px; margin: 0 auto; padding: 12px 0 20px; display: flex;" in gallery_html()


def test_text_size_is_a_segmented_control(tk_app):  # noqa: F811
    wiz, app = tk_app(size=(1280, 820))
    _drive_to(wiz, app, Screen.KEYBOARD, size=(1280, 820))
    _settle(app)
    labels = set(C.TEXT_SIZE_LABELS.values())
    sizes = [
        w for w in _descendants(app._body)
        if isinstance(w, tkui._Button) and w.itemcget(w._label, "text") in labels
    ]
    assert len(sizes) == len(labels)
    track = sizes[0].master.master
    assert isinstance(track, tkui._Box) and track._fill == tkui.TRACK
    assert all(b.master.master is track for b in sizes)
    chosen = [b for b in sizes if b._variant == "selected"]  # #176: the selected token
    assert [b.itemcget(b._label, "text") for b in chosen] == [C.TEXT_SIZE_LABELS[wiz.text_size]]
    assert {b._variant for b in sizes if b not in chosen} == {"segment"}
    html = gallery_html()
    assert 'class="btn choice sel"' in html and ".textsizes button.btn.segment" in html  # #176


@pytest.mark.parametrize("ready", [False, True], ids=["counting", "ready"])
@pytest.mark.parametrize("size", [(800, 600), (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
def test_review_warning_is_a_red_callout_with_the_countdown_beside_its_caption(tk_app, size, ready):  # noqa: F811
    wiz, app = tk_app(size=size)
    _drive_to(wiz, app, Screen.LAST_CHANCE, size=size)
    _settle(app, 50)
    if ready:
        wiz._erase_until = 0.0
        app._refresh_last_chance()
        _settle(app, 20)
    warning = _label(app, f"{C.SEVERITY_WARNING}: {wiz.erase_label()}")
    assert warning.cget("fg") == tkui.DANGER
    assert _boxes_above(warning)[0] == tkui.DANGER_TINT
    ring, caption = app._countdown_ring, app._countdown_label
    # One row: the caption is right of the ring and overlaps it vertically.
    assert ring.master is caption.master
    assert caption.winfo_rootx() >= ring.winfo_rootx() + ring.winfo_width()
    assert caption.winfo_rooty() < ring.winfo_rooty() + ring.winfo_height()
    assert ring.winfo_rooty() < caption.winfo_rooty() + caption.winfo_height()
    # Directly under the warning, and the caption is not squeezed into a tower.
    assert ring.winfo_rooty() >= warning.winfo_rooty() + warning.winfo_height()
    assert caption.winfo_height() <= 3 * app.font_b.metrics("linespace") + 8
    assert not wiz.runner.started
    html = gallery_html()
    callout = html.split('<div class="erase-callout" role="alert">', 1)[1].split("</div>", 1)[0]
    assert '<p class="review-warning">${P.sevWarning}' in callout
    assert 'badge("erase", 24)' in callout


def test_draw_alert_glyph_has_a_red_erase_triangle():
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    try:
        cv = tkui._icon_alert(root, "erase", 24)
        fills = {cv.itemcget(item, "fill") for item in cv.find_all()}
        assert tkui.DANGER in fills and tkui.WARN not in fills
    finally:
        root.destroy()


@pytest.mark.parametrize("phase", ["working", "done"])
def test_sound_and_another_disk_actions_are_links(tk_app, phase):  # noqa: F811
    wiz, app = tk_app(size=(1280, 820))  # live footer: preview=False
    _drive_to(wiz, app, Screen.LAST_CHANCE, size=(1280, 820))
    wiz._erase_until = 0.0
    wiz.tick()
    wiz.runner.duration_s = 30.0 if phase == "working" else 0.2
    wiz.confirm_erase()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        wiz.tick()
        app.root.update()
        if phase == "working" and wiz.screen == Screen.WORKING:
            break
        if wiz.screen == Screen.DONE:
            break
        time.sleep(0.02)
    app._draw()
    _settle(app)
    expected = Screen.WORKING if phase == "working" else Screen.DONE
    assert wiz.screen == expected
    buttons = {
        w.itemcget(w._label, "text"): w
        for w in _descendants(app._footer) if isinstance(w, tkui._Button)
    }
    links = [wiz.sound_toggle_text, C.SOUND_HEAR if phase == "working" else C.SOUND_HEAR_AGAIN]
    if phase == "done":
        links.append(C.BTN_ERASE_ANOTHER)
    for text in links:
        assert buttons[text]._variant == "ghost", text
    if phase == "working":
        assert buttons[C.STOP_ASK]._variant == "secondary"
        wiz.cancel_wipe()
