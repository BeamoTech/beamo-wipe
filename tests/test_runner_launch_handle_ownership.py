"""Exact-source launch ownership regressions, portable without POSIX imports.

Only selected, unmodified AST definitions from the adjacent runner are executed.
Every descriptor, flock, process, disk and runtime safety boundary is fake. Copy
this module with src/beamo_wipe/nwipe_runner.py to run outside root conftest.
"""

import ast
from contextlib import contextmanager
import hashlib
from pathlib import Path
import posixpath
import stat
import sys
from types import MethodType, ModuleType, SimpleNamespace as NS

import pytest


SOURCE = Path(__file__).parents[1] / "src/beamo_wipe/nwipe_runner.py"
TREE = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
ENGINE_PATH = "/inert/nwipe"
LOCK_PATH = "/inert/wipe.lock"
LOG_PATH = "/inert/log"
ELF = b"\x7fELF" + b"inert-engine"


class Refusal(RuntimeError):
    pass


class FakeTimeout(TimeoutError):
    pass


class FakeMutex:
    """The synchronous start method needs no real thread or OS lock."""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _definitions():
    names = {
        "_PinnedEngine", "_close_pinned_engine", "_engine_signature",
        "_engine_digest", "_validate_nwipe_stat", "_stat_nwipe_binary",
        "_open_nwipe_binary_safe", "assert_nwipe_binary_safe",
        "_verify_pinned_nwipe", "_assert_named_wipe_lock",
    }
    nodes = [node for node in TREE.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))
             and node.name in names]
    runner = next(node for node in TREE.body
                  if isinstance(node, ast.ClassDef) and node.name == "NwipeRunner")
    methods = {"start", "start_not_spawned", "_acquire_wipe_lock", "_release_wipe_lock"}
    nodes.extend(node for node in runner.body
                 if isinstance(node, ast.FunctionDef) and node.name in methods)
    # Retain exact bodies/locations, including exception and acquisition scopes.
    future = ast.parse("from __future__ import annotations").body
    return compile(ast.Module(body=future + nodes, type_ignores=[]), str(SOURCE), "exec")


