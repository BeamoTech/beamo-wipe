# SPDX-License-Identifier: GPL-3.0-or-later
"""A terminal key held before Stop opens cannot supply its consent."""

import pytest

from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console
from test_busy_transitions import ready as ready_fixture

ready = ready_fixture


@pytest.fixture
def working(ready, monkeypatch):
    """Use the real controller and fake runner, with no native side effects."""
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native application effect reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    ready.confirm_erase()
    assert ready.screen is Screen.WORKING and ready.runner.started
    original_confirm = ready.confirm_stop
    monkeypatch.setattr(
        ready, "confirm_stop",
        lambda consent: original_confirm(consent, asynchronous=False),
    )
    yield ready
    assert not effects


def run_terminal(monkeypatch, wizard, events):
    """Feed timestamped getch events through the actual curses dispatch loop."""
    now = [0.0]

    class Terminal:
        def __init__(self):
            self.events = iter(events)

        def getmaxyx(self):
            return 24, 80

        def getch(self):
            try:
                now[0], key = next(self.events)
            except StopIteration:
                wizard.wants_shutdown = True
                return -1
            return key() if callable(key) else key

        def __getattr__(self, _name):
            return lambda *_args, **_kwargs: None

    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console, "_footer_lines", lambda *_args: [])
    monkeypatch.setattr(console, "_chrome_lines", lambda *_args: [])
    monkeypatch.setattr(console, "_add", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(console, "_paint_paged", lambda *_args: 0)
    monkeypatch.setattr(console, "_paint_footer", lambda *_args: None)
    monkeypatch.setattr(console.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(console.time, "sleep", lambda _seconds: None)
    assert console._loop(Terminal(), wizard) == 0


@pytest.mark.parametrize(
    "events",
    [
        [(0, ord("s")), (.1, 27), (.2, ord("s"))],
        [(0, ord("S")), (.1, 27), (.2, ord("S"))],
        [(0, ord("s")), (.1, 27), (.2, ord("S"))],
        [(0, ord("S")), (.1, 27), (.2, ord("x")), (.3, ord("s"))],
        [(0, ord("s")), (.1, 27), (.2, -1), (.5, -1), (.6, ord("s"))],
        # Escape and unrelated keys must also interrupt an incomplete quiet gap.
        [(0, ord("s")), (.1, -1), (.5, 27), (.6, -1), (1.3, -1), (1.4, ord("s"))],
        [(0, ord("s")), (.1, 27), (.2, -1), (.8, ord("x")),
         (.9, -1), (1.4, -1), (1.5, ord("s"))],
    ],
    ids=["lowercase", "uppercase", "case-alias", "interleaved",
         "short-quiet", "escape-breaks-quiet", "other-key-breaks-quiet"],
)
def test_held_s_cannot_confirm_a_new_stop_modal(working, monkeypatch, events):
    run_terminal(monkeypatch, working, events)
    assert working.screen is Screen.WORKING
    assert working.stop_confirmation is not None
    assert not working.runner.cancelled


@pytest.mark.parametrize(
    "events",
    [
        [(0, 27), (.1, ord("s"))],
        [(0, 27), (.1, ord("S"))],
        [(0, ord("s")), (.1, 27), (.2, -1), (1.3, -1), (1.4, ord("S"))],
    ],
    ids=["fresh-lowercase", "fresh-uppercase", "fresh-after-quiet"],
)
def test_fresh_s_still_confirms_stop(working, monkeypatch, events):
    run_terminal(monkeypatch, working, events)
    assert working.screen is Screen.DONE
    assert working.runner.cancelled
    assert working.wipe_result is not None and not working.wipe_result.ok
    assert working.stop_confirmation is None


def test_fresh_s_can_confirm_an_already_open_stop_modal(working, monkeypatch):
    working.request_stop()
    run_terminal(monkeypatch, working, [(0, ord("s"))])
    assert working.screen is Screen.DONE and working.runner.cancelled


def test_repeated_escape_leaves_stop_modal_open(working, monkeypatch):
    run_terminal(monkeypatch, working, [(0, 27), (.1, 27), (.2, 27)])
    assert working.screen is Screen.WORKING
    assert working.stop_confirmation is not None
    assert not working.runner.cancelled


def test_s_repeat_also_interrupts_escapes_quiet_interval(working, monkeypatch):
    run_terminal(monkeypatch, working, [
        (0, ord("s")), (.1, 27), (.2, -1), (.8, ord("S")),
        (.9, -1), (1.4, -1), (1.5, 27),
    ])
    assert working.screen is Screen.WORKING
    assert working.stop_confirmation is not None
    assert not working.runner.cancelled


@pytest.mark.parametrize("keep", [ord("k"), ord("K"), 10])
def test_keep_erasing_does_not_reuse_s_as_stop_consent(working, monkeypatch, keep):
    run_terminal(monkeypatch, working, [
        (0, ord("s")), (.1, 27), (.2, keep), (.3, ord("s")),
    ])
    assert working.screen is Screen.WORKING
    assert working.stop_confirmation is None
    assert not working.runner.cancelled


def test_completion_before_dispatch_wins_over_stop_confirmation(working, monkeypatch):
    def complete_before_key_dispatch():
        working.runner._clock = lambda: 20.0
        working.tick()
        assert working.screen is Screen.DONE and working.wipe_result.ok
        return ord("s")

    run_terminal(monkeypatch, working, [(0, 27), (.1, complete_before_key_dispatch)])
    assert working.wipe_result.ok
    assert not working.runner.cancelled
    assert working.stop_confirmation is None
