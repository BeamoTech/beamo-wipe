"""GTK modals must stay visible and focused on the live kiosk's bare X11."""

import ctypes
import os
import sys
from contextlib import contextmanager

import pytest

pytest.importorskip("gi")
from beamo_wipe import audio_jobs, copy as C  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.methods import DEFAULT_METHOD  # noqa: E402
from beamo_wipe.models import Screen, WipeRequest  # noqa: E402
from beamo_wipe.ui import sound_dialog  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gdk, Gtk  # noqa: E402
from test_accessible_runtime import (  # noqa: E402, F401
    _canned_sound,
    _dialog_button,
    drain,
    ui,
    wait_sound,
)
from test_accessible_sound_review_pass15_ui import _review  # noqa: E402


@pytest.fixture(autouse=True)
def _requires_x11():
    if not sys.platform.startswith("linux"):
        pytest.skip("Native modal stacking checks require Linux X11")
    display = Gdk.Display.get_default()
    if display is None or display.__gtype__.name != "GdkX11Display":
        pytest.skip("Native modal stacking checks require an X11 display")


@contextmanager
def _x11():
    """Read stacking/focus from the test display; never send X11 input."""
    library = ctypes.CDLL("libX11.so.6")
    window = ctypes.c_ulong
    pointer = ctypes.POINTER(window)
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]
    library.XOpenDisplay.restype = ctypes.c_void_p
    library.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    library.XDefaultRootWindow.restype = window
    library.XQueryTree.argtypes = [
        ctypes.c_void_p, window, ctypes.POINTER(window), ctypes.POINTER(window),
        ctypes.POINTER(pointer), ctypes.POINTER(ctypes.c_uint),
    ]
    library.XQueryTree.restype = ctypes.c_int
    library.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(window), ctypes.POINTER(ctypes.c_int)]
    library.XFree.argtypes = [ctypes.c_void_p]
    library.XCloseDisplay.argtypes = [ctypes.c_void_p]
    display = library.XOpenDisplay(os.environ["DISPLAY"].encode())
    assert display, "The modal regression needs its isolated X11 display"
    root = library.XDefaultRootWindow(display)

    def tree(xid):
        tree_root, parent = window(), window()
        children, count = pointer(), ctypes.c_uint()
        assert library.XQueryTree(display, xid, ctypes.byref(tree_root), ctypes.byref(parent), ctypes.byref(children), ctypes.byref(count))
        try:
            return parent.value, [children[index] for index in range(count.value)]
        finally:
            if children:
                library.XFree(children)

    def ancestors(xid):
        result = []
        while xid not in (0, 1, root):
            result.append(xid)
            xid, _children = tree(xid)
        return result

    try:
        focused, revert = window(), ctypes.c_int()
        library.XGetInputFocus(display, ctypes.byref(focused), ctypes.byref(revert))
        _parent, stack = tree(root)
        yield stack, focused.value, ancestors
    finally:
        library.XCloseDisplay(display)


def _state(app, modal=None):
    drain()
    Gdk.Display.get_default().sync()
    parent = app.window.get_window().get_xid()
    with _x11() as (stack, focused, ancestors):
        result = {"parent": parent, "focused": focused, "stack": stack}
        result["parent_focused"] = parent in ancestors(focused)
        if modal is not None:
            child = modal.get_window().get_xid()
            parent_frame, child_frame = ancestors(parent)[-1], ancestors(child)[-1]
            result.update({
                "modal": child,
                "modal_above": stack.index(child_frame) > stack.index(parent_frame),
                "modal_focused": child in ancestors(focused),
            })
        return result


@pytest.fixture
def fake_audio(monkeypatch):
    calls = []
    _canned_sound(monkeypatch, calls)
    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs, "worker", worker)
    monkeypatch.setattr(sound_dialog, "worker", worker)
    yield calls
    worker.close()


def _owner():
    wizard = make_demo_wizard()
    wizard.skip_intro()
    return wizard


def _open(app):
    app.actions[C.SOUND_CHECK_BUTTON].clicked()
    wait_sound(app)
    return app._sound_dialog


def _assert_modal(app, controller):
    state = _state(app, controller.dialog)
    assert state["modal_above"] and state["modal_focused"], state


def test_owner_without_modal_has_keyboard_focus(ui):  # noqa: F811
    app = ui(_owner())
    state = _state(app)
    assert state["parent_focused"], state


def test_sound_button_keeps_dialog_above_parent_with_keyboard_focus(ui, fake_audio):  # noqa: F811
    app = ui(_owner())
    controller = _open(app)
    _assert_modal(app, controller)


