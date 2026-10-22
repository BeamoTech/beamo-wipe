"""An optional diagnostic must not abort an explicit fake-process Stop request."""
import json
import os

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest
import beamo_wipe.app as app


@pytest.mark.parametrize('logging_error', [None, OSError, KeyboardInterrupt, SystemExit], ids=['normal', 'io-error', 'keyboard-interrupt', 'system-exit'])
def test_diagnostic_failure_does_not_prevent_requested_stop(tmp_path, monkeypatch, request, logging_error):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE', raising=False)
    effects=[]
    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError('Actual inventory/process/signal/power forbidden')
    monkeypatch.setattr(module.subprocess, 'run', forbidden)
    monkeypatch.setattr(module.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(module.os, 'kill', forbidden)
    monkeypatch.setattr(app, '_shutdown', forbidden)
    monkeypatch.setattr(module.NwipeRunner, 'start', forbidden)
    monkeypatch.setattr('beamo_wipe.discover.run_lsblk', forbidden)
    monkeypatch.setattr('beamo_wipe.discover.read_mount_sources', forbidden)
    monkeypatch.setattr('beamo_wipe.discover.read_cmdline', forbidden)
    log=tmp_path/'fake.log';log.write_text('fake run in progress\n')
    calls=[]
    class FakeProcess:
        returncode=None
        def poll(self):
            calls.append('poll-error')
            raise OSError('Fake status probe failure')
        def terminate(self):
            calls.append('terminate')
            self.returncode=-15
        def wait(self, timeout):
            calls.append('wait')
            return self.returncode
    def diagnostic(*args):
        calls.append('diagnostic')
        if logging_error is not None:
            raise logging_error('Fake optional diagnostic interruption')
    monkeypatch.setattr('beamo_wipe.diagnostics.log_diag', diagnostic)
    proc=FakeProcess();runner=module.NwipeRunner()
    runner._proc=proc
    runner._active_request=WipeRequest('/dev/FAKE-DATA', MethodId.EVERYDAY, '/dev/FAKE-BOOT',str(log))
    runner._last_logfile=str(log)
    escaped=None
    try:
        runner.cancel()
    except BaseException as error:
        escaped=type(error).__name__
    trace={'logging_error':logging_error.__name__ if logging_error else None,'escaped':escaped,'calls':calls,'process_retained':runner._proc is proc,'result':runner.result.reason if runner.result else None,'native_callbacks':len(effects)}
    request.node.user_properties.append(('trace',json.dumps(trace)))
    assert not effects
    assert 'terminate' in calls,trace
    assert escaped is None,trace
    assert runner._proc is None,trace
    assert runner.result.reason=='cancelled',trace
