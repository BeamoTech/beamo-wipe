"""Native Tk callback failures retain erase ownership until system settlement."""

import time
import tkinter as tk

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui.tk_wizard import TkWizard, _Button
from beamo_wipe.wizard import Wizard


def _descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from _descendants(child)


def _button(app, text):
    return next(widget for widget in _descendants(app.root)
                if isinstance(widget, _Button)
                and widget.itemcget(widget._label, "text") == text)


def _click(button):
    button.update_idletasks()
    button.event_generate("<ButtonPress-1>", x=10, y=10)
    button.event_generate("<ButtonRelease-1>", x=10, y=10)


@pytest.fixture
def running_ui(monkeypatch, tmp_path):
    try:
        probe = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    probe.withdraw()
    probe.destroy()
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
    runner = DryRunRunner(clock=lambda: clock[0], duration_s=100)
    wizard = Wizard(discovery_for_scenario("happy"), runner,
                    clock=lambda: clock[0], dry_run=True)
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
    app = TkWizard(wizard)
    app.root.update()
    yield wizard, app
    app._teardown()
    assert not effects


def _drain(app):
    for _ in range(3):
        time.sleep(0.12)
        if not app._ui_dead:
            app.root.update()


@pytest.mark.parametrize("interruption", [False, True], ids=["normal", "interrupted-poll"])
def test_scheduled_poll_callback_keeps_monitoring_or_settles(running_ui, monkeypatch, interruption):
    wizard, app = running_ui
    original_poll = wizard.runner.poll
    polls = []

    def poll(request):
        polls.append(True)
        if interruption and len(polls) == 1:
            raise KeyboardInterrupt("Fake poll interruption")
        return original_poll(request)

    monkeypatch.setattr(wizard.runner, "poll", poll)
    app.root.after_cancel(app._after_id)
    app._after_id = app.root.after(0, app._tick)
    app.root.update()
    _drain(app)
    if interruption:
        assert app._fatal_ui and app._ui_dead
        assert wizard.runner.cancelled
        assert wizard.wipe_result is not None
        assert wizard._interface_failed
        assert not wizard.wants_shutdown
    else:
        assert len(polls) >= 2
        assert not app._fatal_ui and not app._ui_dead
        assert not wizard.runner.cancelled
        assert app._after_id in app.root.tk.call("after", "info")


@pytest.mark.parametrize("error_kind", [None, tk.TclError, KeyboardInterrupt],
                         ids=["normal", "widget-error", "widget-interrupted"])
def test_native_stop_callback_failure_settles_before_destroying(running_ui, monkeypatch, error_kind):
    wizard, app = running_ui
    stop = _button(app, C.STOP_ASK)
    original_label = tk.Label.__init__
    failures = []

    def label(self, *args, **kwargs):
        if error_kind is not None and not failures:
            failures.append(True)
            raise error_kind("Fake one-shot widget allocation failure")
        return original_label(self, *args, **kwargs)

    monkeypatch.setattr(tk.Label, "__init__", label)
    _click(stop)
    _drain(app)
    if error_kind is not None:
        assert failures
        assert app._fatal_ui and app._ui_dead
        assert wizard.runner.cancelled
        assert wizard.wipe_result is not None
        assert wizard._interface_failed
        assert not wizard.wants_shutdown
    else:
        assert wizard.stop_confirmation is not None
        assert _button(app, C.STOP_CONFIRM)
        _click(_button(app, C.STOP_KEEP))
        assert wizard.stop_confirmation is None
        assert not wizard.runner.cancelled
        _click(_button(app, C.STOP_ASK))
        assert wizard.stop_confirmation is not None
        assert _button(app, C.STOP_CONFIRM)


@pytest.mark.parametrize("diagnostic_error", [OSError, KeyboardInterrupt])
def test_callback_recovery_does_not_depend_on_optional_diagnostics(running_ui, monkeypatch, diagnostic_error):
    wizard, app = running_ui

    def broken_log(*_args):
        raise diagnostic_error("Fake diagnostic failure")

    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", broken_log)
    app.root.after(0, lambda: (_ for _ in ()).throw(RuntimeError("Fake native callback failure")))
    app.root.update()
    assert app._fatal_ui and app._ui_dead
    assert wizard.runner.cancelled
    assert wizard.wipe_result is not None


def test_callback_failure_preserves_peer_root_and_is_idempotent(running_ui):
    wizard, app = running_ui
    peer = tk.Tk()
    peer.withdraw()
    callbacks = []
    peer.after(0, lambda: callbacks.append(True))
    try:
        app.root.after(0, lambda: (_ for _ in ()).throw(RuntimeError("Fake owned callback failure")))
        app.root.update()
        peer.update()
        assert callbacks == [True]
        assert peer.winfo_exists()
        assert app._fatal_ui and app._ui_dead
        result = wizard.wipe_result
        assert result is not None and wizard.runner.cancelled
        app._runtime_failure(RuntimeError, RuntimeError("Late callback"), None)
        app._teardown()
        assert wizard.wipe_result == result
        assert peer.winfo_exists()
    finally:
        peer.destroy()
