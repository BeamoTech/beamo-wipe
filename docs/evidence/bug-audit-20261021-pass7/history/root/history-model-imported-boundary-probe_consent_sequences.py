"""Seeded public Wizard action model; fake acquisition and no native actions."""
from pathlib import Path
import collections,hashlib,json,random,sys,tempfile
sys.path.insert(0,str(Path(__file__).parent/'baseline-archive/src'))
from pytest import MonkeyPatch
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen,MethodId
from beamo_wipe.nwipe_runner import DryRunRunner,build_nwipe_argv
from beamo_wipe.wizard import Wizard
from beamo_wipe.safety import token_matches

root=Path(__file__).parent
stats=collections.Counter();screens=collections.Counter();effects=[];failures=[]
with MonkeyPatch.context()as patch:
 patch.setenv('BEAMO_WIPE_DRY_RUN','1');patch.delenv('BEAMO_WIPE_LIVE',raising=False)
 def forbidden(*_a,**_kw):effects.append(True);raise AssertionError('Native boundary forbidden')
 for name in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown','beamo_wipe.sound._run','beamo_wipe.sound._popen'):
  patch.setattr(name,forbidden)
 # These model the already-tested physical acquisition boundary without
 # inspecting even a developer-host /dev entry.
 patch.setattr('beamo_wipe.safety.assert_existing_is_block_device',lambda *_a,**_kw:None)
 patch.setattr('beamo_wipe.safety.assert_size_unchanged',lambda *_a,**_kw:None)
 patch.setattr('beamo_wipe.safety.assert_local_device_transport',lambda *_a,**_kw:None)
 patch.setattr('beamo_wipe.safety.block_rdev',lambda *_a,**_kw:None)
 def excluded(device,boot,**_kw):assert device!=boot
 patch.setattr('beamo_wipe.safety.assert_not_boot',excluded)
 for scenario in ('happy','blocked','empty'):
  for method in MethodId:
   for fail in (False,True):
    for seed in range(20):
     stats['sessions']+=1;rng=random.Random(702026+seed);clock=[0.0]
     with tempfile.TemporaryDirectory(prefix='beamo-pass7-consent-')as d:
      patch.setattr('beamo_wipe.safety.default_log_dir',lambda:Path(d))
      initial=discovery_for_scenario(scenario)
      runner=DryRunRunner(clock=lambda:clock[0],duration_s=1.0,fail=fail)
      w=Wizard(initial,runner,clock=lambda:clock[0],dry_run=True,rediscover=lambda:initial)
      w._apply_keyboard=lambda *_a:(True,'')
      original_start=runner.start;action=['initial'];trace=[]
      def start(request):
       assert action[0]=='erase','Start must follow separate explicit action'
       assert w.owner_ok is True and w.selected is not None and not w.selected.is_boot
       assert w.confirm is not None and token_matches(w.confirm_input,w.confirm)
       assert w._erase_until is not None and clock[0]>=w._erase_until and w._review_overlay_depth==0
       assert w._authorization_matches()
       assert request.device==w.selected.path and request.device!=request.boot_device
       argv=build_nwipe_argv(request)
       assert '--force'not in argv and argv.count('--autonuke')==1
       assert '--exclude='+request.boot_device in argv and argv[-1]==request.device
       stats['authorized_starts']+=1;original_start(request)
      runner.start=start
      for step in range(80):
       screens[w.screen.value]+=1
       if w.screen==Screen.DONE:stats['completed_sessions']+=1;break
       if w.wants_shutdown:stats['accepted_shutdown_intents']+=1;break
       if rng.random()<0.65:
        choice={Screen.SPLASH:'intro',Screen.KEYBOARD:'intro',Screen.OWNER:'owner',Screen.WHAT:'owner',Screen.PICK:'pick',Screen.CONFIRM:'token',Screen.METHOD:'method',Screen.LAST_CHANCE:'erase',Screen.WORKING:'tick',Screen.STOPPING:'tick',Screen.REFRESH_CONFIRM:'refresh-confirm',Screen.ADVANCED:'back',Screen.LIMITS:'back'}.get(w.screen,'refresh')
       else:choice=rng.choice(['erase','back','advanced','close-advanced','owner-false','method','bad-token','refresh','refresh-confirm','overlay','overlay-end','tick','shutdown'])
       action[0]=choice;trace.append((w.screen.value,choice,clock[0]));stats['actions']+=1
       if choice=='intro':w.skip_intro()
       elif choice=='owner':w.set_owner(True);w.continue_owner()
       elif choice=='owner-false':w.set_owner(False);w.continue_owner()
       elif choice=='pick':
        if w.selectable:w.select_disk(w.selectable[0].path)
        w.continue_pick()
       elif choice=='token':
        if w.confirm:w.set_confirm_input(w.confirm.token)
        w.continue_confirm()
       elif choice=='bad-token':w.set_confirm_input('WRONG');w.continue_confirm()
       elif choice=='method':w.set_method(method);w.continue_method()
       elif choice=='erase':w.confirm_erase()
       elif choice=='back':w.back()
       elif choice=='advanced':w.open_advanced()
       elif choice=='close-advanced':w.close_advanced()
       elif choice=='refresh':w.open_refresh_confirm()
       elif choice=='refresh-confirm':w.confirm_refresh()
       elif choice=='overlay':w.begin_review_overlay()
       elif choice=='overlay-end':w.end_review_overlay()
       elif choice=='shutdown':w.shutdown()
       elif choice=='tick':w.tick()
       clock[0]+=rng.choice([0.0,0.1,0.5,1.0,5.0,6.0])
      if scenario!='happy':assert not runner.started
assert not effects and not failures
assert stats['authorized_starts']>0 and stats['completed_sessions']>0
sources={str(p.relative_to(root/'baseline-archive')):hashlib.sha256(p.read_bytes()).hexdigest()for p in (root/'baseline-archive/src/beamo_wipe/wizard.py',root/'baseline-archive/src/beamo_wipe/safety.py',root/'baseline-archive/src/beamo_wipe/nwipe_runner.py')}
result={'seed_base':702026,'base_commit':'938fe60347c78f2a745d5d5b04e30dfa013da809','counts':dict(stats),'screens':dict(screens),'scenarios':['happy','blocked','empty'],'methods':[m.value for m in MethodId],'runner_fail_modes':[False,True],'native_callbacks':len(effects),'failures':failures,'source_sha256':sources,'scope':'Public authorization transitions with fake physical acquisition; no claim of native device acceptance'}
(root/'consent-sequences.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
