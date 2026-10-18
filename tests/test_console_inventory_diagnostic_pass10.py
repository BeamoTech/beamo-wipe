"""Inventory navigation must not hide the diagnostic report workflow."""

import pytest

from beamo_wipe import copy as C
from beamo_wipe import diagnostic_report as D
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


class Terminal:
    def __init__(self, wizard, keys):
        self.wizard = wizard
        self.keys = iter(keys)
        self.rows = {}
        self.frames = []

    def getmaxyx(self):
        return 24, 80

    def addstr(self, y, x, text, _attr=0):
        self.rows[y] = " " * x + text

    def erase(self):
        self.rows = {}

    def getch(self):
        self.frames.append((self.wizard.screen, " ".join(self.rows.values())))
        try:
            return next(self.keys)
        except StopIteration:
            self.wizard.wants_shutdown = True
            return -1

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: None


def _run(monkeypatch, keys):
    wizard = Wizard(discovery_for_scenario("empty"), DryRunRunner(), dry_run=True)
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    assert wizard.screen == Screen.PICK_EMPTY
    assert wizard.can_open_diagnostic
    assert wizard.protected_boot is not None
    assert wizard.other_devices
    terminal = Terminal(wizard, keys)
    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda _seconds: None)
    assert console._loop(terminal, wizard) == 0
    return wizard, terminal


@pytest.mark.parametrize("overlay", ["b", "B", "o", "O"])
@pytest.mark.parametrize("diagnostic", ["d", "D"])
def test_diagnostic_shortcut_replaces_inventory_overlay(monkeypatch, overlay, diagnostic):
    wizard, terminal = _run(monkeypatch, [ord(overlay), ord(diagnostic)])
    assert wizard.screen == Screen.DIAGNOSTIC
    screen, text = terminal.frames[-1]
    assert screen == Screen.DIAGNOSTIC
    assert D.NOTICE in text
    assert C.CON_DIAG_LINE.format(action=C.CON_DIAG_PREPARE) in text
    assert C.CON_READ_ONLY not in text


@pytest.mark.parametrize("overlay", ["b", "o"])
def test_diagnostic_prepare_prompt_follows_visible_diagnostic(monkeypatch, overlay):
    prompts = []

    def confirm(terminal, wizard):
        prompts.append((wizard.screen, " ".join(terminal.rows.values())))

    monkeypatch.setattr(console, "_confirm_diagnostic_action", confirm)
    wizard, _terminal = _run(monkeypatch, [ord(overlay), ord("d"), ord("r")])
    assert wizard.screen == Screen.DIAGNOSTIC
    assert len(prompts) == 1
    assert prompts[0][0] == Screen.DIAGNOSTIC
    assert D.NOTICE in prompts[0][1]
    assert C.CON_READ_ONLY not in prompts[0][1]


@pytest.mark.parametrize("overlay", ["b", "o"])
@pytest.mark.parametrize("shortcut", ["r", "R", "q", "Q"])
def test_unavailable_inventory_shortcuts_do_not_navigate(monkeypatch, overlay, shortcut):
    wizard, terminal = _run(monkeypatch, [ord(overlay), ord(shortcut)])
    assert wizard.screen == Screen.PICK_EMPTY
    assert C.CON_READ_ONLY in terminal.frames[-1][1]


@pytest.mark.parametrize("overlay", ["b", "o"])
def test_escape_closes_only_inventory_overlay(monkeypatch, overlay):
    wizard, terminal = _run(monkeypatch, [ord(overlay), 27])
    assert wizard.screen == Screen.PICK_EMPTY
    assert C.CON_SHUTDOWN_BACK in terminal.frames[-1][1]
    assert C.CON_READ_ONLY not in terminal.frames[-1][1]


@pytest.mark.parametrize("overlay", ["b", "o"])
def test_refresh_shortcut_replaces_inventory_overlay(monkeypatch, overlay):
    wizard, terminal = _run(monkeypatch, [ord(overlay), console.curses.KEY_F5])
    assert wizard.screen == Screen.REFRESH_CONFIRM
    assert C.REFRESH_LEAD in terminal.frames[-1][1]
    assert C.CON_REFRESH_ENTER in terminal.frames[-1][1]
    assert C.CON_READ_ONLY not in terminal.frames[-1][1]
