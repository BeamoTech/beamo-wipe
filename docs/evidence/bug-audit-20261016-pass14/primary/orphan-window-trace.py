"""Prove the observed Tk multi-root event-loop lifetime using owned windows."""
import json,time,tkinter as tk
from pathlib import Path
first=tk.Tk();first.geometry('100x100+0+0')
second=tk.Tk();second.geometry('100x100+200+0')
trace=[];started=time.monotonic()
def close_second():
 second.destroy();trace.append({'event':'startup_root_destroyed','elapsed':time.monotonic()-started})
def inspect():
 trace.append({'event':'mainloop_still_running_with_orphan','first_exists':bool(first.winfo_exists()),'elapsed':time.monotonic()-started})
def finish():
 trace.append({'event':'orphan_destroyed','elapsed':time.monotonic()-started});first.destroy()
second.after(100,close_second)
first.after(220,inspect)
first.after(350,finish)
second.mainloop()
trace.append({'event':'mainloop_returned','elapsed':time.monotonic()-started})
assert [r['event'] for r in trace]==['startup_root_destroyed','mainloop_still_running_with_orphan','orphan_destroyed','mainloop_returned']
Path('/tmp/pass14-primary/orphan-window-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
print(json.dumps(trace,indent=2))
