# SPDX-License-Identifier: GPL-3.0-or-later
"""#164: Review describes the method once.

Review used to show "One overwrite, followed by verification." and then
"Everyday: 1 overwrite pass: random data. Then we check the last
overwrite." It now shows one line: the method name plus the operation
summary from #33 ("Everyday: One overwrite, followed by verification."),
which states the overwrites and whether verification follows. The
operation summaries themselves are unchanged; Working and Done keep their
method lines. Fake disks only; nothing starts the engine.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.ui import console_wizard

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINES = {
    MethodId.EVERYDAY: "Everyday: One overwrite, followed by verification.",
    MethodId.EXTRA: "Three overwrites: Three overwrites, followed by verification.",
    MethodId.QUICK_ZERO: "Quick zero: One overwrite. Verification is not performed.",
}


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at_last(method=MethodId.EVERYDAY):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.set_method(method)
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


@pytest.mark.parametrize("method", list(METHODS))
def test_one_line_names_the_method_and_says_whether_it_verifies(method):
    wiz = _at_last(method)
    spec = METHODS[method]
    assert wiz.review_method_line == LINES[method]
    # #33's operation summary is intact and still matches the nwipe spec.
    assert wiz.review_method_line.endswith(spec.operation_summary)
    if spec.verification_passes:
        assert "followed by verification" in wiz.review_method_line
    else:
        assert "Verification is not performed" in wiz.review_method_line
        assert "verified" not in wiz.review_method_line.lower()


def test_every_language_keeps_name_and_operation():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for method in METHODS:
            spec = METHODS[method]
            line = C.REVIEW_METHOD_LINE.format(method=spec.title, operation=spec.operation_summary)
            assert line.startswith(spec.title) and line.endswith(spec.operation_summary), code
    lang.set_language("fr")
    assert " : " in C.REVIEW_METHOD_LINE


@pytest.mark.parametrize("method", list(METHODS))
def test_plain_console_review_has_one_method_line(method, monkeypatch, capsys):
    wiz = _at_last(method)
    wiz._erase_until = 0

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out
    assert out.count(LINES[method]) == 1
    assert METHODS[method].summary not in out
    assert "overwrite pass" not in out
    assert not wiz.runner.started


@pytest.mark.parametrize("method", list(METHODS))
def test_curses_review_has_one_method_line(method, monkeypatch):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _at_last(method)
    text = " ".join(_curses_text(wiz, 60, 120).split())
    assert text.count(LINES[method]) == 1
    assert METHODS[method].summary not in text and "overwrite pass" not in text


def test_gtk_review_source_uses_the_one_line():
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("elif screen == Screen.LAST_CHANCE:"):]
    block = block[: block.index("self.countdown_label = self.label")]
    assert "self.w.review_method_line" in block
    assert "method_summary" not in block and "operation_summary" not in block


def test_preview_review_uses_the_one_line():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    (script,) = re.findall(r"<script>(.*?)</script>", html, re.S)
    last = script[script.index('} else if (screen === "last")'):]
    last = last[: last.index('} else if (screen === "working")')]
    assert "P.methods[method].reviewLine" in last
    assert "P.methods[method].summary" not in last and "P.methods[method].operation" not in last
    assert LINES[MethodId.EVERYDAY] in html


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((1280, 820), "standard"),
                                            ((1280, 820), "extra")])
@pytest.mark.parametrize("method", [MethodId.EVERYDAY, MethodId.QUICK_ZERO])
def test_tk_review_shows_one_method_line(size, text_size, method):
    from test_tk_runtime import _clipping_problems, _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _at_last(method)
    wiz.text_size = text_size
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        texts = []

        def visit(w):
            if w.winfo_class() == "Label" and w.winfo_ismapped():
                texts.append(str(w.cget("text")).replace("\n", " "))
            for child in w.winfo_children():
                visit(child)

        visit(app._body)
        assert texts.count(LINES[method]) == 1
        assert not any(METHODS[method].summary in t for t in texts)
        assert not any("overwrite pass" in t for t in texts)
        assert _clipping_problems(app) == []
        assert not wiz.erase_enabled and not wiz.runner.started
    finally:
        app._teardown()
