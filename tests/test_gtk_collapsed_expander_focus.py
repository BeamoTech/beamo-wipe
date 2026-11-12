# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK: a collapsed Show more keeps its content out of Tab and Orca.

GTK 3.24 leaves a collapsed expander's child visible and mapped at 1 px, so
Tab walked into the hidden notes and the Storage limits (L) button on the
Method screen (and the same on every other expander: #141, #146, #158,
#160, #161, the disk comparison, Technical details and the Help & settings
keyboard shortcuts). Opening the expander still shows and reaches it.
Fake disks only, never nwipe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("gi")
from beamo_wipe import help_menu as M  # noqa: E402
from beamo_wipe import lang, storage_limits  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk  # noqa: E402
from beamo_wipe.wizard import make_demo_wizard  # noqa: E402
from test_accessible_fit_20261027 import _to_method, _wizard  # noqa: E402
from test_accessible_runtime import drain, wait_for_window_size, widgets  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


@pytest.fixture
def gtk():
    apps = []

    def build(wizard, size=(800, 600)):
        app = AccessibleWizard(wizard)
        apps.append(app)
        app.window.resize(*size)
        wait_for_window_size(app.window, size)
        drain()
        return app

    yield build
    for app in apps:
        app.close()
    drain()


def _collapsed_ancestor(widget):
    node = widget.get_parent()
    while node is not None:
        if isinstance(node, Gtk.Expander) and not node.get_expanded():
            return node
        node = node.get_parent()
    return None


def _tab_order(app, steps=70):
    """Focus each Tab stop in turn, as a keyboard user would."""
    app.window.set_focus(None)
    order = []
    for _ in range(steps):
        app.window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        drain()
        focus = app.window.get_focus()
        if focus is not None:
            order.append(focus)
    return order


def _keyboard():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    return wiz


def _owner():
    wiz = _wizard("en")
    wiz.skip_intro()
    assert wiz.screen == Screen.OWNER
    return wiz


def _pick():
    wiz = _owner()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK and len(wiz.selectable) > 1
    wiz.select_disk(wiz.selectable[0].path)
    return wiz


def _method(path):
    def build():
        wiz = _wizard("en")
        _to_method(wiz, path)
        return wiz

    return build


def _result():
    from test_result_presentations import CASES, case_evidence

    wiz, _evidence, _ = case_evidence(next(c for c in CASES if c[0] == "verified"))
    return wiz


SCREENS = {
    "keyboard": _keyboard,
    "owner": _owner,
    "pick": _pick,
    "method-ssd": _method("/dev/nvme0n1"),
    "method-hdd": _method("/dev/sda"),
    "result": _result,
}


@pytest.mark.parametrize("name", list(SCREENS))
def test_tab_never_lands_inside_a_collapsed_expander(gtk, name):
    app = gtk(SCREENS[name]())
    expanders = [w for w in widgets(app.body) if isinstance(w, Gtk.Expander)]
    assert expanders, f"{name}: expected a Show more expander"
    for expander in expanders:
        assert not expander.get_expanded()
        child = expander.get_child()
        assert not child.get_visible() and not child.get_mapped(), name
    order = _tab_order(app)
    inside = [w for w in order if _collapsed_ancestor(w) is not None]
    assert inside == [], [
        getattr(w, "get_label", lambda: "")() or type(w).__name__ for w in inside
    ]
    # The expander itself is still a Tab stop, so the content stays reachable.
    for expander in expanders:
        assert expander in order, name


@pytest.mark.parametrize("path", ["/dev/nvme0n1", "/dev/sda"])
def test_opening_show_more_reaches_the_notice_and_storage_limits(gtk, path):
    wiz = _wizard("en")
    _to_method(wiz, path)
    app = gtk(wiz)
    pages = app.actions[storage_limits.BUTTON]
    expander = pages.get_parent().get_parent()
    assert isinstance(expander, Gtk.Expander)
    assert pages not in _tab_order(app)
    expander.set_expanded(True)
    drain()
    notice = pages.get_parent().get_children()[0]
    assert notice.get_mapped() and pages.get_mapped()
    order = _tab_order(app)
    assert notice in order and pages in order
    assert order.index(expander) < order.index(notice) < order.index(pages)
    expander.set_expanded(False)
    drain()
    assert pages not in _tab_order(app)
    assert wiz.screen == Screen.METHOD and not wiz.runner.started


def test_help_menu_shortcuts_open_only_when_expanded(gtk):
    wiz = _wizard("en")
    _to_method(wiz, "/dev/sda")
    app = gtk(wiz)
    expander = app._help_items[M.SHORTCUTS]
    assert isinstance(expander, Gtk.Expander) and not expander.get_expanded()
    text = expander.get_child()
    assert not text.get_visible()
    app._show_help_menu(M.SHORTCUTS)
    drain()
    assert not text.get_mapped()
    expander.set_expanded(True)
    drain()
    assert text.get_visible() and text.get_mapped() and text.get_can_focus()
    app.help_popover.popdown()
    drain()


def test_every_gtk_expander_is_folded():
    """A new expander must call _fold, or Tab reaches its hidden content."""
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(
        encoding="utf-8"
    )
    made = src.count("Gtk.Expander.new(")
    folded = src.count("_fold(") - src.count("def _fold(")
    assert made == 7 and folded == made
