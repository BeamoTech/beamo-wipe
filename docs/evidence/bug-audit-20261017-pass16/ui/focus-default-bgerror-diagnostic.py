"""Attribute original 140ms focus failure without changing product/tests/deadline."""
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
from beamo_wipe import copy as C
from beamo_wipe.models import Screen
from beamo_wipe.ui.accessible_wizard import Gdk
from beamo_wipe.ui.tk_wizard import TkWizard, _Box, _Button
from test_accessible_sound_review_pass15_ui import _review

OUT = Path('/tmp/pass16-ui')
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
          ('src/beamo_wipe/ui/tk_wizard.py','tests/test_tk_input_scroll_pass13.py',
           'tests/test_accessible_sound_review_pass15_ui.py')}
rows, effects = [], []
registrations = {}
active_events = []
registration_clock = time.perf_counter()
original_register = tk.Misc._register
def traced_register(widget, function, *args, **kwargs):
    command = original_register(widget, function, *args, **kwargs)
    underlying = function
    if getattr(getattr(function, "__code__", None), "co_name", "") == "callit":
        closure = dict(zip(function.__code__.co_freevars, function.__closure__ or ()))
        if "func" in closure:
            underlying = closure["func"].cell_contents
    code = getattr(underlying, "__code__", None)
    if code is not None and code.co_filename.endswith("tk_wizard.py"):
        record = {"command": command, "widget": str(widget), "name": code.co_name,
                  "file": code.co_filename, "line": code.co_firstlineno,
                  "ms": (time.perf_counter()-registration_clock)*1000}
        registrations[command] = record
        active_events.append(dict(event="register", **record))
    return command

def timer_state(root):
    result = []
    for identifier in root.tk.call("after", "info"):
        script, kind = root.tk.call("after", "info", identifier)
        command = root.tk.splitlist(script)[0]
        record = registrations.get(command)
        if record is not None:
            result.append({"id": identifier, "script": script, "kind": kind,
                           "command_exists": bool(root.tk.call("info", "commands", command)),
                           "source": record})
    return result

def native_windows(root):
    result=[]
    for child in root.tk.splitlist(root.tk.call("winfo", "children", ".")):
        if root.tk.call("winfo", "toplevel", child) == child:
            result.append({"path": child, "mapped": bool(root.tk.call("winfo", "ismapped", child)),
                           "class": root.tk.call("winfo", "class", child)})
    return result
def forbidden(*args, **kwargs):
    effects.append('native application effect')
    raise AssertionError('Native application effect reached')

x11 = ctypes.CDLL('libX11.so.6')
xtst = ctypes.CDLL('libXtst.so.6')
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
x11.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int)]
xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
connection = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
assert connection
def root_focus():
    x11.XSetInputFocus(connection, 1, 0, 0)
    x11.XSync(connection, False)

PATCHES = ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
           'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
           'beamo_wipe.nwipe_runner.NwipeRunner.start',
           'beamo_wipe.nwipe_runner.DryRunRunner.start',
           'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen')
