"""Actual Wizard preference restart with fake disks and no host actions."""
import json
import os

import pytest
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.report_intent import ReportIntentStore


@pytest.mark.parametrize('swap', [False, True], ids=['normal-control','swapped-temporary'])
def test_restart_preserves_requested_report_or_discloses_failed_persistence(tmp_path, monkeypatch, swap, request):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE', raising=False)
    forbidden_calls = []
    def forbidden(*_a, **_kw):
        forbidden_calls.append(True)
        raise AssertionError('Native device/process/power callback forbidden')
    for boundary in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                     'beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources',
                     'beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown'):
        monkeypatch.setattr(boundary, forbidden)
    directory = tmp_path / 'private'; directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory); store.save(False)
    wizard = make_demo_wizard(); wizard.enable_report_intent_recovery(store)
    wizard.screen = Screen.REPORT_HELP
    original_sync = os.fsync
    swaps = []
    def sync(fd):
        original_sync(fd)
        for path in directory.glob('.report-intent-*'):
            if os.fstat(fd).st_ino == path.stat().st_ino and swap and not swaps:
                swaps.append(path.name)
                path.rename(directory / 'retired-written-temporary')
                path.write_bytes(b'not-wanted\n'); path.chmod(0o600)
    monkeypatch.setattr(os,'fsync',sync)
    wizard.set_report_wanted(True)
    monkeypatch.setattr(os,'fsync',original_sync)
    restarted = make_demo_wizard(); restarted.enable_report_intent_recovery(ReportIntentStore(directory))
    restarted.shutdown()
    trace = {'swap':swap,'swaps':swaps,'chosen_report_wanted':wizard.report_wanted,
             'save_warning':wizard.report_recovery_warning,'recovered_wanted':restarted.report_wanted,
             'shutdown_confirm':restarted.screen == Screen.SHUTDOWN_CONFIRM,
             'wants_shutdown':restarted.wants_shutdown,'native_calls':forbidden_calls}
    request.node.user_properties.append(('trace',json.dumps(trace))); print(json.dumps(trace))
    assert not forbidden_calls
    assert wizard.report_recovery_warning or restarted.report_wanted,trace
    if not swap:
        assert restarted.screen == Screen.SHUTDOWN_CONFIRM and not restarted.wants_shutdown
