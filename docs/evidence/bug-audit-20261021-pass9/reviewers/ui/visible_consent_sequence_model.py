"""Independent deterministic consent sequences; fake inventory and DryRunRunner only."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from itertools import product

from beamo_wipe import app, discover, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.nwipe_runner import DryRunRunner, NwipeRunner
from beamo_wipe.wizard import Wizard


class Clock:
    value = 100.0

    def __call__(self):
        return self.value


counts = {"sequences": 0, "blocked_erase_calls": 0,
          "explicit_fake_starts": 0, "automatic_starts": 0,
          "nested_overlay_checks": 0, "native_callbacks": 0}


def forbidden(*args, **kwargs):
    counts["native_callbacks"] += 1
    raise AssertionError("Native process/inventory/engine/power callback forbidden")


subprocess.run = forbidden
subprocess.Popen = forbidden
discover.run_lsblk = forbidden
discover.read_cmdline = forbidden
discover.read_mount_sources = forbidden
NwipeRunner.start = forbidden
app._shutdown = forbidden
sound._run = forbidden
sound._popen = forbidden


def blocked(w):
    w.confirm_erase()
    assert w.runner._started is None
    counts["blocked_erase_calls"] += 1


def ready(method):
    clock = Clock()
    runner = DryRunRunner(clock=clock)
    w = Wizard(make_demo_wizard().discovery, runner, clock=clock,
               wall_clock=lambda: "2026-10-21T00:00:00Z")
    w._write_evidence = lambda **kwargs: None
    blocked(w)
    w.skip_intro()
    w.continue_owner()
    assert w.screen == Screen.OWNER
    blocked(w)
    w.set_owner(True)
    w.continue_owner()
    w.continue_pick()
    assert w.screen == Screen.PICK
    blocked(w)
    w.select_disk(w.selectable[0].path)
    w.continue_pick()
    w.set_confirm_input("incorrect fake token")
    w.continue_confirm()
    assert w.screen == Screen.CONFIRM
    blocked(w)
    w.set_confirm_input(w.confirm.token)
    w.continue_confirm()
    w.set_method(method)
    w.continue_method()
    assert w.screen == Screen.LAST_CHANCE
    assert not w.erase_enabled
    blocked(w)
    clock.value += 4.999
    assert w.countdown_display >= 1
    assert not w.erase_enabled
    blocked(w)
    clock.value += .001
    assert w.erase_enabled and w.countdown_display == 0
    assert runner._started is None
    return w, clock


def detour(w, clock, kind, delay):
    if kind == "keyboard_accept":
        w.open_keyboard(); clock.value += delay; w.accept_keyboard()
    elif kind == "keyboard_back":
        w.open_keyboard(); clock.value += delay; w.back()
    elif kind == "advanced_close":
        w.open_advanced(); clock.value += delay; w.close_advanced()
    elif kind == "advanced_back":
        w.open_advanced(); clock.value += delay; w.back()
    elif kind == "refresh_cancel":
        assert w.open_refresh_confirm()
        clock.value += delay; w.cancel_refresh_confirm()
    elif kind == "refresh_back":
        assert w.open_refresh_confirm()
        clock.value += delay; w.back()
    elif kind == "diagnostic_close":
        w.error = "fake diagnostic reason"; w.open_diagnostic()
        assert w.screen == Screen.DIAGNOSTIC
        clock.value += delay; w.close_diagnostic()
    elif kind == "diagnostic_back":
        w.error = "fake diagnostic reason"; w.open_diagnostic()
        assert w.screen == Screen.DIAGNOSTIC
        clock.value += delay; w.back()
    elif kind == "shutdown_keep":
        w.report_wanted = True; w.shutdown()
        assert w.screen == Screen.SHUTDOWN_CONFIRM
        clock.value += delay; w.keep_report_session()
    elif kind == "shutdown_back":
        w.report_wanted = True; w.shutdown()
        assert w.screen == Screen.SHUTDOWN_CONFIRM
        clock.value += delay; w.back()
    else:
        raise AssertionError(kind)


for method, kind, delay, repetitions in product(
        list(MethodId),
        ["keyboard_accept", "keyboard_back", "advanced_close", "advanced_back",
         "refresh_cancel", "refresh_back", "diagnostic_close", "diagnostic_back",
         "shutdown_keep", "shutdown_back"], [0.0, .125, 7.0, 3600.0], [1, 2, 4]):
    w, clock = ready(method)
    for _ in range(repetitions):
        detour(w, clock, kind, delay)
        assert w.screen == Screen.LAST_CHANCE
        assert not w.erase_enabled and w.countdown_left == 5
        blocked(w)
        clock.value += 4.999
        assert not w.erase_enabled and w.countdown_display >= 1
        blocked(w)
        clock.value += .001
        assert w.erase_enabled and w.countdown_display == 0
        assert w.runner._started is None
    w.confirm_erase()
    assert w.screen == Screen.WORKING
    assert w.runner._started is not None
    assert w._wipe_request.method == method
    counts["explicit_fake_starts"] += 1
    counts["sequences"] += 1


for method, depth, delay in product(list(MethodId), [1, 2, 3, 7], [0, 5, 3600]):
    w, clock = ready(method)
    for _ in range(depth):
        assert w.begin_review_overlay()
    clock.value += delay
    assert not w.erase_enabled
    blocked(w)
    for remaining in range(depth - 1, -1, -1):
        w.end_review_overlay()
        assert not w.erase_enabled
        blocked(w)
        counts["nested_overlay_checks"] += 1
        if remaining:
            clock.value += 10
    assert w.countdown_left == 5
    clock.value += 5
    assert w.erase_enabled and w.runner._started is None
    w.confirm_erase()
    assert w.screen == Screen.WORKING and w.runner._started is not None
    counts["explicit_fake_starts"] += 1
    counts["sequences"] += 1


for method in MethodId:
    w, clock = ready(method)
    w.interface_failed()
    clock.value += 100
    assert not w.erase_enabled
    blocked(w)
    w.restart_review_countdown()
    clock.value += 5
    assert not w.erase_enabled
    blocked(w)
    counts["sequences"] += 1

assert counts["explicit_fake_starts"] > 0
assert counts["automatic_starts"] == counts["native_callbacks"] == 0
Path(__file__).with_suffix(".json").write_text(json.dumps(counts, indent=2) + "\n")
print(json.dumps(counts, sort_keys=True))
