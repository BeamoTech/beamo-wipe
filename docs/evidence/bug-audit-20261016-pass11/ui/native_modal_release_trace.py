"""Native input on a private Xvfb only; all app external effects forbidden."""

import ctypes
import json
import os
from contextlib import ExitStack
from pathlib import Path
import time
from unittest.mock import patch

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import audio_jobs, copy as C, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import sound_dialog
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, Gtk


def forbidden(*args, **kwargs):
    raise AssertionError("External app effect forbidden")


def drain(seconds=0.03):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.002)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    x11 = ctypes.CDLL("libX11.so.6")
    xtst = ctypes.CDLL("libXtst.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XKeysymToKeycode.restype = ctypes.c_uint
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeKeyEvent.restype = ctypes.c_int
    native = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert native

    def key(keysym, pressed):
        code = x11.XKeysymToKeycode(native, keysym)
        assert code
        assert xtst.XTestFakeKeyEvent(native, code, int(pressed), 0)
        x11.XSync(native, False)
        drain(0.25 if pressed else 0.05)

    state = sound.SoundState(True, "", (
        sound.SoundOutput("speaker-fake", "Speakers", "Fake output", True),
    ), 40, False)
    worker = audio_jobs.AudioWorker()
    app = None
    events = []
    snapshots = []
    try:
        with ExitStack() as patches:
            patches.enter_context(patch.object(audio_jobs, "worker", worker))
            patches.enter_context(patch.object(sound_dialog, "worker", worker))
            patches.enter_context(patch.object(sound, "list_outputs", lambda: state))
            patches.enter_context(patch.object(sound, "orca_running", lambda: True))
            for name in ("set_output", "nudge_volume", "set_muted", "play_speech_test", "play_test", "play_outcome", "_run", "_popen"):
                patches.enter_context(patch.object(sound, name, forbidden))
            for name in ("run_lsblk", "read_cmdline", "read_mount_sources"):
                patches.enter_context(patch(f"beamo_wipe.discover.{name}", forbidden))
            for target in ("beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "subprocess.run", "subprocess.Popen"):
                patches.enter_context(patch(target, forbidden))
            wizard = make_demo_wizard()
            wizard.skip_intro()
            app = AccessibleWizard(wizard)
            drain(0.1)

            def snapshot(phase):
                controller = app._sound_dialog
                snapshots.append({
                    "phase": phase,
                    "held": sorted(app.held),
                    "release_times": dict(app._release_times),
                    "modal_open": controller is not None and controller.dialog is not None,
                    "screen": app.w.screen.name,
                })

            app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
            snapshot("parent-ready")
            key(Gdk.KEY_Return, True)
            drain(0.1)
            snapshot("return-pressed-opened-dialog")
            controller = app._sound_dialog
            assert controller is not None and controller.dialog is not None
            controller.dialog.connect("key-release-event", lambda _widget, event: events.append({"target": "modal", "key": event.keyval, "time": event.time}) or False)
            key(Gdk.KEY_Return, False)
            snapshot("release-routed-to-modal")
            controller.dialog.response(Gtk.ResponseType.CLOSE)
            drain(0.1)
            snapshot("modal-closed")
            app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
            key(Gdk.KEY_Return, True)
            snapshot("next-fresh-return-pressed")
            key(Gdk.KEY_Return, False)
            snapshot("next-fresh-return-released")
            if app._sound_dialog.dialog is not None:
                app._sound_dialog.close()
                drain()
            app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
            key(Gdk.KEY_Return, True)
            snapshot("third-return-pressed-control")
            key(Gdk.KEY_Return, False)
            snapshot("third-return-released-control")
    finally:
        if app is not None:
            app.close()
        worker.close()
        x11.XCloseDisplay(native)
        drain()
        result = {"display": os.environ["DISPLAY"], "events": events, "snapshots": snapshots, "owned_teardown": True}
        Path("/tmp/pass11-ui/native-modal-release-trace.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
