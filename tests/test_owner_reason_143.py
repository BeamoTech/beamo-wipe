# SPDX-License-Identifier: GPL-3.0-or-later
"""#143: the greyed Choose a disk on the Owner screen says why.

"Tick the box above to continue." sits beside the disabled button while the
ownership box is clear and disappears once it is ticked; GTK also uses it as
the button's accessible description; curses shows the same line. The gate
itself (owner_ok before Choose a disk) is unchanged. Fake demo disks only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]


def _owner(ticked=False):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    assert wiz.screen == Screen.OWNER
    wiz.set_owner(ticked)
    return wiz


def test_copy():
    assert C.OWNER_CONTINUE_REASON == "Tick the box above to continue."


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_it(code):
    from beamo_wipe import lang

    english = C.OWNER_CONTINUE_REASON
    try:
        lang.set_language(code)
        assert C.OWNER_CONTINUE_REASON and C.OWNER_CONTINUE_REASON != english
    finally:
        lang.set_language("en")


def test_the_gate_is_unchanged():
    wiz = _owner(False)
    wiz.continue_owner()
    assert wiz.screen == Screen.OWNER  # no tick, no way on
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK


# --- Consoles, GTK (source), web preview ---------------------------------------------------


@pytest.mark.parametrize("ticked", [False, True])
def test_curses_footer_shows_the_reason_only_while_unticked(ticked):
    from beamo_wipe.ui import console_wizard as console

    footer = console._primary_footer(_owner(ticked), False)
    assert (C.OWNER_CONTINUE_REASON in footer) is (not ticked)
    assert C.CON_OWNER_FOOTER in footer


def test_gtk_shows_and_describes_the_reason_and_syncs_on_toggle():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "self.owner_reason = self.label(C.OWNER_CONTINUE_REASON, focusable=True)" in src
    sync = src[src.index("def _sync_owner_reason(self)"):]
    sync = sync[:sync.index("\n    def ")]
    assert "reason.set_visible(waiting)" in sync
    assert "set_description(" in sync and "C.OWNER_CONTINUE_REASON if waiting else" in sync
    toggle = src[src.index("    def _owner(self, checked, generation):"):]
    toggle = toggle[:toggle.index("\n    def ")]
    assert "self._sync_owner_reason()" in toggle


def test_web_preview_reason_and_description():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert 'reason.textContent = P.ownerReason;' in html
    assert 'choose.setAttribute("aria-describedby", "owner-reason")' in html
    assert C.OWNER_CONTINUE_REASON in html


# --- Rendered Tk ----------------------------------------------------------------------------


@pytest.fixture
def tk_owner():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(ticked=False, text_size="standard", size=(800, 600)):
        _needs_display()
        wiz = _owner(ticked)
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


def _footer_labels(app):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [str(w.cget("text")) for w in walk(app._footer)
            if w.winfo_class() == "Label" and w.winfo_ismapped()]


def test_tk_reason_beside_the_disabled_button(tk_owner):
    wiz, app = tk_owner(False)
    assert not app._primary._enabled
    assert C.OWNER_CONTINUE_REASON in _footer_labels(app)
    reason = app._owner_reason
    # Beside it: same row, to its left.
    assert reason.master is app._primary.master
    assert reason.winfo_rootx() + reason.winfo_width() <= app._primary.winfo_rootx()


def test_tk_reason_goes_when_ticked_and_returns_when_cleared(tk_owner):
    wiz, app = tk_owner(False)
    app._owner_clicked()
    app.root.update()
    assert wiz.owner_ok and app._primary._enabled
    assert C.OWNER_CONTINUE_REASON not in _footer_labels(app)
    app._owner_clicked()
    app.root.update()
    assert not wiz.owner_ok and not app._primary._enabled
    assert C.OWNER_CONTINUE_REASON in _footer_labels(app)


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_fits_800x600(tk_owner, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    wiz, app = tk_owner(False, text_size)
    assert _clipping_problems(app) == []
    assert _off_window_problems(app) == []
    assert app._primary.winfo_ismapped()
