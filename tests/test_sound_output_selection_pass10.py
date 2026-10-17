"""Visible GTK sound selection must match the sink used by later controls."""

from contextlib import nullcontext
from dataclasses import replace
from types import SimpleNamespace
import threading
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import audio_jobs, copy as C, sound  # noqa: E402
from beamo_wipe.ui import sound_dialog  # noqa: E402
from test_accessible_runtime import (  # noqa: E402, F401
    _dialog_button,
    drain,
    ui,
    wait_sound,
)


@pytest.fixture
def selection_audio_worker(monkeypatch):
    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(sound_dialog, "worker", worker)
    yield worker
    worker.close()


def _open(build_ui, monkeypatch, *, duplicate_labels=False):
    label = "Same output name" if duplicate_labels else "Speakers"
    outputs = (
        sound.SoundOutput("speakers-id", label, "speakers-id", True),
        sound.SoundOutput("headphones-id", label if duplicate_labels else "Headphones", "headphones-id", False),
    )
    calls = []
    state = {"default": "speakers-id", "selection": "success"}

    def list_outputs():
        return sound.SoundState(
            True,
            "",
            tuple(replace(output, is_default=output.id == state["default"]) for output in outputs),
            40,
            False,
        )

    def set_output(sink):
        calls.append(("set", sink))
        if state["selection"] == "exception":
            raise OSError("controlled fake selection error")
        if state["selection"] == "refused":
            return sound.SoundResult(False, "controlled selection refusal")
        state["default"] = sink
        return sound.SoundResult(True, "")

    monkeypatch.setattr(sound, "list_outputs", list_outputs)
    monkeypatch.setattr(sound, "orca_running", lambda: True)
    monkeypatch.setattr(sound, "set_output", set_output)
    monkeypatch.setattr(
        sound,
        "nudge_volume",
        lambda sink, delta: calls.append(("volume", sink, delta)) or sound.SoundResult(True, ""),
    )
    monkeypatch.setattr(
        sound,
        "set_muted",
        lambda sink, muted: calls.append(("mute", sink, muted)) or sound.SoundResult(True, ""),
    )
    app = build_ui()
    app.actions[C.SOUND_CHECK_BUTTON].clicked()
    wait_sound(app)
    controller = app._sound_dialog
    assert controller.chosen.id == "speakers-id"
    assert [radio.get_active() for radio in controller.radios] == [True, False]
    return app, controller, calls, state


def _select(app, controller, monkeypatch, state, outcome):
    state["selection"] = outcome
    context = monkeypatch.context() if outcome in {"timeout", "cancelled"} else nullcontext()
    with context as patch:
        if outcome in {"timeout", "cancelled"}:
            ticket = audio_jobs.AudioTicket(seconds=0 if outcome == "timeout" else 30)
            if outcome == "cancelled":
                ticket.cancel()
            patch.setattr(sound_dialog, "worker", SimpleNamespace(submit=lambda _action: ticket))
        controller.radios[1].set_active(True)
        wait_sound(app)


@pytest.mark.parametrize("outcome", ["success", "refused", "exception", "timeout", "cancelled"])
def test_output_selection_and_following_controls_agree(
    ui, monkeypatch, selection_audio_worker, outcome  # noqa: F811
):
    app, controller, calls, state = _open(ui, monkeypatch)
    _select(app, controller, monkeypatch, state, outcome)
    selected = "headphones-id" if outcome == "success" else "speakers-id"
    _dialog_button(controller.dialog, C.SOUND_LOUDER).clicked()
    wait_sound(app)
    _dialog_button(controller.dialog, C.SOUND_MUTE).clicked()
    wait_sound(app)
    assert ("volume", selected, sound.VOLUME_STEP) in calls
    assert ("mute", selected, True) in calls
    assert controller.chosen.id == selected
    assert [radio.get_active() for radio in controller.radios] == [selected == "speakers-id", selected == "headphones-id"]
    assert app.w.sound_output == (selected if outcome == "success" else "")
    assert [call for call in calls if call[0] == "set"] == (
        [] if outcome in {"timeout", "cancelled"} else [("set", "headphones-id")]
    )


@pytest.mark.parametrize("outcome", ["refused", "exception", "timeout", "cancelled"])
def test_failed_output_selection_can_retry_the_same_radio(
    ui, monkeypatch, selection_audio_worker, outcome  # noqa: F811
):
    app, controller, calls, state = _open(ui, monkeypatch)
    _select(app, controller, monkeypatch, state, outcome)
    state["selection"] = "success"
    controller.radios[1].set_active(True)
    wait_sound(app)
    assert controller.chosen.id == "headphones-id"
    assert [radio.get_active() for radio in controller.radios] == [False, True]
    assert app.w.sound_output == "headphones-id"
    assert [call for call in calls if call[0] == "set"] == (
        [("set", "headphones-id")] * (1 if outcome in {"timeout", "cancelled"} else 2)
    )


def test_closing_output_selection_discards_late_success(
    ui, monkeypatch, selection_audio_worker  # noqa: F811
):
    app, controller, _calls, _state = _open(ui, monkeypatch)
    entered, release = threading.Event(), threading.Event()

    def delayed_selection(_sink):
        entered.set()
        release.wait(timeout=2)
        return sound.SoundResult(True, "")

    monkeypatch.setattr(sound, "set_output", delayed_selection)
    try:
        controller.radios[1].set_active(True)
        assert entered.wait(timeout=1)
        controller.close()
        assert controller.dialog is None
        assert controller.ticket is None
        release.set()
        deadline = time.monotonic() + 2
        while selection_audio_worker._active is not None and time.monotonic() < deadline:
            time.sleep(0.005)
        controller.poll()
        drain()
        assert app.w.sound_output == ""
        assert controller.chosen.id == "speakers-id"
    finally:
        release.set()


def test_failed_duplicate_label_choice_restores_the_accepted_radio(
    ui, monkeypatch, selection_audio_worker  # noqa: F811
):
    app, controller, calls, state = _open(ui, monkeypatch, duplicate_labels=True)
    assert controller.radios[0].get_label() == controller.radios[1].get_label()
    _select(app, controller, monkeypatch, state, "refused")
    assert controller.chosen.id == "speakers-id"
    assert [radio.get_active() for radio in controller.radios] == [True, False]
    assert calls == [("set", "headphones-id")]
