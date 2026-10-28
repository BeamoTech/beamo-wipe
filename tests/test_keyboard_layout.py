# SPDX-License-Identifier: GPL-3.0-or-later
"""Keyboard layout selector. Fake devices only; apply is injected."""

from __future__ import annotations

from pathlib import Path
import threading

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.diagnostic_report import create_report
from beamo_wipe.evidence import build_evidence
from beamo_wipe.keyboard import (
    APPLY_FAILED,
    DEFAULT_LAYOUT,
    GRAPHICAL_ONLY,
    LAYOUT_ORDER,
    LAYOUTS,
    TOOLS_MISSING,
    UNAVAILABLE,
    apply_layout,
    is_allowed,
)
from beamo_wipe.models import MethodId, Screen, WipeResult
from beamo_wipe.ui import console_wizard as console


ROOT = Path(__file__).resolve().parents[1]
KIOSK = ROOT / "packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk"
SERVICE = ROOT / "packaging/live/config/includes.chroot/etc/systemd/system/beamo-wipe-kiosk.service"
XORG = ROOT / "packaging/live/config/includes.chroot/etc/X11/xorg.conf.d/10-beamo.conf"
CONSOLE_KEYBOARD = ROOT / "packaging/live/config/includes.chroot/etc/default/keyboard"


class _Apply:
    def __init__(self, *, ok=True, message="", fail_ids=()):
        self.ok = ok
        self.message = message
        self.fail_ids = set(fail_ids)
        self.calls = []

    def __call__(self, layout_id, **_kw):
        from beamo_wipe.keyboard import ApplyResult

        self.calls.append(layout_id)
        if layout_id in self.fail_ids or not self.ok:
            return ApplyResult(False, self.message or APPLY_FAILED, layout_id)
        return ApplyResult(True, self.message, layout_id)


def _wiz(applier=None):
    wiz = make_demo_wizard()
    wiz._apply_keyboard = applier or _Apply()
    return wiz


