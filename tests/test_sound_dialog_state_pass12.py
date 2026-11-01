"""Sound controls must show accepted state and keep recovery actions visible."""

from dataclasses import replace
from types import SimpleNamespace
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import audio_jobs, copy as C, sound  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.methods import DEFAULT_METHOD  # noqa: E402
from beamo_wipe.models import Screen, WipeRequest  # noqa: E402
from beamo_wipe.ui import sound_dialog  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gdk, Gtk  # noqa: E402
from test_accessible_runtime import (  # noqa: E402, F401
    _dialog_button,
    drain,
    ui,
    wait_sound,
)


@pytest.fixture(autouse=True)
def fake_sound_effects(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Native application effect reached")

    worker = audio_jobs.AudioWorker()
    monkeypatch.setattr(audio_jobs, "worker", worker)
    monkeypatch.setattr(sound_dialog, "worker", worker)
    monkeypatch.setattr(sound, "orca_running", lambda: True)
    for name in ("set_output", "nudge_volume", "set_muted", "play_speech_test", "play_test", "play_outcome", "_run", "_popen"):
        monkeypatch.setattr(sound, name, forbidden)
    for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown"):
        monkeypatch.setattr(target, forbidden)
    yield
    worker.close()


def _owner():
    wizard = make_demo_wizard()
    wizard.skip_intro()
    return wizard


def _open(app):
    app.actions[C.SOUND_CHECK_BUTTON].clicked()
    wait_sound(app)
    return app._sound_dialog


@pytest.mark.parametrize("default", ["speakers", ""])
@pytest.mark.parametrize("restore_ok", [False, True])
def test_remembered_restore_uses_only_an_accepted_output(
    ui, monkeypatch, default, restore_ok  # noqa: F811
):
    outputs = (sound.SoundOutput("speakers", "Speakers", "fake", False),
               sound.SoundOutput("headphones", "Headphones", "fake", False))
    current = {"default": default, "ok": restore_ok}
    calls = []

    def state():
        return sound.SoundState(True, "", tuple(replace(output, is_default=output.id == current["default"]) for output in outputs), 40, False)

    def set_output(sink):
        calls.append(("set", sink))
        if current["ok"]:
            current["default"] = sink
        return sound.SoundResult(current["ok"], "Controlled output refusal")

    monkeypatch.setattr(sound, "list_outputs", state)
    monkeypatch.setattr(sound, "set_output", set_output)
    monkeypatch.setattr(sound, "nudge_volume", lambda sink, delta: calls.append(("volume", sink, delta)) or sound.SoundResult(True, ""))
    monkeypatch.setattr(sound, "set_muted", lambda sink, value: calls.append(("mute", sink, value)) or sound.SoundResult(True, ""))
    wizard = _owner()
    wizard.set_sound_output("headphones")
    app = ui(wizard)
    controller = _open(app)
    accepted = "headphones" if restore_ok else "speakers"
    assert controller.chosen.id == accepted
    assert [radio.get_active() for radio in controller.radios] == [accepted == "speakers", accepted == "headphones"]
    _dialog_button(controller.dialog, C.SOUND_LOUDER).clicked()
    wait_sound(app)
    _dialog_button(controller.dialog, C.SOUND_MUTE).clicked()
    wait_sound(app)
    assert ("volume", accepted, sound.VOLUME_STEP) in calls
    assert ("mute", accepted, True) in calls
    assert wizard.sound_output == "headphones"


def test_failed_remembered_restore_can_retry_the_same_output(ui, monkeypatch):  # noqa: F811
    outputs = (sound.SoundOutput("speakers", "Speakers", "fake", True),
               sound.SoundOutput("headphones", "Headphones", "fake", False))
    current = {"default": "speakers", "ok": False}
    calls = []

    def set_output(sink):
        calls.append(sink)
        if current["ok"]:
            current["default"] = sink
        return sound.SoundResult(current["ok"], "Controlled restore refused")

    monkeypatch.setattr(sound, "list_outputs", lambda: sound.SoundState(True, "", tuple(replace(output, is_default=output.id == current["default"]) for output in outputs), 40, False))
    monkeypatch.setattr(sound, "set_output", set_output)
    wizard = _owner()
    wizard.set_sound_output("headphones")
    app = ui(wizard)
    controller = _open(app)
    assert controller.status.get_text() == "Controlled restore refused"
    current["ok"] = True
    controller.radios[1].set_active(True)
    wait_sound(app)
    assert calls == ["headphones", "headphones"]
    assert current["default"] == controller.chosen.id == wizard.sound_output == "headphones"
    assert [radio.get_active() for radio in controller.radios] == [False, True]


def _bounds(widget, window):
    origin = tuple(window.get_window().get_origin())[-2:]
    relative = widget.translate_coordinates(window, 0, 0)
    assert relative is not None
    allocation = widget.get_allocation()
    return origin[0] + relative[0], origin[1] + relative[1], allocation.width, allocation.height


def _inside(rectangle, area):
    x, y, width, height = rectangle
    return (area.x <= x and area.y <= y and width > 0 and height > 0
            and x + width <= area.x + area.width and y + height <= area.y + area.height)


def _settle_geometry():
    deadline = time.monotonic() + 0.05
    while time.monotonic() < deadline:
        drain()
        time.sleep(0.002)
    Gdk.Display.get_default().sync()


@pytest.mark.parametrize("language", ["en", "fr", "de", "es", "it"])
@pytest.mark.parametrize("working", [False, True])
@pytest.mark.parametrize("count", [1, 2, 8, 16])
@pytest.mark.parametrize("workarea", [(0, 0, 800, 600), (0, 0, 1600, 1000), (120, 80, 800, 600)])
def test_sound_recovery_actions_fit_the_monitor_with_many_outputs(
    ui, monkeypatch, language, working, count, workarea  # noqa: F811
):
    outputs = tuple(sound.SoundOutput(f"fake-{index}", f"HDMI sound {index + 1}", "Fake output", index == 0) for index in range(count))
    monkeypatch.setattr(sound, "list_outputs", lambda: sound.SoundState(True, "", outputs, 40, False))
    wizard = _owner()
    wizard.set_language(language)
    wizard.screen = Screen.WORKING if working else Screen.OWNER
    app = ui(wizard)
    area = SimpleNamespace(**dict(zip(("x", "y", "width", "height"), workarea)))
    monitor = SimpleNamespace(get_workarea=lambda: area)
    display = SimpleNamespace(get_monitor_at_window=lambda _window: monitor,
                              get_primary_monitor=lambda: monitor, get_monitor=lambda _index: monitor)
    with monkeypatch.context() as scoped:
        scoped.setattr(Gtk.Window, "get_display", lambda _window: display)
        controller = _open(app)
    _settle_geometry()
    dialog = controller.dialog
    origin = tuple(dialog.get_window().get_origin())[-2:]
    width, height = dialog.get_size()
    assert _inside((*origin, width, height), area), (origin, width, height, workarea)
    close = _dialog_button(dialog, C.SOUND_CLOSE)
    assert _inside(_bounds(close, dialog), area)
    assert close.get_can_focus() and close.get_sensitive()
    if working:
        stop = _dialog_button(dialog, C.STOP_ASK)
        assert _inside(_bounds(stop, dialog), area)
        assert stop.get_can_focus() and stop.get_sensitive()
    assert len(controller.radios) == count
    assert all(radio.get_can_focus() and radio.get_sensitive() for radio in controller.radios)
    assert not wizard.runner.started


def test_scrolling_outputs_keeps_stop_action_available(ui, monkeypatch, tmp_path):  # noqa: F811
    outputs = tuple(sound.SoundOutput(f"fake-{index}", f"HDMI sound {index + 1}", "Fake output", index == 0) for index in range(32))
    monkeypatch.setattr(sound, "list_outputs", lambda: sound.SoundState(True, "", outputs, 40, False))
    wizard = _owner()
    wizard.screen = Screen.WORKING
    wizard._wipe_request = WipeRequest("/dev/sda", DEFAULT_METHOD, "/dev/sdb", str(tmp_path / "fake.log"))
    app = ui(wizard)
    controller = _open(app)
    stop = _dialog_button(controller.dialog, C.STOP_ASK)
    area = controller.dialog.get_display().get_monitor_at_window(controller.dialog.get_window()).get_workarea()
    controller.play_button.grab_focus()
    _settle_geometry()
    assert controller.dialog.get_focus() is controller.play_button
    assert _inside(_bounds(controller.play_button, controller.dialog), area)
    assert _bounds(controller.play_button, controller.dialog)[1] < _bounds(stop, controller.dialog)[1]
    controller.radios[-1].grab_focus()
    _settle_geometry()
    assert controller.dialog.get_focus() is controller.radios[-1]
    assert _inside(_bounds(controller.radios[-1], controller.dialog), area)
    assert _bounds(controller.radios[-1], controller.dialog)[1] < _bounds(stop, controller.dialog)[1]
    assert _inside(_bounds(stop, controller.dialog), area)
    _dialog_button(controller.dialog, C.SOUND_CLOSE).grab_focus()
    _settle_geometry()
    assert stop.get_sensitive()
    stop.clicked()
    assert controller.dialog is None
    assert wizard.stop_confirmation is not None
    assert not wizard.runner.started and not wizard.runner.cancelled
