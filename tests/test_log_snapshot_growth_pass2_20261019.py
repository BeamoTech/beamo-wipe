"""The captured EOF and identity must describe the same bounded log snapshot."""

import os

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.models import MethodId, WipeRequest


COMPLETE = (
    "********************************* Drive Status *********************************\n"
    "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
).encode()
FAILURE = b"[2026/10/19 04:00:00] error: /dev/sda: >>> FAILURE! <<<\n"


@pytest.mark.parametrize("boundary", ("before_snapshot", "after_snapshot", "after_end_seek"))
@pytest.mark.parametrize("initial_size", (512, runner_module.NWIPE_COMPLETION_LOG_BYTES))
def test_growth_cannot_authenticate_a_prefix(tmp_path, monkeypatch, boundary, initial_size):
    path = tmp_path / "fake.log"
    initial = COMPLETE + b"p" * (initial_size - len(COMPLETE) - 1) + b"\n"
    path.write_bytes(initial)
    native_stat = os.fstat
    native_fdopen = os.fdopen
    fired = False
    saw_end_seek = False

    def grow():
        nonlocal fired
        assert not fired
        fired = True
        # Cross the completion read bound even from a small starting log.
        with path.open("ab") as writer:
            writer.write((b"p" * 65535 + b"\n") * 18 + FAILURE)

    class ObservedFile:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            return self.stream.fileno()

        def seek(self, *args):
            nonlocal saw_end_seek
            result = self.stream.seek(*args)
            if args == (0, os.SEEK_END):
                saw_end_seek = True
                if boundary == "after_end_seek" and not fired:
                    grow()
            return result

        def tell(self):
            return self.stream.tell()

        def read(self, *args):
            return self.stream.read(*args)

        def readline(self, *args):
            return self.stream.readline(*args)

    def fstat(fd):
        # The EOF seek remains a stable boundary if tell() is removed. Grow
        # immediately before/after the identity return, never silently stop
        # exercising the append when snapshot capture is repaired.
        if saw_end_seek and not fired and boundary == "before_snapshot":
            grow()
        result = native_stat(fd)
        if saw_end_seek and not fired and boundary == "after_snapshot":
            grow()
        return result

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

    monkeypatch.setattr(os, "fdopen", lambda *args, **kwargs: ObservedFile(native_fdopen(*args, **kwargs)))
    monkeypatch.setattr(os, "fstat", fstat)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)
    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(path))
    runner._active_request = request
    # This regression targets the terminal read rather than the preceding
    # display-only progress read, which has its own separate byte limit.
    monkeypatch.setattr(runner, "_refresh_progress", lambda *_args, **_kwargs: None)
    result = runner.poll(request)
    assert fired and saw_end_seek
    assert path.read_bytes().startswith(initial) and path.read_bytes().endswith(FAILURE)
    assert result is not None and not result.ok
    assert result.reason in {"engine_failed", "indeterminate"}
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None


@pytest.mark.parametrize("large", (False, True))
def test_unchanged_complete_and_truncated_logs_still_complete(tmp_path, large):
    path = tmp_path / "fake.log"
    path.write_bytes(((b"p" * 65535 + b"\n") * 18 if large else b"") + COMPLETE)

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(path))
    result = runner.poll(request)
    assert result is not None and result.ok
