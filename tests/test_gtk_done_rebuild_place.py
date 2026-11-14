# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK result screen: a live rebuild keeps an Orca user's place (#135, #175).

The report-USB check rebuilds Done whenever its answer changes (the first
answer, a stick plugged in or pulled). The rebuild already kept focus on the
same button or label. It lost it on the Technical details expander (focus
went to the headline), could leave focus on the hidden details text once the
rebuilt expander came back collapsed, and closed an open Help & settings menu.

Fake probe and fake exporter only: nothing scans, mounts or writes a device,
and nothing is saved or erased.
"""

from __future__ import annotations

import pathlib
import threading
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _render_source() -> str:
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    return src[src.index("    def render(self):"):src.index("    def _help_menu_button(self)")]


def test_done_rebuild_keeps_expanders_and_menu_in_source():
    """Runs without GTK: the rebuild records and restores both."""
    render = _render_source()
    capture = render.index("refocus_text = _widget_text(focused)")
    destroy = render.index("old.destroy()")
    assert capture < render.index("reopen_expanders = {") < destroy
    assert capture < render.index("keep_menu = self._open_help_key(focused)") < destroy
    # Expanders reopen before focus is looked for inside them.
    assert render.index("widget.set_expanded(True)") < render.index(
        "_find_by_text(self.window, refocus_text)"
    )
    # An activated item's own reopen rule wins over the live-rebuild one.
    assert render.index("self._show_help_menu(reopen)") < render.index(
        "self._show_help_menu(keep_menu)"
    )


try:
    import gi  # noqa: F401
except ImportError:  # the source check above still runs
    gi = None

if gi is not None:
    from beamo_wipe import copy as C
    from beamo_wipe import recovery as Rec
    from beamo_wipe import support_export as X
    from beamo_wipe.models import Screen
    from beamo_wipe.ui.accessible_wizard import Gtk, _find_by_text
    from test_accessible_runtime import drain, ui, widgets  # noqa: F401
    from test_usb_report_workflow import _done_wizard, _success_receipt

    FOUND = X.ReportUsbProbe(
        X.PROBE_FOUND, label="SanDisk Ultra, 16 GB", filesystem="FAT32"
    )

gtk = pytest.mark.skipif(gi is None, reason="PyGObject (GTK 3) unavailable")


def _tick_until(app, done, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.tick()
        drain()
        if done():
            return True
        time.sleep(0.02)
    return False


def _technical(app):
    return next(
        w for w in widgets(app.window)
        if isinstance(w, Gtk.Expander) and w.get_label() == Rec.RECOVERY_TECHNICAL
    )


@pytest.fixture
def held_answer(ui, tmp_path):  # noqa: F811
    """A failed-result Done screen whose first report-USB answer is held."""
    asked = []
    answer = threading.Event()

    def probe(**_kwargs):
        asked.append(1)
        answer.wait(timeout=10)
        return FOUND

    wizard = _done_wizard(_success_receipt, tmp_path)
    wizard._report_usb_probe = probe
    app = ui(wizard)
    drain()
    assert wizard.screen == Screen.DONE and not wizard.dry_run
    renders = []
    render = app.render

    def counted():
        renders.append(1)
        return render()

    app.render = counted

    def rebuild(before=None):
        assert _tick_until(app, lambda: bool(asked))
        assert renders == []
        if before is not None:
            before()  # right before the answer lands, with no tick between
        answer.set()
        assert _tick_until(app, lambda: bool(renders))
        drain()
        assert len(renders) == 1

    try:
        yield app, wizard, rebuild
    finally:
        answer.set()


@gtk
def test_focus_on_technical_details_stays_there(held_answer):
    app, wizard, rebuild = held_answer
    start = _technical(app)
    assert not start.get_expanded()
    start.grab_focus()
    drain()
    assert app.window.get_focus() is start
    rebuild()
    focus = app.window.get_focus()
    assert focus is not start and focus is not app.arrival
    assert focus is _technical(app) and focus.get_mapped()
    assert not focus.get_expanded()
    assert wizard.screen == Screen.DONE and wizard.report_status != "saved"


@gtk
def test_open_technical_details_stay_open_with_focus_inside(held_answer):
    app, wizard, rebuild = held_answer
    expander = _technical(app)
    expander.set_expanded(True)
    drain()
    details = expander.get_child()
    assert details.get_mapped()
    details.grab_focus()
    drain()
    assert app.window.get_focus() is details
    words = details.get_text()
    rebuild()
    expander = _technical(app)
    assert expander.get_expanded()
    focus = app.window.get_focus()
    assert focus is expander.get_child() and focus is not details
    assert focus.get_visible() and focus.get_mapped()
    assert focus.get_text() == words
    assert wizard.screen == Screen.DONE


@gtk
def test_open_technical_details_stay_open_with_focus_elsewhere(held_answer):
    app, _wizard, rebuild = held_answer
    _technical(app).set_expanded(True)
    footer = app.actions[C.BTN_ERASE_ANOTHER]
    footer.grab_focus()
    drain()
    rebuild()
    assert _technical(app).get_expanded()
    assert app.window.get_focus() is app.actions[C.BTN_ERASE_ANOTHER]


@gtk
def test_closed_technical_details_stay_closed(held_answer):
    app, _wizard, rebuild = held_answer
    app.arrival.grab_focus()
    drain()
    rebuild()
    expander = _technical(app)
    assert not expander.get_expanded()
    assert not expander.get_child().get_visible()
    assert app.window.get_focus() is app.arrival


@gtk
@pytest.mark.parametrize("key", ["text_size", "shortcuts"])
def test_open_help_menu_stays_open_on_its_item(held_answer, key):
    app, wizard, rebuild = held_answer
    app._show_help_menu(key)
    drain()
    assert app.help_popover.get_visible()
    old_item = app._help_items[key]
    assert app.window.get_focus() is old_item
    old_popover = app.help_popover
    rebuild()
    assert app.help_popover is not old_popover
    assert app.help_popover.get_visible()
    item = app._help_items[key]
    assert item is not old_item
    assert app.window.get_focus() is item and item.get_mapped()
    # Closing it still returns to the menu button, as on any screen.
    app.help_popover.popdown()
    assert _tick_until(
        app,
        lambda: not app.help_popover.get_visible()
        and app.window.get_focus() is app.help_button,
    )
    assert wizard.screen == Screen.DONE and wizard.report_status != "saved"


@gtk
def test_help_menu_closed_just_before_rebuild_stays_closed(held_answer):
    """Close lands first, the rebuild follows within a tick: no reopen,
    even while the menu may still be animating closed."""
    app, wizard, rebuild = held_answer
    app._show_help_menu("text_size")
    drain()
    assert app.help_popover.get_visible()
    rebuild(before=app.help_popover.popdown)
    assert _tick_until(
        app,
        lambda: not app.help_popover.get_visible()
        and app.window.get_focus() is app.help_button,
        timeout=2.0,
    )
    # And it stays closed: nothing reopens it a moment later.
    _tick_until(app, lambda: False, timeout=0.5)
    assert not app.help_popover.get_visible()
    assert wizard.screen == Screen.DONE and wizard.report_status != "saved"


@gtk
def test_closed_help_menu_stays_closed(held_answer):
    app, _wizard, rebuild = held_answer
    footer = app.actions[C.BTN_ERASE_ANOTHER]
    footer.grab_focus()
    drain()
    rebuild()
    assert not app.help_popover.get_visible()
    assert app.window.get_focus() is app.actions[C.BTN_ERASE_ANOTHER]


@gtk
def test_find_by_text_skips_hidden_content():
    window = Gtk.Window()
    try:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        expander = Gtk.Expander.new("Details")
        hidden = Gtk.Label(label="Result code: indeterminate")
        hidden.set_can_focus(True)
        expander.add(hidden)
        shown = Gtk.Label(label="Result code: indeterminate")
        shown.set_can_focus(True)
        box.pack_start(expander, False, False, 0)
        box.pack_start(shown, False, False, 0)
        window.add(box)
        window.show_all()
        hidden.set_visible(False)
        assert _find_by_text(window, "Result code: indeterminate") is shown
        assert _find_by_text(window, "Details") is expander
        shown.set_visible(False)
        assert _find_by_text(window, "Result code: indeterminate") is None
    finally:
        window.destroy()
        drain()
