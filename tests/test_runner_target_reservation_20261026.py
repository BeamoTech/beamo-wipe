"""The confirmed disk stays reserved from final rediscovery until nwipe exits.

nwipe opens its positional target by name after its own scan and PRNG
selection. A read-only handle held by the runner keeps the kernel from
reassigning that name to a different disk in between. Every boundary here
is fake: no block device, disk, nwipe or systemd process is opened.
"""

import errno
import os
import stat
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import SafetyError


TARGET_RDEV = 0x0810
BOOT_RDEV = 0x0820


def _is_open(fd, _fstat=os.fstat):
    # Bound at import: tests below replace os.fstat for simulated devices.
    try:
        _fstat(fd)
    except OSError as exc:
        assert exc.errno == errno.EBADF
        return False
    return True


def _request(tmp_path, device="/dev/vda", device_rdev=TARGET_RDEV):
    return WipeRequest(
        device, MethodId.EVERYDAY, "/dev/sr0", str(tmp_path / "engine.log"),
        device_rdev=device_rdev, device_size_bytes=500_000_000_000, boot_rdev=BOOT_RDEV,
    )


class FakeEngine:
    pid = 4242

    def __init__(self):
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode

    def send_signal(self, _sig):
        pass


def _fake_native_boundaries(tmp_path, monkeypatch):
    """Reach the real-engine launch branch with every native boundary faked."""
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr(module, "resolve_nwipe_binary", lambda _b: "/usr/lib/beamo-wipe/nwipe")
    monkeypatch.setattr(module, "require_real_live_for_nwipe", lambda: None)
    monkeypatch.setattr(module, "pinned_nwipe_already_running", lambda **_kw: False)
    monkeypatch.setattr(module, "_verify_pinned_nwipe", lambda _path: None)
    monkeypatch.setattr(module, "assert_existing_is_block_device", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "assert_not_boot", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "assert_size_unchanged", lambda *_a: None)
    monkeypatch.setattr(module, "assert_local_device_transport", lambda _path: None)
    monkeypatch.setattr(module, "assert_log_not_on_target", lambda *_a: None)
    monkeypatch.setattr(
        module, "block_rdev", lambda path: TARGET_RDEV if path == "/dev/vda" else BOOT_RDEV
    )


@pytest.fixture
def real_engine_boundaries(tmp_path, monkeypatch):
    _fake_native_boundaries(tmp_path, monkeypatch)
    events = []
    held = []

    def reserve(request):
        events.append(("reserve", request.device))
        fd = os.open(os.devnull, os.O_RDONLY | os.O_CLOEXEC)
        held.append(fd)
        return fd

    def recheck(request):
        # Rediscovery must observe a name that is already reserved.
        assert held and _is_open(held[-1])
        events.append(("recheck", request.device))

    monkeypatch.setattr(module, "_reserve_target_under_lock", reserve)
    monkeypatch.setattr(module, "_recheck_identity_under_lock", recheck)
    runner = module.NwipeRunner()
    runner._sleep_inhibit = Mock()
    yield SimpleNamespace(runner=runner, events=events, held=held)
    for fd in held:
        if _is_open(fd):
            os.close(fd)


