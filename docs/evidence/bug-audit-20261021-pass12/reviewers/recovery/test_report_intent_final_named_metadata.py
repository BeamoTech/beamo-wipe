"""Product fake proof: preference load must reject unsafe named metadata."""
import os
import stat
import pytest
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError

@pytest.mark.parametrize('wanted', [False, True])
@pytest.mark.parametrize('change', ['normal', 'mode', 'hardlink'])
def test_final_named_metadata(tmp_path, monkeypatch, wanted, change):
    directory = tmp_path / 'private'
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(wanted)
    real_stat = os.stat
    changed = False
    def mutate_at_named_stat(path, *args, **kwargs):
        nonlocal changed
        if path == store.NAME and kwargs.get('dir_fd') is not None and not changed:
            changed = True
            if change == 'mode':
                (directory / store.NAME).chmod(0o644)
            elif change == 'hardlink':
                os.link(directory / store.NAME, directory / 'foreign-link')
        return real_stat(path, *args, **kwargs)
    monkeypatch.setattr(os, 'stat', mutate_at_named_stat)
    if change == 'normal':
        assert store.load() is wanted
    else:
        with pytest.raises(SafetyError):
            store.load()
    assert changed
