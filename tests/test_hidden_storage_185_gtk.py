# SPDX-License-Identifier: GPL-3.0-or-later
"""#185: the GTK/Orca empty screen reads the Intel VMD / RST steps."""

from __future__ import annotations

import pytest

pytest.importorskip("gi")
from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe import recovery as Rec  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402
from test_accessible_runtime import text, ui  # noqa: E402,F401


def _at_empty(scenario):
    wizard = make_demo_wizard(scenario=scenario)
    wizard.skip_intro()
    wizard.accept_what()
    wizard.set_owner(True)
    wizard.continue_owner()
    assert wizard.screen == Screen.PICK_EMPTY
    return wizard


def test_gtk_hidden_scenario_reads_the_steps(ui):  # noqa: F811
    app = ui(_at_empty("hidden"))
    shown = " ".join(text(app).split())
    assert Rec.HIDDEN_STORAGE_HAPPENED in shown
    for line in (*Rec.HIDDEN_STORAGE_STEPS, Rec.HIDDEN_STORAGE_WARNING):
        assert line in shown, line
    assert not any(name.startswith("Select ") for name in app.actions)


def test_gtk_empty_scenario_keeps_the_generic_text(ui):  # noqa: F811
    app = ui(_at_empty("empty"))
    shown = " ".join(text(app).split())
    assert " ".join(C.EMPTY_DISKS.split()) in shown
    assert Rec.HIDDEN_STORAGE_HAPPENED not in shown
