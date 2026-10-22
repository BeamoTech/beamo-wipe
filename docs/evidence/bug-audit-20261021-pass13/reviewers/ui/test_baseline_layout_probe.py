"""Compare existing method geometry against exact baseline accessible bytes."""
import importlib.util
from pathlib import Path
import sys
import time
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen

def test_exact_baseline_method_layout():
    path=Path(__file__).with_name('baseline_accessible_wizard.py')
    spec=importlib.util.spec_from_file_location('beamo_wipe.ui.pass13_baseline_accessible',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ui=module
    wizard=make_demo_wizard()
    wizard.selected=wizard.selectable[0]
    wizard.screen=Screen.METHOD
    app=ui.AccessibleWizard(wizard)
    try:
        app.window.resize(800,600)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            while ui.Gtk.events_pending():
                ui.Gtk.main_iteration_do(False)
            if tuple(app.window.get_size())==(800,600):
                break
            time.sleep(.01)
        footer=app.footer.translate_coordinates(app.window,0,0)[1]
        choices=[child for child in app.body.get_children() if isinstance(child,ui.Gtk.RadioButton)]
        bounds=[(choice.translate_coordinates(app.window,0,0)[1],choice.get_allocated_height()) for choice in choices]
        assert all(y+height<=footer for y,height in bounds), (bounds,footer)
    finally:
        app.close()
