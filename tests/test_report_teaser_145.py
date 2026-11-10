# SPDX-License-Identifier: GPL-3.0-or-later
"""#145: the Owner report panel is one line with a Learn more link.

"Want a report? You can photograph a summary at the end, or save it to a
report USB when asked." (#127's photo record ships, so it leads). Learn more
opens Need a report? by keyboard and in the screen-reader view. Choosing a
wanted report still asks before it is discarded at shutdown (#25). Fake data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]


def _owner():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    assert wiz.screen == Screen.OWNER
    return wiz


def test_copy_is_one_short_line():
    assert C.REPORT_MEDIA_WHAT == (
        "Want a report? You can photograph a summary at the end, "
        "or save it to a report USB when asked."
    )
    assert C.LEARN_MORE == "Learn more"
    assert len(C.REPORT_MEDIA_WHAT) < 110


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_it(code):
    from beamo_wipe import lang

    english = {n: getattr(C, n) for n in ("REPORT_MEDIA_WHAT", "LEARN_MORE",
                                          "LEARN_MORE_REPORT_NAME", "CON_REPORT_LEARN")}
    try:
        lang.set_language(code)
        for name, value in english.items():
            assert getattr(C, name) != value, (code, name)
        assert C.CON_REPORT_LEARN.startswith("R")
    finally:
        lang.set_language("en")


def test_wanted_report_still_asks_before_discarding():
    """#25: a wanted, unsaved report makes Shut down ask first."""
    wiz = _owner()
    wiz.open_report_help()
    assert wiz.screen == Screen.REPORT_HELP
    wiz.set_report_wanted(True)
    wiz.close_report_help()
    assert wiz.screen == Screen.OWNER and wiz.report_wanted
    wiz.shutdown()
    assert wiz.screen == Screen.SHUTDOWN_CONFIRM
    assert not wiz.wants_shutdown


# --- Consoles, GTK (source), web preview ---------------------------------------------------


def test_curses_owner_line_names_the_key(monkeypatch):
    from test_plain_result_134 import _curses_lines

    body = "\n".join(_curses_lines(monkeypatch, _owner(), h=80))
    assert C.REPORT_MEDIA_WHAT[:30] in body and C.CON_REPORT_LEARN in body
    assert "FAT32" not in body.split(C.POWER_REMINDER[:20])[0]  # no long panel


def test_curses_r_opens_the_help():
    from beamo_wipe.ui import console_wizard as console

    wiz = _owner()
    console._handle(wiz, ord("r"))
    assert wiz.screen == Screen.REPORT_HELP


def test_gtk_learn_more_opens_help_and_is_named_for_orca():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "learn = self.button(C.LEARN_MORE, self.w.open_report_help, in_body=True)" in src
    assert "learn.get_accessible().set_name(C.LEARN_MORE_REPORT_NAME)" in src


def test_web_preview_line_and_link():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert 'id="report-learn-more" aria-label="${P.learnMoreReport}"' in html
    assert 'main.querySelector("#report-learn-more").onclick' in html
    assert '${panel("info", P.reportMediaWhat, true)}' not in html


# --- Rendered Tk ------------------------------------------------------------------------------


@pytest.fixture
def tk_owner():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(text_size="standard", size=(800, 600)):
        _needs_display()
        wiz = _owner()
        wiz.text_size = text_size
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _label(app, text):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return next(w for w in walk(app._body) if w.winfo_class() == "Label" and str(w.cget("text")) == text)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_one_line(tk_owner, size):
    wiz, app = tk_owner(size=size)
    label = _label(app, C.REPORT_MEDIA_WHAT)
    line = app.font_s.metrics("linespace")
    assert label.winfo_height() < 2 * line  # one line
    learn = app._report_learn_more
    assert learn.itemcget(learn._label, "text") == C.LEARN_MORE


def test_tk_learn_more_by_keyboard_opens_help(tk_owner):
    wiz, app = tk_owner()
    learn = app._report_learn_more
    # Reachable by Tab from the ownership box.
    start = app.root.focus_lastfor()
    seen, current = [], start
    for _ in range(20):
        current = current.tk_focusNext()
        seen.append(current)
        if current is learn:
            break
    assert learn in seen
    learn._key()
    assert wiz.screen == Screen.REPORT_HELP


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_fits_800x600(tk_owner, text_size):
    from test_tk_runtime import _clipping_problems

    wiz, app = tk_owner(text_size)
    assert _clipping_problems(app) == []
