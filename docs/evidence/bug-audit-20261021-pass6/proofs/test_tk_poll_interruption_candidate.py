"""Outside-Git proof: real Tk callback dispatch with fake running disks only."""
import json
import time

import pytest

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui.tk_wizard import TkWizard
from beamo_wipe.wizard import Wizard


@pytest.mark.parametrize("interruption", [False, True], ids=["normal-control", "poll-interrupted"])
def test_running_tk_poll_stays_owned_after_callback(interruption, monkeypatch, tmp_path, request):
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
    runner = DryRunRunner(clock=lambda: clock[0], duration_s=100)
    wizard = Wizard(discovery_for_scenario("happy"), runner, clock=lambda: clock[0], dry_run=True)
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.continue_method()
    clock[0] = 6.0
    wizard.confirm_erase()
    assert wizard.screen == Screen.WORKING
    events = []
    original_poll = runner.poll
    original_cancel = runner.cancel

    def poll(wipe_request):
        events.append("poll")
        if interruption and events.count("poll") == 1:
            raise KeyboardInterrupt("fake poll interrupted once")
        return original_poll(wipe_request)

    def cancel():
        events.append("cancel")
        return original_cancel()

    monkeypatch.setattr(runner, "poll", poll)
    monkeypatch.setattr(runner, "cancel", cancel)
    app = TkWizard(wizard)
    callback_errors = []
    original_report = app.root.report_callback_exception

    def report_callback(kind, value, tb):
        callback_errors.append(kind.__name__)
        original_report(kind, value, tb)

    app.root.report_callback_exception = report_callback
    try:
        app.root.after_cancel(app._after_id)
        app._after_id = app.root.after(0, app._tick)
        app.root.update()
        time.sleep(0.15)
        if not app._ui_dead:
            app.root.update()
        trace = {
            "interruption": interruption,
            "events": events,
            "callback_errors": callback_errors,
            "screen": wizard.screen.name,
            "fatal_ui": app._fatal_ui,
            "ui_dead": app._ui_dead,
            "scheduled_after": list(app.root.tk.call("after", "info")) if not app._ui_dead else [],
            "native_calls": native_calls,
        }
        request.node.user_properties.append(("trace", json.dumps(trace)))
        print(json.dumps(trace))
        assert not native_calls
        if not interruption:
            assert events.count("poll") >= 2
            assert "cancel" not in events
        else:
            assert events.count("poll") >= 2 or "cancel" in events, trace
    finally:
        app._teardown()
