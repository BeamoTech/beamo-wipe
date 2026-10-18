import json
from types import SimpleNamespace
import pytest
from test_accessible_focus_input_pass11 import native, fake_effects, Gdk, Gtk, drain
from beamo_wipe.ui.accessible_wizard import AccessibleWizard

@pytest.fixture(autouse=True)
def gtk_ready():
    assert Gtk.init_check(None)[0]

def test_zero_delay_fresh_native_keys(native, request):
    state=SimpleNamespace(held=set(), _release_times={})
    events=[]
    window=Gtk.Window()
    window.add(Gtk.Entry())
    def press(_window,event):
        row={"time":event.time,"previous_release":state._release_times.get(event.keyval),"held_before":event.keyval in state.held}
        result=AccessibleWizard._remember_key_press(state,event)
        row["blocked"]=result;events.append(row)
        return result
    window.connect("key-press-event",press)
    window.connect("key-release-event",lambda _window,event:AccessibleWizard._key_release(state,_window,event))
    try:
        window.show_all();window.present();window.get_window().focus(Gdk.CURRENT_TIME);window.get_child().grab_focus();drain()
        for _ in range(256):
            native.key(Gdk.KEY_Return,True);native.key(Gdk.KEY_Return,False)
    finally:
        window.destroy();drain()
        request.node.user_properties.append(("native_fresh_events",json.dumps(events)))
    assert len(events)==256
    assert not any(e["blocked"] for e in events), [e for e in events if e["blocked"]]
