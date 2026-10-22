"""S held on review cannot become new Stop consent after the fake run starts."""
import pytest
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console
from test_busy_transitions import ready as ready_fixture

ready=ready_fixture

@pytest.mark.parametrize('prior_hold',[False,True])
def test_stop_s_must_originate_in_new_modal(ready,monkeypatch,prior_hold):
    w=ready
    now=[0.]
    w._clock=lambda:now[0]
    original=w.confirm_stop
    monkeypatch.setattr(w,'confirm_stop',lambda consent:original(consent,asynchronous=False))
    events=[(5.1,-1)]+([(5.2,ord('s'))]if prior_hold else[])+[(5.3,10),(5.4,27),(5.5,ord('s'))]
    class Terminal:
        def __init__(self):self.events=iter(events)
        def getmaxyx(self):return 1000,200
        def getch(self):
            try:now[0],ch=next(self.events);return ch
            except StopIteration:w.wants_shutdown=True;return -1
        def __getattr__(self,_name):return lambda *_a,**_kw:None
    for name in ('_footer_lines','_chrome_lines'):
        monkeypatch.setattr(console,name,lambda *_a:[])
    for name in ('_curses_opt','_add','_paint_footer'):
        monkeypatch.setattr(console,name,lambda *_a,**_kw:None)
    monkeypatch.setattr(console.time,'monotonic',lambda:now[0])
    monkeypatch.setattr(console.time,'sleep',lambda _seconds:None)
    assert console._loop(Terminal(),w)==0
    assert w.runner.started
    assert w.runner.cancelled is (not prior_hold)
    assert w.screen is (Screen.WORKING if prior_hold else Screen.DONE)
