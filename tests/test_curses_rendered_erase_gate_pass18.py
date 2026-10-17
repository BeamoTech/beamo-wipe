"""A curses Erase action must belong to a visibly enabled final review."""

import json

import pytest

from beamo_wipe.models import MethodId, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard, make_demo_wizard


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("enter", [10, 13, console.curses.KEY_ENTER])
@pytest.mark.parametrize("arrival", [
    "paint-crosses", "ready-before-frame", "too-early", "after-ready-frame",
    "initial-slow", "slow-before-expiry", "back-crosses", "eof-crosses",
])
def test_curses_enter_requires_a_rendered_ready_review(monkeypatch, request, method, arrival, enter):
    clock = [0.0]
    wizard = Wizard(
        make_demo_wizard().discovery,
        DryRunRunner(clock=lambda: clock[0]),
        clock=lambda: clock[0],
        dry_run=True,
    )
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.set_method(method)
    wizard.continue_method()
    assert wizard.screen is Screen.LAST_CHANCE
    assert not wizard.erase_enabled
    launches = []
    frames = []
    effects = []
    monkeypatch.setattr(console, "_curses_opt", lambda *_args: None)
    monkeypatch.setattr(console.time, "sleep", lambda _seconds: clock.__setitem__(0, clock[0] + (6 if arrival == "ready-before-frame" else 2)))

    def forbidden(*_args, **_kwargs):
        effects.append("native action")
        raise AssertionError("A native action was reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)

    class Terminal:
        def __init__(self):
            self.lines = []
            self.frame = 0

        def getmaxyx(self):
            return 200, 200

        def keypad(self, *_args):
            pass

        def nodelay(self, *_args):
            pass

        def erase(self):
            self.lines = []

        def addstr(self, y, x, text, *_args):
            self.lines.append((y, x, text))

        def refresh(self):
            self.frame += 1
            before = clock[0]
            ready_when_painted = wizard.erase_enabled
            if self.frame == 1 and arrival == "initial-slow":
                clock[0] = 6.0
            if self.frame == 2 and arrival == "slow-before-expiry":
                clock[0] = 4.0
            if self.frame == 2 and arrival in {"paint-crosses", "after-ready-frame", "back-crosses", "eof-crosses"}:
                # Simulate output blocking while a review that still says
                # "wait" is sent. An Enter at t=2 stays queued until t=6.
                clock[0] = 6.0
            frames.append({"frame": self.frame, "painted_at": before,
                           "read_at": clock[0], "ready_when_painted": ready_when_painted,
                           "lines": list(self.lines)})

        def getch(self):
            if self.frame == 1:
                return -1
            if self.frame == 2:
                if arrival == "eof-crosses":
                    raise EOFError("Fake terminal input disappeared")
                if arrival == "back-crosses":
                    return 27
                return -1 if arrival == "after-ready-frame" else enter
            if self.frame == 3 and arrival == "after-ready-frame":
                return enter
            wizard.wants_shutdown = True
            return -1

    terminal = Terminal()

    def record_erase():
        launches.append({"at": clock[0], "frame": terminal.frame,
                         "painted_ready": frames[-1]["ready_when_painted"]})

    monkeypatch.setattr(wizard, "confirm_erase", record_erase)
    if arrival == "eof-crosses":
        with pytest.raises(EOFError, match="Fake terminal input disappeared"):
            console._run_loop_guarded(terminal, wizard)
    else:
        assert console._run_loop_guarded(terminal, wizard) == 0
    request.node.user_properties.append(("rendered_gate_trace", json.dumps({
        "arrival": arrival, "method": method.value, "frames": frames, "launches": launches,
    })))
    if arrival not in {"ready-before-frame", "after-ready-frame"}:
        assert launches == []
    else:
        assert len(launches) == 1
        assert launches[0]["painted_ready"]
    assert wizard._review_overlay_depth == 0
    assert not effects
    if arrival == "back-crosses":
        assert wizard.screen is Screen.METHOD
