import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from beamo_wipe.ui import accessible_wizard as ui
from beamo_wipe.startup_stages import StartupRun

source = Path(ui.__file__).resolve()
ui._ensure_gtk_display = lambda: None
records = []
for mode in ('normal-control', 'runtime-error-control', 'keyboard-interrupt'):
    unrelated = ui.Gtk.Window(title='Unrelated audit control')
    unrelated.show_all()
    destroyed = []
    unrelated.connect('destroy', lambda *_: destroyed.append(True))
    before = set(ui.Gtk.Window.list_toplevels())
    original = KeyboardInterrupt('owned startup interruption') if mode == 'keyboard-interrupt' else RuntimeError('owned start failure')
    caught = None
    outcome = None
    def fail_start(_self):
        raise original
    try:
        if mode == 'normal-control':
            outcome = ui.run_accessible_startup(lambda _report: 'inert fake wizard')
        else:
            with patch.object(StartupRun, 'start', fail_start):
                outcome = ui.run_accessible_startup(lambda _report: 'inert fake wizard')
    except BaseException as error:
        caught = error
    owned = [window for window in ui.Gtk.Window.list_toplevels() if window not in before]
    records.append(dict(mode=mode, outcome=[outcome[0], type(outcome[1]).__name__] if outcome else None,
                        caught=type(caught).__name__ if caught else None,
                        preserved_error=caught is original, remaining_owned_windows=len(owned),
                        remaining_visible_windows=sum(window.get_visible() for window in owned),
                        unrelated_destroyed=bool(destroyed)))
    for window in owned:
        window.destroy()
    unrelated.destroy()
print(json.dumps(dict(source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), records=records), indent=2))
assert records[0]['remaining_owned_windows'] == records[1]['remaining_owned_windows'] == 0
assert records[0]['outcome'] == ['wizard', 'str']
assert records[1]['outcome'] == ['failed', 'RuntimeError']
assert records[2]['preserved_error']
assert all(not record['unrelated_destroyed'] for record in records)
assert records[2]['remaining_owned_windows'] == 0, 'interrupted startup retained its own window'