def test_reservation_precedes_rediscovery_and_outlives_launch(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries
    engine = FakeEngine()
    launches = []

    def popen(argv, **kwargs):
        reserved = env.runner._target_fd
        assert reserved is not None and _is_open(reserved)
        assert reserved not in kwargs.get("pass_fds", ())
        assert not os.get_inheritable(reserved)
        env.events.append(("launch", argv[-1]))
        launches.append(kwargs)
        return engine

    monkeypatch.setattr(module.subprocess, "Popen", popen)
    request = _request(tmp_path)
    env.runner.start(request)
    assert env.events == [
        ("reserve", "/dev/vda"), ("recheck", "/dev/vda"), ("launch", "/dev/vda"),
    ]
    reserved = env.runner._target_fd
    assert reserved == env.held[0] and _is_open(reserved)

    # Still running: the name stays reserved while nwipe may not have opened it.
    assert env.runner.poll(request) is None
    assert env.runner._target_fd == reserved and _is_open(reserved)

    engine.returncode = 1
    result = env.runner.poll(request)
    assert result is not None and not result.ok
    assert env.runner._target_fd is None
    assert not _is_open(reserved)


def test_cancel_releases_reservation_only_after_engine_exit(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries
    engine = FakeEngine()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: engine)
    request = _request(tmp_path)
    env.runner.start(request)
    reserved = env.runner._target_fd
    assert _is_open(reserved)
    env.runner.cancel()
    assert engine.terminated
    assert env.runner.result is not None and env.runner.result.reason == "cancelled"
    assert env.runner._target_fd is None and not _is_open(reserved)


def test_unconfirmed_stop_keeps_reservation(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries

    class StuckEngine(FakeEngine):
        def terminate(self):
            self.terminated = True

        def kill(self):
            pass

        def wait(self, timeout=None):
            raise module.subprocess.TimeoutExpired("nwipe", timeout)

    engine = StuckEngine()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: engine)
    request = _request(tmp_path)
    env.runner.start(request)
    reserved = env.runner._target_fd
    with pytest.raises(SafetyError, match="may still be erasing"):
        env.runner.cancel()
    assert env.runner._target_fd == reserved and _is_open(reserved)
    engine.returncode = -9
    assert env.runner.poll(request) is not None
    assert env.runner._target_fd is None and not _is_open(reserved)


def test_reservation_refusal_prevents_launch(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries
    spawn = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", spawn)

    def refuse(_request):
        env.events.append(("reserve", "refused"))
        raise SafetyError("Disk identity changed. Refusing to erase.")

    monkeypatch.setattr(module, "_reserve_target_under_lock", refuse)
    with pytest.raises(SafetyError, match="identity changed"):
        env.runner.start(_request(tmp_path))
    assert env.events == [("reserve", "refused")]
    spawn.assert_not_called()
    assert env.runner.start_not_spawned()


def test_rediscovery_failure_after_reservation_closes_handle(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries
    spawn = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", spawn)

    def changed(_request):
        raise SafetyError("Disk identity changed. Refusing to erase.")

    monkeypatch.setattr(module, "_recheck_identity_under_lock", changed)
    with pytest.raises(SafetyError, match="identity changed"):
        env.runner.start(_request(tmp_path))
    spawn.assert_not_called()
    assert len(env.held) == 1 and not _is_open(env.held[0])
    assert env.runner.start_not_spawned()


def test_held_reservation_blocks_a_second_start(tmp_path, monkeypatch, real_engine_boundaries):
    env = real_engine_boundaries
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_kw: FakeEngine())
    request = _request(tmp_path)
    env.runner.start(request)
    with env.runner._lock:
        env.runner._proc = None  # only the reservation remains registered
    with pytest.raises(SafetyError, match="already running"):
        env.runner.start(request)
    assert not env.runner.start_not_spawned()


def test_launch_holds_a_read_only_handle_to_the_confirmed_disk(tmp_path, monkeypatch):
    """Only the device open is simulated; the production helper runs."""
    _fake_native_boundaries(tmp_path, monkeypatch)
    real_open, real_fstat = os.open, os.fstat
    device_fds = {}

    def fake_open(path, flags, *args, **kwargs):
        if path == "/dev/vda":
            fd = real_open(os.devnull, os.O_RDONLY | os.O_CLOEXEC)
            device_fds[fd] = flags
            return fd
        return real_open(path, flags, *args, **kwargs)

    def fake_fstat(fd):
        if fd in device_fds:
            return SimpleNamespace(st_mode=stat.S_IFBLK | 0o660, st_rdev=TARGET_RDEV)
        return real_fstat(fd)

    monkeypatch.setattr(module.os, "open", fake_open)
    monkeypatch.setattr(module.os, "fstat", fake_fstat)
    order = []
    monkeypatch.setattr(
        module, "_recheck_identity_under_lock",
        lambda _r: order.append(("recheck", sorted(fd for fd in device_fds if _is_open(fd)))),
    )
    engine = FakeEngine()

    def popen(argv, **kwargs):
        held = [fd for fd in device_fds if _is_open(fd)]
        order.append(("launch", held))
        assert held, "the confirmed disk must be held open when nwipe starts"
        assert not set(held) & set(kwargs.get("pass_fds", ()))
        return engine

    monkeypatch.setattr(module.subprocess, "Popen", popen)
    runner = module.NwipeRunner()
    runner._sleep_inhibit = Mock()
    request = _request(tmp_path)
    runner.start(request)
    (fd, flags), = device_fds.items()
    assert order == [("recheck", [fd]), ("launch", [fd])]
    assert flags & os.O_ACCMODE == os.O_RDONLY and not flags & os.O_EXCL
    engine.returncode = 0
    assert runner.poll(request) is not None
    assert not _is_open(fd)


# ---------- the reservation helper itself ----------

def _open_fds():
    return set(os.listdir("/proc/self/fd"))


@pytest.mark.parametrize("kind", ["missing", "regular", "character"])
def test_reservation_refuses_anything_but_a_block_device(tmp_path, kind):
    path = {
        "missing": str(tmp_path / "absent"),
        "regular": str(tmp_path / "file"),
        "character": os.devnull,
    }[kind]
    if kind == "regular":
        (tmp_path / "file").write_bytes(b"\0" * 512)
    before = _open_fds()
    with pytest.raises(SafetyError, match="identity changed"):
        module._reserve_target_under_lock(_request(tmp_path, device=path))
    assert _open_fds() == before


def test_reservation_refuses_symlinked_device_name(tmp_path):
    link = tmp_path / "vda"
    link.symlink_to(os.devnull)
    with pytest.raises(SafetyError, match="identity changed"):
        module._reserve_target_under_lock(_request(tmp_path, device=str(link)))


def _fake_block_stat(monkeypatch, rdev):
    real_fstat = os.fstat
    faked = set()
    real_open = os.open
    seen_flags = []

    def fake_open(path, flags, *args):
        fd = real_open(os.devnull, os.O_RDONLY | os.O_CLOEXEC)
        faked.add(fd)
        seen_flags.append(flags)
        return fd

    def fake_fstat(fd):
        if fd in faked:
            return SimpleNamespace(st_mode=stat.S_IFBLK | 0o660, st_rdev=rdev)
        return real_fstat(fd)

    monkeypatch.setattr(module.os, "open", fake_open)
    monkeypatch.setattr(module.os, "fstat", fake_fstat)
    return seen_flags


def test_reservation_is_read_only_non_exclusive_and_not_inherited(tmp_path, monkeypatch):
    seen_flags = _fake_block_stat(monkeypatch, TARGET_RDEV)
    fd = module._reserve_target_under_lock(_request(tmp_path))
    monkeypatch.undo()
    try:
        (flags,) = seen_flags
        assert flags & os.O_ACCMODE == os.O_RDONLY
        assert not flags & (os.O_EXCL | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        assert flags & os.O_CLOEXEC and flags & os.O_NOFOLLOW and flags & os.O_NOCTTY
        assert not os.get_inheritable(fd)
    finally:
        os.close(fd)


@pytest.mark.parametrize("held_rdev,confirmed_rdev", [
    (0x0830, TARGET_RDEV),  # a different disk now has this name
    (TARGET_RDEV, 0),       # the confirmation carried no device number
    (TARGET_RDEV, None),
])
def test_reservation_refuses_unconfirmed_device_number(tmp_path, monkeypatch, held_rdev, confirmed_rdev):
    _fake_block_stat(monkeypatch, held_rdev)
    request = _request(tmp_path, device_rdev=confirmed_rdev)
    before = _open_fds()
    with pytest.raises(SafetyError, match="identity changed"):
        module._reserve_target_under_lock(request)
    monkeypatch.undo()
    assert _open_fds() == before
