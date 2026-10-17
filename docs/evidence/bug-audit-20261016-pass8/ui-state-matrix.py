import concurrent.futures,copy,json,os,random,threading
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import MethodId,Screen,DiscoveryResult
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard
from beamo_wipe import lang
class Clock:
 def __init__(self):self.t=0.
 def __call__(self):return self.t

def authorized(code,method):
 clock=Clock();w=Wizard(make_demo_wizard().discovery,DryRunRunner(clock=clock),clock=clock,dry_run=True)
 w.set_language(code);w.skip_intro();w.set_owner(True);w.continue_owner();w.select_disk(w.selectable[0].path);w.continue_pick();w.set_confirm_input(w.confirm.token);w.continue_confirm();w.set_method(method);w.continue_method()
 assert w.screen==Screen.LAST_CHANCE
 return w,clock
counts={}
checks=0
for code in ('en','fr','de'):
 for method in MethodId:
  for depth in range(1,7):
   w,c=authorized(code,method)
   for i in range(depth):assert w.begin_review_overlay()
   c.t=100
   for i in range(depth):
    assert not w.erase_enabled
    w.confirm_erase();assert not w.runner.started
    w.end_review_overlay()
   assert w.countdown_left==5
   for value in (100,100.001,104,104.999999):
    c.t=value;w.tick();w.confirm_erase();assert not w.runner.started;assert w.countdown_display>=1
   c.t=105;w.tick();assert w.erase_enabled;assert w.countdown_display==0;assert not w.runner.started
   # Underflow releases cannot bypass/restart a completed review.
   w.end_review_overlay();assert w.erase_enabled
   checks+=1
counts['nested_overlay_language_method']=checks
checks=0
# Duplicate/stale concurrent scan completions and malformed result retries.
for n in range(40):
 w=make_demo_wizard();w.skip_intro();original=copy.deepcopy(w.discovery)
 seq=w.begin_refresh();assert seq is not None
 assert w.begin_refresh() is None
 barrier=threading.Barrier(9)
 def complete(_):barrier.wait();return w.finish_refresh(seq,original)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
  futures=[ex.submit(complete,i) for i in range(8)];barrier.wait();values=[f.result() for f in futures]
 assert sum(values)==1 and w.screen==Screen.OWNER
 for malformed in (None,{},[],ValueError('fake failure'),KeyboardInterrupt()):
  nxt=w.begin_refresh();assert nxt>seq;assert not w.finish_refresh(seq,original)
  assert w.finish_refresh(nxt,malformed);assert w.screen==Screen.PICK_BLOCKED
  assert not w.discovery.boot_identified and not w.selectable and w.selected is None
  assert not w.runner.started and not w.wants_shutdown
 seq=w.begin_refresh();assert w.finish_refresh(seq,original);assert w.screen==Screen.OWNER
 assert not w.owner_ok and not w.confirm_input and w._authorized_operation is None
 checks+=1
counts['concurrent_refresh_and_malformed_retry_sessions']=checks
checks=0
for seed in range(160):
 rng=random.Random(810000+seed);w=make_demo_wizard()
 actions=[w.skip_intro,w.accept_what,lambda:w.set_owner(True),lambda:w.set_owner(False),w.continue_owner,lambda:w.select_disk(w.selectable[0].path) if w.selectable else None,w.continue_pick,lambda:w.set_confirm_input('UNAUTHORIZED'),w.continue_confirm,lambda:w.set_method(rng.choice(list(MethodId))),w.continue_method,w.back,w.open_keyboard,w.accept_keyboard,w.open_limits,w.close_limits,w.open_advanced,w.close_advanced,w.open_refresh_confirm,w.cancel_refresh_confirm,w.open_report_help,w.close_report_help,w.tick,w.confirm_erase,w.begin_erase,w.request_stop,w.keep_erasing,lambda:w.set_language(rng.choice(('en','fr','de'))),w.cycle_text_size,lambda:w.set_report_share_redacted(True),lambda:w.set_report_wanted(True),lambda:w.finish_refresh(999,DiscoveryResult())]
 for _ in range(400):
  rng.choice(actions)();checks+=1
  assert not w.runner.started and w.wipe_result is None and not w.wants_shutdown
counts['seeded_navigation_events']=checks
lang.set_language('en')
print(json.dumps(counts,indent=2))
