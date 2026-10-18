"""Native GTK input must survive sound-modal and startup focus changes."""

import ctypes
import os
import threading
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import audio_jobs, copy as C, sound  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.ui import accessible_wizard, sound_dialog  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gdk, GLib, Gtk  # noqa: E402
from test_accessible_runtime import drain, ui, wait_sound  # noqa: E402, F401
from test_accessible_sound_modal_pass10 import _state  # noqa: E402
from test_accessible_sound_review_pass15_ui import _review  # noqa: E402


@pytest.fixture
def native():
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native input requires an explicitly isolated X11 display")
    display = Gdk.Display.get_default()
    if display is None or display.__gtype__.name != "GdkX11Display":
        pytest.skip("Native input requires Linux X11")
    x11 = ctypes.CDLL("libX11.so.6")
    xtst = ctypes.CDLL("libXtst.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XKeysymToKeycode.restype = ctypes.c_uint
    x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeKeyEvent.restype = ctypes.c_int
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert connection
    down = set()

    class Input:
        @staticmethod
        def key(keyval, pressed):
            code = x11.XKeysymToKeycode(connection, keyval)
            assert code
            assert xtst.XTestFakeKeyEvent(connection, code, int(pressed), 0)
            if pressed:
                down.add(code)
            else:
                down.discard(code)
            x11.XSync(connection, False)
            Gdk.Display.get_default().sync()
            drain()

        @staticmethod
        def pointer(x, y):
            assert xtst.XTestFakeMotionEvent(connection, -1, x, y, 0)
            x11.XSync(connection, False)

        @staticmethod
        def root_focus():
            x11.XSetInputFocus(connection, 1, 0, 0)
            x11.XSync(connection, False)

    try:
        yield Input
    finally:
        for code in down:
            xtst.XTestFakeKeyEvent(connection, code, 0, 0)
        x11.XSync(connection, False)
        x11.XCloseDisplay(connection)
        drain()


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("A native application effect was reached")

    state = sound.SoundState(True, "", (
        sound.SoundOutput("speaker-fake", "Speakers", "Fake output", True),
    ), 40, False)
    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs, "worker", worker)
    monkeypatch.setattr(sound_dialog, "worker", worker)
    monkeypatch.setattr(sound, "list_outputs", lambda: state)
    monkeypatch.setattr(sound, "orca_running", lambda: True)
    for name in ("set_output", "nudge_volume", "set_muted", "play_speech_test", "play_test", "play_outcome", "_run", "_popen"):
        monkeypatch.setattr(sound, name, forbidden)
    for target in ("beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "subprocess.run", "subprocess.Popen"):
        monkeypatch.setattr(target, forbidden)
    yield
    worker.close()


def _wait(predicate):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        drain()
        if predicate():
            return
        time.sleep(0.005)
    assert predicate(), "Owned GTK input did not settle"


def _owner():
    wizard = make_demo_wizard()
    wizard.skip_intro()
    return wizard


def _opened(app):
    return app._sound_dialog is not None and app._sound_dialog.dialog is not None


def _open_with_key(app, native, keyval):
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    native.key(keyval, True)
    if keyval == Gdk.KEY_space:
        native.key(keyval, False)
    _wait(lambda: _opened(app))
    wait_sound(app)
    controller = app._sound_dialog
    if keyval != Gdk.KEY_space:
        native.key(keyval, False)
    return controller


@pytest.mark.parametrize("keyval", [Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space])
def test_native_release_during_sound_dialog_reaches_parent_guard(ui, native, keyval):  # noqa: F811
    app = ui(_owner())
    controller = _open_with_key(app, native, keyval)
    drain()
    assert keyval not in app.held, {"held": app.held, "native": _state(app, controller.dialog)}


@pytest.mark.parametrize("keyval", [Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space])
def test_first_fresh_native_activation_after_sound_close_is_not_lost(ui, native, keyval):  # noqa: F811
    app = ui(_owner())
    controller = _open_with_key(app, native, keyval)
    controller.close()
    drain()
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    native.key(keyval, True)
    native.key(keyval, False)
    _wait(lambda: _opened(app))
    assert app._sound_dialog is not controller


@pytest.mark.parametrize("keyval", [Gdk.KEY_Return, Gdk.KEY_KP_Enter])
def test_modal_open_redraw_close_without_keyup_preserves_hold(ui, native, keyval):  # noqa: F811
    app = ui(_owner())
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    native.key(keyval, True)
    _wait(lambda: _opened(app))
    assert keyval in app.held
    app.render()
    assert keyval in app.held
    app._sound_dialog.close()
    drain()
    assert keyval in app.held
    native.key(keyval, False)
    _wait(lambda: keyval not in app.held)


@pytest.mark.parametrize("keyval", [Gdk.KEY_Return, Gdk.KEY_KP_Enter])
def test_modal_keyup_keeps_same_timestamp_review_repeat_guard(ui, native, keyval):  # noqa: F811
    wizard, clock = _review()
    calls = []
    wizard.begin_erase = lambda: calls.append("erase")
    app = ui(wizard)
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    press = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
    press.keyval, press.time = keyval, 1000
    assert app._key_press(app.window, press)
    controller = app._sound_dialog
    wait_sound(app)
    assert keyval in app.held
    release = Gdk.Event.new(Gdk.EventType.KEY_RELEASE)
    release.keyval, release.time = keyval, 1010
    controller.dialog.emit("key-release-event", release)
    controller.close()
    drain()
    clock.value = 5.0
    app.update_status()
    app.actions[C.BTN_ERASE].grab_focus()
    press.time = 1010
    assert app._key_press(app.window, press)
    assert calls == []
    assert wizard.screen.name == "LAST_CHANCE" and not wizard.runner.started


@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("pointer_inside", [False, True])
def test_first_accessible_startup_accepts_native_escape(
    native, monkeypatch, fullscreen, pointer_inside
):
    native.root_focus()
    native.pointer(100, 100) if pointer_inside else native.pointer(1550, 950)
    monkeypatch.setattr(accessible_wizard, "_ensure_gtk_display", lambda: None)
    release = threading.Event()
    finished = threading.Event()
    seen = {}
    fallback_fired = []

    def build(_report):
        try:
            assert release.wait(timeout=2)
            return object()
        finally:
            finished.set()

    def send_escape():
        windows = [window for window in Gtk.Window.list_toplevels() if window.get_mapped() and window.get_title() == C.STARTING_TITLE]
        assert len(windows) == 1
        window = windows[0]
        seen["window"] = window
        seen["xid"] = window.get_window().get_xid()
        seen["gtk_focus"] = window.get_focus() is not None
        native.key(Gdk.KEY_Escape, True)
        native.key(Gdk.KEY_Escape, False)
        return False

    def rescue():
        fallback_fired.append(True)
        windows = [window for window in Gtk.Window.list_toplevels() if window.get_mapped() and window.get_title() == C.STARTING_TITLE]
        for window in windows:
            window.emit("delete-event", None)
        return False

    GLib.timeout_add(100, send_escape)
    fallback = GLib.timeout_add(350, rescue)
    try:
        outcome = accessible_wizard.run_accessible_startup(build, fullscreen=fullscreen)
        assert outcome == ("abandoned", None)
        assert seen["gtk_focus"]
        assert not fallback_fired, {"fullscreen": fullscreen, "pointer_inside": pointer_inside, "startup_xid": seen["xid"]}
    finally:
        release.set()
        assert finished.wait(timeout=1)
        if not fallback_fired:
            GLib.source_remove(fallback)
        drain()
