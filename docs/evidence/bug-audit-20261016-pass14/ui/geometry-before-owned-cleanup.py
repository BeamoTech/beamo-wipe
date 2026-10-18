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

OUT = Path('/tmp/pass14-ui')
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
    for surface in ('gtk', 'tk'):
        gtk = surface == 'gtk'
        for language in ('en', 'fr', 'de'):
            for text_size in ('standard', 'large', 'extra'):
                for target in ('SPLASH', 'KEYBOARD', 'OWNER', 'PICK', 'CONFIRM', 'METHOD',
                               'LAST_CHANCE', 'LIMITS', 'ADVANCED', 'REPORT_HELP', 'DISK_HELP',
                               'PICK_BLOCKED', 'PICK_EMPTY', 'REFRESH_CONFIRM', 'DIAGNOSTIC'):
                    w = make(target, language, text_size)
                    before = state(w)
                    app = AccessibleWizard(w) if gtk else TkWizard(w)
                    row = dict(surface=surface, language=language, text_size=text_size, screen=target)
                    try:
                        if not gtk:
                            app.root.geometry('800x600+0+0')
                            stable(app, False)
                            app.root.focus_force()
                            app._draw()
                        width, height = stable(app, gtk)
                        row['window'] = [width, height]
                        controls = []
                        host = app.footer if gtk else app._footer
                        for button in descendants(host, gtk):
                            if gtk:
                                if not isinstance(button, Gtk.Button):
                                    continue
                                mapped = button.get_mapped()
                                enabled = button.get_sensitive()
                                pos = button.translate_coordinates(app.window, 0, 0)
                                allocation = button.get_allocation()
                                rect = [*pos, allocation.width, allocation.height]
                                label = button.get_label()
                            else:
                                if not isinstance(button, _Button):
                                    continue
                                mapped = button.winfo_ismapped()
                                enabled = button._enabled
                                rect = [button.winfo_rootx()-app.root.winfo_rootx(),
                                        button.winfo_rooty()-app.root.winfo_rooty(),
                                        button.winfo_width(), button.winfo_height()]
                                label = button.itemcget(button._label, 'text')
                            x, y, cw, ch = rect
                            controls.append(dict(label=label, mapped=bool(mapped), enabled=bool(enabled),
                                rect=rect, inside=bool(mapped and x >= 0 and y >= 0 and x+cw <= width and y+ch <= height)))
                        row['controls'] = controls
                        focus = app.window.get_focus() if gtk else app.root.focus_get()
                        row['focus'] = bool(focus)
                        row['focus_visible'] = False
                        if focus is not None:
                            if gtk:
                                position = focus.translate_coordinates(app.window, 0, 0)
                                allocation = focus.get_allocation()
                                focused_rect = [*position, allocation.width, allocation.height]
                            else:
                                focused_rect = [focus.winfo_rootx()-app.root.winfo_rootx(),
                                                focus.winfo_rooty()-app.root.winfo_rooty(),
                                                focus.winfo_width(), focus.winfo_height()]
                            row['focus_rect'] = focused_rect
                            fx, fy, fw, fh = focused_rect
                            left, top, right, bottom = max(0,fx), max(0,fy), min(width,fx+fw), min(height,fy+fh)
                            node = focus.get_parent() if gtk else focus.master
                            clips = []
                            while node is not None:
                                if gtk and isinstance(node, (Gtk.ScrolledWindow, Gtk.Viewport)):
                                    position = node.translate_coordinates(app.window, 0, 0)
                                    allocation = node.get_allocation()
                                    clip = [*position, allocation.width, allocation.height]
                                elif not gtk and node.winfo_class() == 'Canvas':
                                    clip = [node.winfo_rootx()-app.root.winfo_rootx(),
                                            node.winfo_rooty()-app.root.winfo_rooty(),
                                            node.winfo_width(), node.winfo_height()]
                                else:
                                    clip = None
                                if clip is not None:
                                    cx,cy,cw,ch = clip
                                    clips.append(clip)
                                    left, top, right, bottom = max(left,cx), max(top,cy), min(right,cx+cw), min(bottom,cy+ch)
                                node = node.get_parent() if gtk else node.master
                            row['focus_clips'] = clips
                            row['focus_visible'] = right > left and bottom > top
                            row['focus_fully_visible'] = left <= fx and top <= fy and right >= fx+fw and bottom >= fy+fh
                        row['state_unchanged'] = state(w) == before
                        row['erase_enabled'] = w.erase_enabled
                        row['display_inside'] = width <= 800 and height <= 600
                        row['ok'] = row['display_inside'] and row['state_unchanged'] and row['focus'] and row['focus_visible'] and all(c['inside'] for c in controls)
                        if not row['ok'] or (surface == 'tk' and language == 'en' and ((target == 'OWNER' and text_size == 'standard') or (target == 'KEYBOARD' and text_size == 'extra') or (target == 'CONFIRM' and text_size == 'large'))):
                            capture = OUT / f'fixed-geometry-{surface}-{language}-{text_size}-{target}.png'
                            pixels = Gdk.pixbuf_get_from_window(Gdk.get_default_root_window(), 0, 0, 800, 600)
                            assert pixels is not None
                            pixels.savev(str(capture), 'png', [], [])
                            row['capture'] = capture.name
                    finally:
                        app.close() if gtk else app._teardown()
                        if gtk:
                            drain()
                        rows.append(row)
                        (OUT / 'geometry-matrix.json').write_text(json.dumps(dict(hashes=hashes, rows=rows,
                            forbidden_calls=forbidden_calls, serial_markers=serial_markers, power_reads=len(power_reads)), indent=2), encoding='utf-8')
    summary = dict(cases=len(rows), passed=sum(row.get('ok', False) for row in rows),
                   failed=[{k: row[k] for k in ('surface','language','text_size','screen','window','focus','focus_visible','display_inside')}
                           for row in rows if not row.get('ok')], forbidden_calls=forbidden_calls,
                   hashes=hashes, serial_markers=serial_markers, fake_power_reads=len(power_reads),
                   final_hashes={name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in FILES})
    (OUT / 'geometry-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
finally:
    for item in reversed(patches):
        item.stop()
