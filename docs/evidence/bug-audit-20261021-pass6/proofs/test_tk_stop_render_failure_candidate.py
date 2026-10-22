"""Outside-Git proof: dispatched Stop click with a one-shot Tk Label failure."""
import json
import time
import tkinter as tk

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui.tk_wizard import TkWizard, _Button
from beamo_wipe.wizard import Wizard


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


@pytest.mark.parametrize("fail_label", [False, True], ids=["normal-control", "label-failed"])
def test_stop_callback_keeps_a_usable_owned_interface(fail_label, monkeypatch, tmp_path, request):
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
    app = TkWizard(wizard)
    callback_errors = []
    original_report = app.root.report_callback_exception

    def report_callback(kind, value, tb):
        callback_errors.append(kind.__name__)
        original_report(kind, value, tb)

    app.root.report_callback_exception = report_callback
    try:
        app.root.update()
        stop = next(widget for widget in descendants(app.root)
                    if isinstance(widget, _Button) and widget.itemcget(widget._label, "text") == C.STOP_ASK)
        original_label = tk.Label.__init__
        failed = []

        def label(self, *args, **kwargs):
            if fail_label and not failed:
                failed.append(True)
                raise tk.TclError("fake one-shot Tcl widget allocation error")
            return original_label(self, *args, **kwargs)

        monkeypatch.setattr(tk.Label, "__init__", label)
        stop.event_generate("<ButtonPress-1>", x=10, y=10)
        stop.event_generate("<ButtonRelease-1>", x=10, y=10)
        for _ in range(3):
            time.sleep(0.12)
            if not app._ui_dead:
                app.root.update()
        buttons = [] if app._ui_dead else [widget.itemcget(widget._label, "text") for widget in descendants(app.root)
                                         if isinstance(widget, _Button)]
        trace = {"fail_label": fail_label, "callback_errors": callback_errors,
                 "buttons": buttons, "stop_pending": wizard.stop_confirmation is not None,
                 "screen": wizard.screen.name, "ui_dead": app._ui_dead,
                 "fatal_ui": app._fatal_ui, "native_calls": native_calls}
        request.node.user_properties.append(("trace", json.dumps(trace)))
        print(json.dumps(trace))
        assert not native_calls
        assert app._ui_dead or C.STOP_CONFIRM in buttons, trace
    finally:
        app._teardown()
