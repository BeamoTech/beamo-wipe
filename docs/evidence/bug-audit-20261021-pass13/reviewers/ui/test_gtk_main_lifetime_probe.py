"""Pass13 proof: main accessible window retires after setup/loop failures."""
import os
import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import accessible_wizard as ui

@pytest.fixture(autouse=True)
def safe_boundaries(monkeypatch):
    assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
    assert os.environ.get('DISPLAY') not in {':1', ':99'}
    effects = []
    def forbidden(*args, **kwargs):
        effects.append(True)
        raise AssertionError('native effect forbidden')
    for target in ('subprocess.run','subprocess.Popen','os.system',
        'beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline',
        'beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start',
        'beamo_wipe.nwipe_runner.DryRunRunner.start','beamo_wipe.app._shutdown',
        'beamo_wipe.sound._run','beamo_wipe.sound._popen'):
        monkeypatch.setattr(target, forbidden)
    yield
    assert effects == []

@pytest.mark.parametrize('stage', ['control', 'render', 'timer', 'loop-error', 'loop-return'])
def test_accessible_main_lifetime(monkeypatch, stage, request):
    before = set(ui.Gtk.Window.list_toplevels())
    peer = ui.Gtk.Window(title='Pass13 owned peer control')
    peer.show_all()
    before.add(peer)
    context = ui.GLib.MainContext.default()
    sources = []
    timeout = ui.GLib.timeout_add
    show = ui.Gtk.Window.show_all
    original = RuntimeError('controlled ' + stage)
    def add_timeout(delay, callback, *args):
        if stage == 'timer':
            raise original
        source = timeout(delay, callback, *args)
        sources.append(source)
        return source
    def show_window(window):
        show(window)
        if window not in before and stage == 'render':
            raise original
    def fail_loop():
        raise original
    monkeypatch.setattr(ui.GLib, 'timeout_add', add_timeout)
    monkeypatch.setattr(ui.Gtk.Window, 'show_all', show_window)
    wizard = make_demo_wizard()
    wizard.skip_intro()
    caught = None
    app = None
    try:
        try:
            app = ui.AccessibleWizard(wizard)
            if stage == 'loop-error':
                monkeypatch.setattr(ui.Gtk, 'main', fail_loop)
                app.run()
            elif stage == 'loop-return':
                monkeypatch.setattr(ui.Gtk, 'main', lambda: None)
                app.run()
            else:
                app.close()
        except RuntimeError as error:
            caught = error
        leaked = [window for window in ui.Gtk.Window.list_toplevels() if window not in before]
        pending = [source for source in sources if context.find_source_by_id(source) is not None]
        record = {'stage': stage, 'leaked_windows':len(leaked), 'leaked_sources':len(pending),
                  'original_preserved':caught is original, 'peer_visible':peer.get_visible()}
        request.node.user_properties.append(('pass13_lifetime', str(record)))
        assert caught is (original if stage in {'render','timer','loop-error'} else None), record
        assert peer.get_visible(), record
        assert leaked == [], record
        assert pending == [], record
    finally:
        for source in sources:
            pending_source = context.find_source_by_id(source)
            if pending_source is not None:
                pending_source.destroy()
        for window in ui.Gtk.Window.list_toplevels():
            if window not in before:
                window.destroy()
        peer.destroy()
