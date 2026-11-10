# SPDX-License-Identifier: GPL-3.0-or-later
"""#136: Check disks again cannot silently wipe out confirmations.

Not offered on What/Owner (no disk list yet); a normal action on Pick;
from Confirm, Method and Review (and Advanced/Limits) only through a
guarded dialog whose default is Cancel. Any rediscovery still clears every
confirmation exactly as before, and the automatic pre-launch rediscovery
and identity comparison are unchanged. Fake demo disks only.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import wizard as W
from beamo_wipe.methods import DEFAULT_METHOD
from beamo_wipe.models import Screen
from beamo_wipe.wizard import Wizard, make_demo_wizard

GUARDED = (Screen.CONFIRM, Screen.METHOD, Screen.LAST_CHANCE, Screen.ADVANCED, Screen.LIMITS)
NORMAL = (Screen.PICK, Screen.PICK_EMPTY, Screen.PICK_BLOCKED, Screen.DISK_HELP)


def _wizard() -> Wizard:
    wiz = make_demo_wizard()
    fresh = wiz.discovery
    wiz._rediscover = lambda: fresh
    return wiz


def _drive(wiz: Wizard, screen: Screen) -> Wizard:
    """Walk the real state machine (as the Tk tests do)."""
    wiz.skip_intro()
    if screen == Screen.WHAT:
        wiz.screen = Screen.WHAT  # the separate intro some flows still show
        return wiz
    wiz.accept_what()
    if screen == Screen.OWNER:
        wiz.set_owner(True)
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if screen == Screen.DISK_HELP:
        wiz.open_disk_help()
        return wiz
    if screen in (Screen.PICK_EMPTY, Screen.PICK_BLOCKED):
        wiz.screen = screen  # presentation states reached after discovery
        return wiz
    disk = sorted(wiz.selectable, key=lambda d: d.path)[0]
    wiz.select_disk(disk.path)
    if screen == Screen.PICK:
        return wiz
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    if screen == Screen.CONFIRM:
        return wiz
    wiz.continue_confirm()
    if screen == Screen.METHOD:
        return wiz
    if screen == Screen.ADVANCED:
        wiz.open_advanced()
        return wiz
    if screen == Screen.LIMITS:
        wiz.open_limits()
        return wiz
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


def _answers(wiz: Wizard) -> dict:
    return {
        "selected": wiz.selected,
        "owner_ok": wiz.owner_ok,
        "confirm_input": wiz.confirm_input,
        "method": wiz.method,
        "authorized": wiz._authorized_operation,
        "discovery": wiz.discovery,
    }


# --- Where it is offered -------------------------------------------------------------


@pytest.mark.parametrize("screen", [Screen.WHAT, Screen.OWNER])
def test_not_offered_before_there_is_a_disk_list(screen):
    wiz = _drive(_wizard(), screen)
    assert wiz.screen == screen
    assert not wiz.refresh_offered
    before = _answers(wiz)
    assert wiz.open_refresh_confirm() is False
    assert wiz.screen == screen and _answers(wiz) == before


@pytest.mark.parametrize("screen", NORMAL)
def test_pick_screens_keep_it_as_a_normal_action(screen):
    wiz = _drive(_wizard(), screen)
    assert wiz.refresh_offered
    assert not wiz.refresh_guarded
    assert wiz.open_refresh_confirm()
    assert wiz.screen == Screen.REFRESH_CONFIRM and not wiz.refresh_guarded


@pytest.mark.parametrize("screen", GUARDED)
def test_confirmation_screens_offer_it_only_through_the_guarded_dialog(screen):
    wiz = _drive(_wizard(), screen)
    assert wiz.screen == screen
    assert wiz.refresh_offered and wiz.refresh_guarded
    assert wiz.open_refresh_confirm()
    assert wiz.screen == Screen.REFRESH_CONFIRM and wiz.refresh_guarded


@pytest.mark.parametrize("screen", GUARDED + (Screen.REPORT_HELP,))
def test_no_direct_rescan_from_a_screen_holding_confirmations(screen):
    """Fail closed: nothing may start a scan around the dialog."""
    wiz = _drive(_wizard(), Screen.METHOD if screen == Screen.REPORT_HELP else screen)
    if screen == Screen.REPORT_HELP:
        wiz.open_report_help()
        assert wiz.screen == Screen.REPORT_HELP
    before = _answers(wiz)
    assert wiz.begin_refresh() is None
    assert wiz.refresh_disks() is False
    assert wiz.screen == screen
    assert _answers(wiz) == before


def test_report_help_from_owner_stays_direct():
    wiz = _drive(_wizard(), Screen.OWNER)
    wiz.open_report_help()
    assert wiz.screen == Screen.REPORT_HELP
    assert not wiz.refresh_guarded and not wiz.refresh_offered


def test_unknown_dialog_origin_fails_closed():
    wiz = _drive(_wizard(), Screen.PICK)
    wiz.open_refresh_confirm()
    wiz._refresh_confirm_from = None
    assert wiz.refresh_guarded


# --- Cancel keeps everything; accept clears exactly as before -------------------------


@pytest.mark.parametrize("screen", GUARDED)
def test_cancel_keeps_every_answer(screen):
    wiz = _drive(_wizard(), screen)
    before = _answers(wiz)
    wiz.open_refresh_confirm()
    wiz.back()  # Cancel / Esc / Enter on the default control
    assert wiz.screen == screen
    assert _answers(wiz) == before
    assert not wiz.refresh_then_reader


@pytest.mark.parametrize("screen", GUARDED)
def test_accepting_clears_exactly_what_a_pick_refresh_clears(screen):
    wiz = _drive(_wizard(), screen)
    assert wiz.selected is not None and wiz.owner_ok and wiz.confirm_input
    wiz.open_refresh_confirm()
    assert wiz.confirm_refresh()
    reference = _drive(_wizard(), Screen.PICK)
    reference.open_refresh_confirm()
    assert reference.confirm_refresh()
    for result in (wiz, reference):
        assert result.screen == Screen.OWNER
        assert result.selected is None
        assert result.owner_ok is False
        assert result.confirm_input == ""
        assert result.method == DEFAULT_METHOD
        assert result._erase_until is None
        assert result._authorized_operation is None
        assert result._refresh_confirm_from is None
        assert result.refresh_then_reader is False


def test_reader_switch_uses_the_same_guarded_dialog():
    wiz = _drive(_wizard(), Screen.LAST_CHANCE)
    before = _answers(wiz)
    assert wiz.open_refresh_confirm(then_reader=True)
    assert wiz.refresh_then_reader and wiz.refresh_guarded
    wiz.back()
    assert wiz.screen == Screen.LAST_CHANCE and _answers(wiz) == before
    assert not wiz.refresh_then_reader
    # then_reader cannot open the dialog where the action is not offered.
    owner = _drive(_wizard(), Screen.OWNER)
    assert owner.open_refresh_confirm(then_reader=True) is False


# --- Pre-launch rediscovery is unchanged -----------------------------------------------


def test_prelaunch_rediscovery_still_runs_from_review_and_rejects_changes(monkeypatch, tmp_path):
    from test_wizard_flow import _wiz

    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    wiz, clock = _wiz()
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    target = wiz.selectable[0]
    wiz.select_disk(target.path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    clock.add(5.0)
    mutated = replace(wiz.discovery.selectable[0], serial="CHANGED")
    fresh = type(wiz.discovery)(
        disks=wiz.discovery.disks,
        selectable=(mutated,) + wiz.discovery.selectable[1:],
        boot=wiz.discovery.boot,
        error=wiz.discovery.error,
        boot_identified=wiz.discovery.boot_identified,
    )
    calls = []
    wiz.dry_run = False
    wiz.preview = False
    wiz._rediscover = lambda: calls.append(1) or fresh
    # Review holds confirmations, so a manual rescan is guarded ...
    assert wiz.refresh_guarded and wiz.begin_refresh() is None
    # ... but the automatic pre-launch rediscovery is not a manual rescan.
    wiz.confirm_erase()
    assert calls, "pre-launch rediscovery must still run"
    assert wiz.screen == Screen.LAST_CHANCE
    assert not getattr(wiz.runner, "started", False)
    assert "identity" in (wiz.error or "").lower()


def test_prelaunch_code_is_untouched_by_the_guard():
    import inspect

    source = inspect.getsource(Wizard.confirm_erase)
    assert "begin_refresh" not in source and "refresh_guarded" not in source
    assert W.REFRESH_DIRECT_SCREENS.isdisjoint(set(GUARDED))


# --- Copy ------------------------------------------------------------------------------


def test_dialog_copy_says_what_is_cleared_and_where_it_starts():
    assert C.TITLE_REFRESH == "Check disks again?"
    lead = C.REFRESH_GUARD_LEAD
    # #181: two sentences; the meaning is unchanged.
    assert lead.startswith("This clears your confirmations. You will start again from choosing a disk")
    assert C.BTN_REFRESH_CANCEL == "Cancel"


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_the_guard(code):
    from beamo_wipe import lang

    names = ("REFRESH_GUARD_LEAD", "REFRESH_THEN_READER", "BTN_REFRESH_CANCEL",
             "HINT_REFRESH_GUARD", "CON_REFRESH_GUARD_KEEP", "CON_REFRESH_GUARD_GO",
             "CON_REFRESH_GUARD_PROMPT")
    english = {n: getattr(C, n) for n in names}
    try:
        lang.set_language(code)
        for name, value in english.items():
            assert getattr(C, name) != value, (code, name)
        assert "CHECK DISKS AGAIN" in C.CON_REFRESH_GUARD_PROMPT
        assert C.BTN_REFRESH in C.HINT_REFRESH_GUARD
    finally:
        lang.set_language("en")


# --- Rendered Tk -------------------------------------------------------------------------


@pytest.fixture
def tk_app():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(wiz, size=(800, 600)):
        _needs_display()
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update_idletasks()
        app.root.update()
        created.append(app)
        return app

    yield build
    for app in created:
        app._teardown()


def _buttons(app):
    from beamo_wipe.ui.tk_wizard import _Button

    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [w for w in walk(app.root) if isinstance(w, _Button) and w.winfo_ismapped()]


def _text(button):
    return str(button.itemcget(button._label, "text"))


class _Key:
    def __init__(self, keysym, time=0):
        self.keysym, self.time = keysym, time
        self.char = ""
        self.state = 0
        self.widget = None


@pytest.mark.parametrize("screen", [Screen.WHAT, Screen.OWNER])
def test_tk_owner_has_no_check_disks_again(tk_app, screen):
    wiz = _drive(_wizard(), screen)
    app = tk_app(wiz)
    assert C.BTN_REFRESH_UTILITY not in [_text(b) for b in _buttons(app)]
    before = _answers(wiz)
    app._on_key(_Key("F5"))
    assert wiz.screen == screen and _answers(wiz) == before


@pytest.mark.parametrize("screen", [Screen.PICK] + list(GUARDED[:3]))
def test_tk_offers_it_from_pick_confirm_method_review(tk_app, screen):
    wiz = _drive(_wizard(), screen)
    app = tk_app(wiz)
    assert C.BTN_REFRESH_UTILITY in [_text(b) for b in _buttons(app)]


@pytest.mark.parametrize("screen", [Screen.CONFIRM, Screen.LAST_CHANCE])
def test_tk_guarded_dialog_defaults_to_cancel_and_keys_cannot_accept(tk_app, screen):
    wiz = _drive(_wizard(), screen)
    app = tk_app(wiz)
    before = _answers(wiz)
    app._on_key(_Key("F5", time=1))  # opens the dialog
    app._on_f5_release(_Key("F5", time=2))
    app.root.update()
    assert wiz.screen == Screen.REFRESH_CONFIRM
    texts = [_text(b) for b in _buttons(app)]
    assert C.BTN_REFRESH_CANCEL in texts and C.BTN_REFRESH in texts
    focused = app.root.focus_lastfor()
    assert _text(focused) == C.BTN_REFRESH_CANCEL
    # A second F5 does not accept the guarded dialog.
    app._on_key(_Key("F5", time=3))
    app._on_f5_release(_Key("F5", time=4))
    assert wiz.screen == Screen.REFRESH_CONFIRM
    # Enter follows focus: Cancel keeps every answer.
    focused._command()
    app.root.update()
    assert wiz.screen == screen and _answers(wiz) == before


def test_tk_guarded_dialog_accepts_only_its_own_button(tk_app):
    wiz = _drive(_wizard(), Screen.LAST_CHANCE)
    app = tk_app(wiz)
    applied = []
    app._start_refresh_scan = lambda after: applied.append(after) or 1
    wiz.open_refresh_confirm()
    app._draw()
    app.root.update()
    go = next(b for b in _buttons(app) if _text(b) == C.BTN_REFRESH)
    go._command()
    assert applied and applied[0] == app._redraw_after_refresh


def test_tk_reader_switch_on_review_asks_first(tk_app, monkeypatch):
    import sys

    monkeypatch.setattr(sys, "platform", "linux")
    wiz = _drive(_wizard(), Screen.LAST_CHANCE)
    app = tk_app(wiz)
    scans = []
    app._start_refresh_scan = lambda after: scans.append(after) or 1
    before = _answers(wiz)
    app._click_accessible()
    app.root.update()
    assert scans == [] and wiz.screen == Screen.REFRESH_CONFIRM
    assert wiz.refresh_then_reader
    assert _answers(wiz) == before
    go = next(b for b in _buttons(app) if _text(b) == C.BTN_REFRESH)
    go._command()
    assert scans == [app._open_reader_after_refresh]


def test_tk_pick_dialog_is_unchanged(tk_app):
    wiz = _drive(_wizard(), Screen.PICK)
    app = tk_app(wiz)
    wiz.open_refresh_confirm()
    app._draw()
    app.root.update()
    assert _text(app.root.focus_lastfor()) == C.BTN_REFRESH
    assert C.BTN_BACK in [_text(b) for b in _buttons(app)]


# --- Consoles ------------------------------------------------------------------------------


def test_curses_guarded_dialog_enter_and_esc_keep_c_clears():
    from beamo_wipe.ui import console_wizard as console

    for key in (10, 13, 27):
        wiz = _drive(_wizard(), Screen.LAST_CHANCE)
        before = _answers(wiz)
        wiz.open_refresh_confirm()
        console._handle(wiz, key)
        assert wiz.screen == Screen.LAST_CHANCE and _answers(wiz) == before, key
    wiz = _drive(_wizard(), Screen.LAST_CHANCE)
    wiz.open_refresh_confirm()
    assert console._primary_footer(wiz, False) == [C.CON_REFRESH_GUARD_KEEP, C.CON_REFRESH_GUARD_GO]
    console._handle(wiz, ord("c"))
    assert wiz.screen == Screen.OWNER and wiz.selected is None and not wiz.owner_ok


def test_curses_pick_dialog_still_accepts_enter():
    from beamo_wipe.ui import console_wizard as console

    wiz = _drive(_wizard(), Screen.PICK)
    wiz.open_refresh_confirm()
    console._handle(wiz, 10)
    assert wiz.screen == Screen.OWNER


def test_curses_owner_hides_f5_hint():
    from beamo_wipe.ui import console_wizard as console

    wiz = _drive(_wizard(), Screen.OWNER)
    assert C.CON_REFRESH.format(note=C.REFRESH_UTILITY_NOTE) not in console._chrome_extra(wiz)
    pick = _drive(_wizard(), Screen.PICK)
    assert C.CON_REFRESH.format(note=C.REFRESH_UTILITY_NOTE) in console._chrome_extra(pick)


def test_plain_console_guarded_enter_keeps_typed_words_clear(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _drive(_wizard(), Screen.LAST_CHANCE)
    before = _answers(wiz)
    wiz.open_refresh_confirm()
    answers = iter([""])

    def fake_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    try:
        console._plain_loop(wiz)
    except Exception:
        pass
    out = capsys.readouterr().out
    assert C.REFRESH_GUARD_LEAD.split(":")[0] in out.replace("\n", " ")
    assert _answers(wiz)["selected"] == before["selected"]
    assert _answers(wiz)["confirm_input"] == before["confirm_input"]
