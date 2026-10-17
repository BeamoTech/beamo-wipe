import os
import json
import sys
sys.path.insert(0, os.getcwd() + '/tests')
import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard
from beamo_wipe.ui.accessible_wizard import Gdk
from test_accessible_focus_input_pass11 import native

@pytest.fixture(autouse=True)
def fake_effects(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('Native application operation reached')
    for target in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk', 'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources', 'beamo_wipe.nwipe_runner.NwipeRunner.start', 'beamo_wipe.nwipe_runner.DryRunRunner.start', 'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen'):
        monkeypatch.setattr(target, forbidden)

@pytest.mark.parametrize('fullscreen', [False, True])
@pytest.mark.parametrize('pointer', ['inside', 'outside'])
def test_main_first_native_escape(native, fullscreen, pointer):
    native.root_focus()
    native.pointer(1599, 999)
    wizard = make_demo_wizard()
    app = TkWizard(wizard, fullscreen=fullscreen)
    seen = {}
    def send():
        x,y,w,h = app.root.winfo_rootx(), app.root.winfo_rooty(), app.root.winfo_width(), app.root.winfo_height()
        native.pointer(x + 20, y + 20) if pointer == 'inside' else native.pointer(1599,999)
        seen.update(geometry=[x,y,w,h], focus=str(app.root.focus_get()), before=wizard.screen.name)
        native.key(Gdk.KEY_Escape, True)
        native.key(Gdk.KEY_Escape, False)
    def inspect():
        seen.update(after=wizard.screen.name, after_focus=str(app.root.focus_get()))
        app._teardown()
    app.root.after(120, send)
    app.root.after(320, inspect)
    app.run()
    print(json.dumps(dict(seen,fullscreen=fullscreen,pointer=pointer)))
    assert wizard.screen is Screen.KEYBOARD, seen
