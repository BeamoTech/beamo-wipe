# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK result screen: the first answer from the report-USB check (#135).

On a real (not dry-run) result screen the read-only report-USB check starts
once the evidence file is written. Its first answer rebuilds the screen. This
pins what Orca users get at that moment: exactly one rebuild; focus kept on
the same words when they still exist (the result headline, a footer button,
the Save a report title); moved to the new USB status when the panel line
they were on changed; and no further rebuild while the answer stays the
same.

Fake probe and fake exporter only: nothing scans, mounts or writes a device,
and nothing is saved or erased.
"""

from __future__ import annotations

import threading
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe import support_export as X  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gtk  # noqa: E402
from test_accessible_runtime import drain, text, ui, widgets  # noqa: E402, F401
from test_usb_report_workflow import _done_wizard, _success_receipt  # noqa: E402

FOUND = X.ReportUsbProbe(
    X.PROBE_FOUND, label="SanDisk Ultra, 16 GB", filesystem="FAT32"
)


def _words(widget):
    if isinstance(widget, Gtk.Button):
        return widget.get_label()
    if isinstance(widget, Gtk.Label):
        return widget.get_text()
    return None


def _tick_until(app, done, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.tick()
        drain()
        if done():
            return True
        time.sleep(0.02)
    return False


def _focus_start(app, where):
    if where == "headline":
        return app.arrival
    if where == "footer":
        return app.actions[C.BTN_ERASE_ANOTHER]
    if where == "panel-title":
        return next(w for w in app._panel_widgets if _words(w) == C.REPORT_STATUS_TITLE)
    # The panel's live status line, whose words the answer replaces.
    return app._panel_status


@pytest.mark.parametrize("where", ["headline", "footer", "panel-title", "panel-status"])
def test_first_usb_answer_rebuilds_once_and_keeps_focus(ui, tmp_path, where):  # noqa: F811
    asked = []
    answer = threading.Event()

    def probe(**_kwargs):
        asked.append(threading.get_ident())
        answer.wait(timeout=10)
        return FOUND

    wizard = _done_wizard(_success_receipt, tmp_path)
    wizard._report_usb_probe = probe
    try:
        app = ui(wizard)
        drain()
        assert wizard.screen == Screen.DONE and not wizard.dry_run
        assert app.window.get_focus() is app.arrival
        headline = _words(app.arrival)
        assert headline
        start = _focus_start(app, where)
        start.grab_focus()
        drain()
        assert app.window.get_focus() is start
        start_words = _words(start)

        renders = []
        render = app.render

        def counted():
            renders.append(app.window.get_focus())
            return render()

        app.render = counted

        # The check runs off the GTK thread; while it is out, nothing rebuilds.
        assert _tick_until(app, lambda: bool(asked))
        assert asked[0] != threading.get_ident()
        assert renders == []
        assert app.window.get_focus() is start
        assert C.BTN_SAVE_REPORT in app.actions
        assert not app.actions[C.BTN_SAVE_REPORT].get_sensitive()

        # First answer: exactly one rebuild.
        answer.set()
        assert _tick_until(app, lambda: bool(renders))
        drain()
        assert len(renders) == 1
        focus = app.window.get_focus()
        assert focus is not None and focus is not start
        assert focus.get_mapped()
        if where == "panel-status":
            # Its old words are gone: Orca moves to the new USB status.
            assert start_words != _words(focus)
            assert focus is app._panel_status
            assert "SanDisk Ultra, 16 GB" in _words(focus)
        else:
            assert _words(focus) == start_words
        if where == "headline":
            assert focus is app.arrival and _words(focus) == headline
        save = app.actions[C.BTN_SAVE_REPORT]
        assert save.get_sensitive()
        assert "SanDisk Ultra, 16 GB" in text(app)

        # The same answer again is not news: no second rebuild, focus stays.
        calls = len(asked)
        assert _tick_until(app, lambda: len(asked) > calls, timeout=6)
        assert _tick_until(app, lambda: not wizard._report_usb_busy)
        app.tick()
        drain()
        assert len(renders) == 1
        assert app.window.get_focus() is focus
        assert wizard.screen == Screen.DONE and not wizard.wants_shutdown
        assert wizard.report_status != "saved"
    finally:
        answer.set()
