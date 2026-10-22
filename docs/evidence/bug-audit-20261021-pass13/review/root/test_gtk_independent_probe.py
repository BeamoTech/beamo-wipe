"""Private actual GTK ownership checks at alternate setup/loop boundaries."""
import os
import sys
import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import accessible_wizard as ui


@pytest.mark.parametrize('boundary', ['normal', 'render-failure', 'loop-return', 'loop-interrupt'])
def test_owned_main_view_is_retired(monkeypatch, boundary):
    assert os.environ['BEAMO_ISOLATED_X11_TEST'] == '1'
    assert os.environ['DISPLAY'] not in {':1', ':99'}
    peer = ui.Gtk.Window(title='Owned independent peer')
    peer.show_all()
    before = set(ui.Gtk.Window.list_toplevels())
    sources = []
    real_timer = ui.GLib.timeout_add
    def timer(*args):
        source = real_timer(*args)
        sources.append(source)
        return source
    monkeypatch.setattr(ui.GLib, 'timeout_add', timer)
    original_render = ui.AccessibleWizard.render
    failure = KeyboardInterrupt('owned setup/loop interrupt')
    def render(app):
        original_render(app)
        if boundary == 'render-failure': raise failure
    monkeypatch.setattr(ui.AccessibleWizard, 'render', render)
    def stop_loop():
        if boundary == 'loop-interrupt': raise failure
    context = ui.GLib.MainContext.default()
    previous_hook = sys.excepthook
    app = None
    try:
        if boundary == 'render-failure':
            with pytest.raises(KeyboardInterrupt) as caught:
                ui.AccessibleWizard(make_demo_wizard())
            assert caught.value is failure
        else:
            app = ui.AccessibleWizard(make_demo_wizard())
            if boundary == 'normal':
                app.close()
            else:
                monkeypatch.setattr(ui.Gtk, 'main', stop_loop)
                if boundary == 'loop-interrupt':
                    with pytest.raises(KeyboardInterrupt) as caught: app.run()
                    assert caught.value is failure
                else:
                    assert app.run() == 0
        assert sys.excepthook is previous_hook
        assert peer.get_visible()
        assert set(ui.Gtk.Window.list_toplevels()) == before
        assert all(context.find_source_by_id(source) is None for source in sources)
    finally:
        for source in sources:
            pending = context.find_source_by_id(source)
            if pending is not None: pending.destroy()
        for window in ui.Gtk.Window.list_toplevels():
            if window not in before: window.destroy()
        peer.destroy()