class Harness:
    def __init__(self, monkeypatch):
        self.events = []
        self.handles = {}
        self.opened = []
        self.closes = []
        self.closed_owners = []
        self.faults = {}
        self.close_error = None
        self.next_fd = 7001
        self.magic = ELF
        self.stage = "normal"
        self.primary = Refusal("inert primary")
        self.run_error = None
        self.run_result = NS(returncode=0, stdout="nwipe version 0.42\n", stderr="")
        self.probes = []
        self.spawns = []
        self.probe_count = 0
        self.child = NS(pid=65001)
        self.engine_stat = NS(st_mode=stat.S_IFREG | 0o500, st_uid=0, st_nlink=1,
                              st_dev=3, st_ino=5, st_size=len(ELF),
                              st_mtime_ns=7, st_ctime_ns=11)
        self.lock_stat = NS(**vars(self.engine_stat))
        self.lock_stat.st_mode = stat.S_IFREG | 0o600
        self.lock_stat.st_ino = 13
        self.log_stat = NS(**vars(self.lock_stat))
        self.log_stat.st_ino = 17
        self.named_engine_stat = self.engine_stat
        self.named_lock_stat = self.lock_stat
        self.os = NS(open=self.open, close=self.close, fstat=self.fstat,
                     lstat=self.lstat, pread=self.pread, geteuid=lambda: 0,
                     getuid=lambda: 0, getpid=lambda: 65000, path=posixpath,
                     O_RDONLY=1, O_RDWR=2, O_NOFOLLOW=4, O_CREAT=8)
        self.fcntl = NS(flock=self.flock, LOCK_EX=1, LOCK_NB=2, LOCK_UN=4)
        self.subprocess = NS(run=self.run, Popen=self.popen, DEVNULL=-9001,
                             TimeoutExpired=FakeTimeout)
        self.env = dict(os=self.os, fcntl=self.fcntl, subprocess=self.subprocess,
                        stat=stat, hashlib=hashlib, SafetyError=Refusal,
                        NWIPE_PINNED_VERSION="0.42", NWIPE_VERSION_TIMEOUT_S=5,
                        NWIPE_CLEAN_ENV={"PATH": "/inert/bin"},
                        nwipe_version_is_pinned=lambda text: text == "nwipe version 0.42\n",
                        _try_log_diag=lambda *args: self.events.append(("diag", *args)))
        exec(_definitions(), self.env)  # noqa: S102 - checked-in AST, fake OS/process boundaries
        self.env["_ORIGINAL_ASSERT_NWIPE_BINARY_SAFE"] = self.env["assert_nwipe_binary_safe"]
        actual_named_check = self.env["_assert_named_wipe_lock"]

        def named_check(*args):
            actual_named_check(*args)
            self.events.append(("named-lock",))

        self.env["_assert_named_wipe_lock"] = named_check
        # This is the only product import inside the extracted methods.
        safety = ModuleType("beamo_wipe.safety")
        safety.default_log_dir = lambda: "/inert"
        monkeypatch.setitem(sys.modules, "beamo_wipe.safety", safety)
        self.request = NS(device="/dev/inert-target", boot_device="/dev/inert-boot",
                          logfile=LOG_PATH, device_size_bytes=1000,
                          device_rdev=23, boot_rdev=29)
        self.owner = NS(binary=ENGINE_PATH, _lock=FakeMutex(), _cleanup_failed=False,
                        _proc=None, _lock_fd=None, _lock_path="", _log_fd=None,
                        _progress_read_seq=0, _spawned_this_attempt=False,
                        _sleep_inhibit=NS(start=lambda: self.events.append(("inhibit-start",)),
                                          stop=lambda: self.events.append(("inhibit-stop",))))
        for name in ("start", "start_not_spawned", "_acquire_wipe_lock", "_release_wipe_lock"):
            setattr(self.owner, name, MethodType(self.env[name], self.owner))

    def fail_at(self, point):
        if point in self.faults:
            raise self.faults[point]

    def allocate(self, kind):
        fd = self.next_fd
        self.next_fd += 1
        self.handles[fd] = kind
        self.opened.append((fd, kind))
        return fd

    def open(self, path, flags, *mode):
        kind = {ENGINE_PATH: "engine", LOCK_PATH: "lock"}[path]
        self.events.append(("open", kind, flags, mode))
        self.fail_at("open-" + kind)
        return self.allocate(kind)

    def close(self, fd):
        self.closes.append(fd)
        self.closed_owners.append(self.handles.get(fd, "never-opened"))
        # Immediate reuse makes a second close observable even after an error.
        self.handles[fd] = "unrelated-reused-descriptor"
        self.events.append(("close", fd))
        if self.close_error is not None:
            raise self.close_error

    def fstat(self, fd):
        kind = self.handles[fd]
        self.events.append(("fstat", kind))
        self.fail_at("fstat-" + kind)
        return {"engine": self.engine_stat, "lock": self.lock_stat,
                "log": self.log_stat}[kind]

    def lstat(self, path):
        self.events.append(("lstat", path))
        self.fail_at("lstat-" + path)
        if path == LOG_PATH and self.stage == "preexec-log":
            raise self.primary
        return {ENGINE_PATH: self.named_engine_stat, LOCK_PATH: self.named_lock_stat,
                LOG_PATH: self.log_stat}[path]

    def pread(self, fd, count, offset):
        assert self.handles[fd] == "engine"
        assert 0 < count <= 1024 * 1024 and 0 <= offset <= len(ELF)
        self.fail_at("pread-engine")
        return self.magic[offset:offset + count]

    def flock(self, fd, flags):
        assert self.handles[fd] == "lock"
        self.events.append(("flock", fd, flags))
        self.fail_at("flock")

    def run(self, argv, **kwargs):
        self.probes.append((argv, kwargs))
        if self.run_error is not None:
            raise self.run_error
        return self.run_result

    def popen(self, argv, **kwargs):
        self.spawns.append((argv[:], kwargs))
        self.events.append(("spawn",))
        if self.stage == "spawn":
            raise self.primary
        return self.child

    def open_engine(self):
        return self.env["_open_nwipe_binary_safe"](ENGINE_PATH)

    def prepare_start(self):
        def check(stage):
            def operation(*_args, **_kwargs):
                self.events.append((stage,))
                if self.stage == stage:
                    raise self.primary
            return operation

        def verify(_binary):
            engine = self.open_engine()
            if self.stage == "cleanup-guard":
                self.owner._cleanup_failed = True
            elif self.stage == "busy-guard":
                self.owner._proc = self.child
            return engine

        def running(**_kwargs):
            self.probe_count += 1
            self.events.append(("external-probe", self.probe_count))
            if self.stage == "external-probe" and self.probe_count == 2:
                raise self.primary
            return False

        def argv(_request):
            check("argv")()
            return ["nwipe", "--autonuke", "--nogui", "--nowait", "--quiet",
                    "--method=zero", "--verify=off", "--rounds=1",
                    "--logfile=" + LOG_PATH, "--PDFreportpath=noPDF",
                    "--exclude=" + self.request.boot_device, self.request.device]

        self.env.update(resolve_nwipe_binary=lambda _path: ENGINE_PATH,
                        require_real_live_for_nwipe=lambda: None,
                        pinned_nwipe_already_running=running,
                        _verify_pinned_nwipe=verify,
                        assert_existing_is_block_device=check("preflight"),
                        assert_size_unchanged=lambda *_args: None,
                        assert_local_device_transport=lambda *_args: None,
                        block_rdev=lambda path: (23 if path == self.request.device else 29),
                        assert_not_boot=lambda *_args, **_kwargs: None,
                        build_nwipe_argv=argv,
                        assert_log_not_on_target=lambda *_args: None,
                        truncate_log_file=lambda *_args, **_kwargs: self.allocate("log"),
                        _named_private_log_matches=lambda *_args: True,
                        _recheck_identity_under_lock=check("rediscovery"),
                        _log_is_private=lambda _st: True)
        if self.stage == "acquire":
            self.owner._acquire_wipe_lock = check("acquire")

    def engine_fds(self):
        return [fd for fd, kind in self.opened if kind == "engine"]

    def assert_closed_once(self, kind):
        fds = [fd for fd, owner in self.opened if owner == kind]
        assert fds, "the fake acquisition must actually occur"
        assert [fd for fd in self.closes if fd in fds] == fds, (
            f"{kind} acquisition {fds}: close attempts {self.closes}, "
            f"owners {self.closed_owners}, events {self.events}"
        )
        assert "unrelated-reused-descriptor" not in self.closed_owners


