"""Observe exact new navigate-idle setup; no policy, focus or deadline repair."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from contextlib import ExitStack
from unittest.mock import patch

assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
assert os.environ.get('DISPLAY') not in {':1', ':99'}
sys.path[:0] = [str(Path.cwd() / 'src'), str(Path.cwd() / 'tests')]
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard
from test_accessible_sound_review_pass15_ui import _review

OUT = Path('/tmp/pass16-ui')
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
          ('src/beamo_wipe/ui/tk_wizard.py', 'tests/test_confirm_focus_callback_lifetime_pass16.py')}
rows, effects = [], []
registrations = {}
active_events = []
origin = time.perf_counter()
def forbidden(*_args, **_kwargs):
    effects.append('native application effect')
    raise AssertionError('Native application effect reached')

def authority(wizard):
    return (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
            wizard.method, wizard._erase_until, wizard._authorized_operation,
            wizard._wipe_request, wizard.wants_shutdown, wizard.wants_new_session)

original_register = tk.Misc._register
def register(widget, function, *args, **kwargs):
    command = original_register(widget, function, *args, **kwargs)
    underlying = function
    if getattr(getattr(function, '__code__', None), 'co_name', '') == 'callit':
        cells = dict(zip(function.__code__.co_freevars, function.__closure__ or ()))
        if 'func' in cells:
            underlying = cells['func'].cell_contents
    code = getattr(underlying, '__code__', None)
    if code is not None and code.co_filename.endswith('tk_wizard.py'):
        info = {'command': command, 'owner': str(widget), 'source': code.co_filename,
                'line': code.co_firstlineno, 'function': code.co_name,
                'ms': (time.perf_counter()-origin)*1000}
        registrations[command] = info
        active_events.append(dict(event='register', **info))
    return command

x11 = ctypes.CDLL('libX11.so.6')
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
x11.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int)]
connection = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
assert connection

def snapshot(app):
    xid, revert = ctypes.c_ulong(), ctypes.c_int()
    x11.XGetInputFocus(connection, ctypes.byref(xid), ctypes.byref(revert))
    timers = []
    for timer in app.root.tk.call('after', 'info'):
        script, kind = app.root.tk.call('after', 'info', timer)
        command = str(script)
        if command in registrations:
            timers.append({'id': timer, 'script': command, 'kind': kind,
                           'exists': bool(app.root.tk.call('info', 'commands', command)),
                           'registration': registrations[command]})
    focus = app.root.focus_get()
    return {'ms': (time.perf_counter()-origin)*1000,
            'screen': app.w.screen.name, 'focus': str(focus),
            'focus_class': type(focus).__name__, 'focus_is_primary': focus is app._primary,
            'primary': str(app._primary), 'native_focus_xid': xid.value,
            'root_xid': app.root.winfo_id(), 'mapped': bool(app.root.winfo_ismapped()),
            'geometry': app.root.wm_geometry(),
            'allocation': [app.root.winfo_width(), app.root.winfo_height()],
            'root_focus_last_for': str(app.root.tk.call('focus', '-lastfor', '.')),
            'grab': str(app.root.tk.call('grab', 'current')), 'timers': timers}

PATCHES = ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
           'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
           'beamo_wipe.nwipe_runner.NwipeRunner.start',
           'beamo_wipe.nwipe_runner.DryRunRunner.start',
           'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen')
try:
    with ExitStack() as stack:
        for name in PATCHES:
            stack.enter_context(patch(name, forbidden))
        stack.enter_context(patch.object(tk.Misc, '_register', register))
        stack.enter_context(patch('beamo_wipe.ui.tk_wizard.emit_serial_marker', lambda *_a: None))
        for size in ('standard', 'large', 'extra'):
            origin = time.perf_counter()
            active_events = []
            events, errors = active_events, []
            wizard, _clock = _review()
            wizard.set_language('en')
            wizard.back()
            wizard.back()
            wizard.set_text_size(size)
            original_draw = TkWizard._draw
            def draw(app):
                caller = sys._getframe(1).f_code.co_name
                events.append(dict(event='draw-before', caller=caller, **snapshot(app)))
                try:
                    return original_draw(app)
                finally:
                    events.append(dict(event='draw-after', caller=caller, **snapshot(app)))
            with patch.object(TkWizard, '_draw', draw):
                app = TkWizard(wizard)
                def report(kind, error, _trace):
                    errors.append({'type': kind.__name__, 'message': str(error)})
                app.root.report_callback_exception = report
                app.root.createcommand('pass16_nav_bgerror', lambda message: errors.append({'type': 'Tcl bgerror', 'message': message}))
                app.root.tk.eval('proc bgerror {message} {pass16_nav_bgerror $message}')
                for sequence in ('<Map>', '<Unmap>', '<Configure>', '<FocusIn>', '<FocusOut>'):
                    def record(event, seq=sequence):
                        if seq != '<Configure>' or event.widget is app.root:
                            events.append(dict(event=seq, target=str(event.widget), **snapshot(app)))
                    app.root.bind(sequence, record, add='+')
                try:
                    # Exact currently failing fixture sequence, with no extra
                    # map, focus, production draw or idle-drain intervention.
                    app.root.update()
                    app.root.focus_force()
                    app._draw()
                    events.append(dict(event='mapped-prime-complete', **snapshot(app)))
                    app.root.geometry('800x600+0+0')
                    app.root.deiconify()
                    app.root.focus_force()
                    wizard.back()
                    expected = authority(wizard)
                    assert wizard.screen is Screen.PICK
                    app._draw()
                    events.append(dict(event='lifecycle-render-complete', **snapshot(app)))
                    app.root.update()
                    events.append(dict(event='initial-update-complete', **snapshot(app)))
                    start = time.perf_counter()
                    observations = []
                    for milliseconds in (100, 120, 200):
                        until = start+milliseconds/1000
                        while time.perf_counter() < until:
                            app.root.tk.call('update')
                            time.sleep(.003)
                        app.root.tk.call('update')
                        observations.append(dict(deadline_ms=milliseconds,
                            actual_ms=(time.perf_counter()-start)*1000, **snapshot(app)))
                    rows.append({'size': size, 'events': events, 'observations': observations,
                                 'errors': errors, 'state_unchanged': authority(wizard)==expected,
                                 'engine_started': wizard.runner.started,
                                 'has_request': wizard._wipe_request is not None})
                finally:
                    for timer in app.root.tk.call('after', 'info'):
                        app.root.tk.call('after', 'cancel', timer)
                    app._teardown()
finally:
    x11.XCloseDisplay(connection)
result = {'hashes': hashes, 'rows': rows, 'effects': effects,
          'fixture_sequence_sha256': 'e90f9fa058948711d58e20fa20eedb2cec406096f0298424e7e87a286f8e9a82',
          'note': 'Observer only; 100/120/200ms findings are not a passing product gate.'}
(OUT/'navigate-focus-diagnostic.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
assert len(rows)==3 and not effects
assert all(row['state_unchanged'] and not row['engine_started'] and not row['has_request'] for row in rows)
