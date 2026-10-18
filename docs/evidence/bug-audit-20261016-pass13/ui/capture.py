import ctypes
import json
import hashlib
import os
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from PIL import ImageGrab
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui.tk_wizard import TkWizard
import tkinter as tk


def forbidden(*args, **kwargs):
    raise AssertionError('Native application operation reached')

with ExitStack() as patches:
    for target in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk', 'beamo_wipe.discover.read_cmdline', 'beamo_wipe.discover.read_mount_sources', 'beamo_wipe.nwipe_runner.NwipeRunner.start', 'beamo_wipe.nwipe_runner.DryRunRunner.start', 'beamo_wipe.app._shutdown', 'beamo_wipe.sound._run', 'beamo_wipe.sound._popen'):
        patches.enter_context(patch(target, forbidden))
    x11 = ctypes.CDLL('libX11.so.6')
    xtst = ctypes.CDLL('libXtst.so.6')
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    d = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert d
    x11.XSetInputFocus(d,1,0,0)
    xtst.XTestFakeMotionEvent(d,-1,1599,999,0)
    x11.XSync(d,False)
    wizard = make_demo_wizard()
    wizard.skip_intro()
    app = TkWizard(wizard)
    sw,sh = app.root.winfo_screenwidth(),app.root.winfo_screenheight()
    app.root.geometry(f'800x600+{(sw-800)//2}+{(sh-600)//2}')
    receipts = {'display':os.environ['DISPLAY'],'screen':[sw,sh], 'requested_dpi':72,'tk_pixels_per_inch':app.root.winfo_fpixels('1i'),'source_sha256':hashlib.sha256(Path('/root/dev/Beamo Wipe/src/beamo_wipe/ui/tk_wizard.py').read_bytes()).hexdigest()}
    errors=[]
    def descendants(w):
        for c in w.winfo_children():
            yield c
            yield from descendants(c)
    def scroll():
        try:
            c=app._body_canvas
            receipts['rect']=[app.root.winfo_rootx(),app.root.winfo_rooty(),app.root.winfo_width(),app.root.winfo_height()]
            receipts['focus']=str(app.root.focus_get())
            labels=[l for l in descendants(app._body_inner) if isinstance(l,tk.Label) and l.winfo_ismapped() and l.winfo_rooty()>=c.winfo_rooty() and l.winfo_rooty()+12<c.winfo_rooty()+c.winfo_height()]
            label=labels[0]
            point=(label.winfo_rootx()+10,label.winfo_rooty()+10)
            assert app.root.winfo_containing(*point) is label
            receipts['native_wheel_target']={'widget':str(label),'text':label.cget('text'),'point':point}
            receipts['before']=list(c.yview())
            assert xtst.XTestFakeMotionEvent(d,-1,*point,0)
            x11.XSync(d,False)
            assert xtst.XTestFakeButtonEvent(d,5,True,0)
            assert xtst.XTestFakeButtonEvent(d,5,False,0)
            x11.XSync(d,False)
        except BaseException as e:
            errors.append(repr(e))
    def capture():
        try:
            receipts['after']=list(app._body_canvas.yview())
            assert receipts['after'][0]>receipts['before'][0]
            receipts['consent']={'owner_ok':wizard.owner_ok,'confirm_input':wizard.confirm_input,'screen':wizard.screen.name,'wipe_request':wizard._wipe_request}
            path=Path(f'/tmp/pass13-ui/tk-body-native-{sw}x{sh}.png')
            # ImageGrab reads the X server directly; no pixels are altered.
            image=ImageGrab.grab(xdisplay=os.environ['DISPLAY'])
            assert image.size==(sw,sh)
            image.save(path)
            receipts['image']=str(path)
            receipts['image_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        except BaseException as e:
            errors.append(repr(e))
        finally:
            app._teardown()
    app.root.after(150,scroll)
    app.root.after(300,capture)
    try:
        assert app.run()==0
    finally:
        app._teardown()
        xtst.XTestFakeButtonEvent(d,5,False,0)
        x11.XSync(d,False)
        x11.XCloseDisplay(d)
    receipts['errors']=errors
    receipts['owned_teardown']=True
    Path(f'/tmp/pass13-ui/tk-body-native-{sw}x{sh}.json').write_text(json.dumps(receipts,indent=2)+'\n')
    assert not errors,receipts
    print(json.dumps(receipts))
