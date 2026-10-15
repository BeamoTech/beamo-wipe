"""The launch log descriptor has the same ownership lifetime as the engine."""

import os
import threading
import subprocess
from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError


def test_delayed_start_cannot_overwrite_ambiguous_spawn_ownership(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "engine.log"))
    waiting, resume = threading.Event(), threading.Event()
    errors = []
    resolve = module.resolve_nwipe_binary

    def delay_preflight(binary):
        if threading.current_thread() is delayed:
            waiting.set()
            assert resume.wait(5)
        return resolve(binary)

    def delayed_start():
        try:
            runner.start(request)
        except BaseException as exc:
            errors.append(exc)

    delayed = threading.Thread(target=delayed_start)
    monkeypatch.setattr(module, "resolve_nwipe_binary", delay_preflight)
    spawn = Mock(side_effect=[OSError("ownership uncertain"), Mock()])
    monkeypatch.setattr(module.subprocess, "Popen", spawn)
    old_lock = old_log = None
    delayed.start()
    try:
        assert waiting.wait(5)
        with pytest.raises(OSError, match="ownership uncertain"):
            runner.start(request)
        old_lock, old_log = runner._lock_fd, getattr(runner, "_log_fd", None)
        (tmp_path / "wipe.lock").rename(tmp_path / "ambiguous-wipe.lock")
        resume.set()
        delayed.join(5)
        assert not delayed.is_alive()
        assert errors and isinstance(errors[0], SafetyError)
        assert runner._lock_fd == old_lock and getattr(runner, "_log_fd", None) == old_log
        assert spawn.call_count == 1
    finally:
        resume.set()
        delayed.join(5)
        current_lock, current_log = runner._lock_fd, getattr(runner, "_log_fd", None)
        runner._release_wipe_lock()
        for previous, current in ((old_lock, current_lock), (old_log, current_log)):
            if previous is not None and previous != current:
                os.close(previous)


class FakeProcess:
    def __init__(self):
        self.returncode = None
        self.blocked = False

    def poll(self):
        return self.returncode

    def terminate(self):
        if not self.blocked:
            self.returncode = -15

    def kill(self):
        if not self.blocked:
            self.returncode = -9

    def wait(self, timeout):
        if self.returncode is None:
            raise subprocess.TimeoutExpired("fake-engine", timeout)
        return self.returncode


def setup_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    process = FakeProcess()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: process)
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "engine.log"))
    return runner, request, process


@pytest.mark.parametrize("cancel", [False, True])
def test_log_fd_lives_until_terminal_cleanup_and_can_restart(tmp_path, monkeypatch, cancel):
    runner, request, process = setup_runner(tmp_path, monkeypatch)
    try:
        runner.start(request)
        held = runner._log_fd
        assert held is not None
        assert os.fstat(held).st_ino == runner._active_log_identity[2]
        assert runner.poll(request) is None
        with pytest.raises(SafetyError, match="already running"):
            runner.start(request)
        assert runner._log_fd == held
        if cancel:
            runner.cancel()
        else:
            (tmp_path / "engine.log").write_text(
                "********************************* Drive Status *********************************\n"
                "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
            )
            process.returncode = 0
            assert runner.poll(request).ok
        assert runner._log_fd is None
        assert runner._lock_fd is None
        with pytest.raises(OSError):
            os.fstat(held)
        runner._release_wipe_lock()  # terminal cleanup is idempotent
        process.returncode = None
        runner.start(request)
        assert runner._log_fd is not None
        assert runner.result is None
        assert (tmp_path / "engine.log").stat().st_size == 0
        assert runner.poll(request) is None
        runner.cancel()
        assert runner._log_fd is None
    finally:
        runner._release_wipe_lock()


@pytest.mark.parametrize("failure", ["known_exec", "unknown_spawn", "interrupt"])
def test_spawn_ownership_controls_retained_log_cleanup(tmp_path, monkeypatch, failure):
    runner, request, process = setup_runner(tmp_path, monkeypatch)
    error = {
        "known_exec": FileNotFoundError(2, "fake exec failure", runner.binary),
        "unknown_spawn": OSError("ambiguous parent failure"),
        "interrupt": KeyboardInterrupt(),
    }[failure]
    monkeypatch.setattr(module.subprocess, "Popen", Mock(side_effect=error))
    try:
        with pytest.raises(type(error)):
            runner.start(request)
        if failure == "known_exec":
            assert runner._log_fd is None
            assert runner.start_not_spawned()
            monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: process)
            runner.start(request)
            runner.cancel()
            assert runner._log_fd is None
        else:
            held = runner._log_fd
            assert held is not None
            os.fstat(held)
            assert not runner.start_not_spawned()
            with pytest.raises(SafetyError, match="already running"):
                runner.start(request)
            assert runner._log_fd == held
    finally:
        # No real child exists in these uncertainty fixtures.
        runner._release_wipe_lock()


def test_unconfirmed_cancel_retains_log_until_exit_is_proven(tmp_path, monkeypatch):
    runner, request, process = setup_runner(tmp_path, monkeypatch)
    try:
        runner.start(request)
        held = runner._log_fd
        process.blocked = True
        with pytest.raises(SafetyError, match="may still be erasing"):
            runner.cancel()
        assert runner._log_fd == held
        os.fstat(held)
        assert runner.result is None
        process.returncode = -15
        runner.cancel()
        assert runner._log_fd is None
        assert runner.result is not None and not runner.result.ok
        with pytest.raises(OSError):
            os.fstat(held)
    finally:
        runner._release_wipe_lock()


def test_retained_log_close_failure_is_not_retried_or_published(tmp_path, monkeypatch):
    runner, request, process = setup_runner(tmp_path, monkeypatch)
    runner.start(request)
    held = runner._log_fd
    process.returncode = 1
    close = os.close
    attempted = []

    def close_then_fail(fd):
        close(fd)
        if fd == held:
            attempted.append(fd)
            raise OSError("injected log close failure")

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "close", close_then_fail)
        with pytest.raises(SafetyError, match="cleanup"):
            runner.poll(request)
        with pytest.raises(SafetyError, match="cleanup"):
            runner._release_wipe_lock()
        with pytest.raises(SafetyError, match="cleanup"):
            runner.start(request)
    assert attempted == [held]
    assert runner._log_fd is None
    assert runner._cleanup_failed
    assert runner.result is None
