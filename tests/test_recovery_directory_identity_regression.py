"""Recovery coordinates the current directory, not a retired directory inode."""

import fcntl
import os

import pytest

from beamo_wipe.safety import SafetyError
from beamo_wipe.session_recovery import SessionStore, NAME

BOOT = "00000000-0000-0000-0000-000000000001"
BUILD = "a" * 64


def replace_directory(path):
    old = path.with_name(path.name + "-previous")
    path.rename(old)
    path.mkdir(mode=0o700)
    return old


@pytest.mark.parametrize("cached", [False, True])
def test_replaced_directory_cannot_prove_runner_stopped(tmp_path, cached):
    store = SessionStore(tmp_path / "private", boot=BOOT, build=BUILD).open()
    peer_fd = -1
    try:
        if cached:
            assert store.is_quiescent()
        replace_directory(store.directory)
        peer_fd = os.open(store.directory / "wipe.lock", os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(peer_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SafetyError):
            store.is_quiescent()
        assert store.invalid
    finally:
        if peer_fd >= 0:
            os.close(peer_fd)
        store.close()


def test_replaced_directory_cannot_receive_a_successful_journal_update(tmp_path):
    store = SessionStore(tmp_path / "private", boot=BOOT, build=BUILD).open()
    try:
        old = replace_directory(store.directory)
        before = (old / NAME).read_bytes()
        with pytest.raises(SafetyError):
            store.save({"phase": "preflight"})
        assert store.invalid
        assert (old / NAME).read_bytes() == before
        assert not (store.directory / NAME).exists()
    finally:
        store.close()
