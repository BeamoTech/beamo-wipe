# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical key history survives shortcuts, overlays and consent screens."""

import copy
import curses
import os
import stat
from types import SimpleNamespace

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console


@pytest.fixture
def session(monkeypatch, tmp_path):
    """Actual controller with fake inventory, block metadata and DryRunRunner."""
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native device/process action reached")

    for target in (
        "subprocess.run",
        "subprocess.Popen",
        "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start",
        "beamo_wipe.app._shutdown",
    ):
        monkeypatch.setattr(target, forbidden)
    original_lstat = os.lstat
    fake_nodes = {
        "/dev/" + name: index
        for index, name in enumerate(
            (
                "loop0",
                "sdb",
                "sdb1",
                "nvme0n1",
                "nvme0n1p1",
                "nvme0n1p2",
                "sda",
                "sda1",
                "sdd",
                "sdd1",
            ),
            1,
        )
    }

    def fake_lstat(path, *args, **kwargs):
        value = os.fspath(path)
        if isinstance(value, str) and value.startswith("/dev/"):
            assert value in fake_nodes, value
            return SimpleNamespace(
                st_mode=stat.S_IFBLK | 0o600, st_rdev=fake_nodes[value]
            )
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", fake_lstat)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    wizard = make_demo_wizard()
    wizard.preview = False
    monkeypatch.setattr(wizard, "_write_evidence", lambda **_kwargs: None)
    wizard.runner._clock = lambda: 0.0
    confirm_stop = wizard.confirm_stop
    monkeypatch.setattr(
        wizard,
        "confirm_stop",
        lambda consent: confirm_stop(consent, asynchronous=False),
    )
    scans = []
    inventory = copy.deepcopy(wizard.discovery)
    wizard._rediscover = lambda: scans.append(True) or inventory
    yield SimpleNamespace(wizard=wizard, scans=scans)
    assert not effects


def prepare(wizard, screen):
    if screen is Screen.SPLASH:
        return
    wizard.skip_splash()
    if screen is Screen.KEYBOARD:
        return
    wizard.accept_keyboard()
    if screen is Screen.OWNER:
        return
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    if screen is Screen.PICK:
        return
    wizard.continue_pick()
    if screen is Screen.CONFIRM:
        return
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    if screen is Screen.METHOD:
        return
    wizard.continue_method()
    assert screen is Screen.LAST_CHANCE


