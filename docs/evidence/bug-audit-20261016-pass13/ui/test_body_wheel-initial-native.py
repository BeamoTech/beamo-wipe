import os
import ctypes
import json
import sys
sys.path.insert(0, os.getcwd() + '/tests')
import tkinter as tk
import pytest
from test_main_focus import fake_effects
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui.tk_wizard import TkWizard

@pytest.mark.parametrize('sequence', ['<Button-5>', '<MouseWheel>', 'native-wheel'])
@pytest.mark.parametrize('target_kind', ['label', 'canvas'])
def test_body_scroll_over_visible_prose(sequence, target_kind):
    wizard = make_demo_wizard()
    wizard.skip_intro()
    app = TkWizard(wizard)
    app.root.geometry('800x600+0+0')
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    try:
        app.root.update()
        canvas = app._body_canvas
        assert canvas is not None
        assert canvas.yview()[1] < 1
        labels = [w for w in descendants(app._body_inner) if isinstance(w,tk.Label) and w.winfo_ismapped() and w.winfo_rooty() >= canvas.winfo_rooty() and w.winfo_rooty() + 12 < canvas.winfo_rooty()+canvas.winfo_height()]
        assert labels
        target = labels[0] if target_kind == 'label' else canvas
        before = canvas.yview()
        if sequence == 'native-wheel':
            x11 = ctypes.CDLL('libX11.so.6')
            xtst = ctypes.CDLL('libXtst.so.6')
            x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            x11.XOpenDisplay.restype = ctypes.c_void_p
            x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
            x11.XSync.argtypes = [ctypes.c_void_p,ctypes.c_int]
            xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
            xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
            d = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
            assert d
            try:
                if target_kind == 'canvas':
                    # The narrow scrollbar-free canvas gutter is uncovered.
                    point = (canvas.winfo_rootx()+canvas.winfo_width()-1,canvas.winfo_rooty()+10)
                else:
                    point = (target.winfo_rootx()+10,target.winfo_rooty()+10)
                xtst.XTestFakeMotionEvent(d,-1,*point,0)
                x11.XSync(d,False)
                actual = app.root.winfo_containing(*point)
                assert actual is target, (str(actual),str(target),point)
                assert xtst.XTestFakeButtonEvent(d,5,1,0)
                assert xtst.XTestFakeButtonEvent(d,5,0,0)
                x11.XSync(d,False)
            finally:
                x11.XCloseDisplay(d)
        else:
            target.event_generate(sequence, **({'delta': -120} if sequence == '<MouseWheel>' else {}))
        app.root.update()
        after = canvas.yview()
        print(json.dumps({'sequence':sequence,'target_kind':target_kind,'target':str(target),'before':before,'after':after}))
        assert after[0] > before[0], {'target':str(target),'text':target.cget('text') if target_kind == 'label' else '', 'sequence':sequence,'before':before,'after':after}
    finally:
        app._teardown()
