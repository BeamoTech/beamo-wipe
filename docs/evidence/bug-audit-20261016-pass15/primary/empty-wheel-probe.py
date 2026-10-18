"""Current shipped Tk empty/picker inventory, fake data and effect guards only."""
import hashlib
import json
import os
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
import tkinter as tk
from unittest.mock import patch

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import ExcludedDevice, Screen
from beamo_wipe.ui.accessible_wizard import Gdk
from beamo_wipe.ui.tk_wizard import TkWizard

assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
out = Path('/tmp/pass15-primary')
effects = []


def forbidden(*args, **kwargs):
    effects.append('native')
    raise AssertionError('Native application effect reached')


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


rows = []
with ExitStack() as guards:
    for target in ('subprocess.run', 'subprocess.Popen',
                   'beamo_wipe.discover.run_lsblk',
                   'beamo_wipe.discover.read_cmdline',
                   'beamo_wipe.discover.read_mount_sources',
                   'beamo_wipe.nwipe_runner.NwipeRunner.start',
                   'beamo_wipe.nwipe_runner.DryRunRunner.start',
                   'beamo_wipe.app._shutdown',
                   'beamo_wipe.sound._run', 'beamo_wipe.sound._popen'):
        guards.enter_context(patch(target, forbidden))
    guards.enter_context(patch('beamo_wipe.ui.tk_wizard.emit_serial_marker', lambda *_: None))
    for scenario in ('empty', 'happy'):
        for sequence, delta, direction in (('<Button-5>', None, 1),
                                            ('<Button-4>', None, -1),
                                            ('<MouseWheel>', -120, 1),
                                            ('<MouseWheel>', 120, -1)):
            w = make_demo_wizard(scenario=scenario)
            w.preview = False
            # Information-only records do not participate in discovery/safety.
            w.discovery = replace(w.discovery, excluded=tuple(
                ExcludedDevice(f'Fake component {i}', ('read-only',), path=f'/dev/fake{i}')
                for i in range(16)))
            w.skip_intro()
            w.set_owner(True)
            w.continue_owner()
            assert w.screen is (Screen.PICK_EMPTY if scenario == 'empty' else Screen.PICK)
            app = TkWizard(w)
            callback_errors = []
            original_report = app.root.report_callback_exception
            def record_callback_error(kind, error, trace):
                callback_errors.append({'type': kind.__name__, 'message': str(error)})
                original_report(kind, error, trace)
            app.root.report_callback_exception = record_callback_error
            try:
                if app._after_id is not None:
                    app.root.after_cancel(app._after_id)
                    app._after_id = None
                app.root.geometry('800x600+0+0')
                app.root.update()
                app.root.focus_force()
                app._draw()
                app.root.update()
                reader = next(widget for widget in descendants(app.root)
                              if isinstance(widget, tk.Text) and getattr(widget, '_beamo_inventory', False))
                # Its nearest enclosing canvas owns the inventory section.
                parent = reader.master
                while parent is not None and not isinstance(parent, tk.Canvas):
                    parent = parent.master
                assert parent is not None
                reader.focus_set()
                app.root.update()
                focus_top = reader.winfo_rooty() - parent.winfo_rooty()
                focus_visible = 0 <= focus_top and focus_top + reader.winfo_height() <= parent.winfo_height()
                reader.yview_moveto(0.3)
                bounds = parent.bbox('all')
                assert bounds
                parent.yview_moveto((parent.canvasy(0)+focus_top - max(0, (parent.winfo_height()-reader.winfo_height())/2))/max(1,bounds[3]))
                app.root.update()
                x = reader.winfo_rootx() + min(20, reader.winfo_width()//2)
                y = reader.winfo_rooty() + min(12, reader.winfo_height()//2)
                hit = app.root.winfo_containing(x, y)
                assert hit is reader, {'scenario': scenario, 'point': (x,y), 'hit': str(hit), 'reader': str(reader)}
                own_before, parent_before = reader.yview(), parent.yview()
                state = (w.screen, w.owner_ok, w.selected, w.confirm_input, w.method,
                         w._authorized_operation, w._wipe_request)
                if delta is None:
                    import ctypes
                    x11 = ctypes.CDLL('libX11.so.6')
                    xtest = ctypes.CDLL('libXtst.so.6')
                    x11.XOpenDisplay.restype = ctypes.c_void_p
                    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
                    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
                    x11.XFlush.argtypes = [ctypes.c_void_p]
                    xtest.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
                    xtest.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
                    display = x11.XOpenDisplay(None)
                    assert display
                    try:
                        xtest.XTestFakeMotionEvent(display, -1, x, y, 0)
                        button = 5 if direction > 0 else 4
                        xtest.XTestFakeButtonEvent(display, button, 1, 0)
                        xtest.XTestFakeButtonEvent(display, button, 0, 0)
                        x11.XFlush(display)
                        app.root.update()
                    finally:
                        x11.XCloseDisplay(display)
                else:
                    reader.event_generate(sequence, delta=delta)
                app.root.update()
                own_after, parent_after = reader.yview(), parent.yview()
                unchanged = state == (w.screen, w.owner_ok, w.selected, w.confirm_input, w.method,
                                      w._authorized_operation, w._wipe_request)
                rows.append(dict(scenario=scenario, sequence=sequence, delta=delta,
                                 own_before=own_before, own_after=own_after,
                                 parent_before=parent_before, parent_after=parent_after,
                                 reader_scrolled=direction*(own_after[0]-own_before[0]) > 0,
                                 parent_unchanged=parent_before == parent_after,
                                 focus_unchanged=app.root.focus_get() is reader,
                                 focus_initially_visible=focus_visible,
                                 focus_top=focus_top,
                                 reader_height=reader.winfo_height(),
                                 viewport_height=parent.winfo_height(),
                                 hit_point=[x,y], hit_is_reader=hit is reader,
                                 root_rect=[app.root.winfo_rootx(), app.root.winfo_rooty(), app.root.winfo_width(), app.root.winfo_height()],
                                 state_unchanged=unchanged,
                                 wheel_binding=reader.bind(sequence),
                                 screen=w.screen.name, engine_started=w.runner.started))
                if sequence == '<Button-5>':
                    pixels = Gdk.pixbuf_get_from_window(Gdk.get_default_root_window(), 0, 0, 800, 600)
                    assert pixels is not None
                    capture = out / f'empty-wheel-{scenario}.png'
                    pixels.savev(str(capture), 'png', [], [])
                    rows[-1]['capture'] = capture.name
            finally:
                pending = app.root.tk.call('after', 'info')
                for callback in pending:
                    app.root.tk.call('after', 'cancel', callback)
                app._teardown()
                if rows:
                    rows[-1]['callback_errors'] = list(callback_errors)

data = dict(source_sha256=hashlib.sha256(Path('src/beamo_wipe/ui/tk_wizard.py').read_bytes()).hexdigest(),
            cases=len(rows), effects=effects, rows=rows,
            behavior_failures=sum(not row['reader_scrolled'] or not row['parent_unchanged'] for row in rows))
(out / 'empty-wheel-probe.json').write_text(json.dumps(data, indent=2)+'\n')
print(json.dumps(data, indent=2))
assert not effects
assert all(row['state_unchanged'] and row['focus_unchanged'] and not row['engine_started'] for row in rows)
assert all(not row['callback_errors'] for row in rows)

