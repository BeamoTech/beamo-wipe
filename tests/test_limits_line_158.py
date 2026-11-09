# SPDX-License-Identifier: GPL-3.0-or-later
"""#158 (owner decision B): one storage limits line under the disk.

On the Method screen the storage limits panel became one plain line between
the selected disk and the method cards, for every disk kind: SSD/NVMe "On
SSDs, overwriting may not reach every hidden area."; hard disk and unknown
keep the first sentence(s) of their existing notice. Show more puts the
full, unchanged notice in view. Owner, 2026-11-08 (option b): in Tk and the
web preview the "Storage limits (L)" button shows only with the line opened;
the L key opens the full page in both states and the Keyboard shortcuts list
names it on the Method screen. The line must be visible without scrolling at
800x600 and the largest text size (Ref #18). View only: nothing here chooses
a method. Fake disks only; nothing starts the engine.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe import storage_limits as limits
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import METHODS
from beamo_wipe.models import DiskKind, MethodId, Screen
from beamo_wipe.ui import console_wizard

ROOT = Path(__file__).resolve().parents[1]
ORDER = (MethodId.EVERYDAY, MethodId.EXTRA, MethodId.QUICK_ZERO)
KINDS = ("ssd", "hdd", "unknown")


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _method_wizard(kind="ssd"):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/nvme0n1" if kind == "ssd" else "/dev/sda")
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    if kind == "unknown":
        # Display only: the bound target is not re-chosen.
        wiz.selected = replace(wiz.selected, kind=DiskKind.UNKNOWN)
    want = {"ssd": (DiskKind.SSD, DiskKind.NVME), "hdd": (DiskKind.HDD,),
            "unknown": (DiskKind.UNKNOWN,)}[kind]
    assert wiz.selected.kind in want
    return wiz


# --- the line per disk kind ----------------------------------------------


def test_line_per_disk_kind():
    assert limits.line(DiskKind.SSD) == limits.line(DiskKind.NVME) == limits.LINE_SSD
    assert limits.LINE_SSD == "On SSDs, overwriting may not reach every hidden area."
    assert limits.line(DiskKind.HDD) == limits.LINE_HDD
    assert limits.line(DiskKind.UNKNOWN) == limits.LINE_UNKNOWN
    assert len({limits.LINE_SSD, limits.LINE_HDD, limits.LINE_UNKNOWN}) == 3


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_hdd_and_unknown_lines_keep_their_existing_wording(code):
    """Other disk kinds keep their notice's own opening words, not new copy."""
    lang.set_language(code)
    for kind in (DiskKind.HDD, DiskKind.UNKNOWN):
        line = limits.line(kind)
        assert limits.notice(kind).startswith(line), (code, kind, line)
    # The full notices (Show more, Storage limits page) are unchanged.
    assert limits.notice(DiskKind.SSD) == limits.NOTICE_SSD_LEAD + limits.OVERWRITE_LIMITS
    assert limits.notice(DiskKind.HDD) == limits.NOTICE_HDD_LEAD + limits.OVERWRITE_LIMITS


def test_l_shortcut_line_is_translated_and_names_the_key():
    english = C.MENU_SHORTCUTS_LIMITS
    assert english == "L opens the storage limits."
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        text = C.MENU_SHORTCUTS_LIMITS
        assert text.startswith("L ") and text.endswith(".")
        assert (text == english) == (code == "en"), code


def test_lines_are_translated_and_claim_nothing_new():
    english = {limits.LINE_SSD, limits.LINE_HDD, limits.LINE_UNKNOWN}
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        lines = [limits.line(k) for k in (DiskKind.SSD, DiskKind.HDD, DiskKind.UNKNOWN)]
        if code != "en":
            assert not english & set(lines), code
        for text in lines:
            assert text.endswith("."), (code, text)
            assert len(text) <= 90, (code, text)
            # docs/claims.md: a limitation only, never a promise or a certificate.
            assert not re.search(r"certif|dod|guarant|garant|100 ?%|nist", text, re.I), text


