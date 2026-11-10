# SPDX-License-Identifier: GPL-3.0-or-later
"""#185: the Tk empty screen shows the Intel VMD / RST steps. Fake data only."""

from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")

from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe import recovery as Rec  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402


def _texts(widget):
    out = []
    stack = [widget]
    while stack:
        item = stack.pop()
        try:
            value = item.cget("text")
        except (tk.TclError, AttributeError):
            value = ""
        if value:
            out.append(str(value))
        stack.extend(item.winfo_children())
    return out


@pytest.fixture
def empty_screen():
    from beamo_wipe.ui.tk_wizard import TkWizard

    apps = []

    def build(scenario, size):
        wizard = make_demo_wizard(scenario=scenario)
        wizard.preview = False
        wizard.skip_intro()
        wizard.accept_what()
        wizard.set_owner(True)
        wizard.continue_owner()
        assert wizard.screen == Screen.PICK_EMPTY
        try:
            app = TkWizard(wizard)
        except tk.TclError as exc:
            pytest.skip(f"Tk unavailable: {exc}")
        apps.append(app)
        if app._after_id is not None:
            app.root.after_cancel(app._after_id)
            app._after_id = None
        app.root.geometry(f"{size[0]}x{size[1]}+0+0")
        app.root.update()
        app._draw()
        app.root.update()
        return app

    yield build
    for app in reversed(apps):
        for callback in app.root.tk.call("after", "info"):
            app.root.tk.call("after", "cancel", callback)
        app._teardown()


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_hidden_scenario_shows_the_steps(empty_screen, size):
    app = empty_screen("hidden", size)
    flat = " ".join(" ".join(_texts(app.root)).split())
    assert Rec.HIDDEN_STORAGE_HAPPENED in flat
    for line in (*Rec.HIDDEN_STORAGE_STEPS, Rec.HIDDEN_STORAGE_WARNING):
        assert line in flat, line
    assert C.EMPTY_DISKS not in flat
    assert C.TITLE_EMPTY in flat


def test_tk_empty_scenario_keeps_the_generic_text(empty_screen):
    app = empty_screen("empty", (800, 600))
    flat = " ".join(" ".join(_texts(app.root)).split())
    assert " ".join(C.EMPTY_DISKS.split()) in flat
    assert Rec.HIDDEN_STORAGE_HAPPENED not in flat
