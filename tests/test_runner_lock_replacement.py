"""The wipe lock must still name the acquired regular-file inode."""

import fcntl

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner
from beamo_wipe.safety import SafetyError


def test_wipe_lock_replaced_during_acquisition_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    lock_path = tmp_path / "wipe.lock"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "fake.log"))
    real_flock = fcntl.flock
    replaced = False

    def replace_after_acquisition(fd, operation):
        nonlocal replaced
        real_flock(fd, operation)
        if operation & fcntl.LOCK_EX and not replaced:
            replaced = True
            lock_path.unlink()
            lock_path.touch(mode=0o600)

    monkeypatch.setattr(fcntl, "flock", replace_after_acquisition)
    runner = NwipeRunner()
    try:
        with pytest.raises(SafetyError, match="changed"):
            runner._acquire_wipe_lock(request)
        assert runner._lock_fd is None
    finally:
        runner._release_wipe_lock()


def test_wipe_lock_still_excludes_a_second_runner(tmp_path, monkeypatch):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "fake.log"))
    first, second = NwipeRunner(), NwipeRunner()
    try:
        first._acquire_wipe_lock(request)
        with pytest.raises(SafetyError, match="already running"):
            second._acquire_wipe_lock(request)
    finally:
        first._release_wipe_lock()
        second._release_wipe_lock()


def test_interrupted_wipe_lock_acquisition_closes_unpublished_fd(tmp_path, monkeypatch):
    import os

    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "fake.log"))
    real_flock = fcntl.flock
    acquired = []

    def interrupt_after_acquisition(fd, operation):
        real_flock(fd, operation)
        acquired.append(fd)
        raise KeyboardInterrupt

    monkeypatch.setattr(fcntl, "flock", interrupt_after_acquisition)
    runner = NwipeRunner()
    closed = False
    try:
        with pytest.raises(KeyboardInterrupt):
            runner._acquire_wipe_lock(request)
        assert runner._lock_fd is None
        with pytest.raises(OSError):
            os.fstat(acquired[0])
        closed = True
    finally:
        # Keep the pre-fix reproduction from leaking its fixture descriptor.
        if not closed:
            try:
                os.close(acquired[0])
            except OSError:
                pass
