"""Native held-Escape through a production GTK sound modal; fake effects only."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
assert os.environ.get('DISPLAY') not in {':1', ':99'}
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe import copy as C
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk, Gdk
from beamo_wipe.wizard import Wizard

OUT = Path('/tmp/pass16-ui')
PATHS = ('src/beamo_wipe/ui/accessible_wizard.py', 'src/beamo_wipe/ui/sound_dialog.py',
         'src/beamo_wipe/wizard.py', 'src/beamo_wipe/ui/tk_wizard.py',
         'src/beamo_wipe/ui/console_wizard.py')
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in PATHS}
effects = []
callback_errors = []
rows = []
old_hook = sys.excepthook
def callback_error(kind, error, trace):
    callback_errors.append({'type': kind.__name__, 'error': str(error)})
    old_hook(kind, error, trace)
sys.excepthook = callback_error

def forbidden(*args, **kwargs):
    effects.append('native application effect')
    raise AssertionError('Native application effect reached')

class Ticket:
    def __init__(self):
        self.cancelled = False
    def cancel(self):
        self.cancelled = True
    def poll(self):
        return False, None

class Clock:
    value = 0.0
    def __call__(self):
        return self.value

def drain(seconds=0.1):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.003)
    Gdk.Display.get_default().sync()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)

def make(screen):
    clock = Clock()
    wizard = Wizard(make_demo_wizard().discovery, DryRunRunner(clock=clock),
                    clock=clock, dry_run=True)
    wizard.preview = False
    wizard.skip_intro()
    if screen != Screen.OWNER:
        wizard.set_owner(True)
        wizard.continue_owner()
        wizard.select_disk(wizard.selectable[0].path)
        wizard.continue_pick()
        wizard.set_confirm_input(wizard.confirm.token)
        wizard.continue_confirm()
        if screen == Screen.LAST_CHANCE:
            wizard.continue_method()
        elif screen == Screen.WORKING:
            # Rendering/Stop-request only. Neither fake nor real engine runs.
            wizard.screen = Screen.WORKING
    assert wizard.screen == screen
    return wizard, clock

x11 = ctypes.CDLL('libX11.so.6')
xtst = ctypes.CDLL('libXtst.so.6')
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
x11.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int)]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeKeyEvent.restype = ctypes.c_int
display = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
assert display
escape = x11.XKeysymToKeycode(display, Gdk.KEY_Escape)
assert escape
def send(down):
    assert xtst.XTestFakeKeyEvent(display, escape, bool(down), 0)
    x11.XSync(display, False)
    drain(.07)

PATCHES = ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
           'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
           'beamo_wipe.nwipe_runner.NwipeRunner.start',
           'beamo_wipe.nwipe_runner.DryRunRunner.start',
           'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen')
from contextlib import ExitStack
try:
    with ExitStack() as stack:
        for target in PATCHES:
            stack.enter_context(patch(target, forbidden))
        stack.enter_context(patch('beamo_wipe.ui.accessible_wizard.emit_serial_marker', lambda *_: None))
        stack.enter_context(patch('beamo_wipe.ui.sound_dialog.worker.submit', lambda *_a, **_k: Ticket()))
        for screen in (Screen.OWNER, Screen.METHOD, Screen.LAST_CHANCE, Screen.WORKING):
            for mode in ('hold-repeat', 'fresh-press'):
                wizard, clock = make(screen)
                app = AccessibleWizard(wizard)
                event_trace = []
                def trace(_widget, event, name):
                    event_trace.append({'target': name, 'kind': event.type.value_nick,
                                        'key': event.keyval, 'time': event.time})
                    return False
                app.window.connect('key-press-event', trace, 'parent-press')
                app.window.connect('key-release-event', trace, 'parent-release')
                try:
                    app.window.resize(800, 600)
                    drain()
                    app.open_sound_check()
                    controller = app._sound_dialog
                    dialog = controller.dialog
                    dialog.connect('key-press-event', trace, 'modal-press')
                    dialog.connect('key-release-event', trace, 'modal-release')
                    drain()
                    assert dialog.get_mapped()
                    focus_xid, focus_revert = ctypes.c_ulong(), ctypes.c_int()
                    x11.XGetInputFocus(display, ctypes.byref(focus_xid), ctypes.byref(focus_revert))
                    assert focus_xid.value == dialog.get_window().get_xid(), (focus_xid.value, dialog.get_window().get_xid())
                    state_before = (wizard.owner_ok, wizard.selected, wizard.confirm_input,
                                    wizard.method, wizard._authorized_operation, wizard._wipe_request)
                    send(True)
                    first = {'screen': wizard.screen.name,
                             'modal_closed': controller.dialog is None,
                             'stop': wizard.stop_confirmation is not None,
                             'held': sorted(app.held)}
                    assert first['modal_closed'], first
                    if mode == 'fresh-press':
                        send(False)
                        send(True)
                    else:
                        # A physical key remains down. Let the private X server
                        # deliver its own autorepeat; no direct handler calls.
                        drain(.85)
                    second = {'screen': wizard.screen.name,
                              'stop': wizard.stop_confirmation is not None,
                              'held': sorted(app.held)}
                    state_after = (wizard.owner_ok, wizard.selected, wizard.confirm_input,
                                   wizard.method, wizard._authorized_operation, wizard._wipe_request)
                    rows.append({'screen': screen.name, 'mode': mode, 'first': first,
                                 'second': second, 'trace': event_trace,
                                 'authorization_unchanged': state_before == state_after,
                                 'engine_started': wizard.runner.started,
                                 'engine_cancelled': wizard.runner.cancelled,
                                 'wants_shutdown': wizard.wants_shutdown,
                                 'wants_new_session': wizard.wants_new_session})
                finally:
                    send(False)
                    app.close()
                    drain(.04)
finally:
    x11.XCloseDisplay(display)
    sys.excepthook = old_hook
result = {'hashes': hashes, 'rows': rows, 'effects': effects, 'callback_errors': callback_errors,
          'private_display': os.environ['DISPLAY']}
(OUT / 'modal-escape-probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
assert not effects and not callback_errors
assert len(rows) == 8
assert all(not r['engine_started'] and not r['engine_cancelled'] and not r['wants_shutdown']
           and not r['wants_new_session'] for r in rows)
