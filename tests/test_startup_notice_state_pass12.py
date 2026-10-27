"""A stalled startup remains readable without repeating its event marker."""

import os
import threading

import pytest

from beamo_wipe import copy as C, lang, startup_stages


@pytest.mark.parametrize("language", ["en", "fr", "de", "es"])
def test_one_shot_startup_stall_notices_remain_one_per_stage(monkeypatch, language):
    lang.set_language(language)
    now = [0.0]
    markers = []
    monkeypatch.setattr(startup_stages, "_emit", markers.append)
    run = startup_stages.StartupRun(lambda _report: None, clock=lambda: now[0], stall_after_s=10)
    assert run.stalled_note() is None
    now[0] = 11
    assert run.stalled_note() == C.STARTUP_STILL_WORKING
    assert all(run.stalled_note() is None for _ in range(10))
    run.report(startup_stages.STAGE_BOOT_USB)
    run.drain()
    assert run.stalled_note() is None
    now[0] = 22
    assert run.stalled_note() == C.STARTUP_STILL_WORKING
    assert run.stalled_note() is None
    assert markers.count(startup_stages.STAGE_STALLED_MARKER) == 2


@pytest.mark.parametrize("terminal", ["done", "failed"])
def test_graphical_stall_state_clears_at_stage_and_terminal_boundaries(monkeypatch, terminal):
    now = [0.0]
    markers = []
    monkeypatch.setattr(startup_stages, "_emit", markers.append)
    run = startup_stages.StartupRun(lambda _report: None, clock=lambda: now[0], stall_after_s=10)
    assert run.stalled_note(persistent=True) is None
    now[0] = 11
    assert all(run.stalled_note(persistent=True) == C.STARTUP_STILL_WORKING for _ in range(10))
    assert run.stalled_note() is None
    run.report(startup_stages.STAGE_BOOT_USB)
    run.drain()
    assert run.stalled_note(persistent=True) is None
    now[0] = 22
    assert run.stalled_note(persistent=True) == C.STARTUP_STILL_WORKING
    run.stages.succeed() if terminal == "done" else run.stages.fail()
    assert run.stalled_note(persistent=True) is None
    assert run.stalled_note() is None
    assert markers.count(startup_stages.STAGE_STALLED_MARKER) == 2


@pytest.mark.parametrize("language", ["en", "fr", "de", "es"])
@pytest.mark.parametrize("surface", ["tk", "gtk"])
def test_graphical_startup_keeps_stall_text_until_the_stage_changes(monkeypatch, language, surface):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Graphical startup checks require an explicitly isolated display")
    pytest.importorskip("gi")
    from beamo_wipe.ui import accessible_wizard, tk_wizard
    from beamo_wipe.ui.accessible_wizard import GLib, Gtk

    lang.set_language(language)
    now = [0.0]
    release, finished = threading.Event(), threading.Event()
    frames, windows, rescue_fired, markers = [], [], [], []
    real_run = startup_stages.StartupRun
    frame = [0]
    monkeypatch.setattr(startup_stages, "_emit", markers.append)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("A native application operation was reached")

    for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
        monkeypatch.setattr(target, forbidden)

    def root():
        if surface == "tk":
            return windows[0]
        return next(window for window in Gtk.Window.list_toplevels() if window.get_title() == C.STARTING_TITLE and window.get_mapped())

    def widgets(widget):
        yield widget
        if isinstance(widget, Gtk.Widget):
            children = widget.get_children() if isinstance(widget, Gtk.Container) else ()
        else:
            children = widget.winfo_children()
        for child in children:
            yield from widgets(child)

    def close():
        if surface == "tk":
            root().destroy()
        else:
            root().emit("delete-event", None)
        return False

    def after(callback):
        return root().after_idle(callback) if surface == "tk" else GLib.idle_add(callback)

    def fake_run(build, **_kwargs):
        run = real_run(build, clock=lambda: now[0], stall_after_s=10)
        original = run.stalled_note

        def note(**kwargs):
            index = frame[0]
            frame[0] += 1
            if index == 1:
                now[0] = 11
            value = original(**kwargs)

            def inspect():
                text = [widget.get_text() if isinstance(widget, Gtk.Label) else widget.cget("text") for widget in widgets(root()) if isinstance(widget, (Gtk.Label, tk_wizard.tk.Label))]
                frames.append(C.STARTUP_STILL_WORKING in text)
                if index == 2:
                    now[0] = 12
                    run.report(startup_stages.STAGE_BOOT_USB)
                elif index == 3:
                    now[0] = 23
                elif index == 5:
                    after(close)
                return False

            after(inspect)
            return value

        run.stalled_note = note
        return run

    def build(_report):
        try:
            assert release.wait(timeout=4)
            return object()
        finally:
            finished.set()

    def rescue():
        rescue_fired.append(True)
        return close()

    monkeypatch.setattr(startup_stages, "StartupRun", fake_run)
    if surface == "tk":
        real_tk = tk_wizard.tk.Tk

        def factory():
            window = real_tk()
            windows.append(window)
            window.after(3000, rescue)
            return window

        monkeypatch.setattr(tk_wizard.tk, "Tk", factory)
        monkeypatch.setattr(tk_wizard, "_ensure_tk_display", lambda: None)
        presenter = tk_wizard.run_tk_startup
    else:
        monkeypatch.setattr(accessible_wizard, "_ensure_gtk_display", lambda: None)
        rescue_timer = GLib.timeout_add(3000, rescue)
        presenter = accessible_wizard.run_accessible_startup
    try:
        outcome = presenter(build)
        assert outcome == ("abandoned", None)
        assert not rescue_fired
        assert frames == [False, True, True, False, True, True]
        assert markers.count(startup_stages.STAGE_STALLED_MARKER) == 2
    finally:
        release.set()
        assert finished.wait(timeout=1)
        if surface == "gtk" and not rescue_fired:
            GLib.source_remove(rescue_timer)
