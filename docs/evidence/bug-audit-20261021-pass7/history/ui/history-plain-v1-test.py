"""The plain terminal starts its final review after successful visible output."""

from contextlib import contextmanager
import errno
import io
import json
import os
import sys

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


@pytest.fixture
def last_chance(monkeypatch, tmp_path):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native inventory, engine or power action forbidden")

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
    assert wizard.screen is Screen.LAST_CHANCE
    monkeypatch.setattr(console.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    calls = []

    def claim():
        assert wizard.erase_enabled
        calls.append(clock[0])
        wizard.wants_shutdown = True

    monkeypatch.setattr(wizard, "confirm_erase", claim)
    yield wizard, clock, calls
    assert not effects
    assert not wizard.runner.started


@contextmanager
def _terminal_output(monkeypatch, tmp_path, wizard, clock, *, line_buffered, delay=0, error_kind=None):
    events = []

    class RawOutput(io.FileIO):
        failed = False

        def write(self, data):
            warning = C.SEVERITY_WARNING in bytes(data).decode("utf-8")
            if warning:
                clock[0] += delay
                if error_kind is not None and not self.failed:
                    self.failed = True
                    code = errno.ENOSPC if error_kind is OSError else errno.EACCES
                    raise error_kind(code, "Fake final review flush failure")
            count = super().write(data)
            events.append({"at": clock[0], "warning": warning,
                           "held": wizard._review_overlay_depth > 0,
                           "enabled": wizard.erase_enabled})
            return count

    output = io.TextIOWrapper(
        io.BufferedWriter(RawOutput(tmp_path / "fake-terminal-output.txt", "wb"), 8192),
        encoding="utf-8", line_buffering=line_buffered,
    )
    master, slave = os.openpty()
    terminal = os.fdopen(os.dup(slave), "r", encoding="utf-8")
    original_answer = console._answer

    def answer(wizard, prompt):
        assert prompt == C.CON_ERASE_PROMPT
        # Enqueue only after the real canonical typeahead-retirement boundary.
        os.write(master, b"ERASE\n")
        return original_answer(wizard, prompt)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdin", terminal)
            patch.setattr(sys, "stdout", output)
            patch.setattr(console, "_answer", answer)
            yield events
    finally:
        output.close()
        terminal.close()
        os.close(slave)
        os.close(master)


@pytest.mark.parametrize("line_buffered", [True, False], ids=["line", "block"])
@pytest.mark.parametrize("delay", [0.0, 8.0], ids=["immediate", "slow-flush"])
def test_final_review_requires_five_visible_seconds_after_flush(
    last_chance, monkeypatch, tmp_path, request, line_buffered, delay,
):
    wizard, clock, calls = last_chance
    with _terminal_output(monkeypatch, tmp_path, wizard, clock,
                          line_buffered=line_buffered, delay=delay) as events:
        assert console._plain_loop(wizard) == 0
        visible = next(event for event in events if event["warning"])
        request.node.user_properties.append(("visible_review_trace", json.dumps({
            "line_buffered": line_buffered, "flush_delay": delay,
            "warning": visible, "erase_claims": calls,
        })))
        assert len(calls) == 1
        assert visible["held"] and not visible["enabled"]
        assert calls[0] - visible["at"] >= 5.0
        assert wizard._review_overlay_depth == 0


@pytest.mark.parametrize("line_buffered", [True, False], ids=["line", "block"])
@pytest.mark.parametrize("error_kind", [OSError, PermissionError], ids=["storage-full", "permission"])
def test_failed_review_flush_cannot_reach_erase_or_leave_a_review_hold(
    last_chance, monkeypatch, tmp_path, line_buffered, error_kind,
):
    wizard, clock, calls = last_chance
    with _terminal_output(monkeypatch, tmp_path, wizard, clock,
                          line_buffered=line_buffered, error_kind=error_kind):
        with pytest.raises(error_kind, match="Fake final review flush failure"):
            console._plain_loop(wizard)
        assert calls == []
        assert wizard._interface_failed
        assert not wizard.erase_enabled
        assert wizard._review_overlay_depth == 0
