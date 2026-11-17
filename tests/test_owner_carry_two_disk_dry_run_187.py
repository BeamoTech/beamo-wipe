# SPDX-License-Identifier: GPL-3.0-or-later
"""#187 acceptance: a full two-disk dry run through the real app loop.

Two erases in one app run with the shipped DryRunRunner (no injected
results): the owner ticks the box on screen for the first disk, the erase
runs to Done, Erase another disk starts a brand-new session, the tick
carries over (the Owner screen is skipped and the first disk is marked),
and the second disk still needs its own selection, exact token, method and
five-second review before its own erase runs to Done. All disks are fake.
"""

from __future__ import annotations

import time
from pathlib import Path

from beamo_wipe import app
from beamo_wipe import copy as C
from beamo_wipe import owner_carry as oc
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner

FIXTURE = Path(__file__).parent / "fixtures/lsblk_same_size.json"


def _run_to_done(w, path):
    """Pick ``path`` and pass every per-disk gate, then erase it for real."""
    assert w.selected is None
    w.select_disk(path)
    w.continue_pick()
    assert w.screen == Screen.CONFIRM
    w.set_confirm_input("WRONG")
    w.continue_confirm()
    assert w.screen == Screen.CONFIRM  # the exact token is still required
    w.set_confirm_input(w.confirm.token)
    w.continue_confirm()
    assert w.screen == Screen.METHOD
    w.continue_method()
    assert w.screen == Screen.LAST_CHANCE
    w.confirm_erase()  # during the five-second review: nothing starts
    assert w.screen == Screen.LAST_CHANCE and not w.runner.started
    w._erase_until = 0.0  # the review has elapsed
    w.confirm_erase()
    assert w.screen == Screen.WORKING and w.runner.started
    request = w._wipe_request
    assert request is not None and request.device == path
    deadline = time.monotonic() + 60
    while w.screen != Screen.DONE and time.monotonic() < deadline:
        w.tick()
        time.sleep(0.05)
    assert w.screen == Screen.DONE
    assert w.wipe_result is not None and w.wipe_result.ok
    return request


def test_two_disk_dry_run_carries_the_tick_and_keeps_every_per_disk_gate(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(app, "running_on_live_usb", lambda: False)
    monkeypatch.delenv("BEAMO_WIPE_BOOT_DEVICE", raising=False)
    logs = tmp_path / "logs"
    logs.mkdir()
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: logs)
    source = tmp_path / "disks.json"
    source.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    args = app._parser().parse_args([
        "--lsblk-json", str(source), "--boot-device", "/dev/sdb", "--plain-console",
    ])

    sessions = []
    erased = []

    def ui(w, **kwargs):
        sessions.append(w)
        assert isinstance(w.runner, DryRunRunner)
        assert all(w is not old and w.runner is not old.runner for old in sessions[:-1])
        assert w.screen == Screen.SPLASH and not w.owner_ok
        w.skip_splash()
        w.accept_keyboard()
        if len(sessions) == 1:
            assert w.screen == Screen.OWNER and not w.owner_carried
            w.set_owner(True)
            w.continue_owner()
            assert w.screen == Screen.PICK
            assert w.owner_source == oc.SOURCE_ON_SCREEN
            first, second = (d.path for d in w.selectable)
            erased.append((first, second))
            _run_to_done(w, first)
        elif len(sessions) == 2:
            first, second = erased[0]
            # The tick carried over: Owner was skipped, and the first disk is
            # marked as erased earlier in this app run but stays selectable.
            assert w.screen == Screen.PICK
            assert w.owner_ok and w.owner_carried
            assert w.owner_source == oc.SOURCE_CARRIED
            tags = {d.path: w.disk_tags(d) for d in w.selectable}
            assert set(tags) == {first, second}
            marks = (C.TAG_ERASED_CHECKED, C.TAG_ERASED_UNCHECKED, C.TAG_ERASED_UNCONFIRMED)
            assert any(t in marks for t in tags[first])
            assert tags[second] == ()
            _run_to_done(w, second)
        else:
            assert w.screen == Screen.PICK and w.owner_carried
            w.shutdown()
            return 0
        assert w.can_erase_another
        w.erase_another_disk()
        # No report was saved: the save-or-continue question comes first.
        assert w.screen == Screen.SHUTDOWN_CONFIRM and not w.wants_new_session
        w.confirm_shutdown_without_saving(w.shutdown_generation)
        assert w.wants_new_session
        return 0

    monkeypatch.setattr("beamo_wipe.ui.console_wizard._plain_loop", ui)
    app._run_session(args, session_store=None, use_console=True, want_accessible=False,
                     fullscreen=False, reader=None)
    assert len(sessions) == 3
