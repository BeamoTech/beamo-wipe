"""Owned private-display trace for asset retirement after native init failure."""
import gc,hashlib,json,os,sys,threading,traceback,weakref
from pathlib import Path
from beamo_wipe.ui import tk_wizard as ui
assert os.environ['BEAMO_ISOLATED_X11_TEST']=='1'
assert os.environ['DISPLAY'] not in (':1',':99','')
p=Path(ui.__file__).resolve();assert str(p)==os.environ['BEAMO_TK_PROBE_SOURCE']
assert hashlib.sha256(p.read_bytes()).hexdigest()==os.environ['BEAMO_TK_PROBE_SHA256']
owner=threading.current_thread();root=ui._new_owned_root(owner);root.withdraw()
retained=[];partial_refs=[];original_init=ui.tkfont.Font.__init__
class ControlledBeforeNativeFailure(RuntimeError): pass
def before_native(resource,*args,**kwargs):
    partial_refs.append(weakref.ref(resource))
    raise ControlledBeforeNativeFailure('controlled Font init before name assignment')
result={"source":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
try:
    ui.tkfont.Font.__init__=before_native
    try:
        ui._new_owned_native(root,ui.tkfont.Font,root=root,family='DejaVu Sans',size=-16)
    except ControlledBeforeNativeFailure as error:
        retained.append(error)
    finally:
        ui.tkfont.Font.__init__=original_init
    assert len(retained)==1 and partial_refs[0]() is not None
    font=ui._new_owned_native(root,ui.tkfont.Font,root=root,family='DejaVu Sans',size=-16)
    font_ref=weakref.ref(font);ui._pin_retired_assets((font,),owner);font=None
    try:
        ui._drain_retired_native()
        result.update(passed=font_ref() is None,partial_retained=partial_refs[0]() is not None)
    except BaseException as error:
        result.update(passed=False,error_type=type(error).__name__,traceback=traceback.format_exc())
    print(json.dumps(result),flush=True)
finally:
    retained.clear();gc.collect();ui._collect_retired_interpreters();root.destroy();root=None;gc.collect();ui._collect_retired_interpreters()
raise SystemExit(0 if result['passed'] else 1)
