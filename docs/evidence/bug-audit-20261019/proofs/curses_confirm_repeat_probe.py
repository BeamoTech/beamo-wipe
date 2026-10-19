from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console

source = Path(console.__file__).resolve()
records=[]
for mode,events in [('held-enter', [10,10]), ('fresh-enter-control',[10,-1,-1,10])]:
    wizard=make_demo_wizard()
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(wizard.selectable[0].path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.open_keyboard()
    assert wizard.screen == Screen.KEYBOARD
    class Terminal:
        def __init__(self): self.events=iter(events); self.trace=[]
        def getmaxyx(self): return 24,80
        def keypad(self,*_): pass
        def nodelay(self,*_): pass
        def timeout(self,*_): pass
        def erase(self): pass
        def addstr(self,*_): pass
        def refresh(self): pass
        def getch(self):
            self.trace.append(wizard.screen.name)
            try: return next(self.events)
            except StopIteration:
                wizard.wants_shutdown=True
                return -1
    terminal=Terminal()
    now=[0.0]
    def monotonic():
        now[0]+=1.0
        return now[0]
    with ExitStack() as stack:
        stack.enter_context(patch.object(console,'_curses_opt',lambda *_:None))
        stack.enter_context(patch.object(console.time,'sleep',lambda *_:None))
        stack.enter_context(patch.object(console.time,'monotonic',monotonic))
        console._loop(terminal,wizard)
    records.append(dict(mode=mode, screens_before_reads=terminal.trace, final=wizard.screen.name, runner_started=wizard.runner.started))
print(json.dumps(dict(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=records),indent=2))
assert records[1]['final']=='METHOD'
assert not any(record['runner_started'] for record in records)
assert records[0]['final']=='CONFIRM', 'held Enter closed Keyboard and also accepted retained token'
