"""Five seconds must follow visible final review, including buffered stdout."""
import builtins
import json
import os
import sys

import pytest

from beamo_wipe import copy as C
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard


@pytest.mark.parametrize('line_buffered',[True,False],ids=['visible-normal-control','buffered-output'])
def test_plain_review_delay_starts_after_warning_flush(monkeypatch,tmp_path,request,line_buffered):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE',raising=False)
    monkeypatch.setattr('beamo_wipe.safety.default_log_dir',lambda:tmp_path)
    effects=[]
    def forbidden(*_args,**_kwargs):
        effects.append(True)
        raise AssertionError('Native action forbidden')
    for boundary in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                     'beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources',
                     'beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown',
                     'beamo_wipe.sound._run','beamo_wipe.sound._popen'):
        monkeypatch.setattr(boundary,forbidden)
    clock=[0.0]
    wizard=Wizard(discovery_for_scenario('happy'),DryRunRunner(clock=lambda:clock[0]),clock=lambda:clock[0],dry_run=True)
    wizard.skip_intro();wizard.set_owner(True);wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path);wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token);wizard.continue_confirm();wizard.continue_method()
    assert wizard.screen is Screen.LAST_CHANCE
    monkeypatch.setattr(console.time,'sleep',lambda t:clock.__setitem__(0,clock[0]+t))
    displayed=[]
    class Output:
        pending=''
        def write(self,text):
            self.pending+=text
            if line_buffered and '\n' in text:self.flush()
            return len(text)
        def flush(self):
            if self.pending:
                displayed.append((clock[0],self.pending));self.pending=''
        def isatty(self):return False
    output=Output()
    master,slave=os.openpty()
    terminal=os.fdopen(os.dup(slave),'r',encoding='utf-8')
    monkeypatch.setattr(sys,'stdin',terminal)
    monkeypatch.setattr(sys,'stdout',output)
    original_answer=console._answer
    calls=[]
    def answer(w,prompt):
        assert prompt==C.CON_ERASE_PROMPT
        os.write(master,b'ERASE\n')
        return original_answer(w,prompt)
    monkeypatch.setattr(console,'_answer',answer)
    def claim():
        assert wizard.erase_enabled
        calls.append(clock[0]);wizard.wants_shutdown=True
    monkeypatch.setattr(wizard,'confirm_erase',claim)
    try:
        assert console._plain_loop(wizard)==0
        warning_at=min(t for t,text in displayed if C.SEVERITY_WARNING in text)
        trace={'line_buffered':line_buffered,'warning_visible_at':warning_at,'erase_claims':calls,
               'visible_delay':calls[0]-warning_at,'native_calls':effects}
        request.node.user_properties.append(('trace',json.dumps(trace)))
        assert not effects
        assert len(calls)==1
        assert calls[0]-warning_at>=5.0,trace
    finally:
        terminal.close();os.close(slave);os.close(master)
