# SPDX-License-Identifier: GPL-3.0-or-later
"""#163: the ready state is a check mark plus the word "Ready", not "0".

Tk draws a check mark in the ring (the number is hidden) and "Ready" heads
the caption; GTK shows an alert "Ready. Erase now is available." when the
review period ends (Orca announces it without moving focus); curses and the
plain console say "Ready." too; the web preview shows the check mark, the
word and a polite status. Behaviour is unchanged: zero only enables Erase
now and nothing starts without it. Fake disks; dry-run runner.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _last_chance():
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


def test_ready_copy():
    assert C.COUNTDOWN_READY_WORD == "Ready"
    assert C.COUNTDOWN_AVAILABLE == "Erase now is available."
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        assert C.COUNTDOWN_READY_WORD and not re.search(r"\d", C.COUNTDOWN_READY_WORD)
        assert C.BTN_ERASE in C.COUNTDOWN_AVAILABLE, code


def test_gate_is_unchanged():
    wiz = _last_chance()
    assert not wiz.erase_enabled
    wiz._erase_until = 0
    assert wiz.erase_enabled and not wiz.runner.started and wiz.screen == Screen.LAST_CHANCE


def test_curses_footer_says_ready_only_when_enabled():
    wiz = _last_chance()
    lines = " ".join(console_wizard._primary_footer(wiz, False))
    assert "Ready." not in lines and "Wait" in lines
    wiz._erase_until = 0
    ready = " ".join(console_wizard._primary_footer(wiz, False))
    # #165: the ready line no longer says "Enter to erase"; Enter presses
    # only the highlighted button.
    assert ready.startswith(f"{C.COUNTDOWN_READY_WORD}. {C.COUNTDOWN_AVAILABLE}")
    assert not wiz.runner.started


def test_plain_console_says_ready_before_the_erase_prompt(monkeypatch, capsys):
    wiz = _last_chance()
    wiz._erase_until = 0
    prompts = []

    def answer(prompt):
        prompts.append(prompt)
        if prompt == C.CON_ERASE_PROMPT:
            raise EOFError
        return ""

    monkeypatch.setattr("builtins.input", answer)
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out
    assert f"{C.COUNTDOWN_READY_WORD}. {C.COUNTDOWN_AVAILABLE}" in out
    assert not wiz.runner.started


def test_gtk_source_shows_a_ready_alert_without_moving_focus():
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("# #163:"):src.index("self.primary = self.button(\n                C.BTN_ERASE")]
    assert 'f"{C.COUNTDOWN_READY_WORD}. {C.COUNTDOWN_AVAILABLE}"' in block
    assert "Atk.Role.ALERT" in block and "set_no_show_all(True)" in block
    assert "grab_focus" not in block
    update = src[src.index('ready = getattr(self, "ready_label", None)'):]
    update = update[: update.index("self.primary.set_sensitive")]
    assert "set_visible(self.w.erase_enabled)" in update and "grab_focus" not in update


def test_preview_ready_state_has_check_word_and_status():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    assert payload["countdownReadyWord"] == "Ready"
    assert payload["countdownAvailable"] == C.COUNTDOWN_AVAILABLE
    (script,) = re.findall(r"<script>(.*?)</script>", html, re.S)
    last = script[script.index('} else if (screen === "last")'):]
    last = last[: last.index('} else if (screen === "working")')]
    assert '${ready ? "0"' not in last
    assert 'class="ringcheck"' in last and "readyword" in last
    assert 'role="status" aria-live="polite"' in last and "P.countdownAvailable" in last


@pytest.fixture
def last_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size, text_size="standard", code="en"):
        _needs_display()
        lang.set_language(code)
        wiz = _last_chance()
        wiz.set_language(code)
        wiz.text_size = text_size
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        return wiz, app

    yield build
    for app in created:
        app._teardown()


@pytest.mark.parametrize("size,text_size,code", [((800, 600), "standard", "en"),
                                                 ((800, 600), "large", "en"),
                                                 ((1280, 820), "extra", "en"),
                                                 ((800, 600), "standard", "de")])
def test_tk_renders_the_ready_state(last_app, size, text_size, code):
    from test_tk_runtime import _clipping_problems

    wiz, app = last_app(size, text_size, code)
    ring = app._countdown_ring
    # Counting: a number, no check mark, no Ready word.
    assert app._countdown_num.cget("text") not in ("", "0")
    assert ring.itemcget(app._countdown_num_item, "state") in ("", "normal")
    assert not ring.find_withtag("check")
    assert not app._countdown_ready.winfo_ismapped()
    assert app._countdown_label.cget("text") == C.COUNTDOWN_CAPTION
    wiz._erase_until = 0
    app._refresh_last_chance()
    for _ in range(6):
        app.root.update()
    # Ready: a check mark inside the ring, the number hidden (never "0"),
    # and the word Ready above the caption, in view.
    assert ring.find_withtag("check")
    assert ring.itemcget(app._countdown_num_item, "state") == "hidden"
    assert app._countdown_num.cget("text") != "0"
    word = app._countdown_ready
    assert word.winfo_ismapped() and word.cget("text") == C.COUNTDOWN_READY_WORD
    assert word.winfo_rooty() < app._countdown_label.winfo_rooty()
    assert word.winfo_rooty() + word.winfo_height() <= app._footer.winfo_rooty() + 1
    assert app._countdown_label.cget("text") == C.COUNTDOWN_READY
    # Behaviour unchanged.
    assert wiz.erase_enabled and not wiz.runner.started and wiz.screen == Screen.LAST_CHANCE
    assert _clipping_problems(app) == []


def test_tk_ready_word_goes_away_if_the_countdown_restarts(last_app):
    wiz, app = last_app((1280, 820))
    wiz._erase_until = 0
    app._refresh_last_chance()
    app.root.update()
    assert app._countdown_ready.winfo_ismapped()
    wiz.restart_review_countdown()
    app._refresh_last_chance()
    for _ in range(4):
        app.root.update()
    assert not wiz.erase_enabled
    assert not app._countdown_ready.winfo_ismapped()
    assert not app._countdown_ring.find_withtag("check")
    assert app._countdown_num.cget("text") not in ("", "0")
