# SPDX-License-Identifier: GPL-3.0-or-later
"""Each curses screen opens at its own first page after natural navigation."""

import pytest

from beamo_wipe import copy as C, keyboard, storage_limits
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console


PAGE_DOWN = [console.curses.KEY_NPAGE] * 5
FIRST_LAYOUT = f"> {keyboard.LAYOUTS['us'].title}: {keyboard.LAYOUTS['us'].note}"


@pytest.mark.parametrize(
    "events,screen,opening_text,opening_visible",
    [
        (PAGE_DOWN + [ord("l")], Screen.LIMITS, storage_limits.SECTIONS[0][0], True),
        ([ord("l")] + PAGE_DOWN + [27], Screen.METHOD, C.SELECTED_DISK, True),
        (PAGE_DOWN + [ord("k")], Screen.KEYBOARD, FIRST_LAYOUT, True),
        ([ord("k")] + PAGE_DOWN + [10], Screen.METHOD, C.SELECTED_DISK, True),
        (PAGE_DOWN, Screen.METHOD, C.SELECTED_DISK, False),
        ([ord("l")] + PAGE_DOWN, Screen.LIMITS, storage_limits.SECTIONS[0][0], False),
        ([ord("k")] + PAGE_DOWN, Screen.KEYBOARD, FIRST_LAYOUT, False),
    ],
    ids=["method-limits", "limits-back", "method-keyboard", "keyboard-return",
         "method-scroll-control", "limits-scroll-control", "keyboard-scroll-control"],
)
def test_body_scroll_belongs_to_one_screen(
    monkeypatch, events, screen, opening_text, opening_visible
):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("A device or application action was reached")

    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    wizard = make_demo_wizard()
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    assert wizard.screen is Screen.METHOD
    keys = iter(events)
    frames = []

    class Terminal:
        def __init__(self):
            self.lines = []

        def getmaxyx(self):
            return 24, 80

        def keypad(self, *_args):
            pass

        def nodelay(self, *_args):
            pass

        def erase(self):
            self.lines = []

        def addstr(self, _y, _x, text, *_args):
            self.lines.append(text)

        def refresh(self):
            frames.append((wizard.screen, self.lines.copy()))

        def getch(self):
            try:
                return next(keys)
            except StopIteration:
                wizard.wants_shutdown = True
                return -1

    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda *_args: None)
    assert console._loop(Terminal(), wizard) == 0
    assert wizard.screen is screen
    final_screen, final_lines = frames[-1]
    assert final_screen is screen
    # The first wrapped line is visible only on the opening page, including
    # the shorter viewport used for Keyboard's input and utility footer.
    opening_line = console._lines(opening_text, 80)[0]
    assert (opening_line in final_lines) is opening_visible
    assert not wizard.runner.started
    assert not wizard.erase_enabled
    assert not effects
