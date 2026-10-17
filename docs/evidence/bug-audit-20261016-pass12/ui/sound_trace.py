"""Native fake-only sound-dialog geometry and failed-restore trace."""

from contextlib import ExitStack
from dataclasses import replace
import json
import os
from pathlib import Path
import time
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import audio_jobs, copy as C, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import sound_dialog
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, Gtk


def forbidden(*_args, **_kwargs):
    raise AssertionError("External native operation forbidden")


def drain(seconds=0.06):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.002)


def settle(controller):
    deadline = time.monotonic() + 2
    while controller.ticket is not None and time.monotonic() < deadline:
        controller.poll()
        drain(0.005)
    assert controller.ticket is None
    drain()


def widgets(widget):
    yield widget
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            yield from widgets(child)


def rectangle(widget, window):
    translated = widget.translate_coordinates(window, 0, 0)
    assert translated is not None
    allocation = widget.get_allocation()
    origin = tuple(window.get_window().get_origin())[-2:]
    return [origin[0] + translated[0], origin[1] + translated[1], allocation.width, allocation.height]


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    worker = audio_jobs.AudioWorker()
    results = []
    try:
        with ExitStack() as patches:
            patches.enter_context(patch.object(audio_jobs, "worker", worker))
            patches.enter_context(patch.object(sound_dialog, "worker", worker))
            for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen", "beamo_wipe.sound.nudge_volume", "beamo_wipe.sound.set_muted", "beamo_wipe.sound.play_test", "beamo_wipe.sound.play_outcome", "beamo_wipe.sound.play_speech_test"):
                patches.enter_context(patch(target, forbidden))
            patches.enter_context(patch.object(sound, "orca_running", lambda: True))
            for working in (False, True):
                for count in (1, 2, 8, 16):
                    outputs = tuple(sound.SoundOutput(f"sink-{index}", f"HDMI sound {index + 1}", f"fake-hdmi-{index}", index == 0) for index in range(count))
                    state = sound.SoundState(True, "", outputs, 40, False)
                    with patch.object(sound, "list_outputs", lambda: state), patch.object(sound, "set_output", forbidden):
                        wizard = make_demo_wizard()
                        wizard.skip_intro()
                        wizard.screen = Screen.WORKING if working else Screen.OWNER
                        app = AccessibleWizard(wizard)
                        try:
                            app.open_sound_check()
                            controller = app._sound_dialog
                            settle(controller)
                            dialog = controller.dialog
                            monitor = dialog.get_display().get_monitor_at_window(dialog.get_window())
                            work = monitor.get_workarea()
                            bounds = [work.x, work.y, work.width, work.height]
                            buttons = {widget.get_label(): rectangle(widget, dialog) for widget in widgets(dialog) if isinstance(widget, Gtk.Button) and widget.get_label() in (C.SOUND_CLOSE, C.STOP_ASK)}
                            if working and count == 8 and os.environ.get("PASS12_CAPTURE") == "1":
                                from PIL import ImageGrab
                                Gdk.Display.get_default().sync()
                                captured = ImageGrab.grab(xdisplay=os.environ["DISPLAY"])
                                assert captured.size == (800, 600)
                                assert any(low != high for low, high in captured.getextrema())
                                captured.save(f"/tmp/pass12-ui/{os.environ.get('PASS12_TRACE_LABEL', 'original')}-sound8-working-800x600.png")
                            results.append({"kind": "geometry", "working": working, "outputs": count, "monitor": bounds, "dialog_size": tuple(dialog.get_size()), "buttons": buttons, "buttons_within_monitor": all(rect[1] >= work.y and rect[1] + rect[3] <= work.y + work.height for rect in buttons.values())})
                        finally:
                            app.close()
                            drain()
            outputs = (sound.SoundOutput("speakers", "Speakers", "fake", True), sound.SoundOutput("headphones", "Headphones", "fake", False))
            state = sound.SoundState(True, "", outputs, 30, False)
            calls = []

            def refusal(sink):
                calls.append(sink)
                return sound.SoundResult(False, "Controlled remembered restore refused")

            with patch.object(sound, "list_outputs", lambda: state), patch.object(sound, "set_output", refusal):
                wizard = make_demo_wizard()
                wizard.skip_intro()
                wizard.set_sound_output("headphones")
                app = AccessibleWizard(wizard)
                try:
                    app.open_sound_check()
                    controller = app._sound_dialog
                    settle(controller)
                    controller.radios[1].set_active(True)
                    settle(controller)
                    results.append({"kind": "remembered-restore-refusal", "default_sink": "speakers", "chosen_sink": controller.chosen.id, "radios": [radio.get_active() for radio in controller.radios], "calls_after_same_choice_retry": calls, "status": controller.status.get_text(), "stored_preference": wizard.sound_output})
                finally:
                    app.close()
                    drain()
    finally:
        worker.close()
    result = {"display": os.environ["DISPLAY"], "results": results, "owned_teardown": True}
    label = os.environ.get("PASS12_TRACE_LABEL", "original")
    target = Path(f"/tmp/pass12-ui/{label}-sound-trace.json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
