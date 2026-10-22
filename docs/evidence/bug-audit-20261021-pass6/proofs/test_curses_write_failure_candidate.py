"""Outside-Git proof: a swallowed curses write error must not satisfy review."""
import json

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


@pytest.mark.parametrize("fail_warning", [False, True], ids=["normal-control", "warning-write-failed"])
def test_failed_warning_write_cannot_complete_review(fail_warning, monkeypatch, tmp_path, request):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    native_calls = []

    def forbidden(*_args, **_kwargs):
        native_calls.append(True)
        raise AssertionError("native action forbidden")

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
            self.warning_errors = 0

        def keypad(self, *_args): pass
        def nodelay(self, *_args): pass
        def getmaxyx(self): return (200, 200)
        def erase(self): self.lines = []

        def addstr(self, y, x, text, *_args):
            if fail_warning and C.SEVERITY_WARNING in text:
                self.warning_errors += 1
                raise console.curses.error("fake curses write failed")
            self.lines.append((y, x, text))

        def refresh(self):
            self.frames.append({"lines": list(self.lines), "at": clock[0],
                                "ready": wizard.erase_enabled})

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
                        for _y, _x, text in frame["lines"])
    trace = {"fail_warning": fail_warning, "warnings_seen": warnings_seen,
             "warning_errors": terminal.warning_errors, "launches": launches,
             "ready": [frame["ready"] for frame in terminal.frames], "native_calls": native_calls}
    request.node.user_properties.append(("trace", json.dumps(trace)))
    print(json.dumps(trace))
    assert not native_calls
    if fail_warning:
        assert terminal.warning_errors
        assert not warnings_seen
        assert launches == [], trace
    else:
        assert warnings_seen
        assert launches == [6.0]
