# SPDX-License-Identifier: GPL-3.0-or-later
"""#174: footer key hints collapse into one "Keyboard shortcuts" item.

Chosen over "hints after the first key press": the footer keeps one height
(no row appears under the pointer mid-screen) and is two rows on every
screen — tools, then actions. The screen's keys are one step away: the
Keyboard shortcuts item (Tab-reachable, beside Help & settings) opens the
shortcuts page with them as key-caps; F10 reaches the same page through
Help & settings; GTK/Orca has them in its menu popover; curses keeps its
key lines (keys are its only input). Fake disks only.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from preview_page import inline_script


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _at(name, text_size="standard"):
    if name == "done":
        from test_result_presentations import CASES, case_evidence

        wiz, _ev, _log = case_evidence(next(c for c in CASES if c[0] == "verified"))
        wiz.text_size = text_size
        return wiz
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.text_size = text_size
    wiz.skip_intro()
    if name == "owner":
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if name == "pick":
        return wiz
    wiz.select_disk("/dev/sda")
    wiz.continue_pick()
    if name == "confirm":
        return wiz
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    if name == "method":
        return wiz
    wiz.continue_method()
    if name == "working":
        wiz.screen = Screen.WORKING
    return wiz


def _tk(wiz, size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+20+20")
    app.root.focus_force()
    app._draw()
    for _ in range(8):
        app.root.update()
    return app


def _footer_rows(app):
    """Rows of the footer: each tools line, each note line, the actions."""
    from beamo_wipe.ui.tk_wizard import _Button

    bands = []

    def visit(w):
        if w.winfo_ismapped() and (isinstance(w, _Button) or w.winfo_class() == "Label"):
            top, bottom = w.winfo_rooty(), w.winfo_rooty() + w.winfo_height()
            for band in bands:
                if top < band[1] and bottom > band[0]:  # overlaps: same row
                    band[0], band[1] = min(band[0], top), max(band[1], bottom)
                    break
            else:
                bands.append([top, bottom])
        for child in w.winfo_children():
            visit(child)

    visit(app._footer)
    return len(bands)


@pytest.mark.parametrize("name", ["owner", "pick", "confirm", "method", "last", "working", "done"])
@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "extra"),
                                            ((1280, 820), "large")])
def test_footer_is_two_rows_with_the_shortcuts_item(name, size, text_size):
    if name == "last" and size == (800, 600) and text_size == "extra":
        pytest.skip("known Windows Tk idle hang at 800x600 Extra large on Review (BW-162)")
    app = _tk(_at(name, text_size), size)
    try:
        assert app._hint is None
        assert _footer_rows(app) <= 2
        assert app._shortcuts_button.winfo_ismapped()
        assert app._shortcuts_button.winfo_rooty() == app._help_button.winfo_rooty()
    finally:
        app._teardown()


def test_shortcuts_item_opens_the_screens_keys_and_closes_back_to_it():
    from beamo_wipe.ui.tk_wizard import _Box

    wiz = _at("pick")
    app = _tk(wiz, (1280, 820))
    try:
        before = (wiz.screen, wiz.selected)
        app._shortcuts_button._command()
        for _ in range(4):
            app.root.update()
        assert app._help_open and app._help_view == "shortcuts"
        hint = [w for w in _walk(app._help_popup) if getattr(w, "_beamo_shortcuts_hint", False)]
        (box,) = hint
        texts = " ".join(str(w.cget("text")) for w in _walk(box) if w.winfo_class() == "Label")
        for word in ("Click a disk", "reviews this disk", "goes back"):
            assert word in texts
        assert any(isinstance(w, _Box) for w in _walk(box))  # key-caps
        assert (wiz.screen, wiz.selected) == before
        app._on_escape()
        app.root.update()
        assert not app._help_open
        assert getattr(app.root.focus_lastfor(), "_beamo_shortcuts", False)
        assert (wiz.screen, wiz.selected) == before
    finally:
        app._teardown()


def test_done_note_sits_in_the_action_row_when_the_tools_line_is_full():
    app = _tk(_at("done", "extra"), (800, 600))
    try:
        notes = [w for w in _walk(app._footer) if getattr(w, "_beamo_footer_note", False)]
        (note,) = notes
        assert str(note.cget("text")) in (C.ANOTHER_HINT, app.w.done_actions_reason)
        assert _footer_rows(app) <= 2
    finally:
        app._teardown()


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


@pytest.mark.parametrize("size,text_size,keys", [((800, 600), "extra", False),
                                                  ((1280, 820), "standard", True)])
def test_tools_drop_key_names_only_when_the_line_is_full(size, text_size, keys):
    """Linux 72 DPI (2026-11-08): at 800x600 Extra large the full tools line
    ("Check disks again (F5)", "Screen-reader view (F8)") wrapped into a
    third footer row. The tools then drop their key names; the Keyboard
    shortcuts page beside them still names F5 and F8. Roomy windows keep
    the key names. Every tool stays in the footer either way."""
    import sys

    from beamo_wipe.ui.tk_wizard import _Button

    if not keys and not sys.platform.startswith("linux"):
        pytest.skip("measured with the live image's Linux fonts at 72 DPI")
    app = _tk(_at("confirm", text_size), size)
    try:
        tools = [str(b.itemcget(b._label, "text")) for b in _walk(app._footer)
                 if isinstance(b, _Button) and b._variant == "quiet" and b.winfo_ismapped()]
        refresh = C.BTN_REFRESH_UTILITY if keys else C.BTN_REFRESH_UTILITY.replace(" (F5)", "")
        assert tools[:3] == [C.MENU_TITLE, C.MENU_SHORTCUTS, refresh]
        if sys.platform.startswith("linux"):
            reader = C.SCREEN_READER_VIEW if keys else C.SCREEN_READER_VIEW.replace(" (F8)", "")
            assert tools[3:] == [reader]
        assert all(("(F" in text) == keys for text in tools[2:])
        lines = app._help_shortcut_lines()
        assert C.MENU_SHORTCUTS_REFRESH in lines
        assert "F5" in C.MENU_SHORTCUTS_REFRESH
        if sys.platform.startswith("linux"):
            assert C.MENU_SHORTCUTS_READER in lines and "F8" in C.MENU_SHORTCUTS_READER
        assert _footer_rows(app) <= 2
    finally:
        app._teardown()


def test_web_preview_has_the_shortcuts_item_and_no_hint_row():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert ".assist .fhint { display: none; }" in html
    assert 'shortcuts.id = "shortcuts-button"' in html


def test_web_preview_shortcuts_logic_in_node():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    from beamo_wipe.gallery import gallery_html

    script = inline_script(gallery_html())
    start = script.index("let helpOpen = false")
    end = script.index("function renderHelpTrigger", start)
    program = """
const P = {helpMenu: {states: {pick: []}}, textSizes: [{id: 'standard', label: 'Standard'}]};
let screen = 'pick', textSize = 'standard', soundsOn = false, draws = 0;
let keyboardFrom = null, reportHelpFrom = 'owner';
let focused = '';
const document = {getElementById(id) { return {focus() { focused = id; }}; }};
function draw() { draws += 1; }
""" + script[start:end] + """
openShortcuts();
if (!helpOpen || helpView !== 'shortcuts' || !helpDirect || screen !== 'pick') throw Error('open');
closeHelp();
if (helpOpen || helpDirect || focused !== 'shortcuts-button') throw Error('close: ' + focused);
"""
    result = subprocess.run([node], input=program, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
