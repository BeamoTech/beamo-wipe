"""Finite model: nested final-review holds across discard-dialog epochs.

Independent oracle tracks overlay depth, gate time and dialog generation.
Only inert callbacks and demo discovery are used; no runner starts.
"""
from contextlib import ExitStack
from hashlib import sha256
from itertools import product
import json, os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.wizard import Wizard
from beamo_wipe import copy as C

os.environ['BEAMO_WIPE_DRY_RUN']='1'
os.environ['BEAMO_WIPE_DEMO']='1'
out = Path(__file__).parent
native = []
def forbidden(*args, **kwargs):
    native.append(True)
    raise AssertionError('Native callback forbidden')

targets = ['subprocess.run','subprocess.Popen','os.system','socket.create_connection',
 'beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline',
 'beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start',
 'beamo_wipe.nwipe_runner.DryRunRunner.start','beamo_wipe.app._shutdown',
 'beamo_wipe.sound._run','beamo_wipe.sound._popen']
count = dict(scenarios=0, accepted_discard_controls=0, old_epoch_refusals=0,
             busy_refusals=0, immediate_review_refusals=0, overlay_refusals=0,
             elapsed_gate_controls=0, events=0)
records = []
with ExitStack() as stack:
    for target in targets:
        stack.enter_context(patch(target, forbidden))
    for language, depth, busy, return_action in product(
        ('en','fr','de'),range(3),
        ('none','_report_exporting','_diagnostic_busy','_evidence_saving','_finishing','runner'),
        ('back','keep_report_session')):
        clock = [0.0]
        runner = SimpleNamespace(progress=None,result=None)
        wizard = Wizard(discovery_for_scenario('happy'),runner,clock=lambda:clock[0],dry_run=True)
        assert wizard.set_language(language)
        wizard.skip_intro(); wizard.set_owner(True);wizard.continue_owner()
        wizard.select_disk(wizard.selectable[0].path);wizard.continue_pick()
        wizard.set_confirm_input(wizard.confirm.token);wizard.continue_confirm();wizard.continue_method()
        assert wizard.screen is Screen.LAST_CHANCE
        clock[0]=8.0
        assert wizard.erase_enabled
        for index in range(depth):
            assert wizard.begin_review_overlay()
        assert wizard._review_overlay_depth == depth
        if depth:
            assert not wizard.erase_enabled
            count['overlay_refusals']+=1
        wizard.report_wanted=True
        wizard.shutdown()
        assert wizard.screen is Screen.SHUTDOWN_CONFIRM
        generation = wizard.shutdown_generation
        wizard.confirm_shutdown_without_saving(generation-1)
        assert not wizard.wants_shutdown
        count['old_epoch_refusals']+=1
        clock[0]=20.0
        getattr(wizard,return_action)()
        assert wizard.screen is Screen.LAST_CHANCE
        assert wizard.countdown_left == 5.0
        assert not wizard.erase_enabled
        count['immediate_review_refusals']+=1
        for index in range(depth):
            clock[0]+=9.0
            wizard.end_review_overlay()
            assert wizard._review_overlay_depth == depth-index-1
            assert not wizard.erase_enabled
            count['overlay_refusals']+=1
        clock[0]+=5.0
        assert wizard.erase_enabled
        count['elapsed_gate_controls']+=1
        wizard.shutdown()
        assert wizard.screen is Screen.SHUTDOWN_CONFIRM
        assert wizard.shutdown_generation == generation+1
        wizard.confirm_shutdown_without_saving(generation)
        assert not wizard.wants_shutdown
        count['old_epoch_refusals']+=1
        if busy == 'runner':
            runner._started=1.0
        elif busy != 'none':
            setattr(wizard,busy,True)
        wizard.confirm_shutdown_without_saving(generation+1)
        if busy != 'none':
            assert not wizard.wants_shutdown
            count['busy_refusals']+=1
            if busy == 'runner':
                runner._started=None
            else:
                setattr(wizard,busy,False)
            wizard.confirm_shutdown_without_saving(generation+1)
        assert wizard.wants_shutdown
        assert wizard.shutdown_still_safe()
        assert wizard._wipe_request is None
        count['accepted_discard_controls']+=1
        count['scenarios']+=1
        count['events']+=15+depth*2+(busy!='none')
        records.append(dict(language=language,depth=depth,busy=busy,return_action=return_action))
from beamo_wipe import lang
lang.set_language('en')
source_paths = ['src/beamo_wipe/wizard.py','src/beamo_wipe/ui/accessible_wizard.py',
 'src/beamo_wipe/ui/tk_wizard.py','src/beamo_wipe/ui/console_wizard.py','src/beamo_wipe/app.py']
result = dict(model='nested-review-hold-shutdown-discard-epoch', counts=count,
 native_callbacks=len(native),mismatches=0,fake_callbacks_only=True,
 source_sha256={path:sha256(Path('/workspace/beamo-wipe',path).read_bytes()).hexdigest() for path in source_paths},
 scenarios=records,
 coverage_note='Supporting model observations overlap canonical tests; not additional unique test passes.')
(out/'shutdown_overlay_epoch_model.json').write_text(json.dumps(result,indent=2)+'\n')
assert not native
print(json.dumps({key:value for key,value in result.items() if key != 'scenarios'}))
