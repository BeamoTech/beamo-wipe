"""Fake-only actual runner cleanup: optional inhibitor diagnostic must not abort it."""
import pytest
from beamo_wipe import diagnostics
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner

class StuckInhibitor:
 def poll(self):return None
 def terminate(self):raise PermissionError('owned fake terminate denied')
 def kill(self):raise PermissionError('owned fake kill denied')

class ExitedEngine:
 returncode=0
 def poll(self):return 0

@pytest.mark.parametrize('error',[KeyboardInterrupt,SystemExit,OSError,None])
def test_optional_inhibitor_diagnostic_cannot_abort_exited_engine_retirement(tmp_path,monkeypatch,error):
 def diag(*_a,**_kw):
  if error:raise error('owned diagnostic failure')
 monkeypatch.setattr(diagnostics,'log_diag',diag)
 path=tmp_path/'owned.log';path.write_text('/dev/vda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n')
 request=WipeRequest('/dev/vda',MethodId.EVERYDAY,'/dev/sr0',str(path))
 runner=NwipeRunner();runner._proc=ExitedEngine();runner._active_request=request
 helper=StuckInhibitor();runner._sleep_inhibit._proc=helper
 try:
  result=runner.poll(request)
 except BaseException as exc:
  pytest.fail('optional inhibitor diagnostic escaped confirmed terminal cleanup: '+type(exc).__name__)
 assert result is not None and result.ok
 assert runner._proc is None and runner._active_request is None
 assert runner._sleep_inhibit._proc is helper
