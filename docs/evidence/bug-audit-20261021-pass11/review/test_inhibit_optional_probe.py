"""Independent fake-only probes for optional power diagnostic boundaries."""
from pathlib import Path
import pytest
from beamo_wipe import diagnostics
from beamo_wipe import sleep_inhibit as S
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner


class OwnedUnstoppableHelper:
    def poll(self):
        return None

    def terminate(self):
        raise PermissionError('owned fake helper')

    def kill(self):
        raise PermissionError('owned fake helper')


class OwnedExitedEngine:
    returncode = 23

    def poll(self):
        return 23


@pytest.mark.parametrize('route', ['start', 'stop', 'runner-cancel'])
@pytest.mark.parametrize('diagnostic_error', [KeyboardInterrupt, SystemExit, OSError, None])
def test_optional_power_diagnostic_keeps_required_transition(monkeypatch, tmp_path, route, diagnostic_error):
    monkeypatch.setenv('BEAMO_WIPE_LIVE', '1')
    monkeypatch.delenv('BEAMO_WIPE_DRY_RUN', raising=False)
    calls = []

    def diagnostic(*args):
        calls.append(args[:2])
        if diagnostic_error is not None:
            raise diagnostic_error('optional logger interruption')

    def refused_spawn(*args, **kwargs):
        raise PermissionError('owned fake spawn denial')

    monkeypatch.setattr(diagnostics, 'log_diag', diagnostic)
    monkeypatch.setattr(S.subprocess, 'Popen', refused_spawn)
    helper = OwnedUnstoppableHelper()
    inhibitor = S.SleepInhibit()
    if route != 'start':
        inhibitor._proc = helper
    if route == 'runner-cancel':
        log = tmp_path / 'owned-engine.log'
        log.write_text('No completion marker\n')
        request = WipeRequest('/dev/vda', MethodId.EVERYDAY, '/dev/sr0', str(log))
        runner = NwipeRunner()
        runner._proc = OwnedExitedEngine()
        runner._active_request = request
        runner._sleep_inhibit = inhibitor
        action = runner.cancel
    else:
        action = getattr(inhibitor, route)
    try:
        action()
    except BaseException as exc:
        pytest.fail('optional logger aborted required '+route+' transition: '+type(exc).__name__)
    assert ('power', 'sleep_inhibit_unavailable' if route == 'start' else 'sleep_inhibit_stop_failed') in calls
    assert inhibitor._proc is (None if route == 'start' else helper)
    if route == 'runner-cancel':
        assert runner.result is not None and not runner.result.ok
        assert runner._proc is None and runner._active_request is None
