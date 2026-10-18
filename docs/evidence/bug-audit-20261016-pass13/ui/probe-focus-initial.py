import ctypes
import os
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui.tk_wizard import TkWizard
x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6')
x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p
x.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
x.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int]
xt.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
d=x.XOpenDisplay(os.environ['DISPLAY'].encode());x.XSetInputFocus(d,1,0,0);xt.XTestFakeMotionEvent(d,-1,1599,999,0);x.XSync(d,0)
a=TkWizard(make_demo_wizard());r=a.root

def state(label):
 print(label,'mapped',r.winfo_ismapped(),'focus',str(r.focus_get()),'last',str(r.focus_lastfor()),'primary',str(a._primary),flush=True)
state('constructor')
r.bind('<Map>',lambda e: state('map:'+str(e.widget)) if e.widget is r else None,add='+')
r.after_idle(lambda: (state('firstidle'),r.after_idle(lambda:state('nestedidle'))))
r.after(120,lambda:state('120ms'))
r.after(220,a._teardown)
a.run()
