"""A live startup failure must retain the independent engine poweroff check.

UI, discovery, process inspection and power actions are fake. Session ownership
uses only the fixture's private temporary directory and ordinary lock files.
"""

from types import SimpleNamespace

import pytest

from beamo_wipe import app
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.session_recovery import SessionStore


@pytest.mark.parametrize("use_console", [True, False])
@pytest.mark.parametrize("report_wanted", [True, False])
@pytest.mark.parametrize("initial,late", [
    (False, False), (True, False), (None, False), ("error", False),
    (False, True), (False, None), (False, "error"),
])
def test_failed_live_startup_rechecks_external_engine_before_poweroff(
    tmp_path, monkeypatch, use_console, report_wanted, initial, late,
):
    powered = []
    inspected = []
    state = [initial]
    presented = []

    def probe():
        inspected.append(state[0])
        if state[0] == "error":
            raise OSError("fake unreadable process identity")
        return state[0]

    monkeypatch.setattr(app, "running_on_live_usb", lambda: True)
    monkeypatch.setattr("beamo_wipe.nwipe_runner.pinned_nwipe_already_running", probe)
    monkeypatch.setattr(app, "_shutdown", lambda: powered.append(True) or True)
    monkeypatch.setattr(
        "beamo_wipe.report_intent.ReportIntentStore",
        lambda: SimpleNamespace(load=lambda: report_wanted),
    )

    def failed_build(*_args):
        return app._blocked_wizard(OSError("fake startup discovery failure"))

    monkeypatch.setattr(app, "_build_wizard_with_console_stages", failed_build)
    monkeypatch.setattr(app, "_build_wizard_with_tk_stages", failed_build)

    def interface(wizard, **_kwargs):
        presented.append(wizard)
        assert wizard._startup_blocked and not wizard._recovered
        assert isinstance(wizard.runner, DryRunRunner) and not wizard.dry_run
        assert wizard.screen == Screen.PICK_BLOCKED
        wizard.shutdown()
        if report_wanted and initial is False:
            assert wizard.screen == Screen.SHUTDOWN_CONFIRM
            wizard.confirm_shutdown_without_saving(wizard.shutdown_generation)
        assert wizard.wants_shutdown is (initial is False)
        state[0] = late
        return 0

    monkeypatch.setattr("beamo_wipe.ui.console_wizard.run_console", interface)
    monkeypatch.setattr("beamo_wipe.ui.tk_wizard.run_tk", interface)
    # Leaving a refused shutdown keeps the same ownership boundary. No engine
    # was ever started by this test, so the fake renderer has nothing to settle.
    monkeypatch.setattr("beamo_wipe.wizard.Wizard.settle_failed_interface", lambda _self: None)
    args = SimpleNamespace(demo=False, lang="en", plain_console=False)
    store = SessionStore(
        tmp_path / "private", boot="00000000-0000-0000-0000-000000000001", build="a" * 64,
    ).open()
    try:
        assert not store.previous and not store.invalid and store.is_quiescent()
        assert app._run_one_session(
            args, session_store=store, use_console=use_console,
            want_accessible=False, fullscreen=False, reader=None,
        ) == 0
        assert len(presented) == 1 and inspected
        assert powered == ([True] if initial is False and late is False else [])
        assert presented[0]._wipe_request is None
    finally:
        store.close()


@pytest.mark.parametrize("dry_run,preview", [(True, False), (False, True)])
def test_startup_preview_does_not_inspect_host_processes(monkeypatch, dry_run, preview):
    monkeypatch.setattr(app, "running_on_live_usb", lambda: not dry_run)
    wizard = app._blocked_wizard(OSError("fake startup failure"))
    wizard.preview = preview

    def forbidden():
        pytest.fail("a preview must not inspect host processes")

    monkeypatch.setattr("beamo_wipe.nwipe_runner.pinned_nwipe_already_running", forbidden)
    assert wizard._live_pinned_engine_busy() is False
