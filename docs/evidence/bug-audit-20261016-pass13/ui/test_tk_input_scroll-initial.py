"""The real Tk window keeps native input and routes only its body's wheel."""

import ctypes
import os
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

pytest.importorskip("gi")
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gdk  # noqa: E402
from beamo_wipe.ui.tk_wizard import TkWizard, _Scrollbar  # noqa: E402
from test_accessible_focus_input_pass11 import native  # noqa: E402, F401


@pytest.fixture(autouse=True)
def isolated_fake_effects(monkeypatch):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native Tk input requires an explicitly isolated X11 display")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("A native application operation was reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)


def _children(widget):
    for child in widget.winfo_children():
        yield child
        yield from _children(child)


def _corner():
    geometry = Gdk.Display.get_default().get_monitor(0).get_geometry()
    return geometry.x + geometry.width - 1, geometry.y + geometry.height - 1


def _app():
    wizard = make_demo_wizard()
    wizard.skip_intro()
    app = TkWizard(wizard)
    app.root.geometry("800x600+0+0")
    app.root.update()
    assert app._body_canvas is not None
    assert app._body_canvas.yview()[1] < 1
    return app


def _visible_label(app):
    canvas = app._body_canvas
    return next(
        child for child in _children(app._body_inner)
        if isinstance(child, tk.Label) and child.winfo_ismapped()
        and child.winfo_rooty() >= canvas.winfo_rooty()
        and child.winfo_rooty() + 12 < canvas.winfo_rooty() + canvas.winfo_height()
    )


@pytest.mark.parametrize("key", [Gdk.KEY_Escape, Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space])
@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("pointer", ["inside", "far_corner"])
def test_first_native_key_works_with_pointer_outside_window(native, key, fullscreen, pointer):  # noqa: F811
    native.root_focus()
    native.pointer(*_corner())
    wizard = make_demo_wizard()
    app = TkWizard(wizard, fullscreen=fullscreen)
    seen = {}
    errors = []

    def send():
        try:
            root = app.root
            rect = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height())
            point = ((rect[0] + 20, rect[1] + 20) if pointer == "inside" else
                     (root.winfo_screenwidth() - 1, root.winfo_screenheight() - 1))
            native.pointer(*point)
            seen.update(rect=rect, pointer=point, focused=root.focus_get() is app._primary)
            native.key(key, True)
            native.key(key, False)
        except BaseException as error:
            errors.append(error)

    app.root.after(120, send)
    app.root.after(320, app._teardown)
    try:
        assert app.run() == 0
        assert not errors
        assert seen and seen["focused"], seen
        assert wizard.screen is Screen.KEYBOARD, seen
        assert wizard._wipe_request is None
        assert not wizard.owner_ok
    finally:
        app._teardown()


def test_initial_focus_is_claimed_once_and_held_return_keeps_gate(native):  # noqa: F811
    native.root_focus()
    native.pointer(*_corner())
    wizard = make_demo_wizard()
    app = TkWizard(wizard)
    seen, errors = {}, []

    def first():
        try:
            native.pointer(app.root.winfo_screenwidth() - 1, app.root.winfo_screenheight() - 1)
            seen["initial_child"] = app.root.focus_get() is app._primary
            native.key(Gdk.KEY_Return, True)
        except BaseException as error:
            errors.append(error)

    def held():
        try:
            seen["held_before"] = app._return_held
            app._on_return(SimpleNamespace(time=123))
            seen["held_screen"] = wizard.screen.name
            native.key(Gdk.KEY_Return, False)
            native.root_focus()
        except BaseException as error:
            errors.append(error)

    def inspect():
        seen["no_reclaim"] = app.root.focus_get() is None
        app._teardown()

    app.root.after(120, first)
    app.root.after(200, held)
    app.root.after(400, inspect)
    try:
        assert app.run() == 0
        assert not errors
        assert seen == {"initial_child": True, "held_before": True, "held_screen": "KEYBOARD", "no_reclaim": True}
        assert wizard.screen is Screen.KEYBOARD
        assert wizard._wipe_request is None
    finally:
        app._teardown()


@pytest.mark.parametrize("target_kind", ["label", "canvas", "inner", "panel"])
@pytest.mark.parametrize(("sequence", "delta", "direction"), [
    ("<Button-5>", None, 1), ("<Button-4>", None, -1),
    ("<MouseWheel>", -120, 1), ("<MouseWheel>", 120, -1),
])
def test_body_wheel_over_prose_scrolls_once_without_changing_focus_or_consent(target_kind, sequence, delta, direction):
    app = _app()
    try:
        canvas = app._body_canvas
        canvas.yview_moveto(0.2)
        app.root.update()
        label = _visible_label(app)
        target = {"label": label, "canvas": canvas, "inner": app._body_inner,
                  "panel": next(w for w in _children(app._body_inner) if isinstance(w, tk.Canvas))}[target_kind]
        app.root.focus_force()
        focus = app.root.focus_get()
        consent = (app.w.screen, app.w.selected, app.w.owner_ok, app.w.confirm_input, app.w.method)
        before = canvas.yview()
        target.event_generate(sequence, **({"delta": delta} if delta is not None else {}))
        app.root.update()
        after = canvas.yview()
        canvas.yview_moveto(before[0])
        canvas.yview_scroll(direction, "units")
        expected = canvas.yview()
        assert after == expected
        assert direction * (after[0] - before[0]) > 0
        assert app.root.focus_get() is focus
        assert (app.w.screen, app.w.selected, app.w.owner_ok, app.w.confirm_input, app.w.method) == consent
    finally:
        app._teardown()


