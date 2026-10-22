"""Real curses/controller replay: a shortcut interrupts Enter's quiet interval."""
import copy
import curses

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console


@pytest.mark.parametrize('fresh', [False, True])
def test_refresh_requires_fresh_enter_after_f5(monkeypatch, fresh):
    effects = []
    def forbidden(*_a, **_kw):
        effects.append(True)
        raise AssertionError('Native device/process action reached')
    for target in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                   'beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources',
                   'beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown'):
        monkeypatch.setattr(target, forbidden)
    w = make_demo_wizard()
    now = [0.0]
    w._clock = lambda: now[0]
    w.skip_intro()
    w.set_owner(True)
    w.continue_owner()
    w.select_disk(w.selectable[0].path)
    w.continue_pick()
    w.set_confirm_input(w.confirm.token)
    w.continue_confirm()
    assert w.screen is Screen.METHOD
    scans=[]
    inventory=copy.deepcopy(w.discovery)
    w._rediscover=lambda: scans.append(True) or inventory
    events=[(0,10),(.1,-1),(.9,curses.KEY_F5),(1.2,-1)]
    events += [(2.3,-1),(2.4,10)] if fresh else [(1.3,10)]
    class Terminal:
        def __init__(self): self.events=iter(events)
        def getmaxyx(self): return 1000,200
        def getch(self):
            try:
                now[0], key=next(self.events)
                return key
            except StopIteration:
                w.wants_shutdown=True
                return -1
        def __getattr__(self,_name): return lambda *_a,**_kw:None
    for name in ('_footer_lines','_chrome_lines'):
        monkeypatch.setattr(console,name,lambda *_a:[])
    for name in ('_curses_opt','_add','_paint_footer'):
        monkeypatch.setattr(console,name,lambda *_a,**_kw:None)
    monkeypatch.setattr(console,'_paint_paged',lambda *_a:0)
    monkeypatch.setattr(console.time,'monotonic',lambda:now[0])
    monkeypatch.setattr(console.time,'sleep',lambda _seconds:None)
    assert console._loop(Terminal(),w)==0
    assert not effects
    assert not w.runner.started
    assert scans==([True] if fresh else [])
    assert w.screen is (Screen.OWNER if fresh else Screen.REFRESH_CONFIRM)
