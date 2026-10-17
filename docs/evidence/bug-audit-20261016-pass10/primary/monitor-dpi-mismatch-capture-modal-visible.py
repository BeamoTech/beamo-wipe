"""One fake-only GTK rollback screenshot; run after the parent grants its slot.

Use private XDG_RUNTIME_DIR, dbus-run-session and Xvfb -dpi 72. This helper
never enumerates devices, starts an erase, launches audio tools or powers off.
It uses the application's real 100 ms GTK timer to apply the fake audio job.
"""

from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
from unittest.mock import patch

from PIL import ImageGrab

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import audio_jobs, copy as C, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.power import PowerStatus
from beamo_wipe.ui import accessible_wizard, sound_dialog
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, GLib, Gtk
from test_accessible_sound_modal_pass10 import _state


ARTIFACTS = Path("/tmp/pass10-primary")
SCREENSHOT = ARTIFACTS / "modal-visible-rollback-72dpi.png"
METADATA = ARTIFACTS / "modal-visible-rollback-72dpi.json"


def forbidden(*_args, **_kwargs):
    raise AssertionError("A real device, engine, power or subprocess boundary was reached")


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    calls = []
    outputs = (
        sound.SoundOutput("speakers-fake", "Speakers", "Fake output 1", True),
        sound.SoundOutput("headphones-fake", "Headphones", "Fake output 2", False),
    )
    state = sound.SoundState(True, "", outputs, 40, False)
    worker = audio_jobs.AudioWorker()
    app = None
    result = {}
    failures = []
    main_loop = GLib.MainLoop()
    started = time.monotonic()
    phase = {"name": "opening", "paint_after": 0.0}

    def refuse_output(sink):
        calls.append({"operation": "set_output", "sink": sink})
        assert sink == "headphones-fake"
        return sound.SoundResult(False, C.SOUND_ACTION_FAILED)

    def assert_restored(controller):
        assert controller.ticket is None
        assert controller.chosen.id == "speakers-fake"
        assert [radio.get_active() for radio in controller.radios] == [True, False]
        assert all(radio.get_sensitive() for radio in controller.radios)
        assert controller._chosen_radio is controller.radios[0]
        assert controller.status.get_text() == C.SOUND_ACTION_FAILED
        assert app.w.sound_output == ""
        assert calls == [{"operation": "set_output", "sink": "headphones-fake"}]

    def inspect():
        try:
            if time.monotonic() - started > 10:
                raise AssertionError(f"GTK capture timed out during {phase['name']}")
            if phase["name"] == "opening":
                app.actions[C.SOUND_CHECK_BUTTON].clicked()
                phase["name"] = "discovery"
                return True
            controller = app._sound_dialog
            assert controller is not None and controller.dialog is not None
            if phase["name"] == "discovery":
                if controller.ticket is not None:
                    return True
                assert len(controller.radios) == 2
                assert [radio.get_active() for radio in controller.radios] == [True, False]
                controller.radios[1].set_active(True)
                phase["name"] = "refusal"
                return True
            if phase["name"] == "refusal":
                if controller.ticket is not None:
                    return True
                assert_restored(controller)
                phase["name"] = "paint"
                phase["paint_after"] = time.monotonic() + 0.15
                return True
            if time.monotonic() < phase["paint_after"]:
                return True
            assert_restored(controller)
            dialog = controller.dialog
            assert dialog.get_mapped()
            display = Gdk.Display.get_default()
            monitor = display.get_monitor_at_window(dialog.get_window())
            geometry = monitor.get_geometry()
            dpi_x = geometry.width * 25.4 / monitor.get_width_mm()
            dpi_y = geometry.height * 25.4 / monitor.get_height_mm()
            assert 71 <= dpi_x <= 73 and 71 <= dpi_y <= 73, (dpi_x, dpi_y)
            Gdk.Display.get_default().sync()
            native_state = _state(app, dialog)
            assert native_state["modal_above"] and native_state["modal_focused"], native_state
            assert dialog.get_focus() is controller.status
            captured = ImageGrab.grab(xdisplay=os.environ["DISPLAY"])
            width, height = captured.size
            assert (width, height) == (1600, 1000), (width, height)
            extrema = captured.getextrema()
            assert any(low != high for low, high in extrema), extrema
            captured.save(SCREENSHOT, format="PNG")
            result.update({
                "screenshot": str(SCREENSHOT),
                "sha256": hashlib.sha256(SCREENSHOT.read_bytes()).hexdigest(),
                "dimensions": [width, height],
                "pixel_extrema": extrema,
                "capture_method": "Pillow ImageGrab full private Xvfb root; no cropping or editing",
                "x11_dpi": [dpi_x, dpi_y],
                "native_state": native_state,
                "modal_status_child_focused": dialog.get_focus() is controller.status,
                "status": controller.status.get_text(),
                "accepted_sink": controller.chosen.id,
                "radio_active": [radio.get_active() for radio in controller.radios],
                "radio_sensitive": [radio.get_sensitive() for radio in controller.radios],
                "radio_labels": [radio.get_label() for radio in controller.radios],
                "persisted_output": app.w.sound_output,
                "calls": calls,
                "real_gtk_timer": True,
                "fake_boundaries_only": True,
            })
        except BaseException:
            failures.append(traceback.format_exc())
        main_loop.quit()
        return False

    with ExitStack() as patches:
        patches.enter_context(patch.object(audio_jobs, "worker", worker))
        patches.enter_context(patch.object(sound_dialog, "worker", worker))
        patches.enter_context(patch.object(sound, "list_outputs", lambda: state))
        patches.enter_context(patch.object(sound, "orca_running", lambda: True))
        patches.enter_context(patch.object(sound, "set_output", refuse_output))
        for name in ("nudge_volume", "set_muted", "play_speech_test", "play_test", "play_outcome"):
            patches.enter_context(patch.object(sound, name, forbidden))
        for name in ("_run", "_popen"):
            patches.enter_context(patch.object(sound, name, forbidden))
        for name in ("run_lsblk", "read_cmdline", "read_mount_sources"):
            patches.enter_context(patch(f"beamo_wipe.discover.{name}", forbidden))
        for target in (
            "beamo_wipe.nwipe_runner.NwipeRunner.start",
            "beamo_wipe.nwipe_runner.DryRunRunner.start",
            "beamo_wipe.app._shutdown",
            "subprocess.run",
            "subprocess.Popen",
        ):
            patches.enter_context(patch(target, forbidden))
        patches.enter_context(patch("beamo_wipe.app.running_on_live_usb", lambda: False))
        patches.enter_context(patch("beamo_wipe.wizard.read_power", lambda: PowerStatus(ac=True, complete=True)))
        patches.enter_context(patch("beamo_wipe.power.read_power", lambda: PowerStatus(ac=True, complete=True)))
        patches.enter_context(patch("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a: False))
        patches.enter_context(patch("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None))
        patches.enter_context(patch.object(accessible_wizard, "emit_serial_marker", lambda *_a: False))
        try:
            wizard = make_demo_wizard()
            assert wizard.dry_run and wizard.preview and wizard.power.reader is None
            wizard.skip_intro()
            wizard._apply_keyboard = forbidden
            app = AccessibleWizard(wizard)
            capture_timer = GLib.timeout_add(20, inspect)
            main_loop.run()
        finally:
            if "capture_timer" in locals():
                source = GLib.MainContext.default().find_source_by_id(capture_timer)
                if source is not None:
                    source.destroy()
            if app is not None:
                app.close()
            worker.close()
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
    if failures:
        raise AssertionError("\n".join(failures))
    assert result
    assert app.closed and (worker._thread is None or not worker._thread.is_alive())
    result["owned_window_closed"] = True
    result["owned_worker_retired"] = True
    METADATA.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
