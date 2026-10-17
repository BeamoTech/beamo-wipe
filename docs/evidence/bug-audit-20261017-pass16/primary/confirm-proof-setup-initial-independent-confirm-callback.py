"""A redraw must not delete a still-scheduled focus callback's Tcl command."""
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
from beamo_wipe.ui.tk_wizard import TkWizard
from test_accessible_sound_review_pass15_ui import _review

out = Path('/tmp/pass16-primary')
rows, effects = [], []

def forbidden(*args, **kwargs):
    effects.append('native application effect')
    raise AssertionError('Native application effect reached')

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

with ExitStack() as stack:
    for target in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
                   'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources',
                   'beamo_wipe.nwipe_runner.NwipeRunner.start',
                   'beamo_wipe.nwipe_runner.DryRunRunner.start', 'beamo_wipe.app._shutdown',
                   'beamo_wipe.sound._run', 'beamo_wipe.sound._popen'):
        stack.enter_context(patch(target, forbidden))
    stack.enter_context(patch('beamo_wipe.ui.tk_wizard.emit_serial_marker', lambda *_: None))
    for size in ('standard', 'large', 'extra'):
        wizard, clock = _review()
        wizard.set_text_size(size)
        app = TkWizard(wizard)
        errors = []
        app.root.createcommand('pass16_primary_bgerror', lambda message: errors.append(str(message)))
        app.root.tk.eval('proc bgerror {message} {pass16_primary_bgerror $message}')
        callback_errors = []
        app.root.report_callback_exception = lambda kind, error, _trace: callback_errors.append([kind.__name__, str(error)])
        try:
            entry = next(widget for widget in descendants(app.root) if isinstance(widget, tk.Entry))
            before = (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
                      wizard.method, wizard._authorized_operation, wizard._wipe_request)
            pending = []
            for identifier in app.root.tk.call('after', 'info'):
                script, kind = app.root.tk.call('after', 'info', identifier)
                command = app.root.tk.splitlist(script)[0]
                if command in (entry._tclCommands or ()):
                    pending.append(dict(id=identifier, command=command, kind=kind))
            assert pending, 'The original Entry-owned deferred focus callback must exist'
            app._draw()
            deleted = [row for row in pending if not app.root.tk.call('info', 'commands', row['command'])]
            until = time.monotonic() + .12
            while time.monotonic() < until:
                app.root.update()
                time.sleep(.002)
            after = (wizard.screen, wizard.owner_ok, wizard.selected, wizard.confirm_input,
                     wizard.method, wizard._authorized_operation, wizard._wipe_request)
            assert before == after and not wizard.runner.started
            rows.append(dict(size=size, old_entry_destroyed=not bool(entry.winfo_exists()),
                             scheduled_entry_commands=pending, deleted_commands=deleted,
                             tcl_errors=list(errors), callback_errors=callback_errors,
                             state_unchanged=True, engine_started=False))
        finally:
            for identifier in app.root.tk.call('after', 'info'):
                app.root.tk.call('after', 'cancel', identifier)
            app._teardown()
summary = dict(rows=rows, effects=effects,
               source_sha256=hashlib.sha256(Path('src/beamo_wipe/ui/tk_wizard.py').read_bytes()).hexdigest())
(out / 'independent-confirm-callback.json').write_text(json.dumps(summary, indent=2) + '\n')
assert not effects and all(row['deleted_commands'] and row['tcl_errors'] and not row['callback_errors'] for row in rows)
print('Three original-source redraws delete scheduled Tcl commands; all produce Tcl bgerror, state unchanged, no effects.')
