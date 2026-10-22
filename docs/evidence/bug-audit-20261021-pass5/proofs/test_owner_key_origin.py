"""A Space held on keyboard setup cannot grant new-screen owner consent."""
import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console

@pytest.mark.parametrize('prior_hold',[False,True])
def test_owner_space_must_originate_after_setup(monkeypatch,prior_hold):
    w=make_demo_wizard()
    w.skip_splash()
    assert w.screen is Screen.KEYBOARD
    now=[0.]
    events=([(0,32)]if prior_hold else[])+[(.1,10),(.2,32)]
    class Terminal:
        def __init__(self): self.events=iter(events)
        def getmaxyx(self): return 1000,200
        def getch(self):
            try:now[0],ch=next(self.events);return ch
            except StopIteration:w.wants_shutdown=True;return -1
        def __getattr__(self,_name):return lambda *_a,**_kw:None
    for name in ('_footer_lines','_chrome_lines'):
        monkeypatch.setattr(console,name,lambda *_a:[])
    for name in ('_curses_opt','_add','_paint_footer'):
        monkeypatch.setattr(console,name,lambda *_a,**_kw:None)
    monkeypatch.setattr(console,'_paint_paged',lambda *_a:0)
    monkeypatch.setattr(console.time,'monotonic',lambda:now[0])
    monkeypatch.setattr(console.time,'sleep',lambda _seconds:None)
    assert console._loop(Terminal(),w)==0
    assert w.screen is Screen.OWNER
    assert w.owner_ok is (not prior_hold)
