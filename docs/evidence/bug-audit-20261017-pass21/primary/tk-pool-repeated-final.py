"""Ten owned fake-wizard sessions with live assets released by a later worker."""
import gc,json,sys,threading,weakref
import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.ui import tk_wizard as ui
from test_tk_native_constructor_pass20 import _admit,_guard
provenance=_admit();owner=threading.get_ident();refs=[];finalizers=[];gc_events=[];depth=0;maximum=0;unraisables=[]
assert sum(callback is ui._drain_retired_native_after_gc for callback in gc.callbacks)==1

def observe_gc(phase,info):
    global depth,maximum
    depth+=1 if phase=='start' else -1
    maximum=max(maximum,depth);gc_events.append((phase,threading.get_ident()))

with pytest.MonkeyPatch.context() as patch:
    effects=_guard(patch)
    for kind,cls in [('font',ui.tkfont.Font),('variable',ui.tk.Variable),('image',ui.tk.PhotoImage)]:
        old_init,old_del=cls.__init__,cls.__del__
        def initialize(resource,*args,_initialize=old_init,_kind=kind,**kwargs):
            _initialize(resource,*args,**kwargs);refs.append((_kind,weakref.ref(resource)))
        def finalize(resource,_finalize=old_del,_kind=kind):
            row=dict(kind=_kind,thread=threading.get_ident(),returned=False);finalizers.append(row)
            result=_finalize(resource)
            row['returned']=True
            return result
        patch.setattr(cls,'__init__',initialize);patch.setattr(cls,'__del__',finalize)
    def observe_unraisable(argument):
        unraisables.append(dict(type=type(argument.exc_value).__name__,message=str(argument.exc_value)))
    patch.setattr(sys,'unraisablehook',observe_unraisable)
    gc.callbacks.append(observe_gc)
    try:
        for session in range(10):
            wizard=make_demo_wizard();wizard.skip_splash();app=ui.TkWizard(wizard);app.root.withdraw()
            app_ref,root_ref=weakref.ref(app),weakref.ref(app.root)
            external=[app.font_s,app._typing_var]
            app._typing_var.set('live owner control');assert wizard.typing_check=='live owner control'
            app._teardown()
            def worker_release():external.clear();gc.collect()
            worker=threading.Thread(target=worker_release,daemon=True,name='owned-repeated-release');worker.start();worker.join(2)
            assert not worker.is_alive()
            assert all(row['thread']==owner and row['returned'] for row in finalizers)
            app=None;gc.collect()
            assert app_ref() is None and root_ref() is None
            assert not any(ref() is not None for _,ref in refs)
            assert not ui._RETIRED_NATIVE_ASSETS and not ui._RETIRED_INTERPRETERS
        assert depth==0 and maximum==1
        assert not effects and not unraisables
        print(json.dumps(dict(provenance=provenance,sessions=10,resources=len(refs),finalizers=len(finalizers),all_owner_thread=True,all_returned=True,gc_events=len(gc_events),max_gc_depth=maximum,registered_callbacks=1,pools_empty=True,effects=effects,unraisables=unraisables)),flush=True)
    finally:gc.callbacks.remove(observe_gc)
