"""Independent actual finite-command execution log integrity probe."""
import hashlib
import os
import sys

import pytest

from beamo_wipe import ci_evidence


@pytest.mark.parametrize('gate', ['lint', 'preview'])
@pytest.mark.parametrize('rewrite', [False, True])
def test_gate_receipt_binds_actual_retained_log(tmp_path, monkeypatch, gate, rewrite):
    directory = tmp_path / 'evidence'
    logfile = directory / (gate + '.log')
    real_stat = os.stat
    intercepted = False

    def changed_log(path, *args, **kwargs):
        nonlocal intercepted
        if path == logfile and not intercepted:
            intercepted = True
            if rewrite:
                original = logfile.read_bytes()
                assert original == b'original\n'
                logfile.write_bytes(b'tampered\n')
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, 'stat', changed_log)
    def run():
        return ci_evidence.run_gate(
            gate, [sys.executable, '-c', 'print("original")'],
            root=ci_evidence.Path('/workspace/beamo-wipe'),
            evidence_dir=directory, build_id='local',
        )

    if rewrite:
        with pytest.raises(RuntimeError, match='execution log changed'):
            run()
        assert not (directory / (gate + '.receipt.json')).exists()
    else:
        receipt = run()
        assert receipt['log_sha256'] == hashlib.sha256(logfile.read_bytes()).hexdigest()
    assert intercepted
