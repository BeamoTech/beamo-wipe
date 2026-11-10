# SPDX-License-Identifier: GPL-3.0-or-later
"""#160: the Everyday caveat is off the main card, still one action away.

"This checks only storage the disk exposes. It does not promise how long it
will take. A saved report is not extra proof of hidden areas." is not
required on the card by docs/claims.md; the method-selection warning it does
require (storage_limits.OVERWRITE_LIMITS) stays on the Method screen. The
caveat moves under Show more: the Tk card's own toggle (#159), the web
preview card, a GTK expander, and after the choices in both consoles. Fake
disks only; nothing starts the engine.
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
from preview_page import inline_script

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _method_wizard(path="/dev/sda"):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    return wiz


def test_caveat_wording_and_claims_are_unchanged():
    assert C.EVERYDAY_LIMITS == (
        "This checks only storage the disk exposes. It does not promise how long "
        "it will take. A saved report is not extra proof of hidden areas."
    )
    assert C.METHOD_CARDS[MethodId.EVERYDAY]["limits"] == C.EVERYDAY_LIMITS
    claims = (ROOT / "docs" / "claims.md").read_text(encoding="utf-8")
    limits_doc = (ROOT / "docs" / "storage-and-controller-limits.md").read_text(encoding="utf-8")
    # Neither document requires this caveat on the card; the warning they do
    # require at method selection is the storage limits notice.
    assert "checks only storage" not in claims + limits_doc
    assert "overwrites the storage the drive exposes" in claims
    assert re.search(r"Overwriting reaches only storage the device exposes.*\(method selection",
                     limits_doc)


def test_storage_limits_notice_stays_on_the_method_screen(monkeypatch, capsys):
    wiz = _method_wizard()
    assert wiz.storage_notice

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    assert wiz.storage_notice in capsys.readouterr().out


def test_plain_console_prints_the_caveat_after_the_choices(monkeypatch, capsys):
    wiz = _method_wizard()

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    lines = capsys.readouterr().out.splitlines()
    keyed = {m: i for m in METHODS for i, ln in enumerate(lines)
             if ln.startswith(f"{C.METHOD_CARDS[m]['key']} {METHODS[m].title}")}
    assert set(keyed) == set(METHODS)
    for method, index in keyed.items():
        assert C.EVERYDAY_LIMITS not in lines[index], method
    (note_at,) = [i for i, ln in enumerate(lines) if C.EVERYDAY_LIMITS in ln]
    assert lines[note_at] == f"Everyday: {C.EVERYDAY_LIMITS}"
    assert note_at > max(keyed.values())


def test_curses_first_page_keeps_the_choices_and_pages_the_caveat(monkeypatch):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _method_wizard()
    first = " ".join(_curses_text(wiz, 25, 80).split())
    for spec in METHODS.values():
        assert spec.title in first
    assert "checks only storage" not in first
    wiz.wants_shutdown = False
    tall = " ".join(_curses_text(wiz, 80, 120).split())
    assert C.EVERYDAY_LIMITS in tall
    assert tall.index(C.EVERYDAY_LIMITS) > tall.index(METHODS[MethodId.QUICK_ZERO].title)


def test_gtk_source_puts_the_caveat_in_a_named_expander():
    # Read as text: gi (GTK) is not importable everywhere the suite runs.
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("# #160:"):]
    block = block[: block.index("self.button(storage_limits.BUTTON")]
    assert "Gtk.Expander.new(C.BTN_MORE)" in block
    assert "set_expanded(False)" in block
    assert 'set_name(f"{C.BTN_MORE}: {note_spec.title}")' in block
    assert "self.label(note" not in block


def test_preview_keeps_the_caveat_in_the_opened_details_only():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    script = inline_script(html)
    method = script[script.index('} else if (screen === "method")'):]
    method = method[: method.index("renderHint(P.hints.method)")]
    details = method[method.index('class="methoddetails"'):]
    assert "${m.limits ?" in details
    # Every use of the note is inside the details, which render only when open.
    assert method.count("${m.limits") == details.count("${m.limits") == 2
    assert re.search(r"class=\"methoddetails\">\$\{open \?", method)


@pytest.fixture
def method_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size, text_size="standard"):
        _needs_display()
        wiz = _method_wizard()
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


def _shown(app):
    out = []

    def visit(w):
        if w.winfo_class() == "Label" and w.winfo_ismapped():
            out.append(str(w.cget("text")))
        for child in w.winfo_children():
            visit(child)

    visit(app._body)
    return out


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((1280, 820), "large")])
def test_tk_caveat_is_off_the_card_until_show_more(method_app, size, text_size):
    wiz, app = method_app(size, text_size)
    assert C.EVERYDAY_LIMITS not in _shown(app)
    app._method_more_buttons[MethodId.EVERYDAY]._command()
    for _ in range(8):
        app.root.update()
    assert C.EVERYDAY_LIMITS in _shown(app)
    assert wiz.screen == Screen.METHOD and wiz.method == MethodId.EVERYDAY
