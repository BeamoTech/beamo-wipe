"""Inspect the actual fake preview and invoke its normal close protocol."""
import json
import os
from pathlib import Path
import subprocess
import time
import tkinter as tk

from PIL import ImageGrab

root = Path(__file__).resolve().parent
assert os.environ.get('BEAMO_ISOLATED_X11_TEST') == '1'
assert os.environ['DISPLAY'] not in {':1', ':99', ':100', ':200'}
controller = tk.Tk(className='Pass13AuditController')
controller.withdraw()
receipt = {'command': ['./preview'], 'fake_disks_only': True,
           'display': os.environ['DISPLAY'], 'dpi': 72}
with (root / 'actual-preview.log').open('w') as log:
    child = subprocess.Popen(['./preview'], stdout=log, stderr=subprocess.STDOUT)
    try:
        selected = None
        for attempt in range(32):
            assert child.poll() is None, 'preview exited before inspection'
            controller.update()
            for app in controller.tk.splitlist(controller.tk.call('winfo', 'interps')):
                if app == controller.tk.call('tk', 'appname'):
                    continue
                title = controller.tk.call('send', app, 'wm title .')
                if 'Beamo Wipe' in title:
                    selected = app
                    receipt['window_title'] = title
                    break
            if selected is not None:
                break
            time.sleep(0.25)
        assert selected is not None, 'owned preview window not found'
        # A title exists before the first welcome body paints under load.
        # Observe actual owner-facing text before taking the visual receipt.
        inspect_text = r"""apply {{} {
            set pending [list .]
            set texts {}
            while {[llength $pending]} {
                set widget [lindex $pending 0]
                set pending [lrange $pending 1 end]
                if {![winfo exists $widget]} {continue}
                set pending [concat $pending [winfo children $widget]]
                if {![catch {$widget cget -text} label]} {lappend texts $label}
                if {[winfo class $widget] eq "Canvas"} {
                    foreach item [$widget find all] {
                        if {[$widget type $item] eq "text"} {lappend texts [$widget itemcget $item -text]}
                    }
                }
            }
            return $texts
        }}"""
        for attempt in range(60):
            controller.tk.call('send', selected, 'update idletasks')
            texts = str(controller.tk.call('send', selected, inspect_text))
            if 'Continue' in texts and 'Beamo Wipe' in texts:
                break
            time.sleep(0.1)
        else:
            raise AssertionError('Owned preview welcome content did not become ready')
        time.sleep(0.2)
        receipt['welcome_content_observed_before_capture'] = True
        ImageGrab.grab().save(root / 'actual-preview-72dpi.png')
        protocol = controller.tk.call('send', selected, 'wm protocol . WM_DELETE_WINDOW')
        assert protocol
        try:
            controller.tk.call('send', selected, protocol)
        except tk.TclError:
            # Closing the remote interpreter can retire the reply channel.
            pass
        child.wait(timeout=10)
        assert child.returncode == 0, child.returncode
        receipt.update(normal_close_acceptance=True, returncode=child.returncode,
                       teardown='Invoked actual registered WM_DELETE_WINDOW callback')
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        controller.destroy()
(root / 'actual-preview.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
