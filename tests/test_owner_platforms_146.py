# SPDX-License-Identifier: GPL-3.0-or-later
"""#146: "Not Apple Silicon Macs. Not Chromebooks." is under Show more on Owner.

Once the wizard runs, the PC has already started from this USB, so the
platform bullet (compat_story.PLATFORMS) is pre-boot guidance. The live
Owner screen keeps it under Show more (Tk, web preview), a collapsed
expander (GTK) or after the supporting notes (consoles, which have no
disclosure control). Launchers, the helper pages and docs keep it up front.
docs/claims.md is listing copy and does not require it on this screen.
Fake demo disks only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe.compat_story import PLATFORMS, required_story_phrases
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

ROOT = Path(__file__).resolve().parents[1]
NOT_APPLE = "Not Apple Silicon"


def _owner():
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    assert wiz.screen == Screen.OWNER
    return wiz


def test_owner_split_keeps_every_bullet():
    assert C.owner_platforms_line() == PLATFORMS == C.WHAT_BULLETS[-1]
    assert C.owner_bullets() + (C.owner_platforms_line(),) == C.WHAT_BULLETS
    assert all(NOT_APPLE not in b and "Chromebook" not in b for b in C.owner_bullets())


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_split_follows_the_language(code):
    from beamo_wipe import lang

    try:
        lang.set_language(code)
        assert C.owner_platforms_line() == C.WHAT_BULLETS[-1] != PLATFORMS
        assert C.owner_bullets() == tuple(C.WHAT_BULLETS[:-1])
    finally:
        lang.set_language("en")


# --- Pre-boot surfaces keep it ------------------------------------------------------------


@pytest.mark.parametrize("rel", [
    "helper/index.html", "helper/fr.html", "helper/de.html", "helper/es.html", "helper/it.html",
    "desktop/web/index.html",
])
def test_pre_boot_pages_keep_it(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert "Apple Silicon" in text and "Chromebook" in text


def test_helper_story_still_requires_it():
    assert PLATFORMS in required_story_phrases()
    helper = (ROOT / "helper/index.html").read_text(encoding="utf-8")
    assert "Not Apple Silicon Macs. Not Chromebooks." in helper


def test_launchers_and_docs_keep_it():
    assert "does not support Apple Silicon or Chromebooks" in (ROOT / "desktop/main.go").read_text(encoding="utf-8")
    assert "Apple Silicon and Chromebooks are not supported" in (ROOT / "desktop/readiness.go").read_text(encoding="utf-8")
    assert "Not for Apple Silicon Macs. Not for Chromebooks." in (ROOT / "docs/boot-card.md").read_text(encoding="utf-8")
    assert "Apple Silicon" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_claims_are_listing_copy_not_a_screen_requirement():
    claims = (ROOT / "docs/claims.md").read_text(encoding="utf-8")
    assert claims.startswith("# Amazon / pack copy")
    assert "Not Apple Silicon. Not Chromebooks." in claims  # unchanged
    # No placement rule: nothing names the Owner screen or the live wizard.
    assert "owner" not in claims.lower() and "wizard" not in claims.lower()


# --- Consoles: after the supporting notes, not among the bullets --------------------------


def test_curses_prints_it_after_the_notes(monkeypatch):
    from test_plain_result_134 import _curses_lines

    rows = _curses_lines(monkeypatch, _owner(), h=80)
    body = " ".join(row.strip() for row in rows)  # wrapped at 80 columns
    bullets = [i for i, row in enumerate(rows) if row.lstrip().startswith("*")]
    assert len(bullets) == len(C.owner_bullets())
    assert all(NOT_APPLE not in rows[i] for i in bullets)
    assert body.index(C.POWER_EVENTS[:30]) < body.index("Not Apple Silicon") < body.index(C.OWNER_LEAD[:30])


def test_plain_console_prints_it_before_the_box(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    def stop(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    try:
        console._plain_loop(_owner())
    except Exception:
        pass
    out = capsys.readouterr().out
    assert f" - {PLATFORMS}" not in out
    assert out.index(C.POWER_EVENTS) < out.index(PLATFORMS) < out.index(C.OWNER_CHECKBOX)


# --- GTK (source) and web preview ---------------------------------------------------------


def test_gtk_uses_a_show_more_expander():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("elif screen in (Screen.WHAT, Screen.OWNER):"):]
    block = block[:block.index("elif screen == Screen.PICK:")]
    assert 'self.label("\\n".join(C.owner_bullets()))' in block
    assert "C.WHAT_BULLETS" not in block
    assert "platforms = Gtk.Expander.new(C.BTN_MORE)" in block
    assert "platforms.set_expanded(False)" in block
    assert "Gtk.Label(label=C.owner_platforms_line())" in block
    assert "platforms_text.set_can_focus(True)" in block


def test_web_preview_moves_it_under_show_more():
    from test_single_erase_warning_128 import _gallery_payload

    payload = _gallery_payload()
    assert payload["what"] == list(C.owner_bullets())
    assert payload["platforms"] == PLATFORMS


def test_web_preview_show_more_renders_it():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert '<div class="extra">${P.platforms} ${P.secureBoot}' in html


# --- Rendered Tk ------------------------------------------------------------------------------


@pytest.fixture
def tk_owner():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(text_size="standard", size=(800, 600), more=False):
        _needs_display()
        wiz = _owner()
        wiz.text_size = text_size
        app = TkWizard(wiz)
        app._show_more = more
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _texts(app):
    out = []

    def walk(widget):
        try:
            out.append(str(widget.cget("text")))
        except Exception:
            pass
        for child in widget.winfo_children():
            walk(child)

    walk(app._body)
    return "\n".join(out)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_main_view_hides_it(tk_owner, size):
    _wiz, app = tk_owner(size=size)
    shown = _texts(app)
    for bullet in C.owner_bullets():
        assert bullet in shown
    assert NOT_APPLE not in shown and "Chromebook" not in shown
    assert app._more_button.itemcget(app._more_button._label, "text") == C.BTN_MORE


def test_tk_show_more_reveals_it_by_keyboard(tk_owner):
    _wiz, app = tk_owner()
    app._more_button._key()
    app.root.update()
    assert PLATFORMS in _texts(app).replace("\n", " ") or NOT_APPLE in _texts(app)
    assert app.root.focus_lastfor() is app._more_button  # focus stays on the control


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("more", [False, True])
def test_tk_fits_800x600(tk_owner, text_size, more):
    from test_tk_runtime import _clipping_problems

    _wiz, app = tk_owner(text_size, more=more)
    assert _clipping_problems(app) == []