def test_existing_sound_dialog_reopen_keeps_the_same_modal_visible(ui, fake_audio):  # noqa: F811
    app = ui(_owner())
    controller = _open(app)
    app.actions[C.SOUND_CHECK_BUTTON].clicked()
    drain()
    assert app._sound_dialog is controller
    assert [window for window in Gtk.Window.list_toplevels() if isinstance(window, Gtk.Dialog) and window.get_mapped()] == [controller.dialog]
    _assert_modal(app, controller)


@pytest.mark.parametrize("screen", [Screen.OWNER, Screen.WORKING, Screen.LAST_CHANCE])
def test_parent_rerender_preserves_sound_modal_stacking_and_focus(ui, fake_audio, screen):  # noqa: F811
    wizard = _review()[0] if screen == Screen.LAST_CHANCE else _owner()
    wizard.screen = screen
    app = ui(wizard)
    controller = _open(app)
    # Establish a correct native stack independently of the opening bug.
    controller.dialog.present()
    controller.dialog.get_window().focus(Gdk.CURRENT_TIME)
    controller.radios[1].grab_focus()
    _assert_modal(app, controller)
    app.render()
    _assert_modal(app, controller)
    assert controller.dialog.get_focus() is controller.radios[1]


@pytest.mark.parametrize("response", ["response", "close"])
def test_sound_close_returns_keyboard_focus_to_the_parent(ui, fake_audio, response):  # noqa: F811
    app = ui(_owner())
    controller = _open(app)
    controller.dialog.present()
    controller.dialog.get_window().focus(Gdk.CURRENT_TIME)
    _assert_modal(app, controller)
    if response == "response":
        controller.dialog.response(Gtk.ResponseType.CLOSE)
    else:
        controller.close()
    assert controller.dialog is None
    state = _state(app)
    assert state["parent_focused"], state
    focused = app.window.get_focus()
    assert focused is app.arrival
    assert focused.get_toplevel() is app.window and focused.get_mapped()


def test_sound_review_close_starts_a_fresh_visible_countdown(ui, fake_audio):  # noqa: F811
    wizard, clock = _review()
    app = ui(wizard)
    controller = _open(app)
    clock.value = 10.0
    app.tick()
    assert not wizard.erase_enabled
    controller.dialog.response(Gtk.ResponseType.CLOSE)
    drain()
    assert wizard.countdown_left == 5.0
    assert not wizard.erase_enabled
    clock.value = 15.0
    assert wizard.erase_enabled


@pytest.mark.parametrize("same_screen_revisit", [False, True])
def test_direct_render_closes_sound_modal_from_an_obsolete_screen_epoch(
    ui, fake_audio, same_screen_revisit  # noqa: F811
):
    app = ui(_owner())
    controller = _open(app)
    app.w.screen = Screen.KEYBOARD
    if same_screen_revisit:
        app.w.screen = Screen.OWNER
    app.render()
    assert controller.dialog is None
    state = _state(app)
    assert state["parent_focused"], state


def test_sound_revision_tick_keeps_modal_child_focus(ui, fake_audio):  # noqa: F811
    wizard = _owner()
    wizard.screen = Screen.WORKING
    app = ui(wizard)
    controller = _open(app)
    controller.radios[1].grab_focus()
    wizard.set_sound_message("Controlled fake sound update")
    app.tick()
    _assert_modal(app, controller)
    assert controller.dialog.get_focus() is controller.radios[1]
    app.tick()
    _assert_modal(app, controller)
    assert controller.dialog.get_focus() is controller.radios[1]


def test_stop_from_sound_returns_to_the_running_confirmation(ui, fake_audio):  # noqa: F811
    wizard = _owner()
    wizard.screen = Screen.WORKING
    wizard._wipe_request = WipeRequest(
        "/dev/fake-target", DEFAULT_METHOD, "/dev/fake-boot", "/tmp/fake-modal.log"
    )
    app = ui(wizard)
    controller = _open(app)
    _dialog_button(controller.dialog, C.STOP_ASK).clicked()
    assert controller.dialog is None
    assert wizard.screen == Screen.WORKING
    assert wizard.stop_confirmation is not None
    assert C.STOP_KEEP in app.actions and C.STOP_CONFIRM in app.actions
    assert not wizard.runner.started and not wizard.runner.cancelled
    state = _state(app)
    assert state["parent_focused"], state


def test_app_close_does_not_present_its_parent_again(ui, fake_audio, monkeypatch):  # noqa: F811
    app = ui(_owner())
    controller = _open(app)
    presented = []
    monkeypatch.setattr(app.window, "present", lambda: presented.append(True))
    app.close()
    drain()
    assert app.closed and not app.window.get_mapped()
    assert controller.dialog is None and controller.ticket is None
    assert not presented