def run_keys(monkeypatch, wizard, events):
    """Use real rendering/dispatch, a roomy terminal, and timestamped key input."""
    now = [0.0]
    wizard._clock = lambda: now[0]

    class Terminal:
        def __init__(self):
            self.events = iter(events)

        def getmaxyx(self):
            return 1000, 200

        def getch(self):
            try:
                now[0], key = next(self.events)
            except StopIteration:
                wizard.wants_shutdown = True
                return -1
            return key

        def __getattr__(self, _name):
            return lambda *_args, **_kwargs: None

    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console, "_add", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(console.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(console.time, "sleep", lambda _seconds: None)
    assert console._loop(Terminal(), wizard) == 0


@pytest.mark.parametrize("enter", [10, 13, curses.KEY_ENTER])
@pytest.mark.parametrize("fresh", [False, True])
def test_f5_interrupts_enters_quiet_interval(session, monkeypatch, enter, fresh):
    w = session.wizard
    prepare(w, Screen.METHOD)
    events = [(0, enter), (0.1, -1), (0.9, curses.KEY_F5), (1.2, -1)]
    events += [(2.3, -1), (2.4, enter)] if fresh else [(1.3, enter)]
    run_keys(monkeypatch, w, events)
    assert session.scans == ([True] if fresh else [])
    assert w.screen is (Screen.OWNER if fresh else Screen.REFRESH_CONFIRM)
    assert not w.runner.started


@pytest.mark.parametrize("enter", [10, 13, curses.KEY_ENTER])
@pytest.mark.parametrize("fresh", [False, True])
def test_suppressed_escape_also_interrupts_enters_quiet_interval(
    session, monkeypatch, enter, fresh
):
    w = session.wizard
    prepare(w, Screen.METHOD)
    events = [(0, enter), (0.4, 27), (0.5, -1), (1.0, 27), (1.6, -1)]
    events += [(2.8, -1), (2.9, enter)] if fresh else [(1.7, enter)]
    run_keys(monkeypatch, w, events)
    assert w.screen is (Screen.LAST_CHANCE if fresh else Screen.METHOD)
    assert not session.scans and not w.runner.started


@pytest.mark.parametrize("fresh", [False, True])
def test_enter_pressed_in_inventory_overlay_cannot_advance_picker(
    session, monkeypatch, fresh
):
    w = session.wizard
    prepare(w, Screen.PICK)
    events = [(0, ord("b")), (0.1, 10), (0.2, 27)]
    events += [(0.3, -1), (1.4, -1), (1.5, 10)] if fresh else [(0.3, 10)]
    run_keys(monkeypatch, w, events)
    assert w.screen is (Screen.CONFIRM if fresh else Screen.PICK)
    assert not w.runner.started


@pytest.mark.parametrize("enter", [10, 13, curses.KEY_ENTER])
def test_quiet_inside_inventory_overlay_releases_enter(session, monkeypatch, enter):
    w = session.wizard
    prepare(w, Screen.PICK)
    run_keys(
        monkeypatch,
        w,
        [
            (0, ord("b")),
            (0.1, enter),
            (0.2, -1),
            (1.3, -1),
            (1.4, 27),
            (1.5, enter),
        ],
    )
    assert w.screen is Screen.CONFIRM and not w.runner.started


@pytest.mark.parametrize("origin", [Screen.SPLASH, Screen.KEYBOARD])
@pytest.mark.parametrize("fresh", [False, True])
def test_space_from_setup_does_not_acknowledge_owner(
    session, monkeypatch, origin, fresh
):
    w = session.wizard
    prepare(w, origin)
    events = [(0, 32), (0.1, 10)]
    events += [(0.2, -1), (1.3, -1), (1.4, 32)] if fresh else [(0.2, 32)]
    run_keys(monkeypatch, w, events)
    assert w.screen is Screen.OWNER
    assert w.owner_ok is fresh
    assert not w.runner.started


def test_fresh_owner_space_still_acknowledges(session, monkeypatch):
    w = session.wizard
    prepare(w, Screen.KEYBOARD)
    run_keys(monkeypatch, w, [(0, 10), (0.1, 32)])
    assert w.screen is Screen.OWNER and w.owner_ok


def test_owner_keyboard_detour_keeps_unchecked_consent(session, monkeypatch):
    w = session.wizard
    prepare(w, Screen.OWNER)
    w.set_owner(True)
    run_keys(monkeypatch, w, [(0, 32), (0.1, ord("k")), (0.2, 10), (0.3, 32)])
    assert w.screen is Screen.OWNER and not w.owner_ok


@pytest.mark.parametrize("letter", [ord("s"), ord("S")])
@pytest.mark.parametrize("fresh", [False, True])
def test_s_from_review_cannot_confirm_stop_after_start(
    session, monkeypatch, letter, fresh
):
    w = session.wizard
    prepare(w, Screen.LAST_CHANCE)
    # The first real review frame starts its visible countdown at t=0.
    events = [(5.1, -1), (5.2, letter), (5.3, 10), (5.4, 27)]
    events += [(5.5, -1), (6.6, -1), (6.7, letter)] if fresh else [(5.5, letter)]
    run_keys(monkeypatch, w, events)
    assert w.runner.started and w.runner.cancelled is fresh
    assert w.screen is (Screen.DONE if fresh else Screen.WORKING)


def test_fresh_stop_s_after_start_still_cancels(session, monkeypatch):
    w = session.wizard
    prepare(w, Screen.LAST_CHANCE)
    run_keys(monkeypatch, w, [(5.1, -1), (5.2, 10), (5.3, 27), (5.4, ord("s"))])
    assert w.runner.started and w.runner.cancelled and w.screen is Screen.DONE


@pytest.mark.parametrize("letter", [ord("s"), ord("S")])
@pytest.mark.parametrize("fresh", [False, True])
def test_s_from_owner_does_not_toggle_sharing_after_help_opens(
    session, monkeypatch, letter, fresh
):
    w = session.wizard
    prepare(w, Screen.OWNER)
    events = [(0, letter), (0.1, ord("r"))]
    events += [(0.2, -1), (1.3, -1), (1.4, letter)] if fresh else [(0.2, letter)]
    run_keys(monkeypatch, w, events)
    assert w.screen is Screen.REPORT_HELP
    assert w.report_share_redacted is fresh


@pytest.mark.parametrize("letter", [32, ord("s")])
def test_refresh_detour_does_not_repeat_report_preference(session, monkeypatch, letter):
    w = session.wizard
    prepare(w, Screen.OWNER)
    w.open_report_help()
    run_keys(
        monkeypatch,
        w,
        [
            (0, letter),
            (0.1, -1),
            (0.9, curses.KEY_F5),
            (1.0, 27),
            (1.1, letter),
        ],
    )
    assert w.screen is Screen.REPORT_HELP
    assert (w.report_wanted if letter == 32 else w.report_share_redacted) is True


@pytest.mark.parametrize("screen", [Screen.KEYBOARD, Screen.CONFIRM])
def test_literal_input_keeps_repeated_space_s_and_backspace(
    session, monkeypatch, screen
):
    w = session.wizard
    prepare(w, screen)
    run_keys(
        monkeypatch,
        w,
        [(0, 32), (0.1, 32), (0.2, ord("s")), (0.3, ord("S")), (0.4, 127)],
    )
    assert (w.typing_check if screen is Screen.KEYBOARD else w.confirm_input) == "  s"
    assert w.screen is screen and not w.runner.started


@pytest.mark.parametrize("letter", [32, ord("s")])
@pytest.mark.parametrize("fresh", [False, True])
def test_literal_confirm_key_cannot_become_consent_after_refresh(
    session, monkeypatch, letter, fresh
):
    w = session.wizard
    prepare(w, Screen.CONFIRM)
    events = [(0, letter), (0.1, curses.KEY_F5), (0.2, 10)]
    if letter == ord("s"):
        events.append((0.3, ord("r")))
    events += [(0.4, -1), (1.5, -1), (1.6, letter)] if fresh else [(0.4, letter)]
    run_keys(monkeypatch, w, events)
    assert session.scans == [True]
    assert (w.owner_ok if letter == 32 else w.report_share_redacted) is fresh
    assert w.screen is (Screen.OWNER if letter == 32 else Screen.REPORT_HELP)
    assert not w.runner.started
