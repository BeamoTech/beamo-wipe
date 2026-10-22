"""Early activity cannot disappear behind a late skip when logs cross 1 MiB."""
import os

import pytest

import beamo_wipe.app as app
from beamo_wipe import nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest


@pytest.mark.parametrize('large',[False,True])
@pytest.mark.parametrize('activity',[False,True])
@pytest.mark.parametrize('guard,reason',[
    ('/dev/FAKE-DATA is reported as IN USE\n','occupied'),
    ("Unable to open device '/dev/FAKE-DATA'.\n",'open_failed'),
    ('/dev/FAKE-DATA: No sane device geometry\n','geometry_unusable'),
])
def test_early_activity_survives_late_skip_at_large_log_boundary(tmp_path,monkeypatch,large,activity,guard,reason):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    effects=[]
    def forbidden(*a,**kw):effects.append(True);raise AssertionError('Native action forbidden')
    for name in ('run','Popen'):monkeypatch.setattr(m.subprocess,name,forbidden)
    monkeypatch.setattr(os,'kill',forbidden);monkeypatch.setattr(app,'_shutdown',forbidden)
    monkeypatch.setattr(m,'_try_log_diag',lambda*a,**kw:None)
    actual_realpath=os.path.realpath
    def realpath(path,*a,**kw):
        return os.fspath(path)if os.fsdecode(path).startswith('/dev/')else actual_realpath(path,*a,**kw)
    monkeypatch.setattr(os.path,'realpath',realpath)
    stamp='[2026/10/21 12:34:56] info: '
    progress='/dev/FAKE-DATA: 25.00%, round 1 of 1, pass 1 of 1, eta 00:00:30, [writing]\n'
    text=stamp+'Program options are set as follows\n'+(stamp+progress if activity else '')
    if large:text+=('x'*4095+'\n')*(m.NWIPE_COMPLETION_LOG_BYTES//4096)
    text+=stamp+guard
    path=tmp_path/'fake.log';path.write_text(text)
    class Exited:
        returncode=0
        def poll(self):return self.returncode
    runner=m.NwipeRunner();runner._proc=Exited()
    run=WipeRequest('/dev/FAKE-DATA',MethodId.EVERYDAY,'/dev/FAKE-BOOT',str(path));runner._active_request=run
    result=runner.poll(run)
    assert result is not None and not result.ok
    assert result.reason==('indeterminate'if activity else reason)
    assert check_payloads(runner._assessment_log_text,run.device)==check_payloads(text,run.device)
    assert runner._proc is None and not effects
