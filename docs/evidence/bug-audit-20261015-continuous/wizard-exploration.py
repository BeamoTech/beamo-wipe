import random, tempfile
from pathlib import Path
from unittest.mock import patch
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard, make_demo_wizard

rng=random.Random(20261015)
starts=actions=0
with tempfile.TemporaryDirectory(prefix='beamo-pass4-wizard-') as tmp, patch('beamo_wipe.safety.default_log_dir',lambda:Path(tmp)):
    for session in range(100):
        now=[0.0]
        base=make_demo_wizard()
        runner=DryRunRunner(duration_s=1,clock=lambda:now[0])
        w=Wizard(base.discovery,runner,clock=lambda:now[0],dry_run=True)
        w.preview=True
        w._rediscover=lambda:base.discovery
        source=[None]
        original=runner.start
        def guarded_start(request):
            global starts
            assert source[0]=='erase'
            assert w.owner_ok and w.token_ok
            assert w._authorization_matches()
            assert w.countdown_left==0
            assert request.device!=request.boot_device
            assert request.device in {d.path for d in w.selectable}
            starts+=1
            return original(request)
        runner.start=guarded_start
        if session%10==0:
            source[0]='erase'
            w.skip_intro(); w.set_owner(True); w.continue_owner()
            w.select_disk(w.selectable[0].path); w.continue_pick()
            w.set_confirm_input(w.confirm.token); w.continue_confirm(); w.continue_method()
            now[0]+=5; w.confirm_erase()
        choices=['tick','advance','intro','what','owner','continue_owner','select','pick','token','confirm','method','continue_method','erase','stop','back','refresh','language','report_help','close_report','limits','close_limits']
        for _ in range(300):
            action=rng.choice(choices)
            source[0]=action
            if action=='tick':w.tick()
            elif action=='advance':now[0]+=rng.choice([0,.1,4.9,5,10]);w.tick()
            elif action=='intro':w.skip_intro()
            elif action=='what':w.accept_what()
            elif action=='owner':w.set_owner(rng.choice([True,False]))
            elif action=='continue_owner':w.continue_owner()
            elif action=='select':w.select_disk(rng.choice([d.path for d in base.discovery.disks]))
            elif action=='pick':w.continue_pick()
            elif action=='token':w.set_confirm_input(w.confirm.token if w.confirm and rng.randrange(2) else 'WRONG')
            elif action=='confirm':w.continue_confirm()
            elif action=='method':w.set_method(rng.choice(list(MethodId)))
            elif action=='continue_method':w.continue_method()
            elif action=='erase':w.confirm_erase()
            elif action=='stop':w.cancel_wipe()
            elif action=='back':w.back()
            elif action=='refresh':w.refresh_disks()
            elif action=='language':w.set_language(rng.choice(['en','fr','de']))
            elif action=='report_help':w.open_report_help()
            elif action=='close_report':w.close_report_help()
            elif action=='limits':w.open_limits()
            elif action=='close_limits':w.close_limits()
            assert all(not d.is_boot for d in w.selectable)
            assert w.selected is None or not w.selected.is_boot
            actions+=1
print({'seed':20261015,'sessions':100,'actions':actions,'starts':starts,'safety_invariants':'passed'})