@pytest.fixture
def harness(monkeypatch):
    return Harness(monkeypatch)


@contextmanager
def _interrupt(codes, predicate, primary):
    previous = sys.gettrace()
    state = NS(fired=False, lines=0, captured=None, injection_line=None)

    def trace(frame, event, _arg):
        if frame.f_code not in codes:
            return None
        if event == "line":
            state.lines += 1
            assert state.lines <= 1000, "inert trace exceeded its event budget"
            if not state.fired and predicate(frame, state):
                state.fired = True
                state.injection_line = frame.f_lineno
                raise primary
        return trace

    try:
        sys.settrace(trace)
        yield state
    finally:
        sys.settrace(previous)
    assert state.fired, "the intended interruption boundary was not exercised"


@pytest.mark.parametrize("operation", ["engine", "lock"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_failure", [False, True])
def test_bound_acquisition_interruption_has_one_owner(harness, operation, error_type, close_failure):
    h = harness
    primary = error_type("after acquisition was bound")
    if close_failure:
        h.close_error = OSError(5, "inert close failure")
    function = h.env["_open_nwipe_binary_safe" if operation == "engine" else "_acquire_wipe_lock"]

    def bound(frame, _state):
        engine = frame.f_locals.get("engine")
        raw_fd = frame.f_locals.get("fd")
        acquired = [fd for fd, kind in h.opened if kind == operation]
        return bool(acquired and (raw_fd in acquired or getattr(engine, "fd", -1) in acquired
                                  or h.owner._lock_fd in acquired))

    with _interrupt({function.__code__}, bound, primary):
        with pytest.raises(error_type) as caught:
            if operation == "engine":
                function(ENGINE_PATH)
            else:
                function(h.owner, h.request)
        assert caught.value is primary
    h.assert_closed_once(operation)
    assert h.owner._lock_fd is None
    assert h.owner._cleanup_failed is (close_failure and operation == "lock")


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_failure", [False, True])
def test_interruption_after_named_lock_validation_retires_fd(harness, error_type, close_failure):
    h = harness
    primary = error_type("after named lock validation")
    if close_failure:
        h.close_error = OSError(5, "inert close failure")
    function = h.env["_acquire_wipe_lock"]
    with _interrupt({function.__code__},
                    lambda _frame, _state: ("named-lock",) in h.events, primary):
        with pytest.raises(error_type) as caught:
            function(h.owner, h.request)
        assert caught.value is primary
    h.assert_closed_once("lock")
    assert h.owner._lock_fd is None
    assert h.owner._cleanup_failed is close_failure


@pytest.mark.parametrize("refusal", ["contended", "replaced"])
@pytest.mark.parametrize("close_failure", [False, True])
def test_contended_or_replaced_named_lock_refuses_and_closes(harness, refusal, close_failure):
    h = harness
    if refusal == "contended":
        primary = BlockingIOError(11, "inert contended lock")
        h.faults["flock"] = primary
        message = "already running"
    else:
        h.named_lock_stat = NS(**{**vars(h.lock_stat), "st_ino": 999})
        message = "changed during acquisition"
    if close_failure:
        h.close_error = OSError(5, "inert refused lock close")
    with pytest.raises(Refusal, match=message) as caught:
        h.owner._acquire_wipe_lock(h.request)
    if refusal == "contended":
        assert primary in (caught.value.__cause__, caught.value.__context__)
    h.assert_closed_once("lock")
    assert h.owner._lock_fd is None
    assert h.owner._cleanup_failed is close_failure
    assert h.probes == h.spawns == []


@pytest.mark.parametrize("after_fd", [False, True])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_partial_owner_constructor_cleans_any_acquired_fd_once(harness, after_fd, error_type):
    h = harness
    constructor = h.env["_PinnedEngine"].__init__
    primary = error_type("partial engine owner")

    def boundary(frame, state):
        state.captured = frame.f_locals["self"]
        return hasattr(state.captured, "fd") is after_fd

    with _interrupt({constructor.__code__}, boundary, primary) as trace:
        with pytest.raises(error_type) as caught:
            h.open_engine()
        assert caught.value is primary
    trace.captured.close()
    trace.captured.__del__()
    if h.opened:
        h.assert_closed_once("engine")
    else:
        assert h.closes == []


@pytest.mark.parametrize("operation", ["engine", "lock"])
@pytest.mark.parametrize("point", ["open", "fstat"])
def test_acquisition_oserror_is_reported_and_existing_fd_closed(harness, operation, point):
    h = harness
    primary = OSError(5, "inert " + point + " failure")
    h.faults[point + "-" + operation] = primary
    with pytest.raises((Refusal, OSError)) as caught:
        if operation == "engine":
            h.open_engine()
        else:
            h.owner._acquire_wipe_lock(h.request)
    if point == "open" or operation == "engine":
        assert isinstance(caught.value, Refusal)
        assert caught.value.__cause__ is primary
    else:
        assert caught.value is primary
    if point == "open":
        assert h.opened == h.closes == []
    else:
        h.assert_closed_once(operation)
    assert h.owner._lock_fd is None


@pytest.mark.parametrize("failure", ["read", "magic", "inode", "mode"])
def test_open_engine_validation_refuses_and_closes(harness, failure):
    h = harness
    if failure == "read":
        h.faults["pread-engine"] = OSError(5, "inert pread failure")
    elif failure == "magic":
        h.magic = b"#!no"
    elif failure == "inode":
        h.engine_stat = NS(**{**vars(h.engine_stat), "st_ino": 999})
    else:
        h.engine_stat = NS(**{**vars(h.engine_stat), "st_mode": stat.S_IFDIR | 0o500})
    with pytest.raises((Refusal, OSError)):
        h.open_engine()
    h.assert_closed_once("engine")
    assert h.probes == h.spawns == []


@pytest.mark.parametrize("operation", ["engine", "lock"])
@pytest.mark.parametrize("close_type", [OSError, KeyboardInterrupt, SystemExit])
def test_validation_primary_survives_secondary_close_without_retry(harness, operation, close_type):
    h = harness
    primary = Refusal("inert validation refusal")
    h.faults["fstat-" + operation] = primary
    h.close_error = close_type("inert secondary close")
    with pytest.raises(Refusal) as caught:
        if operation == "engine":
            h.open_engine()
        else:
            h.owner._acquire_wipe_lock(h.request)
    assert caught.value is primary
    h.assert_closed_once(operation)
    assert h.owner._lock_fd is None
    if operation == "lock":
        assert h.owner._cleanup_failed
        with pytest.raises(Refusal, match="cleanup could not be confirmed"):
            h.owner._release_wipe_lock()
        h.assert_closed_once("lock")


@pytest.mark.parametrize("close_type", [OSError, KeyboardInterrupt, SystemExit])
def test_standalone_engine_close_reports_failure_without_retry(harness, close_type):
    h = harness
    engine = h.open_engine()
    h.close_error = close_type("inert standalone close")
    with pytest.raises(close_type) as caught:
        engine.close()
    assert caught.value is h.close_error
    assert engine.fd == -1
    engine.close()
    engine.__del__()
    h.assert_closed_once("engine")


@pytest.mark.parametrize("operation", ["wrapper", "probe"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_failure", [False, True])
def test_caller_bound_engine_interruption_closes_once(harness, operation, error_type, close_failure):
    h = harness
    primary = error_type("after caller bound engine")
    if close_failure:
        h.close_error = OSError(5, "inert caller close failure")
        if operation == "probe":
            def initial_check(_path):
                pass
            h.env["assert_nwipe_binary_safe"] = initial_check
            h.env["_ORIGINAL_ASSERT_NWIPE_BINARY_SAFE"] = initial_check
    function = h.env["assert_nwipe_binary_safe" if operation == "wrapper" else "_verify_pinned_nwipe"]

    def bound(frame, _state):
        engine = frame.f_locals.get("engine")
        acquired = getattr(engine, "fd", -1) in h.engine_fds()
        if acquired:
            h.events.append(("caller-bound-interruption", frame.f_lineno))
        return acquired

    with _interrupt({function.__code__}, bound, primary):
        with pytest.raises(error_type) as caught:
            function(ENGINE_PATH)
        assert caught.value is primary
    h.assert_closed_once("engine")


def test_wrapper_standalone_close_failure_is_visible_and_not_retried(harness):
    h = harness
    h.close_error = OSError(5, "inert wrapper close")
    with pytest.raises(OSError) as caught:
        h.env["assert_nwipe_binary_safe"](ENGINE_PATH)
    assert caught.value is h.close_error
    h.assert_closed_once("engine")


@pytest.mark.parametrize("failure", ["run-oserror", "timeout", "interrupt", "exit", "version", "digest"])
@pytest.mark.parametrize("close_failure", [False, True])
def test_version_probe_preserves_failure_and_closes_retained_engine(harness, failure, close_failure):
    h = harness
    # The injectable initial assertion is still executed; skip its independent
    # open/close here so secondary-close failure hits the retained probe owner.
    initial_checks = []

    def initial_check(path):
        initial_checks.append(path)

    h.env["assert_nwipe_binary_safe"] = initial_check
    h.env["_ORIGINAL_ASSERT_NWIPE_BINARY_SAFE"] = initial_check
    primary = {"run-oserror": OSError(5, "probe run failed"),
               "timeout": FakeTimeout("probe timeout"),
               "interrupt": KeyboardInterrupt("probe interrupted"),
               "exit": SystemExit("probe exited"),
               "digest": Refusal("probe digest refused")}.get(failure)
    if failure == "digest":
        def digest(*_args):
            raise primary
        h.env["_engine_digest"] = digest
    elif failure == "version":
        h.run_result.stdout = "nwipe version 0.420\n"
    else:
        h.run_error = primary
    if close_failure:
        h.close_error = OSError(5, "inert probe close failure")
    expected = Refusal if failure in {"run-oserror", "timeout", "version", "digest"} else type(primary)
    with pytest.raises(expected) as caught:
        h.env["_verify_pinned_nwipe"](ENGINE_PATH)
    assert initial_checks == [ENGINE_PATH]
    if failure in {"run-oserror", "timeout"}:
        assert caught.value.__cause__ is primary
    elif failure != "version":
        assert caught.value is primary
    else:
        assert "pinned version" in str(caught.value)
    h.assert_closed_once("engine")
    assert h.spawns == []


def test_successful_probe_returns_exact_open_engine_to_caller(harness):
    h = harness
    engine = h.env["_verify_pinned_nwipe"](ENGINE_PATH)
    fds = h.engine_fds()
    assert len(fds) == 2 and h.closes == fds[:1]
    assert engine.fd == fds[1]
    argv, kwargs = h.probes[0]
    assert argv == [engine.exec_path, "-V"]
    assert kwargs["pass_fds"] == (engine.fd,)
    assert kwargs["timeout"] == 5 and kwargs["shell"] is False
    engine.close()
    engine.__del__()
    h.assert_closed_once("engine")


STAGES = ["preflight", "argv", "cleanup-guard", "busy-guard", "acquire",
          "rediscovery", "external-probe", "preexec-log", "spawn"]


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("close_failure", [False, True])
def test_start_refusal_preserves_primary_and_closes_engine(harness, stage, close_failure):
    h = harness
    h.stage = stage
    h.prepare_start()
    if close_failure:
        h.close_error = OSError(5, "inert engine close failure")
        # Other owned resources have successful cleanup in this matrix.
        close = h.os.close

        def engine_close_only(fd):
            saved = h.close_error
            if h.handles.get(fd) != "engine":
                h.close_error = None
            try:
                close(fd)
            finally:
                h.close_error = saved

        h.os.close = engine_close_only
    with pytest.raises(Refusal) as caught:
        h.owner.start(h.request)
    if stage in {"cleanup-guard", "busy-guard"}:
        assert str(caught.value) == ("Runner cleanup could not be confirmed."
                                     if stage == "cleanup-guard" else "A wipe is already running.")
    else:
        assert caught.value is h.primary
    h.assert_closed_once("engine")
    assert len(h.spawns) == (1 if stage == "spawn" else 0)
    if stage in {"rediscovery", "external-probe", "preexec-log"}:
        h.assert_closed_once("lock")
        h.assert_closed_once("log")
        assert h.owner._lock_fd is h.owner._log_fd is None
        assert h.owner.start_not_spawned()
    if stage == "spawn":
        assert h.owner._lock_fd is not None and h.owner._log_fd is not None
        assert not h.owner.start_not_spawned()


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_failure", [False, True])
def test_interrupted_spawn_preserves_uncertainty_and_primary(harness, error_type, close_failure):
    h = harness
    h.stage = "spawn"
    h.primary = error_type("inert uncertain spawn")
    h.prepare_start()
    if close_failure:
        h.close_error = OSError(5, "inert engine close failure")
    with pytest.raises(error_type) as caught:
        h.owner.start(h.request)
    assert caught.value is h.primary
    h.assert_closed_once("engine")
    assert h.owner._proc is None
    assert h.handles[h.owner._lock_fd] == "lock"
    assert h.handles[h.owner._log_fd] == "log"
    assert not h.owner.start_not_spawned()
    assert ("inhibit-stop",) not in h.events
    assert any(event[:3] == ("diag", "nwipe", "spawn_ownership_uncertain") for event in h.events)
    # A fresh attempt must refuse before touching retained uncertain resources.
    before = h.opened[:], h.closes[:], len(h.spawns)
    with pytest.raises(Refusal, match="already running"):
        h.owner.start(h.request)
    assert (h.opened, h.closes, len(h.spawns)) == before


@pytest.mark.parametrize("filename", [ENGINE_PATH, "/proc/self/fd/7001"])
def test_reaped_exec_error_can_release_owned_slot(harness, filename):
    h = harness
    h.stage = "spawn"
    h.primary = OSError(2, "inert reaped exec error", filename)
    h.prepare_start()
    with pytest.raises(OSError) as caught:
        h.owner.start(h.request)
    assert caught.value is h.primary
    for kind in ("engine", "lock", "log"):
        h.assert_closed_once(kind)
    assert h.owner.start_not_spawned()


@pytest.mark.parametrize("close_failure", [False, True])
def test_successful_start_retains_child_lock_and_log_after_engine_close(harness, close_failure):
    h = harness
    h.prepare_start()
    if close_failure:
        h.close_error = OSError(5, "inert final engine close")
        with pytest.raises(OSError) as caught:
            h.owner.start(h.request)
        assert caught.value is h.close_error
    else:
        h.owner.start(h.request)
    h.assert_closed_once("engine")
    assert h.owner._proc is h.child and h.owner._active_request is h.request
    assert h.owner._spawned_this_attempt and not h.owner.start_not_spawned()
    argv, kwargs = h.spawns[0]
    assert argv[0] == "/proc/self/fd/" + str(h.engine_fds()[0])
    assert kwargs["pass_fds"] == (h.owner._lock_fd, h.engine_fds()[0])
    assert h.owner._log_fd not in kwargs["pass_fds"]
    assert kwargs["shell"] is False and kwargs["close_fds"] is True
    assert kwargs["start_new_session"] is True and kwargs["cwd"] == "/"
    assert kwargs["env"] == {"PATH": "/inert/bin", "TERM": "linux"}
    assert h.handles[h.owner._lock_fd] == "lock" and h.handles[h.owner._log_fd] == "log"
    assert h.events.index(("inhibit-start",)) < h.events.index(("rediscovery",))
    assert h.events.index(("rediscovery",)) < h.events.index(("external-probe", 2))
    assert h.events.index(("external-probe", 2)) < h.events.index(("spawn",))
