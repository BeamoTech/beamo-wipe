# SPDX-License-Identifier: GPL-3.0-or-later
"""#166: the header names Review as the final check before Erase.

Review is the last Preparation step (#130/#138). Its step name is now
"Final check", so the step bar reads "Step 6 of 6 · Final check" and screen
readers hear "Preparation, step 6 of 6: Final check." It still never uses
the erase verb (#138: Review comes before the Erase stage). The stage
stepper keeps Preparation highlighted. Fake disks only.
"""

from __future__ import annotations

import json
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard
from beamo_wipe.wizard import PREPARATION_PATH

ERASE_STEMS = {"en": "erase", "fr": "effa", "de": "lösch", "es": "borr", "it": "cancell"}


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at_last():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


def test_review_step_says_final_check():
    wiz = _at_last()
    assert PREPARATION_PATH[-1] == Screen.LAST_CHANCE
    assert C.step_name(Screen.LAST_CHANCE) == "Final check"
    assert C.journey_step_caption(wiz) == "Step 6 of 6 · Final check"
    assert C.journey_step_short(wiz) == "Step 6 of 6"
    assert C.journey_step_announcement(wiz) == "Preparation, step 6 of 6: Final check."
    # Still in Preparation: the stage stays the same vocabulary (#138).
    assert C.journey_caption(Screen.LAST_CHANCE) == "Preparation"


@pytest.mark.parametrize("code", ["en", "fr", "de", "es", "it"])
def test_every_language_says_final_without_the_erase_verb(code):
    lang.set_language(code)
    name = C.step_name(Screen.LAST_CHANCE)
    assert name and ERASE_STEMS[code] not in name.lower()
    other_names = {C.step_name(s) for s in PREPARATION_PATH[:-1]}
    assert name not in other_names


def test_curses_and_plain_console_headers(monkeypatch, capsys):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _at_last()
    assert "Step 6 of 6 · Final check" in " ".join(_curses_text(wiz, 40, 120).split())

    def stop(_prompt):
        raise EOFError

    wiz2 = _at_last()
    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz2)
    assert "Step 6 of 6 · Final check" in capsys.readouterr().out


def test_preview_header_uses_the_same_caption():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    assert "Step 6 of 6 · Final check" in json.dumps(payload, ensure_ascii=False)
    assert "Step 6 of 6 · Review" not in json.dumps(payload, ensure_ascii=False)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_header_on_review(size):
    from test_step_progress_130 import _header_texts
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _at_last()
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        texts = [text for text, _ in _header_texts(app)]
        assert "Step 6 of 6 · Final check" in texts
        assert "Step 6 of 6 · Review" not in texts
    finally:
        app._teardown()
