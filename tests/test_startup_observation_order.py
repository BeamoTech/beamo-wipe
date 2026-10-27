"""A delayed main-loop entry must not make a startup frame inspect its successor."""

import os
import time

import pytest


@pytest.mark.parametrize("language", ["en", "de"])
def test_startup_frame_observation_precedes_the_next_due_render(monkeypatch, language):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Startup ordering requires an explicitly private display")
    pytest.importorskip("gi")
    from beamo_wipe.ui.accessible_wizard import Gtk
    from test_startup_notice_state_pass12 import (
        test_graphical_startup_keeps_stall_text_until_the_stage_changes as original_case,
    )

    original_main = Gtk.main
    entered = []

    def delayed_main():
        entered.append(True)
        # The initial render has queued its observer. Make the existing 100ms
        # poll due as well, without changing the fake clock or any deadline.
        time.sleep(0.15)
        return original_main()

    monkeypatch.setattr(Gtk, "main", delayed_main)
    original_case(monkeypatch, language, "gtk")
    assert entered == [True]


@pytest.mark.parametrize("defect", ["missing_text", "lost_persistence", "stale_stage", "extra_marker", "hidden_window"])
def test_completed_render_observer_still_detects_bad_widget_state(monkeypatch, defect):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Startup ordering requires an explicitly private display")
    pytest.importorskip("gi")
    from beamo_wipe import copy as C, startup_stages
    from beamo_wipe.ui.accessible_wizard import Gtk
    from test_startup_notice_state_pass12 import (
        test_graphical_startup_keeps_stall_text_until_the_stage_changes as original_case,
    )

    real_set_text = Gtk.Label.set_text
    stalled_labels = set()
    writes = []

    def altered_text(label, text):
        if text == C.STARTUP_STILL_WORKING:
            stalled_labels.add(label)
            writes.append(text)
            if defect == "missing_text" or defect == "lost_persistence" and len(writes) == 2:
                text = ""
        elif defect == "stale_stage" and label in stalled_labels and text == "":
            text = C.STARTUP_STILL_WORKING
        return real_set_text(label, text)

    real_note = startup_stages.StartupRun.stalled_note

    def extra_marker(run, **kwargs):
        value = real_note(run, **kwargs)
        if value:
            startup_stages._emit(startup_stages.STAGE_STALLED_MARKER)
        return value

    monkeypatch.setattr(Gtk.Label, "set_text", altered_text)
    if defect == "extra_marker":
        monkeypatch.setattr(startup_stages.StartupRun, "stalled_note", extra_marker)
    elif defect == "hidden_window":
        monkeypatch.setattr(Gtk.Window, "show_all", lambda _window: None)
        monkeypatch.setattr(Gtk.Window, "present", lambda _window: None)
    expected = {"extra_marker": "startup stall marker count", "hidden_window": "startup window is not mapped"}.get(defect, "startup frame history")
    with pytest.raises(AssertionError, match=expected):
        original_case(monkeypatch, "en", "gtk")
    if defect != "hidden_window":
        assert writes  # The fault reached actual stall-label writes.
