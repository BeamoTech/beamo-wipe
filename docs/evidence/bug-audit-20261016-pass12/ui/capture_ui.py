"""Unedited native full-root captures of final fake-only UI recovery paths."""

from contextlib import ExitStack
import ctypes
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from unittest.mock import patch

from PIL import ImageGrab

os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
os.environ["BEAMO_WIPE_DEMO"] = "1"
os.environ.pop("BEAMO_WIPE_LIVE", None)

from beamo_wipe import audio_jobs, copy as C, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import sound_dialog, tk_wizard
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, Gtk


def forbidden(*_args, **_kwargs):
    raise AssertionError("Native application operation forbidden")


def drain(seconds=0.15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.002)


def main():
    assert os.environ.get("BEAMO_TEST_PRIVATE_DISPLAY") == os.environ["DISPLAY"]
    assert os.environ["DISPLAY"] not in (":0", ":1", ":99")
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int)]
    for name in ("XDisplayWidth", "XDisplayHeight", "XDisplayWidthMM", "XDisplayHeightMM"):
        getattr(x11, name).argtypes = [ctypes.c_void_p, ctypes.c_int]
        getattr(x11, name).restype = ctypes.c_int
    connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert connection
    worker = audio_jobs.AudioWorker()
    states = []
    screen = x11.XDefaultScreen(connection)
    width, height, width_mm, height_mm = (getattr(x11, name)(connection, screen) for name in ("XDisplayWidth", "XDisplayHeight", "XDisplayWidthMM", "XDisplayHeightMM"))
    dpi = width * 25.4 / width_mm, height * 25.4 / height_mm
    assert all(71 < value < 73 for value in dpi), dpi

    def focused():
        window, revert = ctypes.c_ulong(), ctypes.c_int()
        x11.XGetInputFocus(connection, ctypes.byref(window), ctypes.byref(revert))
        return window.value

    def capture(name, native):
        Gdk.Display.get_default().sync()
        image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"])
        assert image.size == (width, height)
        assert any(low != high for low, high in image.getextrema())
        target = Path(f"/tmp/pass12-ui/{name}-{width}x{height}-72dpi.png")
        image.save(target, format="PNG")
        states.append({"surface": name, "image": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "root_size": [width, height], "xserver_dpi": dpi, "native": native, "focused_xid": focused(), "capture": "Pillow full private-Xvfb root; unedited"})

    try:
        with ExitStack() as patches:
            patches.enter_context(patch.object(audio_jobs, "worker", worker))
            patches.enter_context(patch.object(sound_dialog, "worker", worker))
            for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen", "beamo_wipe.sound.set_output", "beamo_wipe.sound.nudge_volume", "beamo_wipe.sound.set_muted", "beamo_wipe.sound.play_speech_test", "beamo_wipe.sound.play_test", "beamo_wipe.sound.play_outcome"):
                patches.enter_context(patch(target, forbidden))
            outputs = tuple(sound.SoundOutput(f"fake-{index}", f"HDMI sound {index + 1}", "Fake output", index == 0) for index in range(16))
            patches.enter_context(patch.object(sound, "list_outputs", lambda: sound.SoundState(True, "", outputs, 40, False)))
            patches.enter_context(patch.object(sound, "orca_running", lambda: True))
            wizard = make_demo_wizard()
            wizard.skip_intro()
            wizard.screen = Screen.WORKING
            app = AccessibleWizard(wizard, fullscreen=True)
            try:
                app.actions[C.SOUND_CHECK_BUTTON].clicked()
                drain(0.4)
                controller = app._sound_dialog
                assert controller.ticket is None
                dialog = controller.dialog
                assert dialog is not None and dialog.get_mapped()
                assert focused() == dialog.get_window().get_xid()
                capture("sound-working-16outputs", {"size": tuple(dialog.get_size()), "origin": tuple(dialog.get_window().get_origin())[-2:], "xid": dialog.get_window().get_xid(), "gtk_child_focus": dialog.get_focus() is controller.status, "outputs": len(controller.radios), "modal": dialog.get_modal()})
            finally:
                app.close()
                drain()
            patches.enter_context(patch.object(tk_wizard, "_ensure_tk_display", lambda: None))
            for fullscreen in (False, True):
                release, finished = threading.Event(), threading.Event()
                real_tk = tk_wizard.tk.Tk
                errors = []

                def build(_report):
                    try:
                        assert release.wait(timeout=2)
                        return object()
                    finally:
                        finished.set()

                def factory():
                    root = real_tk()

                    def inspect():
                        try:
                            size = root.winfo_width(), root.winfo_height()
                            origin = root.winfo_rootx(), root.winfo_rooty()
                            assert root.winfo_ismapped() and root.focus_get() is root
                            if fullscreen:
                                assert size == (width, height) and origin == (0, 0)
                            else:
                                assert size == (min(640, width), min(440, height))
                                assert origin == ((width - size[0]) // 2, (height - size[1]) // 2)
                            capture("tk-startup-fullscreen" if fullscreen else "tk-startup-windowed", {"size": size, "origin": origin, "tk_xid": root.winfo_id(), "tk_focused": True, "fullscreen": fullscreen})
                        except BaseException as error:
                            errors.append(error)
                        root.destroy()

                    root.after(200, inspect)
                    return root

                with patch.object(tk_wizard.tk, "Tk", factory):
                    try:
                        assert tk_wizard.run_tk_startup(build, fullscreen=fullscreen) == ("abandoned", None)
                        assert not errors, errors
                    finally:
                        release.set()
                        assert finished.wait(timeout=1)
    finally:
        worker.close()
        x11.XCloseDisplay(connection)
    output = {"display": os.environ["DISPLAY"], "states": states, "owned_teardown": True}
    Path(f"/tmp/pass12-ui/final-capture-{width}x{height}.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
