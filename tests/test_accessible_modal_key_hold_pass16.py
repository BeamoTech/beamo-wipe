"""A native sound-modal key hold cannot become a second parent action."""

import os
import sys
import time

import pytest

pytest.importorskip("gi")
from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.models import Screen, WipeRequest  # noqa: E402
from beamo_wipe.nwipe_runner import DryRunRunner  # noqa: E402
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gdk, Gtk  # noqa: E402
from beamo_wipe.wizard import Wizard  # noqa: E402
from test_accessible_focus_input_pass11 import native  # noqa: E402, F401


class Clock:
    value = 0.0

    def __call__(self):
        return self.value


class PendingAudio:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def poll(self):
        return False, None


def _drain(seconds=0.0):
    until = time.monotonic() + seconds
    while True:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        if time.monotonic() >= until:
            return
        time.sleep(0.003)


def _wait(predicate):
    until = time.monotonic() + 2.0
    while time.monotonic() < until:
        _drain()
        if predicate():
            return
        time.sleep(0.003)
    assert predicate(), "The owned modal did not receive its native event"


def _authority(wizard):
    return (wizard.owner_ok, wizard.selected, wizard.confirm_input, wizard.method,
            wizard._authorized_operation, wizard._wipe_request,
            wizard.wants_shutdown, wizard.wants_new_session)


def _wizard(screen):
    clock = Clock()
    wizard = Wizard(make_demo_wizard().discovery, DryRunRunner(clock=clock),
                    clock=clock, dry_run=True)
    wizard.set_language("en")
    wizard.skip_intro()
    if screen is not Screen.OWNER:
        wizard.set_owner(True)
        wizard.continue_owner()
        wizard.select_disk(wizard.selectable[0].path)
        wizard.continue_pick()
        wizard.set_confirm_input(wizard.confirm.token)
        wizard.continue_confirm()
        if screen is Screen.LAST_CHANCE:
            wizard.continue_method()
        elif screen is Screen.WORKING:
            # A real immutable request and a nonterminal fake poll model the
            # running UI. No start method or process is invoked.
            wizard._wipe_request = WipeRequest(
                wizard.selected.path, wizard.method, wizard.discovery.boot.path,
                "/tmp/beamo-modal-held-key-fake.log",
            )
            wizard.screen = Screen.WORKING
    assert wizard.screen is screen
    return wizard, clock


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native modal keys require an explicitly isolated X11 display")
    assert os.environ.get("DISPLAY") not in {":1", ":99"}
    effects, errors, tickets = [], [], []

    def forbidden(*_args, **_kwargs):
        effects.append("native application effect")
        raise AssertionError("Native application effect reached")

    def submit(*_args, **_kwargs):
        ticket = PendingAudio()
        tickets.append(ticket)
        return ticket

    def callback_error(kind, error, _trace):
        errors.append((kind.__name__, str(error)))

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.nwipe_runner.DryRunRunner.cancel", "beamo_wipe.app._shutdown",
        "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    monkeypatch.setattr(sys, "excepthook", callback_error)
    monkeypatch.setattr("beamo_wipe.ui.sound_dialog.worker.submit", submit)
    monkeypatch.setattr("beamo_wipe.ui.accessible_wizard.emit_serial_marker", lambda *_args: None)
    yield
    assert not errors
    assert not effects
    assert all(ticket.cancelled for ticket in tickets)


@pytest.fixture
def ui():
    apps = []

    def build(screen):
        wizard, clock = _wizard(screen)
        app = AccessibleWizard(wizard)
        apps.append(app)
        app.window.resize(800, 600)
        _drain(0.08)
        return app, clock

    yield build
    for app in reversed(apps):
        app.close()
    _drain()


def _open(app):
    app.open_sound_check()
    controller = app._sound_dialog
    _drain(0.05)
    assert controller.dialog is not None and controller.dialog.get_mapped()
    assert controller.dialog.get_focus() is controller.status
    return controller


def _key_event(window, key, pressed, timestamp):
    event = Gdk.Event.new(Gdk.EventType.KEY_PRESS if pressed else Gdk.EventType.KEY_RELEASE)
    event.window = window.get_window()
    event.keyval = key
    event.time = timestamp
    return bool(window.emit("key-press-event" if pressed else "key-release-event", event))


