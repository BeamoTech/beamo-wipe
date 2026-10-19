import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as ui
from beamo_wipe import storage_limits as limits

source=Path(ui.__file__).resolve()
records=[]
for mode,events in [('unscrolled-control',[ord('l')]),('scrolled-before-open',[ui.curses.KEY_NPAGE]*5+[ord('l')])]:
    w=make_demo_wizard()
    w.skip_intro(); w.set_owner(True); w.continue_owner()
    w.select_disk(w.selectable[0].path); w.continue_pick()
    w.set_confirm_input(w.confirm.token); w.continue_confirm()
    assert w.screen == Screen.METHOD
    class Terminal:
        def __init__(self): self.keys=iter(events); self.lines=[]; self.frames=[]
        def getmaxyx(self): return 24,80
        def keypad(self,*_): pass
        def nodelay(self,*_): pass
        def erase(self): self.lines=[]
        def addstr(self,y,x,text,*_): self.lines.append((y,text))
        def refresh(self): self.frames.append(dict(screen=w.screen.name,lines=self.lines.copy()))
        def getch(self):
            try:return next(self.keys)
            except StopIteration:
                w.wants_shutdown=True
                return -1
    terminal=Terminal()
    with patch.object(ui,'_curses_opt',lambda *_:None), patch.object(ui.time,'sleep',lambda *_:None):
        ui._loop(terminal,w)
    frame=terminal.frames[-1]
    assert frame['screen']=='LIMITS'
    page='\n'.join(text for _,text in frame['lines'])
    records.append(dict(mode=mode,first_section=limits.SECTIONS[0][0],first_section_visible=limits.SECTIONS[0][0] in page,frame=page))
print(json.dumps(dict(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=records),indent=2))
assert records[0]['first_section_visible']
assert records[1]['first_section_visible'], 'Limits inherited a different screen scroll offset and skipped its opening guidance'