def _authorized(wiz):
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    disk = sorted(wiz.selectable, key=lambda item: item.path)[0]
    wiz.select_disk(disk.path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    assert wiz.owner_ok
    assert wiz.confirm_input
    assert wiz.selected is not None


ALL_LAYOUTS = ("us", "fr", "de", "gb", "es", "latam", "it")


def test_allowlist_is_qwerty_azerty_qwertz():
    assert set(LAYOUTS) == set(ALL_LAYOUTS)
    assert LAYOUT_ORDER == ALL_LAYOUTS
    assert LAYOUTS["us"].family == "qwerty"
    assert LAYOUTS["fr"].family == "azerty"
    assert LAYOUTS["de"].family == "qwertz"
    for layout_id in ("gb", "es", "latam", "it"):
        assert LAYOUTS[layout_id].family == "qwerty"
        assert not LAYOUTS[layout_id].digits_need_shift
    assert LAYOUTS["fr"].dead_keys and LAYOUTS["de"].dead_keys
    assert LAYOUTS["es"].dead_keys and LAYOUTS["latam"].dead_keys and LAYOUTS["it"].dead_keys
    assert not LAYOUTS["us"].dead_keys
    assert not LAYOUTS["gb"].dead_keys
    assert LAYOUTS["fr"].digits_need_shift
    assert not is_allowed("dvorak")
    assert not is_allowed("us;fr")
    assert not is_allowed("us\nfr")


def test_apply_rejects_non_allowlisted_argv(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: f"/usr/bin/{name}")

    def fake_run(argv, **kw):
        raise AssertionError(argv)

    monkeypatch.setattr("beamo_wipe.keyboard.subprocess.run", fake_run)
    result = apply_layout("dvorak", graphical=True)
    assert not result.ok
    assert result.message == UNAVAILABLE


@pytest.mark.parametrize("layout_id", ALL_LAYOUTS)
def test_apply_uses_exact_allowlisted_argv(monkeypatch, layout_id):
    seen = []

    def which(name):
        return f"/usr/bin/{name}"

    def fake_run(argv, **kw):
        seen.append(tuple(argv))
        assert kw.get("shell") is False
        env = kw.get("env") or {}
        assert "LD_PRELOAD" not in env
        assert env.get("PATH") == "/usr/sbin:/usr/bin:/sbin:/bin"
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", which)
    monkeypatch.setattr("beamo_wipe.keyboard.subprocess.run", fake_run)
    result = apply_layout(layout_id, graphical=True)
    assert result.ok
    spec = LAYOUTS[layout_id]
    assert ("/usr/bin/setxkbmap", *spec.xkb_argv[1:]) in seen
    assert ("/usr/bin/loadkeys", spec.console_map) in seen


def test_missing_tools_are_visible(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda _name: None)
    result = apply_layout("fr", graphical=True)
    assert not result.ok
    assert result.message == TOOLS_MISSING


def test_graphical_change_warns_when_console_layout_tool_is_missing(monkeypatch):
    from beamo_wipe import keyboard

    monkeypatch.setattr(
        "beamo_wipe.safety.resolve_system_binary",
        lambda name: "/usr/bin/setxkbmap" if name == "setxkbmap" else None,
    )
    monkeypatch.setattr(keyboard, "_run_allowlisted", lambda _argv: True)

    result = apply_layout("fr", graphical=True)

    assert result.ok
    assert GRAPHICAL_ONLY in result.message
    assert result.layout_id == "fr"


def test_failed_apply_does_not_change_layout_or_clear_auth():
    applier = _Apply(ok=False, message=APPLY_FAILED)
    wiz = _wiz(applier)
    _authorized(wiz)
    assert not wiz.set_keyboard_layout("fr")
    assert wiz.keyboard_layout == "us"
    assert wiz.owner_ok
    assert wiz.selected is not None
    assert wiz.confirm_input
    assert wiz.screen == Screen.LAST_CHANCE
    assert APPLY_FAILED in (wiz.error or "")
    assert applier.calls == ["fr"]


@pytest.mark.parametrize("layout_id", ALL_LAYOUTS[1:])
def test_successful_layout_change_clears_full_confirmation_flow(layout_id):
    wiz = _wiz()
    _authorized(wiz)
    assert wiz.set_keyboard_layout(layout_id)
    assert wiz.keyboard_layout == layout_id
    assert not wiz.owner_ok
    assert wiz.confirm_input == ""
    assert wiz.selected is None
    assert wiz._authorized_operation is None
    assert wiz._erase_until is None
    assert wiz.screen == Screen.OWNER
    wiz.accept_what()
    assert wiz.screen == Screen.OWNER
    wiz.continue_owner()
    assert wiz.screen == Screen.OWNER


def test_layout_apply_and_erase_claim_cannot_cross(tmp_path, monkeypatch):
    from beamo_wipe.keyboard import ApplyResult

    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    started = threading.Event()
    release = threading.Event()
    confirmed = threading.Event()
    results = []

    def delayed_apply(layout_id):
        started.set()
        assert release.wait(3)
        return ApplyResult(True, "", layout_id)

    wiz = _wiz(delayed_apply)
    _authorized(wiz)
    wiz._erase_until = 0
    layout_thread = threading.Thread(target=lambda: results.append(wiz.set_keyboard_layout("fr")))
    claim_thread = threading.Thread(target=lambda: (wiz.confirm_erase(), confirmed.set()))
    layout_thread.start()
    try:
        assert started.wait(2)
        claim_thread.start()
        assert not confirmed.wait(0.1)
    finally:
        release.set()
        layout_thread.join(3)
        if claim_thread.ident is not None:
            claim_thread.join(3)
    assert results == [True]
    assert confirmed.is_set()
    assert wiz.keyboard_layout == "fr"
    assert wiz.screen == Screen.OWNER
    assert wiz.selected is None and not wiz.owner_ok
    assert wiz._wipe_request is None


def test_repeated_same_layout_does_not_invalidate():
    wiz = _wiz()
    _authorized(wiz)
    assert wiz.set_keyboard_layout("us")
    assert wiz.owner_ok
    assert wiz.screen == Screen.LAST_CHANCE
    assert wiz.set_keyboard_layout("fr")
    assert wiz.set_keyboard_layout("de")
    assert wiz.set_keyboard_layout("us")
    assert wiz.keyboard_layout == "us"
    assert not wiz.owner_ok
    assert wiz.screen == Screen.OWNER


def test_splash_then_keyboard_then_what():
    wiz = _wiz()
    assert wiz.screen == Screen.SPLASH
    assert wiz.keyboard_layout == DEFAULT_LAYOUT
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    wiz.set_keyboard_layout("fr")
    wiz.set_typing_check("azerty 123")
    assert wiz.typing_check == "azerty 123"
    wiz.accept_keyboard()
    assert wiz.screen == Screen.OWNER
    assert wiz.typing_check == ""
    assert wiz.keyboard_layout == "fr"


def test_typing_check_never_enters_evidence_or_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    wiz = _wiz()
    wiz.skip_splash()
    secret = "édeadkey-SECRET-99"
    wiz.set_typing_check(secret)
    assert secret in wiz.typing_check
    disk = sorted(wiz.selectable, key=lambda item: item.path)[0]
    result = WipeResult(True, 0, "completed", str(tmp_path / "nwipe.log"), "completed")
    ev = build_evidence(
        disk=disk,
        discovery=wiz.discovery,
        method=MethodId.EVERYDAY,
        request=None,
        result=result,
        started_at_wall="",
        ended_at_wall="",
        started_mono=0,
        ended_mono=1,
        argv=[],
        log_text="",
        interrupted=False,
        cancelled=False,
    )
    blob = str(ev)
    assert secret not in blob
    assert "édeadkey" not in blob
    report = create_report("discovery_failed", wiz.discovery, ui="console", session_started=0)
    assert secret.encode() not in report
    # Even a failed layout apply may log the allowlisted id, never the check text.
    wiz._apply_keyboard = _Apply(ok=False)
    wiz.set_keyboard_layout("fr")
    for path in tmp_path.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert secret not in text


def test_unavailable_layout_is_visible_and_rejected():
    wiz = _wiz()
    wiz.skip_splash()
    assert not wiz.set_keyboard_layout("dvorak")
    assert wiz.keyboard_layout == "us"
    assert UNAVAILABLE in (wiz.error or "")


def test_open_keyboard_from_later_screen_and_back_without_change():
    wiz = _wiz()
    _authorized(wiz)
    wiz.open_keyboard()
    assert wiz.screen == Screen.KEYBOARD
    wiz.set_typing_check("hello")
    wiz.back()
    assert wiz.screen == Screen.LAST_CHANCE
    assert wiz.owner_ok
    assert wiz.selected is not None
    assert wiz.typing_check == ""


def test_console_keyboard_and_plain_check_field(monkeypatch, capsys):
    wiz = _wiz()
    wiz.skip_splash()
    answers = iter(["2", "azerty", ""])

    def fake_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr("builtins.input", fake_input)
    console._plain_loop(wiz)
    text = capsys.readouterr().out
    assert C.TITLE_KEYBOARD in text
    assert "AZERTY" in text
    assert "QWERTZ" in text
    assert "dead keys" in text.lower()
    assert wiz.keyboard_layout == "fr"
    assert wiz.screen == Screen.OWNER
    assert "azerty" not in (wiz.typing_check or "")


def test_curses_keyboard_keeps_check_and_actions_on_80x24(monkeypatch):
    wiz = _wiz()
    wiz.skip_splash()
    rows = {}

    class Terminal:
        def getmaxyx(self):
            return 24, 80

        def addstr(self, y, x, text, attr=0):
            assert 0 <= y < 24
            assert len(text) < 80
            rows[y] = text

        def getch(self):
            wiz.wants_shutdown = True
            return -1

        def __getattr__(self, name):
            return lambda *a, **k: None

    monkeypatch.setattr(console.curses, "curs_set", lambda *a, **k: None)
    monkeypatch.setattr(console.curses, "use_default_colors", lambda *a, **k: None)
    console._loop(Terminal(), wiz)
    shown = " ".join(rows[y] for y in sorted(rows))
    assert C.TITLE_KEYBOARD.split()[0] in shown or "Check your keyboard" in shown or "QWERTY" in shown
    assert "QWERTY" in shown and "AZERTY" in shown and "QWERTZ" in shown
    assert "Enter continues" in shown or "1/2/3" in shown
    assert max(rows) < 24


def test_rendered_keyboard_screen_keeps_check_field_and_layouts(monkeypatch):
    from test_adaptive_layout import _texts, _buttons
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wiz()
    app = TkWizard(wiz)
    try:
        app.root.geometry("1280x820+40+40")
        wiz.skip_splash()
        app._draw()
        app.root.update_idletasks()
        app.root.update()
        shown = _texts(app.root)
        assert C.TITLE_KEYBOARD in shown
        assert "QWERTY" in shown and "AZERTY" in shown and "QWERTZ" in shown
        assert C.KEYBOARD_CHECK_LABEL in shown
        labels = [b.itemcget(b._label, "text") for b in _buttons(app)]
        assert C.BTN_CONTINUE in labels
        wiz.set_keyboard_layout("fr")
        app._draw()
        app.root.update()
        assert wiz.keyboard_layout == "fr"
        wiz.set_typing_check("azé 12")
        assert "azé 12" == wiz.typing_check
        wiz.accept_keyboard()
        app._draw()
        app.root.update()
        assert wiz.screen == Screen.OWNER
        assert wiz.typing_check == ""
    finally:
        app._teardown()


def test_kiosk_restart_returns_to_shipped_us_qwerty():
    service = SERVICE.read_text(encoding="utf-8")
    kiosk = KIOSK.read_text(encoding="utf-8")
    xorg = XORG.read_text(encoding="utf-8")
    default = CONSOLE_KEYBOARD.read_text(encoding="utf-8")
    assert "Restart=no" in service
    assert "setxkbmap" not in kiosk
    assert "loadkeys" not in kiosk
    assert 'Option "XkbLayout" "us"' in xorg
    assert "XKBLAYOUT=\"us\"" in default
    wiz = _wiz()
    wiz.skip_splash()
    wiz.set_keyboard_layout("fr")
    wiz.set_typing_check("secret-check")
    wiz.reset_for_preview()
    assert wiz.screen == Screen.SPLASH
    assert wiz.keyboard_layout == DEFAULT_LAYOUT
    assert wiz.typing_check == ""
    assert not wiz.owner_ok
    assert wiz.confirm_input == ""


def test_layout_names_match_debian_xkb_data_and_console_data():
    """XKB names exist in bookworm xkb-data (/usr/share/X11/xkb/symbols/<name>);
    console names exist in console-data (/usr/share/keymaps/i386/*/<name>.kmap.gz).
    scripts/qemu-verify.sh checks both against the built ISO."""
    expected = {
        "us": ("us", "us"),
        "fr": ("fr", "fr"),
        "de": ("de", "de"),
        "gb": ("gb", "uk"),
        "es": ("es", "es"),
        "latam": ("latam", "la-latin1"),
        "it": ("it", "it"),
    }
    assert {lid: (s.xkb_layout, s.console_map) for lid, s in LAYOUTS.items()} == expected
    for layout_id, spec in LAYOUTS.items():
        # _run_allowlisted looks setxkbmap argv up by layout id.
        assert spec.id == layout_id == spec.xkb_layout
        assert spec.xkb_argv == ("setxkbmap", "-layout", spec.xkb_layout, "-option", "")
        assert spec.console_argv == ("loadkeys", spec.console_map)
    # Digit shortcuts 1..N must stay single keys.
    assert 1 <= len(LAYOUT_ORDER) <= 9
    assert len(set(LAYOUT_ORDER)) == len(LAYOUT_ORDER)


def test_apply_rejects_console_map_names_as_layout_ids(monkeypatch):
    monkeypatch.setattr("beamo_wipe.safety.resolve_system_binary", lambda name: f"/usr/bin/{name}")

    def fake_run(argv, **kw):
        raise AssertionError(argv)

    monkeypatch.setattr("beamo_wipe.keyboard.subprocess.run", fake_run)
    for bogus in ("uk", "la-latin1", "latam;us", "es ", "ES", "it2"):
        assert not is_allowed(bogus)
        result = apply_layout(bogus, graphical=True)
        assert not result.ok and result.message == UNAVAILABLE


def test_every_layout_has_translated_title_and_note():
    from beamo_wipe import keyboard, lang

    english = {lid: (LAYOUTS[lid].title, LAYOUTS[lid].note) for lid in LAYOUT_ORDER}
    try:
        for code in ("fr", "de", "es", "it"):
            lang.set_language(code)
            for layout_id in LAYOUT_ORDER:
                spec = keyboard.LAYOUTS[layout_id]
                assert spec.note != english[layout_id][1], (code, layout_id)
                assert spec.title.split(" ", 1)[0] == english[layout_id][0].split(" ", 1)[0]
                assert spec.xkb_layout == LAYOUTS[layout_id].xkb_layout
                assert spec.console_map == LAYOUTS[layout_id].console_map
            assert keyboard.LIMITS.endswith(keyboard.SESSION_ONLY)
    finally:
        lang.set_language("en")


def test_keyboard_hints_name_every_layout_shortcut():
    from beamo_wipe import lang

    try:
        for code in ("en", "fr", "de", "es", "it"):
            lang.set_language(code)
            # The Tk check box has focus and takes digits, so the hint names
            # the keys that always work there, not 1-7.
            assert C.HINT_KEYBOARD.startswith("Up/Down"), code
            assert "1–" not in C.HINT_KEYBOARD, code
            # The curses screen keeps every digit for the typing check.
            assert C.CON_KEYBOARD_FOOTER.startswith("Left/Right"), code
    finally:
        lang.set_language("en")


@pytest.mark.parametrize("index,layout_id", list(enumerate(ALL_LAYOUTS, 1)))
def test_plain_console_digit_chooses_every_layout(monkeypatch, capsys, index, layout_id):
    wiz = _wiz()
    wiz.skip_splash()
    answers = iter([str(index), ""])

    def fake_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr("builtins.input", fake_input)
    console._plain_loop(wiz)
    text = capsys.readouterr().out
    for number, other in enumerate(LAYOUT_ORDER, 1):
        assert f" {number} {LAYOUTS[other].title}" in text
    assert wiz.keyboard_layout == layout_id
    assert wiz.screen == Screen.OWNER


@pytest.mark.parametrize("language", ["en", "es", "it"])
def test_curses_keyboard_pages_to_every_layout_at_80x24(monkeypatch, language):
    import curses

    from beamo_wipe import keyboard, lang

    wiz = _wiz()
    try:
        assert wiz.set_language(language)
        wiz.skip_splash()
        seen = []
        keys = iter([curses.KEY_DOWN] * 60)

        class Terminal:
            def getmaxyx(self):
                return 24, 80

            def addstr(self, y, x, text, attr=0):
                assert 0 <= y < 24
                assert len(text) < 80
                seen.append(text)

            def getch(self):
                try:
                    return next(keys)
                except StopIteration:
                    wiz.wants_shutdown = True
                    return -1

            def __getattr__(self, name):
                return lambda *a, **k: None

        monkeypatch.setattr(console.curses, "curs_set", lambda *a, **k: None)
        monkeypatch.setattr(console.curses, "use_default_colors", lambda *a, **k: None)
        console._loop(Terminal(), wiz)
        shown = "\n".join(seen)
        for layout_id in LAYOUT_ORDER:
            assert keyboard.LAYOUTS[layout_id].title in shown, layout_id
        for code in lang.LANGUAGE_ORDER:
            assert lang.LANGUAGE_NAMES[code] in shown
        assert C.CON_KEYBOARD_FOOTER in shown
        assert wiz.screen == Screen.KEYBOARD
    finally:
        wiz.set_language("en")


def test_curses_arrows_reach_every_layout_and_digits_stay_typeable(monkeypatch):
    wiz = _wiz()
    wiz.skip_splash()
    reached = [wiz.keyboard_layout]
    for _ in LAYOUT_ORDER:
        console._handle(wiz, console.curses.KEY_RIGHT)
        reached.append(wiz.keyboard_layout)
    assert reached == [*LAYOUT_ORDER, LAYOUT_ORDER[0]]
    console._handle(wiz, console.curses.KEY_LEFT)
    assert wiz.keyboard_layout == LAYOUT_ORDER[-1]
    console._handle(wiz, console.curses.KEY_RIGHT)
    assert wiz.keyboard_layout == LAYOUT_ORDER[0]
    # Every digit goes into the typing check and never switches layout.
    for digit in "0123456789":
        console._handle(wiz, ord(digit))
    assert wiz.keyboard_layout == LAYOUT_ORDER[0]
    assert wiz.typing_check == "0123456789"


@pytest.mark.parametrize("size", [(800, 600), (1024, 600), (1280, 720), (1600, 1000)])
@pytest.mark.parametrize("language", ["en", "fr", "de", "es", "it"])
def test_keyboard_screen_fits_and_reaches_every_layout(size, language):
    from test_adaptive_layout import _assert_actions_on_window, _buttons, _texts
    from test_tk_runtime import _needs_display

    from beamo_wipe import keyboard, lang
    from beamo_wipe.ui.layout import MIN_SIZE
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wiz()
    app = TkWizard(wiz)
    try:
        assert wiz.set_language(language)
        app.root.minsize(*MIN_SIZE)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app.root.update_idletasks()
        app.root.focus_force()
        wiz.skip_splash()
        app._draw()
        app.root.update()
        assert wiz.screen == Screen.KEYBOARD
        shown = _texts(app.root)
        for layout_id in LAYOUT_ORDER:
            assert keyboard.LAYOUTS[layout_id].title in shown, layout_id
        for code in lang.LANGUAGE_ORDER:
            assert lang.LANGUAGE_NAMES[code] in shown
        assert keyboard.LAYOUTS["us"].note in shown
        assert C.KEYBOARD_CHECK_LABEL in shown
        assert set(app._keyboard_layout_cards) == set(LAYOUT_ORDER)
        assert set(app._keyboard_language_cards) == set(lang.LANGUAGE_ORDER)
        # Footer Continue stays on the window; nothing clips at this size.
        _assert_actions_on_window(app)
        labels = [b.itemcget(b._label, "text") for b in _buttons(app) if b.winfo_ismapped()]
        assert C.BTN_CONTINUE in labels
        for index, layout_id in enumerate(LAYOUT_ORDER, 1):
            card = app._keyboard_layout_cards[layout_id]
            card.focus_set()
            app.root.update()
            canvas = app._body_canvas
            if canvas is not None:
                top = card.winfo_rooty() - canvas.winfo_rooty()
                assert top >= -2, (layout_id, top)
                assert top + card.winfo_height() <= canvas.winfo_height() + 2, layout_id
            app.root.event_generate("<KeyPress>", keysym=str(index))
            app.root.update()
            app.root.event_generate("<KeyRelease>", keysym=str(index))
            app.root.update()
            assert wiz.keyboard_layout == layout_id
            assert keyboard.LAYOUTS[layout_id].note in _texts(app.root)
            assert _clipping_free(app), layout_id
    finally:
        app._teardown()
        lang.set_language("en")


def _clipping_free(app) -> bool:
    from test_tk_runtime import _clipping_problems

    problems = _clipping_problems(app)
    assert problems == []
    return True


def _tk_keyboard(language="en", size=(1280, 720)):
    from test_tk_runtime import _needs_display

    from beamo_wipe.ui.layout import MIN_SIZE
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wiz()
    app = TkWizard(wiz)
    assert wiz.set_language(language)
    app.root.minsize(*MIN_SIZE)
    app.root.geometry(f"{size[0]}x{size[1]}+40+40")
    app.root.update_idletasks()
    app.root.focus_force()
    wiz.skip_splash()
    app._draw()
    app.root.update()
    assert wiz.screen == Screen.KEYBOARD
    return wiz, app


def _press(app, keysym):
    # A layout change redraws the screen, so the release goes to whatever
    # holds focus afterwards (a new check box).
    for event in ("<KeyPress>", "<KeyRelease>"):
        (app.root.focus_get() or app.root).event_generate(event, keysym=keysym)
        app.root.update()


def test_tk_up_down_choose_layouts_while_the_check_box_has_focus():
    import tkinter as tk

    from beamo_wipe import lang

    wiz, app = _tk_keyboard()
    try:
        assert isinstance(app.root.focus_get(), tk.Entry)
        reached = [wiz.keyboard_layout]
        for _ in LAYOUT_ORDER:
            _press(app, "Down")
            assert isinstance(app.root.focus_get(), tk.Entry)
            reached.append(wiz.keyboard_layout)
        assert reached == [*LAYOUT_ORDER, LAYOUT_ORDER[0]]
        _press(app, "Up")
        assert wiz.keyboard_layout == LAYOUT_ORDER[-1]
        # Digits still type into the check box and never switch layout.
        for digit in "123":
            _press(app, digit)
        assert wiz.keyboard_layout == LAYOUT_ORDER[-1]
        assert wiz.typing_check.endswith("123")
    finally:
        app._teardown()
        lang.set_language("en")


@pytest.mark.parametrize("language", ["en", "fr", "de", "es", "it"])
def test_tk_keyboard_hint_stays_inside_the_window_on_tall_screens(language):
    from beamo_wipe import lang

    wiz, app = _tk_keyboard(language, size=(1024, 740))
    try:
        hint = app._hint
        assert hint is not None and hint.winfo_ismapped()
        right = hint.winfo_rootx() + hint.winfo_reqwidth()
        assert right <= app.root.winfo_rootx() + app.root.winfo_width(), language
        assert _clipping_free(app)
    finally:
        app._teardown()
        lang.set_language("en")


@pytest.mark.parametrize("rows", [14, 16, 18, 20])
@pytest.mark.parametrize("language", ["en", "fr", "de", "es", "it"])
def test_curses_keyboard_reaches_every_layout_on_short_consoles(monkeypatch, language, rows):
    # The lead paragraphs alone fill a short console; they page with the
    # list so Down still reaches every layout and language.
    import curses

    from beamo_wipe import keyboard, lang

    wiz = _wiz()
    try:
        assert wiz.set_language(language)
        wiz.skip_splash()
        seen = []
        keys = iter([curses.KEY_DOWN] * 80)

        class Terminal:
            def getmaxyx(self):
                return rows, 80

            def addstr(self, y, x, text, attr=0):
                assert 0 <= y < rows
                assert len(text) < 80
                seen.append(text)

            def getch(self):
                try:
                    return next(keys)
                except StopIteration:
                    wiz.wants_shutdown = True
                    return -1

            def __getattr__(self, name):
                return lambda *a, **k: None

        monkeypatch.setattr(console.curses, "curs_set", lambda *a, **k: None)
        monkeypatch.setattr(console.curses, "use_default_colors", lambda *a, **k: None)
        console._loop(Terminal(), wiz)
        shown = "\n".join(seen)
        for layout_id in LAYOUT_ORDER:
            assert keyboard.LAYOUTS[layout_id].title in shown, layout_id
        for code in lang.LANGUAGE_ORDER:
            assert lang.LANGUAGE_NAMES[code] in shown
        assert wiz.screen == Screen.KEYBOARD
    finally:
        wiz.set_language("en")
