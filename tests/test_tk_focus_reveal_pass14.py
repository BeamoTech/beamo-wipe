"""Focused consent and typing controls must be visible in the scrolling body."""
import os

import pytest

from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard


@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    if os.environ.get('BEAMO_ISOLATED_X11_TEST') != '1':
        pytest.skip('Focus geometry requires an explicitly isolated X11 display')

    def forbidden(*_a, **_k):
        raise AssertionError('Native application effect reached')
    for name in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
                 'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
                 'beamo_wipe.nwipe_runner.NwipeRunner.start', 'beamo_wipe.nwipe_runner.DryRunRunner.start',
                 'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen'):
        monkeypatch.setattr(name, forbidden)
    monkeypatch.setattr('beamo_wipe.ui.tk_wizard.emit_serial_marker', lambda *_a: None)


def _app(screen, language='en', size='standard'):
    w = make_demo_wizard()
    w.preview = False
    w.set_language(language)
    w.set_text_size(size)
    w.skip_splash()
    if screen != Screen.KEYBOARD:
        w.accept_keyboard()
    if screen == Screen.CONFIRM:
        w.set_owner(True)
        w.continue_owner()
        w.select_disk(w.selectable[0].path)
        w.continue_pick()
    assert w.screen is screen
    app = TkWizard(w)
    app.root.geometry('800x600+0+0')
    app.root.update()
    app.root.focus_force()
    app._draw()
    app.root.update()
    return app


def _state(w):
    return (w.screen, w.owner_ok, w.selected, w.confirm_input, w.method,
            w._authorized_operation, w._wipe_request)


def _visible(app):
    focus = app.root.focus_get()
    canvas = app._body_canvas
    assert focus is not None and canvas is not None
    top = focus.winfo_rooty() - canvas.winfo_rooty()
    return 0 <= top and top + focus.winfo_height() <= canvas.winfo_height()


@pytest.mark.parametrize('screen', [Screen.KEYBOARD, Screen.OWNER, Screen.CONFIRM])
@pytest.mark.parametrize('language', ['en', 'fr', 'de'])
@pytest.mark.parametrize('size', ['standard', 'large', 'extra'])
def test_initial_typing_and_consent_focus_is_visible(screen, language, size):
    app = _app(screen, language, size)
    before = _state(app.w)
    try:
        assert _visible(app)
        app.root.update()
        assert _state(app.w) == before
        assert not app.w.erase_enabled and app.w._wipe_request is None
    finally:
        app._teardown()
        lang.set_language('en')


def test_manual_scroll_is_preserved_until_focus_changes():
    app = _app(Screen.OWNER)
    try:
        assert _visible(app)
        focus = app.root.focus_get()
        before = _state(app.w)
        canvas = app._body_canvas
        canvas.yview_moveto(0)
        app.root.update()
        assert canvas.yview()[0] == 0
        assert app.root.focus_get() is focus
        # Scrolling alone must not continually pull the owner back to focus.
        canvas.event_generate('<Button-5>')
        app.root.update()
        moved = canvas.yview()
        app.root.update()
        assert canvas.yview() == moved and moved[0] > 0
        app._primary.focus_set()
        app.root.update()
        assert canvas.yview() == moved  # Footer focus is outside the body.
        focus.focus_set()
        app.root.update()
        assert _visible(app)
        assert _state(app.w) == before
    finally:
        app._teardown()


def test_stale_focus_callback_cannot_scroll_replacement_screen():
    app = _app(Screen.OWNER)
    errors = []
    app.root.report_callback_exception = lambda *args: errors.append(args)
    try:
        focus = app.root.focus_get()
        app._primary.focus_set()
        app.root.update()
        focus.focus_set()
        app.w.back()
        app._draw()
        app.root.update()
        assert app.w.screen is Screen.KEYBOARD
        assert _visible(app)
        assert not errors and not app.w.owner_ok and app.w._wipe_request is None
    finally:
        app._teardown()
