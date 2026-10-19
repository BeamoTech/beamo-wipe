# SPDX-License-Identifier: GPL-3.0-or-later
"""Confirm uses the same physical Enter hold as the surrounding screens."""

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console


@pytest.mark.parametrize(
    "events,expected",
    [
        ([10, 10], Screen.CONFIRM),
        ([10, ord("x"), 127, 10], Screen.CONFIRM),
        ([10, -1, -1, 10], Screen.METHOD),
    ],
    ids=["held-enter", "interleaved-enter", "fresh-enter-control"],
)
def test_keyboard_return_cannot_accept_confirm_with_the_same_enter(
    monkeypatch, events, expected
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
    assert wizard.token_ok
    wizard.open_keyboard()
    assert wizard.screen is Screen.KEYBOARD
    reads = []
    keys = iter(events)

    class Terminal:
        def getmaxyx(self):
            return 24, 80

        def keypad(self, *_args):
            pass

        def nodelay(self, *_args):
            pass

        def timeout(self, *_args):
            pass

        def erase(self):
            pass

        def addstr(self, *_args):
            pass

        def refresh(self):
            pass

        def getch(self):
            reads.append(wizard.screen)
            try:
                return next(keys)
            except StopIteration:
                wizard.wants_shutdown = True
                return -1

    now = [0.0]

    def monotonic():
        now[0] += 1.0  # Two empty reads establish more than the release interval.
        return now[0]

    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda *_args: None)
    monkeypatch.setattr(console.time, "monotonic", monotonic)
    assert console._loop(Terminal(), wizard) == 0
    assert reads[:2] == [Screen.KEYBOARD, Screen.CONFIRM]
    assert wizard.screen is expected
    assert wizard.token_ok
    assert not wizard.runner.started
    assert not effects
