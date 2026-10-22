"""A held S from before Stop confirmation is not a new confirmation press."""
from types import SimpleNamespace
import pytest
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console

@pytest.mark.parametrize('events,expected',[
 ([(0,ord('s')),(0,27),(0,ord('s'))],0),
 ([(0,27),(0,ord('s'))],1),
])
def test_stop_confirmation_does_not_consume_preexisting_s_hold(monkeypatch,events,expected):
 calls=[]
 wizard=SimpleNamespace(
  screen=Screen.WORKING,stop_confirmation=None,wants_shutdown=False,wants_new_session=False,
  can_open_diagnostic=False,can_open_keyboard=False,can_open_report_help=False,can_refresh=False,
  error='',progress_view=SimpleNamespace(status_text='Working'),operation_disk=None,
  operation_identity_text='',operation_method_text='',evidence_warning='',power_text='',
  tick=lambda:None,
 )
 wizard.request_stop=lambda:setattr(wizard,'stop_confirmation',object())
 wizard.keep_erasing=lambda:setattr(wizard,'stop_confirmation',None)
 wizard.confirm_stop=lambda confirmation:calls.append(confirmation)
 clock={'now':0.0}
 class Terminal:
  def __init__(self):self.events=iter(events)
  def getmaxyx(self):return 24,80
  def getch(self):
   try:clock['now'],key=next(self.events);return key
   except StopIteration:wizard.wants_shutdown=True;return -1
  def __getattr__(self,_name):return lambda *_args,**_kwargs:None
 for name in ('_footer_lines','_chrome_lines'):
  monkeypatch.setattr(console,name,lambda *_args:[])
 for name in ('_add','_paint_paged','_paint_footer'):
  monkeypatch.setattr(console,name,lambda *_args,**_kwargs:0)
 monkeypatch.setattr(console.time,'monotonic',lambda:clock['now'])
 monkeypatch.setattr(console.time,'sleep',lambda _seconds:None)
 assert console._loop(Terminal(),wizard)==0
 assert len(calls)==expected