try:
    with ExitStack() as stack:
        stack.enter_context(patch.object(tk.Misc, '_register', traced_register))
        for target in PATCHES:
            stack.enter_context(patch(target, forbidden))
        stack.enter_context(patch('beamo_wipe.ui.tk_wizard.emit_serial_marker', lambda *_: None))
        for screen in (Screen.KEYBOARD, Screen.OWNER, Screen.CONFIRM, Screen.LAST_CHANCE):
            for mapped in (False, True):
                root_focus()
                monitor = Gdk.Display.get_default().get_monitor(0).get_geometry()
                assert xtst.XTestFakeMotionEvent(connection, -1, monitor.width-1, monitor.height-1, 0)
                x11.XSync(connection, False)
                wizard, clock = _review()
                if screen is Screen.KEYBOARD:
                    wizard.open_keyboard()
                else:
                    while wizard.screen is not screen:
                        wizard.back()
                events, errors = [], []
                active_events = events
                start = time.perf_counter()
                registration_clock = start
                app_box = []
                def focus_info(root):
                    try:
                        focus = root.focus_get()
                        xid, revert = ctypes.c_ulong(), ctypes.c_int()
                        x11.XGetInputFocus(connection, ctypes.byref(xid), ctypes.byref(revert))
                        return {'focus': str(focus), 'class': type(focus).__name__,
                                'x_focus': xid.value,
                                'root_xid': root.winfo_id(), 'mapped': bool(root.winfo_ismapped()),
                                'dimensions': [root.winfo_width(), root.winfo_height()],
                                'tcl_focus': str(root.tk.call('focus')),
                                'grab': str(root.tk.call('grab', 'current')),
                                'toplevels': native_windows(root)}
                    except (tk.TclError, KeyError) as error:
                        return {'query_error': str(error)}
                original_draw = TkWizard._draw
                def traced_draw(app):
                    call = sys._getframe(1).f_code.co_name
                    events.append({'event': 'draw-start', 'caller': call,
                                   'ms': (time.perf_counter()-start)*1000, 'timers': timer_state(app.root)})
                    try:
                        return original_draw(app)
                    finally:
                        events.append({'event': 'draw-end', 'caller': call,
                                       'ms': (time.perf_counter()-start)*1000,
                                       **focus_info(app.root), 'timers': timer_state(app.root)})
                with patch.object(TkWizard, '_draw', traced_draw):
                    app = TkWizard(wizard)
                    app_box.append(app)
                    original_report = app.root.report_callback_exception
                    def callback_error(kind, error, trace):
                        errors.append({'type': kind.__name__, 'error': str(error)})
                        original_report(kind, error, trace)
                    app.root.report_callback_exception = callback_error
                    # Observe the interpreter's existing default handler; never
                    # replace it or suppress its native error window/focus.
                    default_bgerror = app.root.tk.splitlist(app.root.tk.call('interp', 'bgerror', ''))[0]
                    def trace_bgerror(*args):
                        events.append({'event': 'default-bgerror-enter', 'args': [str(a) for a in args],
                                       'ms': (time.perf_counter()-start)*1000,
                                       **focus_info(app.root), 'timers': timer_state(app.root)})
                    app.root.createcommand('pass16_trace_bgerror', trace_bgerror)
                    app.root.tk.call('trace', 'add', 'execution', default_bgerror, 'enter', 'pass16_trace_bgerror')
                    for sequence in ('<Map>', '<FocusIn>', '<FocusOut>'):
                        app.root.bind(sequence, lambda event, seq=sequence: events.append({
                            'event': seq, 'target': str(event.widget),
                            'ms': (time.perf_counter()-start)*1000,
                            **focus_info(app.root)}), add='+')
                    if mapped:
                        app.root.update()
                        root_focus()
                    clock.value = 2
                    before = (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
                              wizard.method, wizard._erase_until, wizard._authorized_operation)
                    scheduled = time.perf_counter()
                    snapshots = []
                    def inspect(deadline):
                        try:
                            focus = app.root.focus_get()
                            focus_error = ''
                        except (tk.TclError, KeyError) as error:
                            focus, focus_error = None, repr(error)
                        if screen in {Screen.KEYBOARD, Screen.CONFIRM}:
                            variable = app._typing_var if screen is Screen.KEYBOARD else app._confirm_var
                            match = isinstance(focus, tk.Entry) and focus.cget('textvariable') == str(variable)
                        elif screen is Screen.OWNER:
                            match = isinstance(focus, _Box) and 'owner_key' in focus.bind('<space>')
                        else:
                            match = isinstance(focus, _Button) and focus.itemcget(focus._label, 'text') == C.BTN_BACK
                        snapshots.append({'deadline_ms': deadline,
                            'actual_ms': (time.perf_counter()-scheduled)*1000,
                            'matches_original_focus_assertion': bool(match), 'focus_query_error': focus_error,
                            'countdown': wizard.countdown_left, **focus_info(app.root),
                            'pending_timers': timer_state(app.root)})
                    def cleanup():
                        for timer in app.root.tk.call('after', 'info'):
                            app.root.tk.call('after', 'cancel', timer)
                        app._teardown()
                    for deadline in (140, 300, 600):
                        app.root.after(deadline, lambda d=deadline: inspect(d))
                    app.root.after(650, cleanup)
                    code = app.run()
                    after = (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
                             wizard.method, wizard._erase_until, wizard._authorized_operation)
                    rows.append({'screen': screen.name, 'premapped': mapped,
                                 'code': code, 'snapshots': snapshots, 'trace': events,
                                 'state_unchanged': before == after, 'errors': errors,
                                 'engine_started': wizard.runner.started,
                                 'has_request': wizard._wipe_request is not None})
                    app._teardown()
finally:
    x11.XCloseDisplay(connection)
result = {'hashes': hashes, 'rows': rows, 'effects': effects,
          'note': '140ms is unchanged original assertion deadline; later observations only attribute failures.'}
(OUT / 'focus-default-bgerror-diagnostic.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
assert len(rows) == 8 and not effects
assert all(r['code'] == 0 and r['state_unchanged'] and not r['engine_started']
           and not r['has_request'] for r in rows)
# Existing default-bgerror behavior and focus mismatches are measured findings,
# not silently reclassified as a passing product check.