@pytest.mark.parametrize("delta", [-119, -1, 0, 1, 119])
def test_small_wheel_deltas_do_not_move_body(delta):
    app = _app()
    try:
        canvas = app._body_canvas
        canvas.yview_moveto(0.2)
        before = canvas.yview()
        _visible_label(app).event_generate("<MouseWheel>", delta=delta)
        app.root.update()
        assert canvas.yview() == before
    finally:
        app._teardown()


@pytest.mark.parametrize("kind", ["Text", "Listbox", "Treeview", "nested_canvas", "custom_scrollbar", "footer"])
@pytest.mark.parametrize("sequence", ["<Button-5>", "<MouseWheel>"])
def test_independent_scroll_surfaces_and_footer_do_not_scroll_parent(kind, sequence):
    app = _app()
    try:
        parent = app._body_canvas
        parent.yview_moveto(0.2)
        if kind == "Text":
            target = tk.Text(app._body_inner, height=2)
            target.insert("1.0", "\n".join(str(n) for n in range(60)))
        elif kind == "Listbox":
            target = tk.Listbox(app._body_inner, height=2)
            for n in range(60):
                target.insert(tk.END, str(n))
        elif kind == "Treeview":
            target = ttk.Treeview(app._body_inner, height=2)
            for n in range(60):
                target.insert("", tk.END, text=str(n))
        elif kind == "nested_canvas":
            target = tk.Canvas(app._body_inner, height=20, scrollregion=(0, 0, 100, 1000))
            target.bind(sequence, lambda _event: target.yview_scroll(1, "units"))
        elif kind == "custom_scrollbar":
            calls = []
            target = _Scrollbar(app._body_inner, lambda *args: calls.append(args))
        else:
            target = tk.Label(app._footer, text="Outside the body")
        target.pack()
        app.root.update()
        before = parent.yview()
        own_before = target.yview() if kind in {"Text", "Listbox", "Treeview", "nested_canvas"} else None
        target.event_generate(sequence, **({"delta": -120} if sequence == "<MouseWheel>" else {}))
        app.root.update()
        assert parent.yview() == before
        if own_before is not None:
            assert target.yview()[0] > own_before[0]
        if kind == "custom_scrollbar":
            assert calls == [("scroll", 1, "units")]
    finally:
        app._teardown()


def test_wheel_uses_current_body_after_redraw_and_leaves_picker_controls_intact():
    app = _app()
    try:
        old = app._body_canvas
        app._draw()
        app.root.update()
        current = app._body_canvas
        assert current is not old
        before = current.yview()
        _visible_label(app).event_generate("<Button-5>")
        app.root.update()
        assert current.yview()[0] > before[0]
        app.w.set_owner(True)
        app.w.continue_owner()
        app._draw()
        app.root.update()
        assert app.w.screen is Screen.PICK
        assert app._body_canvas is None
        picker = app._pick_canvas
        selected = app.w.selected
        label = next(w for w in _children(picker) if isinstance(w, tk.Label))
        picker.yview_moveto(0)
        before = picker.yview()
        label.event_generate("<Button-5>")
        app.root.update()
        after = picker.yview()
        picker.yview_moveto(before[0])
        picker.yview_scroll(1, "units")
        assert after == picker.yview()
        assert app.w.selected is selected
    finally:
        app._teardown()


@pytest.mark.parametrize("button", [4, 5])
def test_native_wheel_over_hit_tested_prose_works(button):
    app = _app()
    connection = None
    try:
        canvas = app._body_canvas
        canvas.yview_moveto(0.2)
        app.root.update()
        label = _visible_label(app)
        point = (label.winfo_rootx() + 10, label.winfo_rooty() + 10)
        assert app.root.winfo_containing(*point) is label
        x11 = ctypes.CDLL("libX11.so.6")
        xtst = ctypes.CDLL("libXtst.so.6")
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
        xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        connection = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
        assert connection
        assert xtst.XTestFakeMotionEvent(connection, -1, *point, 0)
        x11.XSync(connection, False)
        before = canvas.yview()
        assert xtst.XTestFakeButtonEvent(connection, button, True, 0)
        assert xtst.XTestFakeButtonEvent(connection, button, False, 0)
        x11.XSync(connection, False)
        app.root.update()
        assert (1 if button == 5 else -1) * (canvas.yview()[0] - before[0]) > 0
    finally:
        if connection:
            x11.XCloseDisplay(connection)
        app._teardown()
