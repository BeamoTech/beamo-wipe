import os,tempfile,threading
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from pathlib import Path
from unittest.mock import patch
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
for iteration in range(40):
 with tempfile.TemporaryDirectory(prefix='beamo-pass7-fake-session-') as td,patch('beamo_wipe.safety.default_log_dir',lambda:Path(td)):
  w=make_demo_wizard();w.runner=DryRunRunner(duration_s=600)
  w.skip_intro();w.set_owner(True);w.continue_owner();w.select_disk(w.selectable[0].path);w.continue_pick();w.set_confirm_input(w.confirm.token);w.continue_confirm();w.continue_method();w._erase_until=0
  barrier=threading.Barrier(5);claims=[]
  def start():
   barrier.wait();claims.append(w.begin_erase())
  threads=[threading.Thread(target=start) for _ in range(4)]
  for t in threads:t.start()
  barrier.wait()
  for t in threads:t.join(5);assert not t.is_alive()
  if w._operation_thread:w._operation_thread.join(5)
  assert sum(claims)==1 and w.screen==Screen.WORKING and w.runner.started
  w.shutdown();assert not w.wants_shutdown
  w.request_stop();assert w.stop_confirmation is not None
  w.keep_erasing();assert w.screen==Screen.WORKING and w.stop_confirmation is None
  assert w.begin_cancel()
  if w._operation_thread:w._operation_thread.join(5);assert not w._operation_thread.is_alive()
  assert w.screen==Screen.DONE and not w.wipe_result.ok and w.wipe_result.summary=='interrupted'
  assert not w.begin_erase() and not w.begin_cancel()
  w.tick();assert w.screen==Screen.DONE
print('40 fake sessions: 160 simultaneous start callers yield exactly40 starts; running shutdown blocked; stop dialog cancel, explicit async stop and terminal duplicate/retry actions pass')
