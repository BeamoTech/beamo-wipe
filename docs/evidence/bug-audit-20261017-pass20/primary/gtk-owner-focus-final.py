"""Fresh fake-only GUI geometry matrix; no native inventory or erase operation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
assert os.environ.get('DISPLAY') not in {':1', ':99'}
sys.path[:0] = [str(Path.cwd() / 'src'), str(Path.cwd() / 'tests')]
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.power import PowerStatus
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk, Gdk
from beamo_wipe.ui.tk_wizard import TkWizard, _Button

OUT = Path('/tmp/pass20-ui')
FILES = ['src/beamo_wipe/ui/tk_wizard.py', 'src/beamo_wipe/ui/accessible_wizard.py',
         'src/beamo_wipe/ui/console_wizard.py', 'src/beamo_wipe/ui/sound_dialog.py',
         'src/beamo_wipe/wizard.py', 'src/beamo_wipe/copy.py', 'src/beamo_wipe/ui/layout.py']
hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in FILES}
rows = []
forbidden_calls = []
serial_markers = []
power_reads = []

def fake_power():
    power_reads.append(True)
    return PowerStatus(ac=True, batteries=(75,), complete=True)

def forbidden(*args, **kwargs):
    forbidden_calls.append(repr((args, kwargs)))
    raise AssertionError('A native application effect was reached')


def make(target, language, size):
    scenario = {'PICK_BLOCKED': 'blocked', 'PICK_EMPTY': 'empty', 'DIAGNOSTIC': 'blocked'}.get(target, 'happy')
    w = make_demo_wizard(scenario=scenario)
    # Render shipped controls against fake discovery/runner with effect guards.
    w.preview = False
    w.set_language(language)
    w.set_text_size(size)
    if target == 'SPLASH':
        return w
    w.skip_splash()
    if target == 'KEYBOARD':
        return w
    w.accept_keyboard()
    if target == 'OWNER':
        return w
    w.set_owner(True)
    w.continue_owner()
    if target in {'PICK', 'PICK_BLOCKED', 'PICK_EMPTY'}:
        assert w.screen.name == target
        return w
    if target == 'DISK_HELP':
        w.open_disk_help()
    elif target == 'DIAGNOSTIC':
        w.open_diagnostic()
    else:
        w.select_disk(w.selectable[0].path)
        w.continue_pick()
        if target != 'CONFIRM':
            w.set_confirm_input(w.confirm.token)
            w.continue_confirm()
            if target == 'LAST_CHANCE':
                w.continue_method()
            elif target == 'LIMITS':
                w.open_limits()
            elif target == 'ADVANCED':
                w.open_advanced()
            elif target == 'REPORT_HELP':
                w.open_report_help()
            elif target == 'REFRESH_CONFIRM':
                w.open_refresh_confirm()
    assert w.screen.name == target, (target, w.screen)
    return w


def descendants(widget, gtk):
    for child in widget.get_children() if gtk and isinstance(widget, Gtk.Container) else ([] if gtk else widget.winfo_children()):
        yield child
        yield from descendants(child, gtk)


def state(w):
    return (w.screen, w.owner_ok, w.selected, w.confirm_input, w.method,
            w._authorized_operation, w._wipe_request, w.wants_shutdown, w.wants_new_session)


def drain():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def stable(app, gtk):
    # Observe actual native allocations, rather than assuming a timer means mapped.
    previous = None
    count = 0
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if gtk:
            drain()
            current = tuple(app.window.get_size())
            mapped = app.window.get_mapped()
        else:
            app.root.update()
            current = (app.root.winfo_width(), app.root.winfo_height())
            mapped = app.root.winfo_ismapped()
        count = count + 1 if current == previous and mapped else 0
        if count >= 3:
            return current
        previous = current
        time.sleep(.008)
    raise AssertionError(('Allocation failed to settle', gtk, previous))


patches = [patch(name, forbidden) for name in (
    'subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
    'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
    'beamo_wipe.nwipe_runner.NwipeRunner.start', 'beamo_wipe.nwipe_runner.DryRunRunner.start',
    'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen')]
patches.extend([
    patch('beamo_wipe.ui.tk_wizard.emit_serial_marker', serial_markers.append),
    patch('beamo_wipe.ui.accessible_wizard.emit_serial_marker', serial_markers.append),
    patch('beamo_wipe.diagnostics.emit_serial_marker', serial_markers.append),
    patch('beamo_wipe.power.read_power', fake_power),
    patch('beamo_wipe.wizard.read_power', fake_power),
])
for item in patches:
    item.start()
try:
    for language in ('en','fr','de'):
        for size in ('standard','large','extra'):
            w=make('OWNER',language,size);before=state(w);app=AccessibleWizard(w)
            try:
                stable(app,True)
                checks=[v for v in descendants(app.body,True) if isinstance(v,Gtk.CheckButton)]
                assert len(checks)==1
                check=checks[0];steps=0
                while app.window.get_focus() is not check and steps<30:
                    app.window.child_focus(Gtk.DirectionType.TAB_FORWARD);drain();steps+=1
                assert app.window.get_focus() is check,(language,size,steps)
                deadline=time.monotonic()+.4
                while time.monotonic()<deadline:drain();time.sleep(.005)
                pos=check.translate_coordinates(app.window,0,0);a=check.get_allocation();rect=[*pos,a.width,a.height]
                x,y,width,height=rect;clips=[];node=check.get_parent()
                while node is not None:
                    if isinstance(node,(Gtk.ScrolledWindow,Gtk.Viewport)):
                        p=node.translate_coordinates(app.window,0,0);a=node.get_allocation();clip=[*p,a.width,a.height];clips.append(clip)
                        assert x>=p[0] and y>=p[1] and x+width<=p[0]+a.width and y+height<=p[1]+a.height,(language,size,rect,clip)
                    node=node.get_parent()
                assert state(w)==before and not w.owner_ok and not app.primary.get_sensitive()
                rows.append(dict(language=language,text_size=size,tab_steps=steps,owner_checkbox_rect=rect,viewport_clips=clips,fully_visible=True,authorization_unchanged=True))
            finally:app.close();drain()
    assert not forbidden_calls
    print(json.dumps(dict(source=hashes,cases=len(rows),rows=rows,forbidden_calls=forbidden_calls)),flush=True)
finally:
    for item in reversed(patches):item.stop()
