"""An undelivered stop signal cannot turn a natural failure into owner abort."""
import pytest

from beamo_wipe import nwipe_runner
from test_cancel_after_exit_regression import _runner


@pytest.mark.parametrize('delivery', ('permission', 'lookup', 'delivered'))
@pytest.mark.parametrize('log,code,reason', (
    ('[2026/10/19 05:00:00] error: /dev/vda: >>> FAILURE! <<<\n', 1, 'engine_failed'),
    ("[2026/10/19 05:00:00] error: Verification mismatch on '/dev/vda'\n", 1, 'verification_failed'),
    ('Nwipe successfully completed.\n', 0, 'completion_missing'),
))
def test_failed_signal_keeps_terminal_reason(tmp_path, monkeypatch, delivery, log, code, reason):
    monkeypatch.setattr(nwipe_runner, '_try_log_diag', lambda *_args: None)
    runner = _runner(tmp_path, log)
    class Process:
        returncode = None
        def poll(self):
            return self.returncode
        def terminate(self):
            if delivery == 'permission':
                raise PermissionError('injected signal refusal')
            if delivery == 'lookup':
                raise ProcessLookupError('exited before signal')
        def wait(self, timeout=None):
            self.returncode = code
            return code
    runner._proc = Process()
    runner.cancel()
    assert runner.result is not None
    assert runner.result.reason == ('cancelled' if delivery == 'delivered' else reason)
