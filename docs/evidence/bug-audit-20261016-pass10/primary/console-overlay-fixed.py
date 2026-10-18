import json
from pathlib import Path
from unittest.mock import patch

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


wizard = Wizard(discovery_for_scenario("empty"), DryRunRunner(), dry_run=True)
wizard.skip_intro()
wizard.set_owner(True)
wizard.continue_owner()
assert wizard.screen == Screen.PICK_EMPTY
assert wizard.can_open_diagnostic
assert wizard.protected_boot is not None


class Terminal:
    def __init__(self):
        self.keys = iter((ord("b"), ord("d")))
        self.frames = []
        self.rows = {}

    def getmaxyx(self):
        return 24, 80

    def addstr(self, y, x, text, attr=0):
        self.rows[y] = " " * x + text

    def erase(self):
        self.rows = {}

    def getch(self):
        self.frames.append({"screen": wizard.screen.value, "rows": self.rows.copy()})
        try:
            return next(self.keys)
        except StopIteration:
            wizard.wants_shutdown = True
            return -1

    def __getattr__(self, name):
        return lambda *a, **kw: None


terminal = Terminal()
with patch.object(console, "_curses_opt"), patch.object(console.time, "sleep"):
    assert console._loop(terminal, wizard) == 0
rendered = json.dumps(terminal.frames, indent=2)
Path("/tmp/pass10-primary/console-overlay-fixed.json").write_text(rendered + "\n")
print(rendered)
last = " ".join(terminal.frames[-1]["rows"].values())
assert wizard.screen == Screen.DIAGNOSTIC
assert "Support diagnostics only" in last, "Diagnostic explanation is hidden by stale inventory overlay"
assert "r: prepare baseline" in last.lower(), "Diagnostic action footer is hidden by stale inventory overlay"
