"""The curses final review credits successful native painting only."""

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


@pytest.mark.parametrize("failure", ["none", "write-error", "resize", "narrow-5", "narrow-18", "exact-19"])
def test_failed_native_review_paint_cannot_enable_erase(monkeypatch, failure, tmp_path):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native device/process/power action forbidden")

    for boundary in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(boundary, forbidden)
    clock = [0.0]
    wizard = Wizard(discovery_for_scenario("happy"), DryRunRunner(clock=lambda: clock[0]),
                    clock=lambda: clock[0], dry_run=True)
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.continue_method()
    assert wizard.screen == Screen.LAST_CHANCE
    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda _seconds: clock.__setitem__(0, clock[0] + 6))
    launches = []
    monkeypatch.setattr(wizard, "confirm_erase", lambda: launches.append(clock[0]))

    class Terminal:
        def __init__(self):
            self.frames = []
            self.lines = []
            self.errors = 0
            self.height = 200

        def keypad(self, *_args): pass
        def nodelay(self, *_args): pass
        def getmaxyx(self):
            columns = {"narrow-5": 5, "narrow-18": 18, "exact-19": 19}.get(failure, 200)
            return self.height, columns
        def erase(self): self.lines = []

        def addstr(self, y, x, text, *_args):
            if failure == "resize":
                # The frame measured a roomy terminal; the first native write
                # arrives after it shrinks. Later review rows are now absent.
                self.height = 5
            if failure == "write-error" and C.SEVERITY_WARNING in text:
                self.errors += 1
                raise console.curses.error("Fake native write failed")
            self.lines.append((y, x, text))

        def refresh(self):
            self.frames.append(tuple(self.lines))

        def getch(self):
            if len(self.frames) == 1:
                return -1
            if len(self.frames) == 2:
                return 10
            wizard.wants_shutdown = True
            return -1

    terminal = Terminal()
    assert console._run_loop_guarded(terminal, wizard) == 0
    warnings_seen = any(C.SEVERITY_WARNING in text for frame in terminal.frames
                        for _y, _x, text in frame)
    assert not effects
    if failure not in {"none", "exact-19"}:
        if failure in {"write-error", "resize", "narrow-5"}:
            assert not warnings_seen
        if failure == "write-error":
            assert terminal.errors
        assert launches == []
    else:
        assert warnings_seen
        assert launches == [6.0]


@pytest.mark.parametrize("text,height,width,y,x,throws,expected", [
    ("Visible", 20, 80, 3, 0, False, True),
    ("", 20, 80, 3, 0, False, True),
    ("", 20, 80, 20, 0, False, False),
    ("Visible", 20, 80, -1, 0, False, False),
    ("Visible", 20, 80, 20, 0, False, False),
    ("Visible", 20, 80, 3, 79, False, False),
    ("Visible", 20, 1, 3, 0, False, False),
    ("Visible", 20, 80, 3, 0, True, False),
    ("Visible", 20, 5, 3, 0, False, False),
    ("Wide: 漢字", 20, 9, 3, 0, False, False),
])
def test_native_add_reports_whether_content_was_painted(text, height, width, y, x, throws, expected):
    calls = []

    class Terminal:
        def getmaxyx(self): return height, width

        def addstr(self, *args):
            calls.append(args)
            if throws:
                raise console.curses.error("Fake native write failed")

    assert console._add(Terminal(), y, x, text) is expected
    if expected and text:
        assert calls
    elif not text or y < 0 or y >= height or width - 1 - x <= 0:
        assert not calls


def test_successful_retry_can_complete_the_previously_failed_review_line():
    visible = set()
    lines = ["Disk identity", "", "Warning: irreversible"]
    failures = [True]

    class Terminal:
        def getmaxyx(self): return 20, 80

        def addstr(self, _y, _x, text, *_args):
            if text.startswith("Warning") and failures[0]:
                raise console.curses.error("Fake transient write error")

    terminal = Terminal()
    console._paint_paged(terminal, 0, lines, 0, 20, 80, visible)
    assert visible == {0, 1}
    failures[0] = False
    console._paint_paged(terminal, 0, lines, 0, 20, 80, visible)
    assert visible == {0, 1, 2}


def test_existing_paint_boundary_stubs_keep_the_explicit_failure_contract(monkeypatch):
    class Terminal:
        def getmaxyx(self): return 20, 80

    monkeypatch.setattr(console, "_add", lambda *_args: None)
    visible = set()
    console._paint_paged(Terminal(), 0, ["fake successful paint"], 0, 20, 80, visible)
    assert visible == {0}
