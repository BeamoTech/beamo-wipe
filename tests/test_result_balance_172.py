# SPDX-License-Identifier: GPL-3.0-or-later
"""#172: the result screen is balanced at every supported size.

The badge and headline no longer take a third of a short window, so the
summary and What next start in the first view; when the whole result fits,
the space is shared above and below instead of all below; when it scrolls,
it starts at the top as before. Fake disks and fake nwipe logs only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import lang
from test_result_presentations import CASES, case_evidence


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _app(case_name, size, text_size="standard", preview=False):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz, _ev, _log = case_evidence(next(c for c in CASES if c[0] == case_name))
    wiz.text_size = text_size
    wiz.preview = preview
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+20+20")
    app._draw()
    for _ in range(12):
        app.root.update()
    return wiz, app


def _spacer(app):
    found = []

    def visit(w):
        if getattr(w, "_beamo_balance", False):
            found.append(w)
        for child in w.winfo_children():
            visit(child)

    visit(app._body)
    (spacer,) = found
    return spacer


@pytest.mark.parametrize("case_name,size,text_size,preview", [
    ("verified", (800, 600), "standard", False),
    ("verified", (800, 600), "extra", False),
    ("engine_failed", (1280, 820), "standard", False),
    ("verified", (1280, 820), "standard", True),
    ("verified", (1024, 740), "large", True),
])
def test_result_is_centered_when_it_fits_and_top_aligned_when_it_scrolls(
        case_name, size, text_size, preview):
    from test_tk_runtime import _clipping_problems

    _wiz, app = _app(case_name, size, text_size, preview)
    try:
        spacer = _spacer(app)
        col = spacer.master
        view = app._body_canvas.winfo_height()
        content = col.winfo_reqheight() - spacer.winfo_reqheight()
        expected = max(0, (view - content) // 2)
        assert abs(spacer.winfo_reqheight() - expected) <= 1
        if content >= view:
            assert spacer.winfo_reqheight() <= 1  # scrolls: starts at the top (Tk reports 1 for 0)
        assert not _clipping_problems(app)
    finally:
        app._teardown()


def test_first_view_reaches_what_next_at_800x600():
    from beamo_wipe.outcomes import WHAT_NEXT as WHAT_NEXT_TITLE

    _wiz, app = _app("verified", (800, 600))
    try:
        view_bottom = app._body_canvas.winfo_rooty() + app._body_canvas.winfo_height()
        heading = []

        def visit(w):
            if w.winfo_class() == "Label" and str(w.cget("text")) == WHAT_NEXT_TITLE:
                heading.append(w)
            for child in w.winfo_children():
                visit(child)

        visit(app._body)
        (label,) = heading
        # The heading and three steps below it are in the first view.
        assert label.winfo_rooty() + 4 * label.winfo_height() + 3 * 4 <= view_bottom
    finally:
        app._teardown()


def test_badge_is_smaller_than_before():
    _wiz, app = _app("verified", (1280, 820))
    try:
        spacer = _spacer(app)
        badge = [c for c in spacer.master.winfo_children() if c.winfo_class() == "Canvas"][0]
        assert badge.winfo_reqheight() <= 56
    finally:
        app._teardown()