@pytest.mark.parametrize("screen", [Screen.OWNER, Screen.METHOD, Screen.LAST_CHANCE, Screen.WORKING])
@pytest.mark.parametrize("rerender", [False, True])
def test_native_escape_closes_modal_once_and_waits_for_a_fresh_press(ui, native, screen, rerender):  # noqa: F811
    app, clock = ui(screen)
    controller = _open(app)
    if rerender:
        app.render()
        _drain()
        assert app._sound_dialog is controller and controller.dialog is not None
    before = _authority(app.w)
    observed = []
    releases = []

    def observe(_widget, event):
        if event.type == Gdk.EventType.KEY_PRESS and event.keyval == Gdk.KEY_Escape:
            observed.append(event.time)
        if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
            releases.append(event.time)
        return False

    # GtkWidget::event precedes its key-specific handler, including a handler
    # that returns True to consume repeats. This only observes native events.
    controller.dialog.connect("event", observe)
    app.window.connect("event", observe)
    native.key(Gdk.KEY_Escape, True)
    _wait(lambda: controller.dialog is None)
    _drain(0.85)
    assert len(observed) >= 2, "The private X server did not deliver native hold-repeat"
    assert app.w.screen is screen
    assert app.w.stop_confirmation is None
    assert _authority(app.w) == before
    assert not app.w.runner.started and not app.w.runner.cancelled
    if screen is Screen.LAST_CHANCE:
        clock.value = 4.0
        assert not app.w.erase_enabled

    native.key(Gdk.KEY_Escape, False)
    assert releases
    # Distinct physical presses must also have distinct X server timestamps;
    # same-timestamp release/press remains an intentional repeat guard case.
    _drain(0.02)
    native.key(Gdk.KEY_Escape, True)
    assert observed[-1] != releases[-1]
    native.key(Gdk.KEY_Escape, False)
    expected = {Screen.OWNER: Screen.KEYBOARD, Screen.METHOD: Screen.CONFIRM,
                Screen.LAST_CHANCE: Screen.METHOD, Screen.WORKING: Screen.WORKING}[screen]
    assert app.w.screen is expected
    assert (app.w.stop_confirmation is not None) is (screen is Screen.WORKING)
    assert _authority(app.w) == before
    assert not app.w.runner.started and not app.w.runner.cancelled


@pytest.mark.parametrize("key", [Gdk.KEY_Escape, Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space, Gdk.KEY_F5])
@pytest.mark.parametrize("repeat", ["direct", "same-timestamp-pair"])
def test_modal_owns_guarded_press_and_repeat_without_dispatching_parent(ui, key, repeat):
    app, _clock = ui(Screen.OWNER)
    controller = _open(app)
    before = _authority(app.w)
    _key_event(controller.dialog, key, True, 1000)
    assert key in app.held
    assert app.w.screen is Screen.OWNER and _authority(app.w) == before
    target = controller.dialog or app.window
    if repeat == "same-timestamp-pair":
        _key_event(target, key, False, 1020)
        timestamp = 1020
    else:
        timestamp = 1010
    assert _key_event(target, key, True, timestamp)
    assert app.w.screen is Screen.OWNER and _authority(app.w) == before
    if controller.dialog is not None:
        controller.close()
    _key_event(app.window, key, False, 1100)
    assert key not in app.held
    _key_event(app.window, key, True, 1200)
    expected = (Screen.KEYBOARD if key == Gdk.KEY_Escape else
                Screen.REFRESH_CONFIRM if key == Gdk.KEY_F5 else Screen.OWNER)
    assert app.w.screen is expected
    assert not app.w.runner.started and not app.w.runner.cancelled
    _key_event(app.window, key, False, 1300)


@pytest.mark.parametrize("key", [Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space])
def test_release_in_modal_keeps_the_next_fresh_native_activation(ui, native, key):  # noqa: F811
    app, _clock = ui(Screen.OWNER)
    before = _authority(app.w)
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    native.key(key, True)
    if key == Gdk.KEY_space:
        native.key(key, False)
    _wait(lambda: app._sound_dialog is not None and app._sound_dialog.dialog is not None)
    first = app._sound_dialog
    if key != Gdk.KEY_space:
        native.key(key, False)
    assert key not in app.held
    first.close()
    _drain()
    app.actions[C.SOUND_CHECK_BUTTON].grab_focus()
    native.key(key, True)
    native.key(key, False)
    _wait(lambda: app._sound_dialog is not first and app._sound_dialog.dialog is not None)
    assert app.w.screen is Screen.OWNER and _authority(app.w) == before
    assert not app.w.runner.started and not app.w.runner.cancelled
