# SPDX-License-Identifier: GPL-3.0-or-later
"""#138: one stage vocabulary for the start roadmap and the header.

Stages (Preparation, Erase, Result) name the header stepper, the progress
strip, spoken announcements and the start-screen roadmap. Steps inside
Preparation keep their #130 names; the last one is "Review" because Review
comes before the Erase stage (#166). Both come from one source in copy.py
and wizard.PREPARATION_PATH.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.models import Screen
from beamo_wipe.wizard import PREPARATION_PATH, journey_step_for, make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]


def test_roadmap_is_the_header_stages_in_order():
    parts = C.roadmap_parts(PREPARATION_PATH)
    assert parts == ("Preparation (6 steps)", "Erase", "Result")
    assert C.splash_roadmap(PREPARATION_PATH) == C._ROADMAP_ARROW.join(parts)
    # The count is the header's "Step n of N" total.
    total = journey_step_for(Screen.LAST_CHANCE)[1]
    assert f"({total} " in parts[0]


def test_roadmap_and_header_come_from_one_source(monkeypatch):
    """Change the shared stage names: roadmap, header caption and spoken
    stage all follow, so they cannot drift apart."""
    monkeypatch.setattr(C, "JOURNEY_LABELS", ("Getting ready", "Wiping", "Done"))
    parts = C.roadmap_parts(PREPARATION_PATH)
    assert parts[0].startswith("Getting ready") and parts[1:] == ("Wiping", "Done")
    assert C.journey_caption(Screen.WORKING) == "Wiping"
    assert C.journey_caption(Screen.DONE) == "Done"
    wiz = make_demo_wizard()
    wiz.skip_intro()
    assert C.journey_step_announcement(wiz).startswith("Getting ready")
    # And the step total follows the path.
    shorter = PREPARATION_PATH[1:]
    assert f"({len(shorter)} " in C.roadmap_parts(shorter)[0]


def test_review_is_the_last_step_and_does_not_say_erase():
    assert PREPARATION_PATH[-1] == Screen.LAST_CHANCE
    assert C.step_name(Screen.LAST_CHANCE) == "Review"
    for screen in PREPARATION_PATH:
        assert "erase" not in C.step_name(screen).lower()


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_uses_its_own_stage_names(code):
    try:
        lang.set_language(code)
        parts = C.roadmap_parts(PREPARATION_PATH)
        assert parts[0].startswith(C.JOURNEY_LABELS[0]) and "6" in parts[0]
        assert parts[1:] == tuple(C.JOURNEY_LABELS[1:])
        assert "{" not in parts[0]
        assert C.step_name(Screen.LAST_CHANCE) != "Review"
        erase_stem = {"fr": "effa", "de": "lösch", "es": "borr", "it": "cancell"}[code]
        assert erase_stem not in C.step_name(Screen.LAST_CHANCE).lower()
    finally:
        lang.set_language("en")


def test_web_preview_and_helper_use_the_same_stages():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    assert payload["splashRoadmap"] == C.splash_roadmap(PREPARATION_PATH)
    assert payload["journey"] == list(C.JOURNEY_LABELS)
    helper = (ROOT / "helper/index.html").read_text(encoding="utf-8")
    assert " → ".join(C.roadmap_parts(PREPARATION_PATH)) in helper
    assert "Review and erase" not in helper


def test_consoles_show_the_roadmap(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.screen = Screen.SPLASH

    def stop(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    assert C.splash_roadmap(PREPARATION_PATH) in out
    source = (ROOT / "src/beamo_wipe/ui/console_wizard.py").read_text(encoding="utf-8")
    assert source.count("C.splash_roadmap(PREPARATION_PATH)") == 2  # curses + plain
    gtk = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "C.splash_roadmap(PREPARATION_PATH)" in gtk


def test_tk_splash_roadmap_and_header_stepper_use_the_same_names():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    _needs_display()
    wiz = make_demo_wizard()
    wiz.preview = False
    app = TkWizard(wiz)
    try:
        app.root.geometry("1280x820+40+40")
        app._draw()
        app.root.update()

        def walk(widget):
            yield widget
            for child in widget.winfo_children():
                yield from walk(child)

        labels = [str(w.cget("text")) for w in walk(app.root)
                  if w.winfo_class() == "Label" and w.winfo_ismapped()]
        assert C.splash_roadmap(PREPARATION_PATH) in labels
        # Leave the splash: the header stepper draws the same stage names.
        wiz.skip_intro()
        app._draw()
        app.root.update()
        header = app._header
        canvases = [w for w in walk(header) if w.winfo_class() == "Canvas"]
        texts = {cv.itemcget(item, "text") for cv in canvases
                 for item in cv.find_all() if cv.type(item) == "text"}
        for stage in C.JOURNEY_LABELS:
            assert stage in texts
        assert C.roadmap_parts(PREPARATION_PATH)[1:] == tuple(C.JOURNEY_LABELS[1:])
    finally:
        app._teardown()
