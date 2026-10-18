import os,random
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe import lang
from beamo_wipe.models import MethodId,Screen
from beamo_wipe.wizard import Wizard
from beamo_wipe.nwipe_runner import DryRunRunner
class Clock:
    value=0.0
    def __call__(self):return self.value
count=0
for seed in range(180):
 rng=random.Random(7000+seed);w=make_demo_wizard()
 events=[lambda:w.skip_intro(),lambda:w.accept_what(),lambda:w.set_owner(True),lambda:w.set_owner(False),lambda:w.continue_owner(),lambda:w.select_disk(w.selectable[0].path) if w.selectable else None,lambda:w.continue_pick(),lambda:w.set_confirm_input('INVALID'),lambda:w.continue_confirm(),lambda:w.set_method(rng.choice(list(MethodId))),lambda:w.continue_method(),lambda:w.open_keyboard(),lambda:w.accept_keyboard(),lambda:w.open_advanced(),lambda:w.close_advanced(),lambda:w.open_limits(),lambda:w.close_limits(),lambda:w.open_report_help(),lambda:w.close_report_help(),lambda:w.open_refresh_confirm(),lambda:w.cancel_refresh_confirm(),lambda:w.back(),lambda:w.tick(),lambda:w.confirm_erase(),lambda:w.begin_erase(),lambda:w.request_stop(),lambda:w.keep_erasing(),lambda:w.set_language(rng.choice(('en','fr','de'))),lambda:w.finish_refresh(rng.choice((-1,0,1,999)),RuntimeError('fake stale result')),lambda:w.set_text_size(rng.choice(('standard','large','extra'))),lambda:w.set_report_share_redacted(True),lambda:w.set_report_wanted(True)]
 for step in range(300):
  events[rng.randrange(len(events))]()
  assert not w.runner.started,(seed,step,w.screen)
  assert w.wipe_result is None,(seed,step,w.screen)
  count+=1
print(count,'seeded public fake navigation events: no unconfirmed start/fabricated result')
cases=0
for code in ('en','fr','de'):
 for method in MethodId:
  for detour,returned in (('keyboard','accept_keyboard'),('keyboard','back'),('advanced','close_advanced'),('advanced','back'),('refresh_confirm','cancel_refresh_confirm'),('refresh_confirm','back')):
   clock=Clock();w=Wizard(make_demo_wizard().discovery,DryRunRunner(clock=clock),clock=clock,dry_run=True)
   w.set_language(code);w.skip_intro();w.set_owner(True);w.continue_owner();w.select_disk(w.selectable[0].path);w.continue_pick();w.set_confirm_input(w.confirm.token);w.continue_confirm();w.set_method(method);w.continue_method()
   assert w.screen==Screen.LAST_CHANCE
   for t in (0,0.1,4.999):
    clock.value=t;w.confirm_erase();assert not w.runner.started
   getattr(w,'open_'+detour)();clock.value=100;getattr(w,returned)();assert w.screen==Screen.LAST_CHANCE
   assert w.countdown_left==5 and not w.erase_enabled
   clock.value=104.999;w.confirm_erase();assert not w.runner.started
   clock.value=105;w.tick();assert w.erase_enabled and not w.runner.started
   cases+=1
print(cases,'language/method/detour combinations: full visible countdown required, reaching zero does not launch')
lang.set_language('en')
