"""A log replaced by a FIFO cannot strand pre-exec refusal or wipe ownership."""

import multiprocessing
import os
from pathlib import Path
import stat

import pytest


def _exercise_log(folder, route, replace, reader_present, ready, done, outcomes):
    from beamo_wipe import nwipe_runner as module, safety
    from beamo_wipe.models import MethodId, WipeRequest

    directory = Path(folder)
    path = directory / "engine.log"
    prior = directory / "prior.log"
    runner = module.NwipeRunner(binary=str(directory / "fake-engine"))
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(path))
    original_guard = safety.assert_log_not_on_target
    original_truncate = module.truncate_log_file
    original_open, original_close = os.open, os.close
    opened = set()
    armed = changed = False
    fifo_reader = None
    spawns = []

    class Process:
        returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def wait(self, timeout):
            return self.returncode

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Native device, inventory or engine action reached")

    def open_owned(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        # Track the pre-exec lock/log ownership path. Subsequent log readers
        # transfer their handle to fdopen(), whose C-level close is separate.
        if armed:
            opened.add(fd)
        return fd

    def close_owned(fd):
        original_close(fd)
        opened.discard(fd)

    def guard(log, target, **kwargs):
        nonlocal changed, fifo_reader
        original_guard(log, target, **kwargs)
        if armed and not changed:
            changed = True
            if route == "runner":
                assert runner._lock_fd is not None
            assert Path(log).is_file()
            if replace:
                Path(log).rename(prior)
                os.mkfifo(log, 0o600)
                if reader_present:
                    fifo_reader = os.open(log, os.O_RDONLY | os.O_NONBLOCK)
            ready.set()

    def truncate(*args, **kwargs):
        nonlocal armed
        armed = True
        try:
            return original_truncate(*args, **kwargs)
        finally:
            armed = False

    def spawn(*_args, **_kwargs):
        spawns.append(True)
        return Process()

    def invoke():
        if route == "runner":
            runner.start(request)
            runner.cancel()
            assert runner._proc is None
            assert runner._lock_fd is None and runner._log_fd is None
        else:
            retained = safety.truncate_log_file(
                str(path), request.device, retain_fd=route == "retain"
            )
            if route == "retain":
                assert retained is not None
                assert stat.S_ISREG(os.fstat(retained).st_mode)
                assert os.fstat(retained).st_size == 0
                os.close(retained)
            else:
                assert retained is None

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("BEAMO_WIPE_DRY_RUN", "1")
        patch.delenv("BEAMO_WIPE_LIVE", raising=False)
        patch.setattr(safety, "default_log_dir", lambda: directory)
        patch.setattr(safety, "assert_log_not_on_target", guard)
        patch.setattr(safety.os, "open", open_owned)
        patch.setattr(safety.os, "close", close_owned)
        patch.setattr(module, "truncate_log_file", truncate)
        patch.setattr(module, "assert_not_boot", lambda *_a, **_kw: None)
        patch.setattr(module.subprocess, "Popen", spawn)
        patch.setattr(module.subprocess, "run", forbidden)
        patch.setattr(module, "pinned_nwipe_already_running", forbidden)
        patch.setattr(module, "_try_log_diag", lambda *_a: None)
        patch.setattr("beamo_wipe.discover.run_lsblk", forbidden)
        patch.setattr("beamo_wipe.discover.read_mount_sources", forbidden)
        patch.setattr("beamo_wipe.discover.read_cmdline", forbidden)
        try:
            # Direct calls also arm the real path guard/open boundary.
            armed = True
            if replace:
                with pytest.raises(safety.SafetyError):
                    invoke()
                assert not spawns
                assert runner.start_not_spawned()
                assert not opened or opened == {fifo_reader}
                if fifo_reader is not None:
                    os.close(fifo_reader)
                    fifo_reader = None
                assert prior.read_bytes() == b"prior log bytes"
                path.unlink()
                path.write_bytes(b"retry log bytes")
                invoke()
            else:
                invoke()
            assert path.read_bytes() == b""
            assert len(spawns) == (1 if route == "runner" else 0)
            assert not opened
            outcome = {"ok": True}
        except BaseException as exc:
            outcome = {"ok": False, "error": type(exc).__name__, "detail": str(exc)}
        finally:
            if fifo_reader is not None:
                os.close(fifo_reader)
            runner._release_wipe_lock()
    outcomes.put(outcome)
    done.set()


@pytest.mark.parametrize("route", ["runner", "close", "retain"])
@pytest.mark.parametrize(
    "replace,reader_present",
    [(False, False), (True, False), (True, True)],
    ids=["regular", "fifo-alone", "fifo-with-reader"],
)
def test_log_refusal_and_retry_do_not_require_a_fifo_reader(
    tmp_path, route, replace, reader_present
):
    path = tmp_path / "engine.log"
    path.write_bytes(b"prior log bytes")
    path.chmod(0o600)
    context = multiprocessing.get_context("spawn")
    ready, done, outcomes = context.Event(), context.Event(), context.Queue()
    child = context.Process(
        target=_exercise_log,
        args=(str(tmp_path), route, replace, reader_present, ready, done, outcomes),
    )
    child.start()
    parent_reader = None
    try:
        assert ready.wait(5), "Owned helper did not reach the validated log boundary"
        refused_without_reader = done.wait(1)
        if not refused_without_reader and replace and not reader_present:
            # Release only this owned FIFO so the old-code failure can clean
            # up naturally. No real engine or host device is involved.
            parent_reader = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        child.join(5)
        assert not child.is_alive()
        assert child.exitcode == 0
        outcome = outcomes.get(timeout=2)
        assert outcome["ok"], outcome
        assert refused_without_reader, "Log refusal blocked waiting for a FIFO reader"
    finally:
        if parent_reader is not None:
            os.close(parent_reader)
        if child.is_alive():
            child.terminate()
            child.join(5)
        outcomes.close()
