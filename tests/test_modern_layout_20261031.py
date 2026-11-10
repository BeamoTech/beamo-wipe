# SPDX-License-Identifier: GPL-3.0-or-later
"""Modernised wizard layout: white content on a quiet page, actions in view.

- The page is a soft gray field; cards, panels, fields, key caps, the header
  and the footer are white, so content reads as cards rather than boxes of
  borders on white.
- Footer tools are quiet gray buttons; the primary action is the only strong
  colour in the footer.
- The owner check follows "Here's what happens" directly, so the one action
  on that screen is visible without scrolling at every supported size (it
  was below the fold at 800x600 through 1280x820).
- The Pick list leads with the disks at every size; the protected boot USB,
  selection notes and Compare follow them.
- On roomy windows the review facts are one white card.

Fake disks and DryRunRunner only; nothing is erased.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.models import Screen
from beamo_wipe.ui import tk_wizard as tkui
from beamo_wipe.ui.layout import MIN_SIZE, NETBOOK_SIZE
from test_tk_runtime import _drive_to
from test_ui_fit_20261027 import _descendants, _settle, tk_app  # noqa: F401

SIZES = (MIN_SIZE, NETBOOK_SIZE, (1280, 720), (1280, 820))


def test_page_is_gray_and_content_surfaces_are_white():
    assert tkui.BG == "#EEF2F6"
    assert tkui.SURFACE == "#FFFFFF"
    assert tkui.FOOTER_BG == tkui.SURFACE
    assert tkui._Button._VARIANTS["quiet"][1] == tkui.MUTED


def _owner_check(app):
    return next(
        w for w in _descendants(app._body)
        if w.winfo_class() == "Label" and str(w.cget("text")) == C.OWNER_CHECKBOX
    )


@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_owner_check_is_in_view_without_scrolling(tk_app, code, size):  # noqa: F811
    wiz, app = tk_app(size=size, code=code)
    _drive_to(wiz, app, Screen.OWNER, size=size)
    _settle(app)
    check = _owner_check(app)
    bottom = check.winfo_rooty() + check.winfo_height()
    assert bottom <= app._footer.winfo_rooty(), (code, size)
    # The supporting notes come after the check.
    report = next(
        w for w in _descendants(app._body)
        if w.winfo_class() == "Label" and str(w.cget("text")) == C.REPORT_MEDIA_WHAT
    )
    assert report.winfo_rooty() > check.winfo_rooty()
    assert not wiz.runner.started


@pytest.mark.parametrize("size", ((1280, 820), (1600, 1000)), ids=lambda s: f"{s[0]}x{s[1]}")
def test_tall_pick_leads_with_the_disks(tk_app, size):  # noqa: F811
    wiz, app = tk_app(size=size)
    _drive_to(wiz, app, Screen.PICK, size=size)
    _settle(app)
    disks = sorted(wiz.selectable, key=lambda d: d.path)
    first = app._pick_cards[disks[0].path]
    last = app._pick_cards[disks[-1].path]
    banner = next(
        w for w in _descendants(app._pick_canvas)
        if w.winfo_class() == "Label" and C.BOOT_USB_BANNER in str(w.cget("text"))
    )
    assert banner.winfo_rooty() >= last.winfo_rooty() + last.winfo_height()
    # The first selectable disk is whole in the list view.
    view = app._pick_canvas
    top = first.winfo_rooty() - view.winfo_rooty()
    assert 0 <= top and top + first.winfo_height() <= view.winfo_height()
    assert wiz.discovery.boot.path not in app._pick_cards
    assert not wiz.runner.started


def test_footer_is_a_white_bar_with_quiet_tools(tk_app):  # noqa: F811
    wiz, app = tk_app(size=(1280, 820))
    _drive_to(wiz, app, Screen.PICK, size=(1280, 820))
    _settle(app)
    assert app._footer.cget("bg") == tkui.SURFACE
    buttons = [w for w in _descendants(app._footer) if isinstance(w, tkui._Button)]
    tools = [b for b in buttons if b._variant == "quiet"]
    assert tools and any(
        b.itemcget(b._label, "text") == C.MENU_TITLE for b in tools  # #175
    )
    # The primary action keeps its strong fill.
    assert any(b._variant == "primary" for b in buttons)
    # Nothing in the footer shows the gray page through.
    for widget in _descendants(app._footer):
        if widget.winfo_class() in {"Frame", "Label"} and str(widget.cget("bg")).upper() != tkui.BORDER:
            assert str(widget.cget("bg")).upper() == tkui.SURFACE, widget


def test_roomy_review_groups_its_facts_in_a_white_card(tk_app):  # noqa: F811
    wiz, app = tk_app(size=(1280, 820))
    _drive_to(wiz, app, Screen.LAST_CHANCE, size=(1280, 820))
    _settle(app)
    warning = next(
        w for w in _descendants(app._body)
        if w.winfo_class() == "Label" and str(w.cget("text")).startswith(C.SEVERITY_WARNING + ":")
    )
    # The warning is a red callout (test_modern_polish_20261101) inside the
    # one white review card.
    boxes = []
    node = warning
    while node is not None:
        if isinstance(node, tkui._Box):
            boxes.append(node._fill)
        node = node.master
    assert boxes[:2] == [tkui.DANGER_TINT, tkui.SURFACE]
    assert not wiz.erase_enabled and not wiz.runner.started


def test_web_gallery_mirrors_the_new_order():
    from beamo_wipe import gallery

    owner = gallery._TEMPLATE.split('} else if (screen === "owner")', 1)[1].split('} else if (screen === "blocked")', 1)[0]
    assert owner.index("${P.ownerLead}") < owner.index("P.reportMediaWhat")
    assert owner.index('id="own"') < owner.index("${P.powerReminder}")
    pick = gallery._TEMPLATE.split('} else if (screen === "pick")', 1)[1].split("main.innerHTML", 1)[0]
    disks = pick.index("selectable().forEach(d => { html += diskCard(d); });")
    assert disks < pick.index("d.isBoot") < pick.index('class="compare"')
    assert disks < pick.index("P.reportMediaWanted") and disks < pick.index("P.ssd")
    assert "--bg: #EEF2F6; --surface: #FFFFFF;" in gallery._TEMPLATE
