# SPDX-License-Identifier: GPL-3.0-or-later
"""#155: Confirm's keyboard line appears only after a wrong entry.

Hidden by default. After a wrong entry (a complete entry that does not match,
or Enter/Continue on a non-matching one) Confirm shows "Not matching? Check
your keyboard layout (currently QWERTY (US))." with Change. Changing the
layout from Confirm keeps the owner tick and the chosen disk (nothing is
authorized before Method), never changes the token, and clears only an entry
that does not match. Every later gate still applies. Fake disks only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C, lang
from beamo_wipe.keyboard import APPLY_FAILED, ApplyResult
from beamo_wipe.models import Screen
from beamo_wipe.wizard import make_demo_wizard

HINT_EN = "Not matching? Check your keyboard layout (currently QWERTY (US))."


class _Apply:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def __call__(self, layout_id, **_kw):
        self.calls.append(layout_id)
        return ApplyResult(self.ok, "" if self.ok else APPLY_FAILED, layout_id)


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _confirm(applier=None):
    wiz = make_demo_wizard()
    wiz._apply_keyboard = applier or _Apply()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(wiz.selectable[0].path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    return wiz


def _wrong(token):
    return "".join("X" if ch.upper() != "X" else "Y" for ch in token)


# -- when the hint shows --------------------------------------------------------


def test_hidden_until_a_wrong_entry_then_hidden_when_it_matches():
    wiz = _confirm()
    token = wiz.confirm.token
    assert not wiz.confirm_layout_hint
    for i in range(1, len(token)):
        wiz.set_confirm_input(token[:i])  # still typing the right characters
        assert not wiz.confirm_layout_hint
    wiz.set_confirm_input(_wrong(token))  # complete and wrong
    assert wiz.confirm_layout_hint
    wiz.set_confirm_input(_wrong(token)[:1])  # editing keeps the help
    assert wiz.confirm_layout_hint
    wiz.set_confirm_input(token)  # matches: no longer needed
    assert not wiz.confirm_layout_hint
    wiz.set_confirm_input("")
    assert wiz.confirm_layout_hint  # once seen, it stays for this visit


def test_enter_on_a_short_wrong_entry_counts_and_never_advances():
    wiz = _confirm()
    wiz.continue_confirm()  # empty entry: not a wrong entry
    assert not wiz.confirm_layout_hint and wiz.screen == Screen.CONFIRM
    wiz.set_confirm_input("Z")
    assert not wiz.confirm_layout_hint
    wiz.continue_confirm()
    assert wiz.confirm_layout_hint and wiz.screen == Screen.CONFIRM
    assert not wiz.token_ok and wiz._authorized_operation is None


def test_a_new_confirm_visit_starts_hidden():
    wiz = _confirm()
    wiz.set_confirm_input(_wrong(wiz.confirm.token))
    assert wiz.confirm_layout_hint
    wiz.back()
    assert wiz.screen == Screen.PICK
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM and not wiz.confirm_layout_hint


def test_hint_copy_names_the_current_layout():
    wiz = _confirm()
    from beamo_wipe import keyboard

    assert C.CONFIRM_LAYOUT_HINT.format(layout=keyboard.LAYOUTS[wiz.keyboard_layout].title) == HINT_EN
    assert C.CONFIRM_LAYOUT_CHANGE == "Change"
    assert not hasattr(C, "CONFIRM_KEYBOARD_LINE")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_language_has_the_hint(code):
    import string

    def get(key):
        return getattr(C, key) if code == "en" else lang.translated(code, "copy", key)

    fields = {n for _, n, _, _ in string.Formatter().parse(get("CONFIRM_LAYOUT_HINT")) if n}
    assert fields == {"layout"}
    assert get("CONFIRM_LAYOUT_CHANGE").strip()
    assert "F2" in get("CON_CONFIRM_LAYOUT_KEY")


# -- changing the layout from Confirm --------------------------------------------


def test_layout_change_from_confirm_keeps_owner_disk_and_token_and_clears_a_wrong_entry():
    applier = _Apply()
    wiz = _confirm(applier)
    token, path = wiz.confirm.token, wiz.selected.path
    wiz.set_confirm_input(_wrong(token))
    assert wiz.confirm_layout_hint
    wiz.open_keyboard()
    assert wiz.screen == Screen.KEYBOARD
    assert wiz.set_keyboard_layout("fr") and applier.calls == ["fr"]
    assert wiz.owner_ok and wiz.selected.path == path
    assert wiz.confirm.token == token  # the token is the disk's, not the layout's
    assert wiz.confirm_input == ""  # typed with the old layout
    assert wiz._authorized_operation is None and wiz._erase_until is None
    wiz.accept_keyboard()
    assert wiz.screen == Screen.CONFIRM
    assert not wiz.confirm_layout_hint  # the box is empty again
    # Every gate after Confirm still applies.
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM
    wiz.set_confirm_input(token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    assert not wiz.erase_enabled and not wiz.runner.started


def test_esc_from_the_layout_screen_returns_to_confirm():
    wiz = _confirm()
    wiz.set_confirm_input(_wrong(wiz.confirm.token))
    wiz.open_keyboard()
    assert wiz.set_keyboard_layout("de")
    wiz.back()
    assert wiz.screen == Screen.CONFIRM and wiz.owner_ok


def test_a_failed_layout_change_changes_nothing():
    wiz = _confirm(_Apply(ok=False))
    wrong = _wrong(wiz.confirm.token)
    wiz.set_confirm_input(wrong)
    wiz.open_keyboard()
    assert not wiz.set_keyboard_layout("fr")
    assert wiz.keyboard_layout == "us"
    assert wiz.confirm_input == wrong and wiz.owner_ok and wiz.selected is not None


def test_a_change_from_later_screens_still_starts_over():
    for later in ("method", "last"):
        wiz = _confirm()
        wiz.set_confirm_input(wiz.confirm.token)
        wiz.continue_confirm()
        if later == "last":
            wiz.continue_method()
            assert wiz.screen == Screen.LAST_CHANCE
        wiz.open_keyboard()
        assert wiz.set_keyboard_layout("fr")
        assert not wiz.owner_ok and wiz.selected is None and wiz.confirm_input == ""
        assert wiz._authorized_operation is None and wiz._erase_until is None


# -- views -----------------------------------------------------------------------


def test_plain_console_shows_the_hint_after_a_wrong_answer(monkeypatch):
    from beamo_wipe.ui.console_wizard import _plain_loop

    wiz = _confirm()
    answers = iter([_wrong(wiz.confirm.token)])
    printed = []
    rounds = []

    def fake_input(_prompt=""):
        rounds.append(list(printed))
        try:
            return next(answers)
        except StopIteration:
            wiz.shutdown()
            return ""

    monkeypatch.setattr("builtins.print", lambda *a, **_k: printed.append(" ".join(map(str, a))))
    monkeypatch.setattr("builtins.input", fake_input)
    _plain_loop(wiz)
    assert HINT_EN not in "\n".join(rounds[0])
    assert HINT_EN in "\n".join(rounds[1])
    assert C.CON_KEYBOARD in "\n".join(rounds[1])  # K changes the layout
    assert wiz.screen != Screen.METHOD


def test_curses_confirm_shows_the_hint_and_f2_opens_the_layouts(monkeypatch):
    import curses

    from beamo_wipe.ui import console_wizard as console

    wiz = _confirm()
    token = wiz.confirm.token
    painted = []
    keys = iter([*(ord(c) for c in _wrong(token)), 10, -1, curses.KEY_F2])

    class Terminal:
        def getmaxyx(self):
            return 24, 80

        def keypad(self, *_a):
            pass

        def nodelay(self, *_a):
            pass

        def timeout(self, *_a):
            pass

        def erase(self):
            pass

        def addstr(self, *args):
            painted.append(str(args[2]) if len(args) > 2 else "")

        def refresh(self):
            pass

        def getch(self):
            try:
                return next(keys)
            except StopIteration:
                wiz.wants_shutdown = True
                return -1

    now = [0.0]

    def monotonic():
        now[0] += 1.0
        return now[0]

    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_a: None)
    monkeypatch.setattr(console, "_curses_opt", lambda *_a: None)
    monkeypatch.setattr(console.time, "sleep", lambda *_a: None)
    monkeypatch.setattr(console.time, "monotonic", monotonic)
    assert console._loop(Terminal(), wiz) == 0
    text = "\n".join(painted)
    assert "Not matching? Check your keyboard layout" in text
    assert C.CON_CONFIRM_LAYOUT_KEY in text
    assert wiz.screen == Screen.KEYBOARD  # F2 opened the layouts
    assert wiz.owner_ok and wiz.selected is not None


def test_gtk_source_hides_the_hint_until_a_wrong_entry():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/accessible_wizard.py").read_text(
        encoding="utf-8")
    block = source[source.index("elif screen == Screen.CONFIRM:"):]
    block = block[:block.index("elif screen == Screen.METHOD:")]
    assert "CONFIRM_KEYBOARD_LINE" not in block
    assert "C.CONFIRM_LAYOUT_HINT.format(" in block and "focusable=True" in block
    assert "self.button(C.CONFIRM_LAYOUT_CHANGE, self.w.open_keyboard, in_body=True)" in block
    assert "widget.set_no_show_all(True)" in block
    assert 'entry.connect("activate", lambda _widget: self._token_entered(generation))' in block
    sync = source[source.index("    def _sync_layout_hint(self) -> None:"):]
    assert "shown = bool(self.w.confirm_layout_hint)" in sync[:400]


def test_preview_source_hides_the_hint_until_a_wrong_entry():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert "confirmKeyboard" not in html
    assert '<div class="layout-hint" id="layout-hint" hidden>' in html
    assert 'main.querySelector("#layout-hint").hidden = !(confirmMismatch && !tokenOk());' in html
    assert 'keyboardFrom = "confirm"; screen = "keyboard"' in html
    assert 'if (keyboardFrom === "confirm" && selected) {' in html


# -- Tk --------------------------------------------------------------------------


def _hint_frame(app):
    found = []

    def walk(widget):
        if getattr(widget, "_beamo_layout_hint", False):
            found.append(widget)
        for child in widget.winfo_children():
            walk(child)

    walk(app.root)
    assert len(found) == 1
    return found[0]


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "extra"),
                                            ((1280, 820), "standard")])
def test_tk_hint_hidden_then_shown_after_a_wrong_entry_and_change_works(size, text_size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _confirm()
    wiz.text_size = text_size
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        hint = _hint_frame(app)
        assert not hint.winfo_manager()  # hidden by default
        texts = []

        def walk(widget):
            try:
                texts.append(str(widget.cget("text")))
            except Exception:  # noqa: BLE001 - frames have no text
                pass
            for child in widget.winfo_children():
                walk(child)

        walk(app.root)
        assert not any("Keyboard:" in t for t in texts)
        token = wiz.confirm.token
        app._confirm_var.set(token[:-1])
        app.root.update()
        assert not hint.winfo_manager()
        app._confirm_var.set(_wrong(token))
        for _ in range(4):
            app.root.update()
        assert hint.winfo_manager() == "pack" and hint.winfo_ismapped()
        app._confirm_var.set(token)
        app.root.update()
        assert not hint.winfo_manager()
        app._confirm_var.set(_wrong(token))
        app.root.update()
        change = next(w for w in hint.winfo_children() if getattr(w, "_beamo_layout_change", False))
        change._command()
        for _ in range(4):
            app.root.update()
        assert wiz.screen == Screen.KEYBOARD and wiz.owner_ok
    finally:
        app._teardown()


def test_tk_enter_on_a_short_wrong_entry_shows_the_hint():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _confirm()
    app = TkWizard(wiz)
    try:
        app.root.geometry("800x600+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        app._confirm_var.set("Z")
        app.root.focus_force()
        app.root.update()
        (app.root.focus_get() or app.root).event_generate("<Return>", time=55_000)
        for _ in range(4):
            app.root.update()
        assert wiz.screen == Screen.CONFIRM
        assert _hint_frame(app).winfo_manager() == "pack"
    finally:
        app._teardown()
