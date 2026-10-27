"""A new startup uses the selected session language, including spoken status."""

import pytest

from beamo_wipe import copy as C, lang
from beamo_wipe.startup_stages import StartupStages


@pytest.fixture(autouse=True)
def restore_language():
    previous = lang.current()
    yield
    lang.set_language(previous)


def assert_current_stage_copy(stages):
    rows = stages.snapshot()
    assert [(row["title"], row["hint"]) for row in rows] == [
        (C.STARTUP_TITLE, C.STARTUP_TITLE_HINT),
        (C.STARTUP_STAGE_BOOT_USB, C.STARTUP_STAGE_BOOT_USB_HINT),
        (C.STARTUP_STAGE_FINDING, C.STARTUP_STAGE_FINDING_HINT),
    ]


@pytest.mark.parametrize("language", ["en", "fr", "de", "es"])
def test_new_startup_uses_current_stage_translations(monkeypatch, language):
    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
    lang.set_language(language)
    assert_current_stage_copy(StartupStages())


def test_stage_states_survive_language_switch_and_english_restore(monkeypatch):
    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)
    lang.set_language("en")
    stages = StartupStages()
    stages.begin("checking-boot-usb")
    before = stages.states.copy()
    for language in ("fr", "de", "es", "en"):
        lang.set_language(language)
        assert_current_stage_copy(stages)
        assert stages.states == before


def labels(widget, ui):
    result = [widget.get_text()] if isinstance(widget, ui.Gtk.Label) else []
    if isinstance(widget, ui.Gtk.Container):
        for child in widget.get_children():
            result.extend(labels(child, ui))
    return result


@pytest.mark.parametrize("language", ["fr", "de", "es"])
def test_spoken_startup_status_uses_selected_language(monkeypatch, language):
    pytest.importorskip("gi")
    from beamo_wipe.ui import accessible_wizard as ui

    lang.set_language(language)
    captured = []
    unrelated = ui.Gtk.Window(title="Unrelated existing window")
    unrelated_destroyed = []
    unrelated.connect("destroy", lambda *_args: unrelated_destroyed.append(True))
    previous_windows = set(ui.Gtk.Window.list_toplevels())
    monkeypatch.setattr(ui, "_ensure_gtk_display", lambda: None)
    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_args: None)

    def inspect_window():
        owned = [window for window in ui.Gtk.Window.list_toplevels()
                 if window not in previous_windows]
        assert len(owned) == 1
        window = owned[0]
        captured.extend(labels(window, ui))
        window.emit("delete-event", None)

    monkeypatch.setattr(ui.Gtk, "main", inspect_window)
    try:
        ui.run_accessible_startup(lambda _report: object())
        assert C.STARTUP_TITLE in captured
        assert any(" — " + C.STARTUP_STATE_WORKING in value for value in captured)
        assert not unrelated_destroyed
    finally:
        for window in ui.Gtk.Window.list_toplevels():
            if window not in previous_windows:
                window.destroy()
        unrelated.destroy()
