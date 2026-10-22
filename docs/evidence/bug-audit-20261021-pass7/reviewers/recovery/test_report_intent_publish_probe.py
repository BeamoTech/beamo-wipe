"""Fake local files: a swapped temporary name must not silently change intent."""
import json
import os
from pathlib import Path

import pytest
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize('swap', [False, True], ids=['normal-control', 'swapped-temporary'])
def test_save_cannot_confirm_wanted_while_publishing_not_wanted(tmp_path, monkeypatch, swap, request):
    directory = tmp_path / 'private'
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(False)
    original_sync = os.fsync
    changed = []

    def sync(fd):
        original_sync(fd)
        for path in directory.glob('.report-intent-*'):
            if path.stat().st_ino != os.fstat(fd).st_ino:
                continue
            if swap and not changed:
                changed.append(path.name)
                path.rename(directory / 'retired-owned-temporary')
                path.write_bytes(b'not-wanted\n')
                path.chmod(0o600)
            return

    monkeypatch.setattr(os, 'fsync', sync)
    error = None
    try:
        store.save(True)
    except SafetyError as exc:
        error = str(exc)
    monkeypatch.setattr(os, 'fsync', original_sync)
    loaded = store.load()
    trace = {'swap': swap, 'changed': changed, 'save_error': error,
             'requested_wanted': True, 'loaded_wanted': loaded,
             'named_bytes': (directory / store.NAME).read_text()}
    request.node.user_properties.append(('trace', json.dumps(trace)))
    print(json.dumps(trace))
    assert error is not None or loaded is True, trace
    if not swap:
        assert error is None and loaded is True
