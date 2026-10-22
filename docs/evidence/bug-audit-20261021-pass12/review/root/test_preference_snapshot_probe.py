"""Independent owned-file preference read race, injected after final fstat."""
import os
import stat
import pytest
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize('wanted', [False, True])
@pytest.mark.parametrize('mutation', ['normal', 'chmod', 'new-link', 'rewrite'])
def test_preference_read_checks_the_final_named_snapshot(tmp_path, monkeypatch, wanted, mutation):
    directory = tmp_path / 'private'
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(wanted)
    path = directory / store.NAME
    identity = path.stat().st_ino
    real_fstat = os.fstat
    reads = 0

    def raced_fstat(fd):
        nonlocal reads
        snapshot = real_fstat(fd)
        if stat.S_ISREG(snapshot.st_mode) and snapshot.st_ino == identity:
            reads += 1
            if reads == 2:
                if mutation == 'chmod':
                    path.chmod(0o644)
                elif mutation == 'new-link':
                    os.link(path, directory / 'owned-link')
                elif mutation == 'rewrite':
                    # Actual same-sized replacement bytes alter ctime/mtime,
                    # while preserving the old coherent fstat return value.
                    path.write_bytes(b'?' * snapshot.st_size)
        return snapshot

    monkeypatch.setattr(os, 'fstat', raced_fstat)
    if mutation == 'normal':
        assert store.load() is wanted
    else:
        with pytest.raises(SafetyError):
            store.load()
    assert reads == 2
