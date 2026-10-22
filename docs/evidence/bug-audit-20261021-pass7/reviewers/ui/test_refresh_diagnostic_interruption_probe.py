"""Refresh must retire its claim even if optional diagnostic logging is interrupted."""
import json

import pytest

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard


@pytest.mark.parametrize('diagnostic_error',[None,OSError,KeyboardInterrupt,SystemExit])
def test_refresh_failure_resolves_before_optional_diagnostic_interruption(monkeypatch,tmp_path,request,diagnostic_error):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE',raising=False)
    monkeypatch.setattr('beamo_wipe.safety.default_log_dir',lambda:tmp_path)
    effects=[]
    def forbidden(*_args,**_kwargs):
        effects.append(True)
        raise AssertionError('Native action forbidden')
    for boundary in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                     'beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources',
                     'beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown',
                     'beamo_wipe.sound._run','beamo_wipe.sound._popen'):
        monkeypatch.setattr(boundary,forbidden)
    def failed_scan():
        raise OSError('Fake inventory scan failed')
    wizard=Wizard(discovery_for_scenario('happy'),DryRunRunner(),rediscover=failed_scan,dry_run=True)
    wizard.skip_intro()
    assert wizard.open_refresh_confirm()
    diagnostics=[]
    def log_diag(*args):
        diagnostics.append(args[:2])
        if diagnostic_error:
            raise diagnostic_error('Fake optional logging interruption')
    monkeypatch.setattr('beamo_wipe.diagnostics.log_diag',log_diag)
    escaped=None
    try:
        wizard.confirm_refresh()
    except BaseException as error:
        escaped=type(error).__name__
    before=wizard.screen
    wizard.back()
    wizard.shutdown()
    trace={'error':diagnostic_error.__name__ if diagnostic_error else None,'escaped':escaped,
           'screen_after_refresh':before.name,'screen_after_back_and_shutdown':wizard.screen.name,
           'can_refresh':wizard.can_refresh,'wants_shutdown':wizard.wants_shutdown,
           'diagnostic_calls':diagnostics,'native_calls':effects}
    request.node.user_properties.append(('trace',json.dumps(trace)))
    print(json.dumps(trace))
    assert not effects
    assert before is Screen.PICK_BLOCKED,trace
    assert escaped is None,trace
    # A fresh scan remains possible instead of staying in REFRESHING forever.
    assert wizard.screen is not Screen.REFRESHING,trace
