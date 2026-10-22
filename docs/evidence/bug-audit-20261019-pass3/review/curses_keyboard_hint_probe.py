import hashlib, json
from pathlib import Path
from unittest.mock import patch
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as ui

records=[]
for start in (Screen.CONFIRM, Screen.METHOD):
    w=make_demo_wizard();w.skip_intro();w.set_owner(True);w.continue_owner()
    w.select_disk(w.selectable[0].path);w.continue_pick()
    if start==Screen.METHOD:
        w.set_confirm_input(w.confirm.token);w.continue_confirm()
    assert w.screen==start
    class Terminal:
        def __init__(self):self.events=iter([ord('k')]);self.lines=[];self.frames=[]
        def getmaxyx(self):return 24,80
        def keypad(self,*_):pass
        def nodelay(self,*_):pass
        def timeout(self,*_):pass
        def erase(self):self.lines=[]
        def addstr(self,y,x,text,*_):self.lines.append(text)
        def refresh(self):self.frames.append(self.lines.copy())
        def getch(self):
            try:return next(self.events)
            except StopIteration:w.wants_shutdown=True;return -1
    terminal=Terminal()
    with patch.object(ui,'_curses_opt',lambda *_:None),patch.object(ui.time,'sleep',lambda *_:None):
        ui._loop(terminal,w)
    records.append(dict(start=start.name,keyboard_hint=[line for line in terminal.frames[0] if 'K: Keyboard layout' in line],final=w.screen.name,typed=w.confirm_input))
source=Path(ui.__file__).resolve()
print(json.dumps(dict(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=records),indent=2))
assert records[1]['keyboard_hint'] and records[1]['final']=='KEYBOARD'
assert not records[0]['keyboard_hint'] or records[0]['final']=='KEYBOARD','Confirm advertises Keyboard layout shortcut that edits the token instead'
