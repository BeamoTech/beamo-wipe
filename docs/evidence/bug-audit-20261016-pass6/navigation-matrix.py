import os,random
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe import lang
from beamo_wipe.models import MethodId
count=0
for seed in range(100):
 rng=random.Random(seed)
 w=make_demo_wizard()
 events=[lambda:w.skip_intro(),lambda:w.accept_what(),lambda:w.set_owner(True),lambda:w.continue_owner(),lambda:w.select_disk(w.selectable[0].path) if w.selectable else None,lambda:w.continue_pick(),lambda:w.set_confirm_input('WRONG TOKEN'),lambda:w.continue_confirm(),lambda:w.set_method(rng.choice(list(MethodId))),lambda:w.continue_method(),lambda:w.open_keyboard(),lambda:w.accept_keyboard(),lambda:w.open_advanced(),lambda:w.close_advanced(),lambda:w.open_limits(),lambda:w.close_limits(),lambda:w.open_report_help(),lambda:w.close_report_help(),lambda:w.open_refresh_confirm(),lambda:w.cancel_refresh_confirm(),lambda:w.back(),lambda:w.tick(),lambda:w.confirm_erase(),lambda:w.begin_erase(),lambda:w.request_stop(),lambda:w.keep_erasing(),lambda:w.set_language(rng.choice(('en','fr','de'))),lambda:w.finish_refresh(rng.choice((-1,0,1,999)),RuntimeError('fake stale result'))]
 for step in range(200):
  events[rng.randrange(len(events))]()
  assert not w.runner.started,(seed,step,w.screen)
  assert w.wipe_result is None,(seed,step,w.screen)
  count+=1
lang.set_language('en')
print(f'{count} seeded fake UI transitions across 100 seeds: no unconfirmed start or fabricated result')
