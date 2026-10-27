"""Fake-only regression for inhibitor startup preceding final disk rediscovery.

Handoff BW-INHIBITOR-ORDER-20261023 / Codex test sub-agent: LOCAL UNRUN.
Repo BeamoTech/beamo-wipe, shared Windows checkout, parent HEAD 9764d93,
branch fix/windows-development-setup-20261022, dirty source. Only this new
file is authorized here. Root must independently run these cases before any
production edit, then repeat against the final source. No test, engine,
inventory, child process, network, staging or publication was run by the author.
The old ordering should fail the three mutation cases and pass the control.
This synthetic ordering regression is not a physical hotplug reproduction;
even moving startup cannot eliminate the residual rediscovery-to-exec window.
"""

from __future__ import annotations

import builtins
from dataclasses import replace
import errno
import importlib
import io
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe import safety
from beamo_wipe.models import DiscoveryResult, Disk, DiskKind, MethodId, WipeRequest


class _ExitedProcess:
    returncode = 0

    def poll(self):
        return self.returncode


def _disk(path, serial, *, boot=False):
    return Disk(
        path=path,
        name=Path(path).name,
        model="Synthetic fixture",
        serial=serial,
        size_bytes=1_000_000,
        size_gb_label="0",
        kind=DiskKind.HDD,
        bus="sata",
        label="",
        is_boot=boot,
    )


def _inventory(target, boot):
    return DiscoveryResult(
        disks=(target, boot),
        selectable=(target,),
        boot=boot,
        boot_identified=True,
    )


@pytest.fixture
def launch_case(tmp_path, monkeypatch):
    # The basename selects the real-engine branch; its bytes are never executed.
    engine = tmp_path / "nwipe"
    shutil.copyfile("/bin/true", engine)
    engine.chmod(0o700)
    engine_stat = engine.stat()
    target = _disk("/dev/sda", "TARGET-A")
    boot = _disk("/dev/sdb", "BOOT-A", boot=True)
    case = SimpleNamespace(
        target=target,
        boot=boot,
        current=_inventory(target, boot),
        mutate=lambda: None,
        events=[],
        spawns=[],
        scans=[],
        probe_fds=[],
        lock_fds=[],
        log_fds=[],
    )

    def guarded(original):
        def call(path, *args, **kwargs):
            if isinstance(path, (str, bytes, os.PathLike)):
                text = os.fsdecode(path)
                assert not any(
                    text == root or text.startswith(root + "/")
                    for root in ("/dev", "/proc", "/sys")
                ), f"Unexpected native device/inventory access: {text}"
            return original(path, *args, **kwargs)

        return call

    native_realpath = os.path.realpath

    def fake_device_realpath(path, *args, **kwargs):
        text = os.fsdecode(path)
        if text.startswith("/dev/"):
            assert text in (target.path, boot.path)
            return text
        return native_realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_device_realpath)
    for name in ("open", "stat", "lstat", "readlink", "listdir", "scandir"):
        monkeypatch.setattr(os, name, guarded(getattr(os, name)))
    monkeypatch.setattr(builtins, "open", guarded(builtins.open))
    monkeypatch.setattr(io, "open", guarded(io.open))

    def device_check(path, **_kwargs):
        assert path in (target.path, boot.path)

    def size_check(path, size):
        assert (path, size) == (target.path, target.size_bytes)

    def distinct_check(device, boot_device, **_kwargs):
        assert (device, boot_device) == (target.path, boot.path)

    monkeypatch.setattr(module, "resolve_nwipe_binary", lambda _path: str(engine))
    monkeypatch.setattr(module, "require_real_live_for_nwipe", lambda: None)
    monkeypatch.setattr(module, "assert_existing_is_block_device", device_check)
    monkeypatch.setattr(module, "assert_size_unchanged", size_check)
    monkeypatch.setattr(module, "assert_local_device_transport", device_check)
    monkeypatch.setattr(safety, "assert_local_device_transport", device_check)
    monkeypatch.setattr(module, "assert_not_boot", distinct_check)
    monkeypatch.setattr(
        module, "block_rdev", lambda path: {target.path: 1, boot.path: 2}[path]
    )
    monkeypatch.setattr(safety, "default_log_dir", lambda: tmp_path)
    monkeypatch.setattr(safety, "_log_filesystem_is_target", lambda *_a: False)

    request = WipeRequest(
        device=target.path,
        method=MethodId.EVERYDAY,
        boot_device=boot.path,
        logfile=str(tmp_path / "engine.log"),
        device_rdev=1,
        device_size_bytes=target.size_bytes,
        boot_rdev=2,
        device_identity=safety.disk_identity(target),
        boot_identity=safety.disk_identity(boot),
        inventory_identity=tuple(
            sorted(safety.disk_identity(disk) for disk in (target, boot))
        ),
    )
    runner = module.NwipeRunner()
    case.runner, case.request = runner, request

    def discover():
        # Keep _recheck_identity_under_lock and assert_rediscovered_identity real.
        assert runner._lock_fd is not None
        case.events.append("discover")
        case.scans.append(case.current)
        return case.current

    monkeypatch.setattr(
        importlib.import_module("beamo_wipe.discover"), "discover", discover
    )

    def external_process_probe(**_kwargs):
        case.events.append("process-probe")
        return False

    monkeypatch.setattr(module, "pinned_nwipe_already_running", external_process_probe)

    def version_probe(argv, **kwargs):
        assert len(argv) == 2 and argv[1] == "-V"
        fd = int(argv[0].removeprefix("/proc/self/fd/"))
        assert argv[0] == f"/proc/self/fd/{fd}"
        assert kwargs["pass_fds"] == (fd,)
        assert os.fstat(fd).st_ino == engine_stat.st_ino
        case.probe_fds.append(fd)
        return subprocess.CompletedProcess(argv, 0, "nwipe version 0.42\n", "")

    def fake_popen(argv, **kwargs):
        case.spawns.append((argv, kwargs))
        case.events.append("engine-popen")
        assert len(case.probe_fds) == 1
        fd = case.probe_fds[0]
        assert argv[0] == f"/proc/self/fd/{fd}"
        assert fd in kwargs["pass_fds"]
        assert runner._lock_fd in kwargs["pass_fds"]
        assert os.fstat(fd).st_ino == engine_stat.st_ino
        return _ExitedProcess()

    monkeypatch.setattr(module.subprocess, "run", version_probe)
    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)

    acquire = runner._acquire_wipe_lock
    truncate = module.truncate_log_file

    def acquire_and_record(req):
        acquire(req)
        case.lock_fds.append(runner._lock_fd)

    def truncate_and_record(*args, **kwargs):
        fd = truncate(*args, **kwargs)
        case.log_fds.append(fd)
        return fd

    monkeypatch.setattr(runner, "_acquire_wipe_lock", acquire_and_record)
    monkeypatch.setattr(module, "truncate_log_file", truncate_and_record)

    def inhibitor_start():
        assert runner._lock_fd is not None
        case.events.append("inhibitor-start")
        case.mutate()

    monkeypatch.setattr(runner._sleep_inhibit, "start", inhibitor_start)
    monkeypatch.setattr(
        runner._sleep_inhibit, "stop", lambda: case.events.append("inhibitor-stop")
    )
    try:
        yield case
    finally:
        # Even an expected red regression leaves only closed regular-file FDs.
        runner._proc = None
        runner._active_request = None
        runner._release_wipe_lock()


