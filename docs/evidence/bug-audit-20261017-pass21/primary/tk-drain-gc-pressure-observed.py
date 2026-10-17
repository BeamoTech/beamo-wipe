"""Bounded real-dict/native Font snapshot probe; fixture GC changes only."""
import gc,hashlib,json,os,sys,threading,traceback,weakref
from pathlib import Path
from beamo_wipe.ui import tk_wizard as ui
assert os.environ['BEAMO_ISOLATED_X11_TEST']=='1' and os.environ['DISPLAY'] not in (':1',':99','')
p=Path(ui.__file__).resolve();assert str(p)==os.environ['BEAMO_TK_PROBE_SOURCE'];assert hashlib.sha256(p.read_bytes()).hexdigest()==os.environ['BEAMO_TK_PROBE_SHA256']
original_threshold=gc.get_threshold();original_enabled=gc.isenabled();gc.disable()
root=ui._new_owned_root(threading.current_thread());root.withdraw();ui._pin_retired_interpreter(root,threading.current_thread())
events=[]
def observe(phase,info):
    frame=sys._getframe(1)
    while frame is not None and frame.f_code.co_filename!=str(p): frame=frame.f_back
    events.append(dict(phase=phase,thread=threading.get_ident(),function=frame.f_code.co_name if frame else None,line=frame.f_lineno if frame else None,instruction=frame.f_lasti if frame else None))
    del frame
gc.callbacks.append(observe)
row=dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),threshold_mode='current_generation0_count_plus_offset',runs=[],errors=[])
try:
    for attempt in range(12):
        gc.disable();before_events=len(events)
        fonts=[ui.tkfont.Font(root=root,family='DejaVu Sans',size=-14) for _ in range(128)]
        refs=[weakref.ref(font) for font in fonts]
        ui._pin_retired_assets(fonts,threading.current_thread());fonts=None
        primer=threading.Thread(target=gc.collect,daemon=True,name='owned-count-reset');primer.start();primer.join(2);assert not primer.is_alive()
        offset=(1,2,3,4,8,12,16,24,32,48,64,96)[attempt]
        threshold=gc.get_count()[0]+offset
        gc.set_threshold(threshold,1,1);gc.enable()
        try:
            ui._drain_retired_native()
        except BaseException as error:
            row['errors'].append(dict(attempt=attempt,type=type(error).__name__,traceback=traceback.format_exc()))
        finally:
            gc.disable()
        ui._collect_retired_interpreters()
        alive=sum(ref() is not None for ref in refs)
        row['runs'].append(dict(attempt=attempt,native_fonts=128,threshold=threshold,offset=offset,alive_after_owner_sweep=alive,gc_events=events[before_events:]))
        assert alive==0
        if row['errors']:break
finally:
    gc.disable();gc.callbacks.remove(observe);gc.set_threshold(*original_threshold);root.destroy();root=None;gc.collect();ui._collect_retired_interpreters()
    if original_enabled:gc.enable()
print(json.dumps(row),flush=True)
raise SystemExit(1 if row['errors'] else 0)
