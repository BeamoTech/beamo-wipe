"""Recovery must own the named coordination inode, using ordinary files only."""

import os

import pytest

from beamo_wipe import session_recovery as recovery
from beamo_wipe.safety import SafetyError

BOOT = "00000000-0000-0000-0000-000000000001"
BUILD = "a" * 64


def _replace_lock(path):
    path.rename(path.with_name(path.name + ".previous"))
    path.touch(mode=0o600)


@pytest.mark.parametrize("name", ["interface.lock", "wipe.lock"])
def test_recovery_rejects_lock_replaced_during_acquisition(tmp_path, monkeypatch, name):
    store = recovery.SessionStore(tmp_path / "private", boot=BOOT, build=BUILD)
    real_flock = recovery.fcntl.flock

    def replace_after_acquisition(fd, operation):
        real_flock(fd, operation)
        path = store.directory / name
        if path.exists() and os.fstat(fd).st_ino == path.stat().st_ino:
            _replace_lock(path)

    try:
        if name == "wipe.lock":
            store.open()
        monkeypatch.setattr(recovery.fcntl, "flock", replace_after_acquisition)
        with pytest.raises(SafetyError):
            if name == "interface.lock":
                store.open()
            else:
                store.is_quiescent()
        if name == "interface.lock":
            assert store.fd == store.owner == -1
        else:
            assert store.quiescent == -1
    finally:
        store.close()


def test_cached_quiescence_does_not_outlive_named_lock(tmp_path):
    store = recovery.SessionStore(tmp_path / "private", boot=BOOT, build=BUILD).open()
    try:
        assert store.is_quiescent()
        _replace_lock(store.directory / "wipe.lock")
        with pytest.raises(SafetyError):
            store.is_quiescent()
        assert store.invalid
    finally:
        store.close()


def test_replaced_interface_lock_blocks_journal_writes(tmp_path):
    store = recovery.SessionStore(tmp_path / "private", boot=BOOT, build=BUILD).open()
    try:
        before = (store.directory / recovery.NAME).read_bytes()
        _replace_lock(store.directory / "interface.lock")
        with pytest.raises(SafetyError):
            store.save({"phase": "preflight"})
        assert store.invalid
        assert (store.directory / recovery.NAME).read_bytes() == before
    finally:
        store.close()