def _assert_closed(fd):
    assert fd is not None
    with pytest.raises(OSError) as caught:
        os.fstat(fd)
    assert caught.value.errno == errno.EBADF


def _assert_refusal_cleanup(case):
    assert case.runner.start_not_spawned()
    assert len(case.probe_fds) == len(case.lock_fds) == len(case.log_fds) == 1
    for fd in (*case.probe_fds, *case.lock_fds, *case.log_fds):
        _assert_closed(fd)
    assert "inhibitor-stop" in case.events
    # Prove that the actual fixture lock can be acquired again, not just cleared
    # in Python state. This opens only a regular file in pytest's private tmpdir.
    with open(Path(case.request.logfile).parent / "wipe.lock", "rb") as stream:
        module.fcntl.flock(stream.fileno(), module.fcntl.LOCK_EX | module.fcntl.LOCK_NB)
        module.fcntl.flock(stream.fileno(), module.fcntl.LOCK_UN)


@pytest.mark.parametrize("mutation", ["target_serial", "mounted", "boot_serial"])
def test_inhibitor_inventory_change_is_refused_before_engine_popen(
    launch_case, mutation
):
    case = launch_case

    def mutate():
        target, boot = case.target, case.boot
        if mutation == "target_serial":
            target = replace(target, serial="TARGET-B")
        elif mutation == "mounted":
            target = replace(target, mountpoints=("/mnt/newly-mounted",))
        else:
            boot = replace(boot, serial="BOOT-B")
        assert target.path == case.request.device
        assert target.size_bytes == case.request.device_size_bytes
        assert boot.path == case.request.boot_device
        case.current = _inventory(target, boot)

    case.mutate = mutate
    message = (
        "Boot device identity changed"
        if mutation == "boot_serial"
        else "Disk identity changed"
    )
    with pytest.raises(module.SafetyError, match=message):
        case.runner.start(case.request)
    assert case.spawns == []
    assert case.scans and case.scans[-1] is case.current
    assert case.events.index("inhibitor-start") < case.events.index("discover")
    _assert_refusal_cleanup(case)


def test_unchanged_inventory_still_launches_only_the_fake_engine(launch_case):
    case = launch_case
    case.runner.start(case.request)
    assert len(case.spawns) == 1
    assert case.scans == [case.current]
    assert case.events.count("inhibitor-start") == 1
    assert case.events.count("process-probe") == 2
    # The final external-engine probe must remain after both optional startup
    # and rediscovery, even though this unchanged control tolerates old ordering.
    final_probe = len(case.events) - 1 - case.events[::-1].index("process-probe")
    assert final_probe > case.events.index("inhibitor-start")
    assert final_probe > case.events.index("discover")
    assert final_probe < case.events.index("engine-popen")
    _assert_closed(case.probe_fds[0])
    assert case.runner._lock_fd == case.lock_fds[0]
    assert case.runner._log_fd == case.log_fds[0]