@pytest.mark.parametrize("kind", KINDS)
def test_wizard_storage_line_follows_the_selected_disk(kind):
    wiz = _method_wizard(kind)
    assert wiz.storage_line == limits.line(wiz.selected.kind)
    assert wiz.storage_notice == limits.notice(wiz.selected.kind)
    wiz.selected = None
    assert wiz.storage_line == limits.LINE_UNKNOWN


# --- Tk -----------------------------------------------------------------


def _settle(app, n=8):
    for _ in range(n):
        app.root.update()


def _walk(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(_walk(child))
    return out


@pytest.fixture
def method_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size=(800, 600), *, kind="ssd", text_size="standard"):
        _needs_display()
        wiz = _method_wizard(kind)
        wiz.text_size = text_size
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        _settle(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _button_texts(row):
    from beamo_wipe.ui.tk_wizard import _Button

    return [w.itemcget(w._label, "text") for w in row.winfo_children() if isinstance(w, _Button)]


def _press_l(app):
    assert app._on_key(SimpleNamespace(keysym="l", char="l")) == "break"
    _settle(app)


def _line_label(app):
    (label,) = [w for w in _walk(app._body) if getattr(w, "_beamo_limits_line", False)]
    return label


def _card_tops(app):
    tops = {}
    for w in _walk(app._body):
        method = getattr(w, "_beamo_method_time", None)
        if method is not None:
            box = w
            while not hasattr(box, "inner"):
                box = box.master
            tops[method] = box.winfo_rooty()
    return tops


def _in_view(app, widget):
    top, bottom = app._body.winfo_rooty() - 1, app._footer.winfo_rooty() + 1
    return (widget.winfo_ismapped() and widget.winfo_rooty() >= top
            and widget.winfo_rooty() + widget.winfo_height() <= bottom)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("size,text_size", [
    ((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
    ((1280, 820), "standard"),
])
def test_tk_line_sits_between_disk_and_cards_and_is_above_the_fold(
    method_app, kind, size, text_size
):
    wiz, app = method_app(size, kind=kind, text_size=text_size)
    label = _line_label(app)
    assert str(label.cget("text")) == f"{C.SEVERITY_LIMITS}: {wiz.storage_line}"
    # Not scrolled, and the whole line is above the footer (Ref #18).
    if app._body_canvas is not None:
        assert app._body_canvas.canvasy(0) == 0
    assert _in_view(app, label), (label.winfo_rooty(), app._footer.winfo_rooty())
    more = app._limits_more_button
    assert more is not None and _in_view(app, more)
    # Closed: Show more only; Storage limits (L) waits for the opened line.
    assert app._limits_pages_button is None
    assert limits.BUTTON not in _button_texts(more.master)
    # Order: disk summary (serial shown) above the line, cards below it.
    serial = [w for w in _walk(app._body) if w.winfo_class() == "Label"
              and str(w.cget("text")) == wiz.selected.serial]
    assert serial and serial[0].winfo_rooty() < label.winfo_rooty()
    tops = _card_tops(app)
    assert list(tops) == list(ORDER)
    assert label.winfo_rooty() + label.winfo_height() <= min(tops.values())
    # Closed, the long notice is not repeated on the screen.
    texts = [str(w.cget("text")) for w in _walk(app._body) if w.winfo_class() == "Label"]
    assert not any(limits.OVERWRITE_LIMITS in t for t in texts)
    assert not wiz.runner.started


@pytest.mark.parametrize("kind", KINDS)
def test_tk_show_more_shows_the_full_notice_and_never_chooses(method_app, kind):
    wiz, app = method_app((800, 600), kind=kind)
    app.root.focus_force()
    _settle(app)
    wiz.set_method(MethodId.EXTRA)
    app._draw()
    _settle(app)
    app._limits_more_button._command()
    _settle(app)
    label = _line_label(app)
    assert str(label.cget("text")) == f"{C.SEVERITY_LIMITS}: {wiz.storage_notice}"
    toggle = app._limits_more_button
    assert toggle.itemcget(toggle._label, "text") == C.BTN_LESS
    assert app.root.focus_lastfor() is toggle
    assert _in_view(app, label)
    assert wiz.method == MethodId.EXTRA and wiz.screen == Screen.METHOD
    # Show less returns to the one line.
    toggle._command()
    _settle(app)
    assert str(_line_label(app).cget("text")) == f"{C.SEVERITY_LIMITS}: {wiz.storage_line}"
    assert wiz.method == MethodId.EXTRA


@pytest.mark.parametrize("text_size", ["standard", "extra"])
def test_tk_storage_limits_button_shows_when_open_and_opens_the_full_page(method_app, text_size):
    wiz, app = method_app((800, 600), text_size=text_size)
    assert app._limits_pages_button is None
    app._limits_more_button._command()
    _settle(app)
    pages = app._limits_pages_button
    assert pages is not None and pages.itemcget(pages._label, "text") == limits.BUTTON
    assert _button_texts(app._limits_more_button.master) == [limits.BUTTON, C.BTN_LESS]
    assert _in_view(app, pages)
    pages._command()
    _settle(app)
    assert wiz.screen == Screen.LIMITS
    assert not wiz.runner.started
    # Show less hides it again.
    wiz.back()
    app._draw()
    _settle(app)
    assert wiz.screen == Screen.METHOD
    app._limits_more_button._command()
    _settle(app)
    assert app._limits_pages_button is None


@pytest.mark.parametrize("opened", [False, True], ids=["closed", "open"])
def test_tk_l_key_opens_the_full_page_in_both_states(method_app, opened):
    wiz, app = method_app((800, 600))
    if opened:
        app._limits_more_button._command()
        _settle(app)
    assert (app._limits_pages_button is not None) == opened
    _press_l(app)
    assert wiz.screen == Screen.LIMITS
    assert not wiz.runner.started


def test_tk_shortcuts_list_names_the_l_key_on_the_method_screen_only(method_app):
    wiz, app = method_app((800, 600))
    assert C.MENU_SHORTCUTS_LIMITS in app._help_shortcut_lines()
    wiz.back()
    app._draw()
    _settle(app)
    assert wiz.screen != Screen.METHOD
    assert C.MENU_SHORTCUTS_LIMITS not in app._help_shortcut_lines()


@pytest.mark.parametrize("kind", ["ssd", "hdd"])
@pytest.mark.parametrize("size,text_size", [
    ((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
    ((1280, 820), "standard"), ((1280, 820), "large"), ((1280, 820), "extra"),
])
def test_tk_line_does_not_clip_open_or_closed(method_app, size, text_size, kind):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    _wiz, app = method_app(size, kind=kind, text_size=text_size)
    assert _clipping_problems(app) == []
    assert not _off_window_problems(app)
    app._limits_more_button._command()
    _settle(app)
    assert _clipping_problems(app) == []


# --- GTK accessible view at runtime (Linux; skipped without gi) ----------


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_gtk_line_and_every_choice_fit_above_the_footer_at_800x600(code, kind):
    """#158: the line sits before the radios and all three stay above the
    footer at 800x600 in every language and disk kind (preview stripe on,
    the tightest case); the full notice stays reachable under Show more."""
    pytest.importorskip("gi")
    from test_accessible_fit_20261027 import _to_method, _window_y, _wizard
    from test_accessible_runtime import drain, wait_for_window_size, widgets

    from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk

    wizard = _wizard(code, preview=True)
    _to_method(wizard, "/dev/nvme0n1" if kind == "ssd" else "/dev/sda")
    if kind == "unknown":
        wizard.selected = replace(wizard.selected, kind=DiskKind.UNKNOWN)
    app = AccessibleWizard(wizard)
    try:
        app.window.resize(800, 600)
        wait_for_window_size(app.window, (800, 600))
        drain()
        footer = _window_y(app, app.footer)
        labels = [w for w in widgets(app.body) if isinstance(w, Gtk.Label)]
        (line,) = [w for w in labels if w.get_text() == f"{C.SEVERITY_LIMITS}: {wizard.storage_line}"]
        radios = [w for w in widgets(app.body) if isinstance(w, Gtk.RadioButton)]
        assert len(radios) == 3
        assert line.get_can_focus()
        assert _window_y(app, line) + line.get_allocated_height() <= _window_y(app, radios[0])
        for radio in radios:
            bottom = _window_y(app, radio) + radio.get_allocated_height()
            assert bottom <= footer, (code, kind, bottom, footer)
        (notice,) = [w for w in labels if w.get_text() == f"{C.SEVERITY_LIMITS}: {wizard.storage_notice}"]
        expander = notice.get_parent().get_parent()
        assert isinstance(expander, Gtk.Expander) and notice.get_can_focus()
        assert not expander.get_expanded()
        # Storage limits (L) is with the notice, not in the footer.
        pages = app.actions[limits.BUTTON]
        assert pages.get_parent() is notice.get_parent()
        assert pages not in list(widgets(app.utilities))
        # The button is the expander's content with the notice (as the #160
        # and #161 Show more expanders hold their notes), and opening it
        # never changes the screen or the method.
        assert expander.get_child() is pages.get_parent() and pages.get_sensitive()
        method = wizard.method
        expander.set_expanded(True)
        drain()
        assert expander.get_expanded()
        assert wizard.screen == Screen.METHOD and wizard.method == method
        assert not wizard.runner.started
    finally:
        app.close()
        drain()
        lang.set_language("en")


@pytest.mark.parametrize("opened", [False, True], ids=["closed", "open"])
def test_gtk_storage_limits_button_and_l_key_open_the_full_page(opened):
    pytest.importorskip("gi")
    from test_accessible_fit_20261027 import _to_method, _wizard
    from test_accessible_runtime import drain, wait_for_window_size

    from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk

    wizard = _wizard("en", preview=True)
    _to_method(wizard, "/dev/nvme0n1")
    app = AccessibleWizard(wizard)
    try:
        app.window.resize(800, 600)
        wait_for_window_size(app.window, (800, 600))
        drain()
        if opened:
            pages = app.actions[limits.BUTTON]
            pages.get_parent().get_parent().set_expanded(True)
            drain()
            pages.clicked()
        else:
            assert app._key_press(app.window, SimpleNamespace(keyval=Gdk.KEY_l))
        drain()
        assert wizard.screen == Screen.LIMITS
        assert not wizard.runner.started
    finally:
        app.close()
        drain()
        lang.set_language("en")


# --- GTK accessible view (read as text: gi is not importable everywhere) ---


def test_gtk_line_precedes_the_choices_and_the_notice_is_under_show_more():
    src = (ROOT / "src" / "beamo_wipe" / "ui" / "accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("elif screen == Screen.METHOD:"):]
    block = block[: block.index("elif screen == Screen.DISK_HELP:")]
    line = block.index('self.label(f"{C.SEVERITY_LIMITS}: {self.w.storage_line}", focusable=True)')
    radios = block.index("Gtk.RadioButton.new_with_label_from_widget")
    assert block.index("self.identity()") < line < radios
    expander = block.index('limits_more = Gtk.Expander.new(C.BTN_MORE)')
    assert radios < expander
    tail = block[expander:]
    assert "limits_more.set_expanded(False)" in tail
    assert 'set_name(f"{C.BTN_MORE}: {C.SEVERITY_LIMITS}")' in tail
    assert 'Gtk.Label(label=f"{C.SEVERITY_LIMITS}: {self.w.storage_notice}")' in tail
    assert "self.button(storage_limits.BUTTON, self.w.open_limits, in_body=True)" in tail
    # Option b in GTK too: the button lives with the opened notice, not in
    # the footer utilities.
    assert "limits_box.pack_start(pages" in tail and "limits_more.add(limits_box)" in tail
    assert "storage_limits.BUTTON, self.w.open_limits, utility=True" not in src
    shortcuts = src[src.index("def _help_shortcut_lines"):]
    shortcuts = shortcuts[: shortcuts.index("return lines")]
    assert "if self.w.screen == Screen.METHOD:" in shortcuts
    assert "C.MENU_SHORTCUTS_LIMITS" in shortcuts
    # The full notice is no longer a plain always-shown label.
    assert 'self.label(f"{C.SEVERITY_LIMITS}: {self.w.storage_notice}"' not in block


# --- consoles -----------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_plain_console_prints_the_line_first_and_the_notice_after(monkeypatch, capsys, kind):
    wiz = _method_wizard(kind)

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out.splitlines()
    line = out.index(f"{C.SEVERITY_LIMITS}: {wiz.storage_line}")
    notice = out.index(f"{C.SEVERITY_LIMITS}: {wiz.storage_notice}")
    firsts = [i for i, ln in enumerate(out)
              for m in ORDER if ln.startswith(f"{C.METHOD_CARDS[m]['key']} {METHODS[m].title}")]
    assert len(firsts) == 3
    assert line < min(firsts) and max(firsts) < notice
    assert out[notice + 1] == limits.BUTTON


@pytest.mark.parametrize("kind", KINDS)
def test_curses_first_page_has_the_line_before_every_choice(monkeypatch, kind):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _method_wizard(kind)
    first = " ".join(_curses_text(wiz, 25, 80).split())
    line = " ".join(f"{C.SEVERITY_LIMITS}: {wiz.storage_line}".split())
    assert line in first
    for spec in METHODS.values():
        assert spec.title in first and first.index(line) < first.index(spec.title)
    wiz.wants_shutdown = False
    tall = " ".join(_curses_text(wiz, 80, 120).split())
    notice = " ".join(f"{C.SEVERITY_LIMITS}: {wiz.storage_notice}".split())
    assert notice in tall
    assert tall.index(notice) > tall.index(METHODS[MethodId.QUICK_ZERO].title)


# --- web preview --------------------------------------------------------


def _payload():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    match = re.search(r"const P = (\{.*?\});\n", html, re.S)
    assert match, "payload not found"
    return html, json.loads(match.group(1))


def test_preview_carries_the_line_per_disk_and_a_view_only_show_more():
    html, data = _payload()
    assert data["limitsLineSsd"] == limits.LINE_SSD
    eligible = [d for d in data["disks"] if d["eligible"]]
    assert {d["kind"] for d in eligible} >= {"HDD"}
    assert {d["kind"] for d in eligible} & {"SSD", "NVMe"}
    for disk in eligible:
        kind = DiskKind(disk["kind"])
        assert disk["storageLine"] == limits.line(kind)
        assert disk["storageNotice"] == limits.notice(kind)
    (script,) = re.findall(r"<script>(.*?)</script>", html, re.S)
    method = script[script.index('} else if (screen === "method")'):]
    method = method[: method.index("renderHint(P.hints.method)")]
    # Between the disk summary and the cards.
    page = method[method.index("let html = "):]
    assert page.index("summaryCard(selected)") < page.index("${limitsLine()}") < page.index('<div class="cz">')
    assert 'id="limits-more" aria-expanded="${limitsMore}"' in method
    assert "selected.storageNotice" in method and "selected.storageLine" in method
    # Storage limits (L) only with the line opened (owner, 2026-11-08).
    assert re.search(r'\$\{limitsMore \? `<button type="button" id="limits" class="linkbtn"', method)
    assert 'main.querySelector("#limits")?.addEventListener("click"' in method
    # The L key does not depend on the line's state, and the shortcuts list
    # names it on the Method screen.
    assert 'if (screen === "method" && e.key.toLowerCase() === "l") {' in script
    assert 'if (screen === "method") lines.push(P.helpMenu.limits);' in script
    assert data["helpMenu"]["limits"] == C.MENU_SHORTCUTS_LIMITS
    # Returning from the full page focuses a control that exists.
    assert 'main.querySelector("#limits").focus()' not in script
    handler = method[method.index('querySelector("#limits-more")'):]
    handler = handler[: handler.index("};")]
    assert "limitsMore = !limitsMore" in handler and "method =" not in handler
