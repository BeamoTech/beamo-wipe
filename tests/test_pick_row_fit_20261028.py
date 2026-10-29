# SPDX-License-Identifier: GPL-3.0-or-later
"""A whole disk row fits the picker at 800x600 and 1024x600 (BW-FIN-PICK-ROW).

The boot menu's safe-video entry (``vga=788``) opens the live kiosk at
800x600. The first row started below the same-size warning and the Compare
toggle, so only its name, capacity and serial were in view: the connection,
comparison note, contents and nested partitions needed a scroll. Short
windows now use a denser row and list the Compare toggle after the disks;
every fact stays in the row. Taller windows keep the roomy row.

Fake disks and DryRunRunner only; no engine, no real device.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import inventory, lang
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as tkui
from beamo_wipe.ui.layout import MIN_SIZE, NETBOOK_SIZE, SUPPORTED_SIZE
from test_adaptive_layout import _assert_actions_on_window
from test_tk_runtime import _drive_to
from test_ui_fit_20261027 import CONTENTS, _descendants, _extent, _settle, tk_app  # noqa: F401

SHORT = (MIN_SIZE, NETBOOK_SIZE)
TALL = (SUPPORTED_SIZE, (1280, 820))


def _open_pick(wiz, app, selected):
    if selected:
        # Keyboard path: the first disk (an SSD, so the limits note shows).
        _drive_to(wiz, app, Screen.PICK)
    else:
        wiz.skip_intro()
        wiz.accept_what()
        wiz.set_owner(True)
        wiz.continue_owner()
        app._draw()
    _settle(app)
    assert wiz.screen == Screen.PICK


def _labels(widget):
    return [
        w for w in _descendants(widget)
        if w.winfo_class() == "Label" and w.winfo_ismapped()
    ]


def _texts(widget):
    return [str(w.cget("text")) for w in _labels(widget)]


def _row_facts(wiz, disk):
    """Every fact a picker row shows, in the current language."""
    view = wiz.disk_view(disk)
    facts = [view.title, view.capacity, view.id_label, view.marked_id, *view.notes]
    chip = " · ".join(part for part in (view.kind_chip, view.connection) if part)
    if chip:
        facts.append(chip)
    hint = C.contents_hint(disk)
    if hint:
        facts.append(hint)
    children = wiz.nested_components(disk)
    if children:
        facts.append(inventory.NESTED_INTRO)
        for child in children:
            facts.append(inventory.nested_heading(child))
            reason = inventory.nested_reason_text(child)
            if reason:
                facts.append(reason)
    return facts


def _shown(card, fact) -> bool:
    # Wrapped labels may carry soft breaks inside unbroken tokens.
    flat = [" ".join(text.split()) for text in _texts(card)]
    wanted = " ".join(fact.split())
    return any(wanted in text for text in flat)


@pytest.mark.parametrize("selected", [False, True], ids=["arrival", "selected"])
@pytest.mark.parametrize("size", SHORT, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_first_disk_row_is_whole_without_scrolling(tk_app, code, size, selected):  # noqa: F811
    wiz, app = tk_app(size=size, code=code, contents=CONTENTS)
    _open_pick(wiz, app, selected)
    canvas = app._pick_canvas
    assert canvas.canvasy(0) == 0
    view = canvas.winfo_height()
    disks = sorted(wiz.selectable, key=lambda d: d.path)
    first = disks[0]
    card = app._pick_cards[first.path]
    top, bottom = _extent(card, canvas)
    assert 0 <= top and bottom <= view, (code, size, top, bottom, view)
    # Nothing in the row is cut, and nothing was dropped to make it fit.
    for label in _labels(card):
        label_top, label_bottom = _extent(label, canvas)
        assert 0 <= label_top and label_bottom <= view, (str(label.cget("text"))[:40], view)
    facts = _row_facts(wiz, first)
    assert len(facts) >= 8  # name, capacity, serial label/value, note, chip, contents, nesting
    missing = [fact for fact in facts if not _shown(card, fact)]
    assert missing == [], (code, size, missing)
    # The same-size warning still comes before the disks; Compare follows them.
    warning = next(w for w in _labels(canvas) if str(w.cget("text")) == C.SAME_SIZE_HINT)
    assert _extent(warning, canvas)[1] <= top
    compare = next(
        w for w in _descendants(canvas)
        if isinstance(w, tkui._CheckRow) and w.cget("text") == inventory.COMPARE_TITLE
    )
    last = app._pick_cards[disks[-1].path]
    assert compare.winfo_rooty() >= last.winfo_rooty() + last.winfo_height()
    # The listing and the selection are unchanged; nothing started.
    assert set(app._pick_cards) == {disk.path for disk in wiz.selectable}
    assert wiz.discovery.boot.path not in app._pick_cards
    assert (wiz.selected.path if wiz.selected else None) == (first.path if selected else None)
    _assert_actions_on_window(app)
    assert not wiz.runner.started


@pytest.mark.parametrize("size", TALL, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", ("en", "de"))
def test_tall_windows_keep_the_roomy_row(tk_app, code, size):  # noqa: F811
    wiz, app = tk_app(size=size, code=code, contents=CONTENTS)
    _open_pick(wiz, app, selected=False)
    assert not app.lay.short
    canvas = app._pick_canvas
    disks = sorted(wiz.selectable, key=lambda d: d.path)
    first = disks[0]
    card = app._pick_cards[first.path]
    # One line per nested component, and Compare above the disks as before.
    nested = inventory.card_nesting_text(wiz.nested_components(first))
    assert nested.count("\n") >= 2
    assert nested in _texts(card)
    compare = next(
        w for w in _descendants(canvas)
        if isinstance(w, tkui._CheckRow) and w.cget("text") == inventory.COMPARE_TITLE
    )
    assert compare.winfo_rooty() + compare.winfo_height() <= card.winfo_rooty()
    assert card._pady == 12 and card._padx == 20
    assert not wiz.runner.started
