"""The main GTK view retires owned resources across setup and loop exits."""

import os
import sys
from types import SimpleNamespace

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen


class ErrorWithoutNotes(RuntimeError):
    add_note = None


@pytest.fixture
def gtk_lifetime(monkeypatch):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("GTK lifetime requires an explicitly private display")
    assert os.environ.get("DISPLAY") not in {":1", ":99"}
    pytest.importorskip("gi")
    from beamo_wipe.ui import accessible_wizard as ui

    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native application effect forbidden")

    for target in (
        "subprocess.run", "subprocess.Popen", "os.system", "socket.create_connection",
        "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
        "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start",
        "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    before = set(ui.Gtk.Window.list_toplevels())
    sources = []
    real_timeout = ui.GLib.timeout_add

    def timeout(*args):
        source = real_timeout(*args)
        sources.append(source)
        return source

    monkeypatch.setattr(ui.GLib, "timeout_add", timeout)
    peer = ui.Gtk.Window(title="Owned GTK lifetime peer control")
    peer.show_all()
    peer_source = real_timeout(60_000, lambda: True)
    context = ui.GLib.MainContext.default()
    try:
        yield ui, peer, peer_source, sources, context
    finally:
        # Retire only this fixture's resources, including original-code leaks.
        for source in [*sources, peer_source]:
            pending = context.find_source_by_id(source)
            if pending is not None:
                pending.destroy()
        for window in ui.Gtk.Window.list_toplevels():
            if window not in before:
                window.destroy()
        assert not effects


def _assert_retired(ui, peer, peer_source, sources, context, before):
    assert set(ui.Gtk.Window.list_toplevels()) == before
    assert peer.get_visible()
    assert context.find_source_by_id(peer_source) is not None
    assert all(context.find_source_by_id(source) is None for source in sources)


@pytest.mark.parametrize("stage", ["name", "style", "render", "timer"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, ErrorWithoutNotes])
def test_constructor_failure_retires_partial_view_preserving_primary(
    gtk_lifetime, monkeypatch, stage, error_type
):
    ui, peer, peer_source, sources, context = gtk_lifetime
    before = set(ui.Gtk.Window.list_toplevels())
    error = error_type("Controlled GTK setup failure")
    wizard = make_demo_wizard()
    wizard.skip_intro()
    cancelled = []
    quit_calls = []

    def cancel_audio():
        cancelled.append(True)
        raise OSError("Secondary audio cleanup failure")

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(wizard, "cancel_audio", cancel_audio)
    # A setup failure inside a peer's loop must not quit that peer's loop.
    monkeypatch.setattr(ui.Gtk, "main_level", lambda: 2)
    monkeypatch.setattr(ui.Gtk, "main_quit", lambda: quit_calls.append(True))
    if stage == "name":
        monkeypatch.setattr(ui.Gtk.Window, "set_name", fail)
    elif stage == "style":
        monkeypatch.setattr(ui.AccessibleWizard, "_apply_type_css", fail)
    elif stage == "render":
        monkeypatch.setattr(ui.Gtk.Window, "show_all", fail)
    else:
        monkeypatch.setattr(ui.GLib, "timeout_add", fail)
    with pytest.raises(error_type) as caught:
        ui.AccessibleWizard(wizard)
    assert caught.value is error
    _assert_retired(ui, peer, peer_source, sources, context, before)
    assert cancelled == [True]
    assert quit_calls == []


@pytest.mark.parametrize("mode", ["normal-close", "external-return", "exception", "interrupted"])
@pytest.mark.parametrize("peer_level", [0, 2])
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_loop_exit_retires_window_timer_and_hook_without_quitting_peer(
    gtk_lifetime, monkeypatch, mode, peer_level, cleanup_fails
):
    ui, peer, peer_source, sources, context = gtk_lifetime
    before = set(ui.Gtk.Window.list_toplevels())
    wizard = make_demo_wizard()
    wizard.skip_intro()
    app = ui.AccessibleWizard(wizard)
    original = (KeyboardInterrupt("Controlled GTK loop interruption") if mode == "interrupted"
                else RuntimeError("Controlled GTK loop failure"))
    cleanup_error = OSError("Controlled GTK cleanup failure")
    cancelled = []
    quits = []
    level = [peer_level]
    hook = sys.excepthook

    def cancel_audio():
        cancelled.append(True)
        if cleanup_fails:
            raise cleanup_error

    def main():
        assert sys.excepthook == app._runtime_failure
        level[0] += 1
        try:
            if mode == "normal-close":
                app.close()
            elif mode in {"exception", "interrupted"}:
                raise original
        finally:
            level[0] -= 1

    monkeypatch.setattr(wizard, "cancel_audio", cancel_audio)
    monkeypatch.setattr(ui.Gtk, "main_level", lambda: level[0])
    monkeypatch.setattr(ui.Gtk, "main_quit", lambda: quits.append(level[0]))
    monkeypatch.setattr(ui.Gtk, "main", main)
    expected = (original if mode in {"exception", "interrupted"}
                else cleanup_error if cleanup_fails else None)
    if expected is None:
        assert app.run() == 0
    else:
        with pytest.raises(type(expected)) as caught:
            app.run()
        assert caught.value is expected
    assert sys.excepthook is hook
    _assert_retired(ui, peer, peer_source, sources, context, before)
    assert app.closed and app.timer == 0
    assert cancelled == [True]
    assert quits == ([peer_level + 1] if mode == "normal-close" else [])
    app.close()
    assert cancelled == [True]


def test_close_inside_nested_peer_loop_does_not_quit_peer(gtk_lifetime, monkeypatch):
    ui, peer, peer_source, sources, context = gtk_lifetime
    before = set(ui.Gtk.Window.list_toplevels())
    app = ui.AccessibleWizard(make_demo_wizard())
    level = [1]
    quits = []

    def main():
        level[0] = 3  # The owned level 2 is covered by a peer's nested loop.
        app.close()
        level[0] = 1

    monkeypatch.setattr(ui.Gtk, "main_level", lambda: level[0])
    monkeypatch.setattr(ui.Gtk, "main_quit", lambda: quits.append(level[0]))
    monkeypatch.setattr(ui.Gtk, "main", main)
    assert app.run() == 0
    assert quits == []
    _assert_retired(ui, peer, peer_source, sources, context, before)


@pytest.mark.parametrize("callback", ["key", "button", "token"])
def test_retired_view_refuses_queued_input(gtk_lifetime, monkeypatch, callback):
    ui, _peer, _peer_source, _sources, _context = gtk_lifetime
    wizard = make_demo_wizard()
    wizard.skip_intro()
    callbacks = []
    original_connect = ui.Gtk.Button.connect

    def connect(widget, signal, action, *args):
        if signal == "clicked":
            callbacks.append((widget, action))
        return original_connect(widget, signal, action, *args)

    monkeypatch.setattr(ui.Gtk.Button, "connect", connect)
    if callback == "token":
        wizard.set_owner(True)
        wizard.continue_owner()
        wizard.select_disk(wizard.selectable[0].path)
        wizard.continue_pick()
        assert wizard.screen == Screen.CONFIRM
    app = ui.AccessibleWizard(wizard)
    generation = app.generation
    old_screen = wizard.screen
    old_input = wizard.confirm_input
    renders = []
    actions = []
    button = app.button("Owned inert callback", lambda: actions.append(True))
    queued = next(action for widget, action in callbacks if widget is button)
    app.close()
    monkeypatch.setattr(app, "render", lambda: renders.append(True))
    if callback == "key":
        app._key_press(None, SimpleNamespace(keyval=ui.Gdk.KEY_Escape, time=123))
    elif callback == "button":
        queued(button)
    else:
        app._token("retired input", generation)
    assert wizard.screen == old_screen
    assert wizard.confirm_input == old_input
    assert actions == []
    assert renders == []
