"""Bind engine execution and active logs to the objects that passed checks.

Only copied regular files and fake process/device callbacks are used. No nwipe,
block device, mount, native inventory, or audio process can execute.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest


COMPLETE = (
    "********************************* Drive Status *********************************\n"
    "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)


class ExitedProcess:
    returncode = 0

    def poll(self):
        return self.returncode


def _engine(path: Path) -> os.stat_result:
    shutil.copyfile("/bin/true", path)
    path.chmod(0o700)
    return path.stat()


def _replacement(path: Path) -> None:
    other = path.with_name("replacement-engine")
    other.write_text("#!/bin/sh\nprintf 'nwipe version 0.42\\n'\n", encoding="utf-8")
    other.chmod(0o700)
    os.replace(other, path)


def test_version_probe_rejects_named_replacement_and_closes_descriptor(
    tmp_path, monkeypatch
):
    path = tmp_path / "nwipe"
    original = _engine(path)
    observed_fd = None

    def probe(argv, **kwargs):
        nonlocal observed_fd
        assert argv[0].startswith("/proc/self/fd/")
        observed_fd = int(argv[0].rsplit("/", 1)[1])
        assert kwargs["pass_fds"] == (observed_fd,)
        assert os.fstat(observed_fd).st_ino == original.st_ino
        assert os.pread(observed_fd, 4, 0) == b"\x7fELF"
        _replacement(path)
        assert path.stat().st_ino != original.st_ino
        assert os.fstat(observed_fd).st_ino == original.st_ino
        return subprocess.CompletedProcess(argv, 0, "nwipe version 0.42\n", "")

    monkeypatch.setattr(module.subprocess, "run", probe)
    with pytest.raises(module.SafetyError, match="changed during version check"):
        module._verify_pinned_nwipe(str(path))
    assert observed_fd is not None
    with pytest.raises(OSError):
        os.fstat(observed_fd)


@pytest.mark.parametrize("mutation", ["mode", "same_inode_bytes"])
def test_version_probe_rejects_same_inode_metadata_drift(
    tmp_path, monkeypatch, mutation
):
    path = tmp_path / "nwipe"
    _engine(path)
    observed_fd = None

    def probe(argv, **_kwargs):
        nonlocal observed_fd
        observed_fd = int(argv[0].rsplit("/", 1)[1])
        if mutation == "mode":
            path.chmod(0o744)
        else:
            before = path.stat()
            with path.open("r+b") as stream:
                stream.seek(4)
                byte = stream.read(1)
                stream.seek(4)
                stream.write(bytes([byte[0] ^ 1]))
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        return subprocess.CompletedProcess(argv, 0, "nwipe version 0.42\n", "")

    monkeypatch.setattr(module.subprocess, "run", probe)
    with pytest.raises(module.SafetyError, match="changed during version check"):
        module._verify_pinned_nwipe(str(path))
    assert observed_fd is not None
    with pytest.raises(OSError):
        os.fstat(observed_fd)


def test_runner_execs_the_descriptor_that_passed_the_version_probe(
    tmp_path, monkeypatch
):
    path = tmp_path / "nwipe"
    original = _engine(path)
    logfile = tmp_path / "engine.log"
    request = WipeRequest(
        "/dev/sda",
        MethodId.EVERYDAY,
        "/dev/sr0",
        str(logfile),
        device_rdev=1,
        device_size_bytes=1_000_000,
        boot_rdev=2,
    )
    seen = {}

    monkeypatch.setattr(module, "resolve_nwipe_binary", lambda _path: str(path))
    monkeypatch.setattr(module, "require_real_live_for_nwipe", lambda: None)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", lambda **_kw: False)
    monkeypatch.setattr(
        module, "assert_existing_is_block_device", lambda *_a, **_kw: None
    )
    monkeypatch.setattr(module, "assert_size_unchanged", lambda *_a: None)
    monkeypatch.setattr(module, "assert_local_device_transport", lambda *_a: None)
    monkeypatch.setattr(module, "assert_not_boot", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "block_rdev", lambda p: 1 if p == "/dev/sda" else 2)
    monkeypatch.setattr(module, "_recheck_identity_under_lock", lambda _request: None)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda argv, **_kw: subprocess.CompletedProcess(
            argv, 0, "nwipe version 0.42\n", ""
        ),
    )

    def spawn(argv, **kwargs):
        fd = int(argv[0].rsplit("/", 1)[1])
        seen.update(fd=fd, argv=argv, pass_fds=kwargs["pass_fds"])
        assert argv[0] == f"/proc/self/fd/{fd}"
        assert fd in kwargs["pass_fds"]
        assert os.fstat(fd).st_ino == original.st_ino
        assert os.pread(fd, 4, 0) == b"\x7fELF"
        return ExitedProcess()

    monkeypatch.setattr(module.subprocess, "Popen", spawn)
    runner = module.NwipeRunner()
    monkeypatch.setattr(runner._sleep_inhibit, "start", lambda: None)
    runner.start(request)
    assert seen["argv"][0].startswith("/proc/self/fd/")
    with pytest.raises(OSError):
        os.fstat(seen["fd"])
    result = runner.poll(request)
    assert result is not None and not result.ok


def test_verified_descriptor_closes_when_lock_acquisition_fails(
    tmp_path, monkeypatch
):
    path = tmp_path / "nwipe"
    _engine(path)
    logfile = tmp_path / "engine.log"
    request = WipeRequest(
        "/dev/sda",
        MethodId.EVERYDAY,
        "/dev/sr0",
        str(logfile),
        device_rdev=1,
        device_size_bytes=1_000_000,
        boot_rdev=2,
    )
    observed_fd = None

    monkeypatch.setattr(module, "resolve_nwipe_binary", lambda _path: str(path))
    monkeypatch.setattr(module, "require_real_live_for_nwipe", lambda: None)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", lambda **_kw: False)
    monkeypatch.setattr(
        module, "assert_existing_is_block_device", lambda *_a, **_kw: None
    )
    monkeypatch.setattr(module, "assert_size_unchanged", lambda *_a: None)
    monkeypatch.setattr(module, "assert_local_device_transport", lambda *_a: None)
    monkeypatch.setattr(module, "assert_not_boot", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "block_rdev", lambda p: 1 if p == "/dev/sda" else 2)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)

    def probe(argv, **_kwargs):
        nonlocal observed_fd
        observed_fd = int(argv[0].rsplit("/", 1)[1])
        return subprocess.CompletedProcess(argv, 0, "nwipe version 0.42\n", "")

    monkeypatch.setattr(module.subprocess, "run", probe)
    runner = module.NwipeRunner()
    monkeypatch.setattr(
        runner,
        "_acquire_wipe_lock",
        lambda _request: (_ for _ in ()).throw(module.SafetyError("lock refused")),
    )
    with pytest.raises(module.SafetyError, match="lock refused"):
        runner.start(request)
    assert observed_fd is not None
    with pytest.raises(OSError):
        os.fstat(observed_fd)


def _start_fake(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: ExitedProcess())
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    runner.start(request)
    return runner, request, logfile


def _mutate_log(logfile: Path, mutation: str) -> None:
    if mutation == "mode":
        logfile.chmod(0o644)
    else:
        os.link(logfile, logfile.with_name("exposed-engine.log"))


@pytest.mark.parametrize("mutation", ["mode", "hardlink"])
def test_private_log_drift_immediately_before_spawn_is_refused(
    tmp_path, monkeypatch, mutation
):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    logfile = tmp_path / "engine.log"
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
    runner = module.NwipeRunner(binary=str(tmp_path / "fake-engine"))
    spawned = []
    original_lock_check = module._assert_named_wipe_lock

    def mutate_after_lock_check(fd, path):
        original_lock_check(fd, path)
        if logfile.exists():
            _mutate_log(logfile, mutation)

    monkeypatch.setattr(module, "_assert_named_wipe_lock", mutate_after_lock_check)
    monkeypatch.setattr(
        module.subprocess, "Popen", lambda *_a, **_kw: spawned.append(1)
    )
    with pytest.raises(module.SafetyError, match="Log file changed before launch"):
        runner.start(request)
    assert spawned == [] and runner.start_not_spawned()


@pytest.mark.parametrize("mutation", ["mode", "hardlink"])
def test_private_log_drift_before_terminal_read_is_indeterminate(
    tmp_path, monkeypatch, mutation
):
    runner, request, logfile = _start_fake(tmp_path, monkeypatch)
    logfile.write_text(COMPLETE, encoding="utf-8")
    logfile.chmod(0o600)
    _mutate_log(logfile, mutation)
    result = runner.poll(request)
    assert result is not None and not result.ok
    assert result.reason == "indeterminate"


@pytest.mark.parametrize("mutation", ["mode", "hardlink"])
def test_private_log_drift_during_read_is_indeterminate(
    tmp_path, monkeypatch, mutation
):
    runner, request, logfile = _start_fake(tmp_path, monkeypatch)
    logfile.write_text(COMPLETE, encoding="utf-8")
    logfile.chmod(0o600)
    native_fdopen = os.fdopen
    mutated = False

    class MutatingRead:
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
            return self.stream.seek(*args)

        def read(self, *args):
            nonlocal mutated
            if not mutated:
                mutated = True
                _mutate_log(logfile, mutation)
            return self.stream.read(*args)

    monkeypatch.setattr(
        os,
        "fdopen",
        lambda *args, **kwargs: MutatingRead(native_fdopen(*args, **kwargs)),
    )
    result = runner.poll(request)
    assert mutated
    assert result is not None and not result.ok
    assert result.reason == "indeterminate"


def test_unchanged_private_log_still_completes(tmp_path, monkeypatch):
    runner, request, logfile = _start_fake(tmp_path, monkeypatch)
    logfile.write_text(COMPLETE, encoding="utf-8")
    logfile.chmod(0o600)
    result = runner.poll(request)
    assert result is not None and result.ok and result.reason == "completed"
