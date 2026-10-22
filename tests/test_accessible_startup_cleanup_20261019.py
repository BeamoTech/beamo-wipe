# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK startup owns its window and polling source through every exit."""

import os

import pytest

from beamo_wipe import startup_stages


@pytest.fixture
def gtk_startup(monkeypatch):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("GTK startup lifetime requires an explicitly private display")
    assert os.environ.get("DISPLAY") not in {":1", ":99"}
    pytest.importorskip("gi")
    from beamo_wipe.ui import accessible_wizard as ui

    monkeypatch.setattr(ui, "_ensure_gtk_display", lambda: None)
    monkeypatch.setattr(startup_stages, "_emit", lambda *_args: None)
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("A device or application action was reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    yield ui
    assert not effects


@pytest.mark.parametrize(
    "ending",
    ["wizard", "failed-build", "close", "failed-start", "interrupted-start",
     "failed-show", "failed-timer", "failed-loop", "interrupted-loop"],
)
def test_startup_retires_owned_window_and_source(monkeypatch, gtk_startup, ending):
    ui = gtk_startup
    peer = ui.Gtk.Window(title="Unrelated control window")
    peer.show_all()
    peer_destroyed = []
    peer.connect("destroy", lambda *_args: peer_destroyed.append(True))
    before = set(ui.Gtk.Window.list_toplevels())
    context = ui.GLib.MainContext.default()
    sources = []
    peer_source = ui.GLib.timeout_add(60_000, lambda: True)
    real_timeout = ui.GLib.timeout_add
    real_show = ui.Gtk.Window.show_all
    original = (KeyboardInterrupt("owned startup interruption") if ending.startswith("interrupted")
                else RuntimeError("owned startup failure"))
    runs = []

    def start(run):
        runs.append(run)
        if ending in {"failed-start", "interrupted-start"}:
            raise original
        # Publish an inert outcome synchronously: no worker, discovery or process.
        run._run()

    def build(_report):
        if ending == "failed-build":
            raise original
        return "inert fake wizard"

    def show(window):
        real_show(window)
        if window not in before and ending == "failed-show":
            raise original

    def timeout(milliseconds, callback, *args):
        if ending == "failed-timer":
            raise original
        source = real_timeout(milliseconds, callback, *args)
        sources.append(source)
        return source

    def fail_loop():
        raise original

    def close_loop():
        owned = [window for window in ui.Gtk.Window.list_toplevels() if window not in before]
        assert len(owned) == 1
        owned[0].emit("delete-event", None)

    monkeypatch.setattr(startup_stages.StartupRun, "start", start)
    monkeypatch.setattr(ui.Gtk.Window, "show_all", show)
    monkeypatch.setattr(ui.GLib, "timeout_add", timeout)
    if ending in {"failed-loop", "interrupted-loop"}:
        monkeypatch.setattr(ui.Gtk, "main", fail_loop)
    elif ending == "close":
        monkeypatch.setattr(ui.Gtk, "main", close_loop)
    try:
        if ending in {"interrupted-start", "failed-show", "failed-timer", "failed-loop", "interrupted-loop"}:
            with pytest.raises(type(original)) as caught:
                ui.run_accessible_startup(build)
            assert caught.value is original
        else:
            result = ui.run_accessible_startup(build)
            expected = ("wizard" if ending == "wizard" else "abandoned" if ending == "close" else "failed")
            assert result[0] == expected
            if expected == "failed":
                assert result[1] is original
        assert set(ui.Gtk.Window.list_toplevels()) == before
        assert not peer_destroyed
        assert peer.get_visible()
        assert context.find_source_by_id(peer_source) is not None
        assert all(context.find_source_by_id(source) is None for source in sources)
    finally:
        # Clean only this fixture's resources, including leaks from original code.
        for source in [*sources, peer_source]:
            pending = context.find_source_by_id(source)
            if pending is not None:
                pending.destroy()
        for window in ui.Gtk.Window.list_toplevels():
            if window not in before:
                window.destroy()
        peer.destroy()


def test_startup_keeps_primary_error_without_exception_notes(monkeypatch, gtk_startup):
    """Two cleanup failures still retire both resources and retain the cause."""
    from types import SimpleNamespace

    ui = gtk_startup
    peer = ui.Gtk.Window(title="Unrelated control window")
    peer.show_all()
    before = set(ui.Gtk.Window.list_toplevels())
    real_context = ui.GLib.MainContext.default()
    real_destroy = ui.Gtk.Window.destroy
    original_timeout = ui.GLib.timeout_add
    calls, sources = [], []

    class ErrorWithoutNotes(RuntimeError):
        add_note = None

    original = ErrorWithoutNotes("primary loop failure")

    def timeout(*args):
        source = original_timeout(*args)
        sources.append(source)
        return source

    def find_source(source):
        pending = real_context.find_source_by_id(source)
        if pending is None:
            return None

        def destroy():
            calls.append("retire-source")
            pending.destroy()
            raise OSError("secondary source cleanup error")

        return SimpleNamespace(destroy=destroy)

    def destroy_window(window):
        real_destroy(window)
        if window not in before:
            calls.append("destroy-window")
            raise ValueError("secondary window cleanup error")

    def fail_loop():
        raise original

    monkeypatch.setattr(startup_stages.StartupRun, "start", lambda run: run._run())
    monkeypatch.setattr(ui.GLib, "timeout_add", timeout)
    monkeypatch.setattr(ui.GLib.MainContext, "default", lambda: SimpleNamespace(find_source_by_id=find_source))
    monkeypatch.setattr(ui.Gtk.Window, "destroy", destroy_window)
    monkeypatch.setattr(ui.Gtk, "main", fail_loop)
    caught = []
    try:
        try:
            ui.run_accessible_startup(lambda _report: "inert fake wizard")
        except BaseException as error:
            caught.append(error)
        assert calls == ["retire-source", "destroy-window"]
        assert set(ui.Gtk.Window.list_toplevels()) == before
        assert all(real_context.find_source_by_id(source) is None for source in sources)
        assert peer.get_visible()
        assert caught == [original]
    finally:
        for source in sources:
            pending = real_context.find_source_by_id(source)
            if pending is not None:
                pending.destroy()
        for window in ui.Gtk.Window.list_toplevels():
            if window not in before:
                real_destroy(window)
        real_destroy(peer)
