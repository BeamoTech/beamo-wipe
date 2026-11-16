"""Exact-source AST cleanup regressions using stdlib fakes, never real FDs.

These portable checks exercise the checked-in function bodies without importing
the Linux product module. They do not qualify real filesystem or Linux behavior.
"""

import __future__
import ast
import builtins
import errno
import hashlib
import json
from pathlib import Path
import stat
import sys
from types import SimpleNamespace


SOURCE = Path(__file__).resolve().parents[1] / "src/beamo_wipe/evidence.py"
DIRECTORY, FILE, PIN = 90, 91, 92
ERROR_TYPES = (None, OSError, RuntimeError, KeyboardInterrupt, SystemExit)
_CODE_CACHE = {}


class SafetyError(RuntimeError):
    pass


class _Filesystem:
    def __init__(self, operation, stage=None, primary=None, close_errors=None):
        self.operation = operation
        self.stage = stage
        self.primary = primary
        self.close_errors = close_errors or {}
        self.events = []
        self.acquired = []
        self.closes = []
        self.detached = []
        self.logs = []
        self.offset = 0
        self.data = b"x"
        self.published = False
        self.log_error = False
        self.changed = None
        self.short_write = False
        self.boundary_line = None
        self.observed_lines = []
        self.error_occurrence = 1
        self.close_error_after = 1
        self.counts = {}
        self.snapshot = SimpleNamespace(
            st_dev=1, st_ino=2, st_size=1, st_mode=stat.S_IFREG | 0o600,
            st_uid=0, st_nlink=1, st_mtime_ns=3, st_ctime_ns=4,
        )

    def step(self, stage):
        self.events.append((stage,))
        self.counts[stage] = self.counts.get(stage, 0) + 1
        if stage == self.stage and self.counts[stage] == self.error_occurrence:
            raise self.primary

    def open(self, _path, _flags, *_args, **kwargs):
        directory = self.operation != "read" and "dir_fd" not in kwargs
        self.step("open-directory" if directory else "open-file")
        fd = DIRECTORY if directory else FILE
        self.acquired.append(fd)
        if fd == FILE:
            self.offset = 0
        return fd

    def close(self, fd):
        self.events.append(("close", fd))
        self.closes.append(fd)
        # Inspect only fake call frames, proving detachment precedes close.
        frame = sys._getframe(1)
        if frame.f_code.co_name == "_close_evidence_fds":
            frame = frame.f_back
        owners = ("fd", "pinned_fd", "dir_fd", "directory_fd", "dfd")
        self.detached.append(all(frame.f_locals.get(key, -1) != fd for key in owners))
        if fd in self.close_errors and self.closes.count(fd) >= self.close_error_after:
            raise self.close_errors[fd]

    def fstat(self, fd):
        self.step("stat-pin" if fd == PIN else "stat-file")
        result = vars(self.snapshot).copy()
        if self.changed == "owner":
            result["st_uid"] = 1
        elif self.changed == "permissions":
            result["st_mode"] = stat.S_IFREG | 0o644
        elif self.changed == "links":
            result["st_nlink"] = 2
        elif self.changed == "size":
            result["st_size"] = 2
        return SimpleNamespace(**result)

    def stat(self, _name, **_kwargs):
        self.step("stat-published" if self.published else "stat-temporary")
        result = vars(self.snapshot).copy()
        if self.changed == "inode":
            result["st_ino"] = 22
        return SimpleNamespace(**result)

    def read(self, _fd, size):
        self.step("read")
        result = self.data[self.offset:self.offset + size]
        self.offset += len(result)
        return result

    def pread(self, _fd, size, offset):
        self.step("pread-published" if self.published else "pread-temporary")
        return (b"y" if self.changed == "bytes" else self.data)[offset:offset + size]

    def lseek(self, _fd, offset, _whence):
        self.step("seek")
        self.offset = offset

    def write(self, _fd, data):
        self.step("write")
        return 0 if self.short_write else len(data)

    def fsync(self, fd):
        self.step("sync-directory" if fd == DIRECTORY else "sync-file")

    def dup(self, _fd):
        self.step("dup-file")
        self.acquired.append(PIN)
        return PIN

    def token_hex(self, _size):
        self.step("token")
        return "inert-token"

    def publish(self, *_args):
        self.step("publish")
        self.published = True

    def log(self, message):
        self.logs.append(message)
        if self.log_error:
            raise KeyboardInterrupt("PRIVATE logging error")


def _namespace(raw, filename, fs):
    names = {
        "_close_evidence_fds", "_read_regular_nofollow", "_atomic_write_bytes",
        "_exact_private_file", "verify_evidence_checksum", "recover_result",
        "_verified_evidence_bytes", "_unique_evidence_fields", "export_evidence",
        "EvidenceFinalizationError", "_EvidencePublicationCollision", "_publish_or_accept_exact",
    }
    cache_key = (raw, filename)
    if cache_key not in _CODE_CACHE:
        nodes = [node for node in ast.parse(raw).body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        _CODE_CACHE[cache_key] = compile(
            ast.Module(body=nodes, type_ignores=[]), filename, "exec",
            flags=__future__.annotations.compiler_flag,
        )

    def only_presenter(name, *_args, **_kwargs):
        assert name == "beamo_wipe.outcomes", name
        return SimpleNamespace(present_evidence=lambda _value: "indeterminate")

    env = dict(
        __builtins__={**vars(builtins), "__import__": only_presenter},
        os=SimpleNamespace(
            open=fs.open, close=fs.close, fstat=fs.fstat, stat=fs.stat,
            read=fs.read, pread=fs.pread, write=fs.write, lseek=fs.lseek,
            fsync=fs.fsync, dup=fs.dup, getuid=lambda: 0,
            lstat=lambda _path: SimpleNamespace(st_mode=stat.S_IFDIR | 0o700),
            O_RDONLY=1, O_NOFOLLOW=2, O_NONBLOCK=4, O_DIRECTORY=8,
            O_RDWR=16, O_CREAT=32, O_EXCL=64, SEEK_SET=0,
        ),
        sys=SimpleNamespace(stderr=SimpleNamespace(write=fs.log)),
        secrets=SimpleNamespace(token_hex=fs.token_hex), stat=stat,
        SafetyError=SafetyError, MAX_EVIDENCE_FILE_BYTES=100, errno=errno,
        Path=Path, hashlib=hashlib, json=json, CHECKSUM_SUFFIX=".sha256",
        _rename_noreplace=fs.publish, assert_log_not_on_target=lambda *_a, **_k: None,
    )
    exec(  # noqa: S102 - exact checked-in AST with inert OS and imports
        _CODE_CACHE[cache_key], env,
    )
    return env


def _invoke(env, fs, operation, trace_owner=None, ambient=None):
    path = Path("/inert/evidence.json")
    if operation == "read":
        function = env["_read_regular_nofollow"]
        args, kwargs = (path,), {"private": True}
    elif operation == "write":
        function = env["_atomic_write_bytes"]
        args, kwargs = (path, b"x"), {}
    elif operation == "inspect":
        function = env["_exact_private_file"]
        args, kwargs = (path, b"x"), {}
    elif operation == "export":
        function = env["export_evidence"]
        # All preceding export operations are inert; only its final FD scope runs.
        env["Path"] = lambda value: value
        destination = _Destination()
        env["_verified_evidence_bytes"] = lambda _path: b"x"
        env["_exact_private_file"] = lambda *_args: (1, 2)
        env["_publish_or_accept_exact"] = lambda *_args: (1, 2)
        args, kwargs = (_Destination(), destination), {}
    else:
        function = env[operation]
        args, kwargs = (path,), {}

    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if (trace_owner is not None and event == "line"
                and frame.f_code is function.__code__
                and frame.f_locals.get(trace_owner[0]) == trace_owner[1]):
            if fs.primary is None:
                if fs.acquired == [DIRECTORY] and frame.f_lineno not in fs.observed_lines:
                    fs.observed_lines.append(frame.f_lineno)
            elif not fired and (fs.boundary_line is None or frame.f_lineno == fs.boundary_line):
                fired = True
                fs.events.append(("trace-interruption", frame.f_lineno))
                raise fs.primary
        return interrupt

    def call():
        previous = sys.gettrace()
        try:
            if trace_owner is not None:
                sys.settrace(interrupt)
            return function(*args, **kwargs), None
        except BaseException as exc:
            return None, exc
        finally:
            if trace_owner is not None:
                sys.settrace(previous)

    if ambient == "except":
        try:
            raise RuntimeError("PRIVATE ambient error")
        except RuntimeError:
            result = call()
    elif ambient == "finally":
        try:
            try:
                raise RuntimeError("PRIVATE ambient error")
            finally:
                result = call()
        except RuntimeError:
            pass
    else:
        result = call()
    return *result, fired


class _Destination:
    name = "evidence.json"

    def exists(self):
        return True

    def __truediv__(self, _name):
        return self


def _row(name, fs, error, checks):
    return dict(
        case=name, passed=all(checks.values()), checks=checks,
        outcome=type(error).__name__ if error is not None else "returned",
        events=fs.events, logs=fs.logs,
    )


def cleanup_probe_cases(raw, filename):
    """Finite fake cases shared by pytest and source-bound causal probes."""
    stages = {
        "read": (None, "open-file", "stat-file", "read"),
        "write": (None, "open-directory", "token", "open-file", "stat-file",
                  "write", "sync-file", "dup-file", "stat-pin", "stat-temporary",
                  "pread-temporary", "publish", "stat-published",
                  "pread-published", "sync-directory"),
        "inspect": (None, "open-directory", "open-file", "stat-file", "seek", "read"),
        "export": (None, "open-directory", "sync-directory"),
    }
    for operation, operation_stages in stages.items():
        for stage in operation_stages:
            for error_type in (ERROR_TYPES if stage is not None else (None,)):
                if stage is not None and error_type is None:
                    continue
                primary = error_type("PRIVATE primary") if error_type else None
                for close_type in ERROR_TYPES:
                    failures = {fd: close_type("PRIVATE close")
                                for fd in (FILE, PIN, DIRECTORY)} if close_type else {}
                    if operation == "write" and stage in {
                        "stat-pin", "stat-temporary", "pread-temporary", "publish",
                        "stat-published", "pread-published", "sync-directory",
                    }:
                        # The original file close must succeed to reach these
                        # later operation failures; only its pin remains owned.
                        failures.pop(FILE, None)
                    fs = _Filesystem(operation, stage, primary, failures)
                    env = _namespace(raw, filename, fs)
                    value, error, _ = _invoke(env, fs, operation)
                    translated = (
                        operation == "read" and stage == "open-file"
                        or operation == "inspect" and stage != "open-directory"
                        or operation == "write" and fs.published
                    ) and isinstance(primary, OSError if operation != "write" else Exception)
                    ignored = operation == "export" and isinstance(primary, OSError)
                    if primary is not None and not ignored:
                        identity = (isinstance(error, SafetyError) if operation != "write"
                                    else isinstance(error, env["EvidenceFinalizationError"]))
                        preserved = identity and error.__cause__ is primary if translated else error is primary
                    elif ignored:
                        preserved = error is None
                    elif fs.closes and close_type:
                        preserved = error is failures[fs.closes[0]]
                    else:
                        expected = b"x" if operation == "read" else (1, 2)
                        preserved = error is None and (operation == "export" or value == expected)
                    acquired = set(fs.acquired)
                    checks = dict(
                        outcome=preserved,
                        all_owned_closed=set(fs.closes) == acquired,
                        exactly_once=len(fs.closes) == len(acquired),
                        detached=all(fs.detached),
                        private_logs=all("PRIVATE" not in message for message in fs.logs),
                        refusal=(operation != "write" or primary is None or fs.published or stage == "publish"
                                 or not any(event[0] == "publish" for event in fs.events)),
                    )
                    yield _row(f"{operation}/{stage}/{error_type}/{close_type}", fs, error, checks)


def close_chain_probe_cases(raw, filename):
    for error_type in (None, OSError, KeyboardInterrupt, SystemExit):
        for file_type in ERROR_TYPES:
            for pin_type in ERROR_TYPES:
                for directory_type in ERROR_TYPES:
                    primary = error_type("PRIVATE primary") if error_type else None
                    failures = {
                        fd: kind("PRIVATE close")
                        for fd, kind in ((FILE, file_type), (PIN, pin_type), (DIRECTORY, directory_type))
                        if kind is not None
                    }
                    fs = _Filesystem("write", primary=primary, close_errors=failures)
                    fs.log_error = True
                    env = _namespace(raw, filename, fs)
                    _value, error, fired = _invoke(
                        env, fs, "write", trace_owner=("pinned_fd", PIN) if primary else None,
                    )
                    expected = primary if primary is not None else next(
                        (failures[fd] for fd in (FILE, PIN, DIRECTORY) if fd in failures), None,
                    )
                    yield _row(f"close-chain/{error_type}/{file_type}/{pin_type}/{directory_type}", fs, error, dict(
                        identity=error is expected,
                        all_owned_closed=fs.closes == [FILE, PIN, DIRECTORY],
                        detached=all(fs.detached),
                        fired=fired is (primary is not None),
                        private_logs=all("PRIVATE" not in message for message in fs.logs),
                        refused_before_publish=FILE not in failures or not fs.published,
                    ))


def acquisition_probe_cases(raw, filename):
    targets = {
        "read": (("fd", FILE),),
        "write": (("dir_fd", DIRECTORY), ("fd", FILE), ("pinned_fd", PIN)),
        "inspect": (("directory_fd", DIRECTORY), ("fd", FILE)),
        "export": (("dfd", DIRECTORY),),
    }
    for operation, owners in targets.items():
        for owner in owners:
            for error_type in (KeyboardInterrupt, SystemExit):
                for close_type in ERROR_TYPES:
                    primary = error_type("PRIVATE post-open interruption")
                    failures = {fd: close_type("PRIVATE close")
                                for fd in (FILE, PIN, DIRECTORY)} if close_type else {}
                    fs = _Filesystem(operation, primary=primary, close_errors=failures)
                    env = _namespace(raw, filename, fs)
                    _value, error, fired = _invoke(env, fs, operation, trace_owner=owner)
                    yield _row(f"acquired/{operation}/{owner}/{error_type}/{close_type}", fs, error, dict(
                        fired=fired, identity=error is primary,
                        all_owned_closed=set(fs.closes) == set(fs.acquired),
                        exactly_once=len(fs.closes) == len(fs.acquired),
                        detached=all(fs.detached),
                    ))


def caller_probe_cases(raw, filename):
    for operation in ("recover_result", "verify_evidence_checksum", "_verified_evidence_bytes"):
        for error_type in (KeyboardInterrupt, SystemExit):
            for close_type in ERROR_TYPES:
                for member in ("evidence", "sidecar"):
                    primary = error_type("PRIVATE cancellation")
                    failures = {FILE: close_type("PRIVATE close")} if close_type else {}
                    fs = _Filesystem("read", "read", primary, failures)
                    fs.error_occurrence = 1 if member == "evidence" else 3
                    fs.close_error_after = 1 if member == "evidence" else 2
                    env = _namespace(raw, filename, fs)
                    _value, error, _ = _invoke(env, fs, operation)
                    yield _row(f"caller/{operation}/{member}/{error_type}/{close_type}", fs, error, dict(
                        identity=error is primary,
                        exactly_once=fs.closes == [FILE] * fs.close_error_after,
                    ))
    for operation in ("read", "write", "inspect", "export"):
        for ambient in (None, "except", "finally"):
            for fd in ((FILE,) if operation == "read" else
                       (FILE, PIN, DIRECTORY) if operation == "write" else
                       (FILE, DIRECTORY) if operation == "inspect" else (DIRECTORY,)):
                failure = OSError("PRIVATE standalone close")
                fs = _Filesystem(operation, close_errors={fd: failure})
                fs.log_error = True
                env = _namespace(raw, filename, fs)
                _value, error, _ = _invoke(env, fs, operation, ambient=ambient)
                yield _row(f"standalone/{operation}/{ambient}/{fd}", fs, error, dict(
                    identity=error is failure,
                    all_owned_closed=set(fs.closes) == set(fs.acquired),
                    exactly_once=len(fs.closes) == len(fs.acquired),
                ))


def boundary_probe_cases(raw, filename):
    control = _Filesystem("inspect")
    env = _namespace(raw, filename, control)
    value, error, fired = _invoke(env, control, "inspect", trace_owner=("directory_fd", DIRECTORY))
    yield _row("inspect-directory-boundaries/control", control, error, dict(
        normal=value == (1, 2) and error is None and not fired,
        lines_found=bool(control.observed_lines),
        all_closed=control.closes == [FILE, DIRECTORY],
    ))
    for line in control.observed_lines:
        for error_type in (KeyboardInterrupt, SystemExit):
            for close_type in ERROR_TYPES:
                primary = error_type("PRIVATE directory-boundary cancellation")
                failures = {DIRECTORY: close_type("PRIVATE close")} if close_type else {}
                fs = _Filesystem("inspect", primary=primary, close_errors=failures)
                fs.boundary_line = line
                env = _namespace(raw, filename, fs)
                _value, error, fired = _invoke(env, fs, "inspect", trace_owner=("directory_fd", DIRECTORY))
                yield _row(f"inspect-directory-boundaries/{line}/{error_type}/{close_type}", fs, error, dict(
                    fired=fired, identity=error is primary,
                    directory_only_acquired=fs.acquired == [DIRECTORY],
                    directory_closed_once=fs.closes == [DIRECTORY],
                    detached=all(fs.detached),
                ))


def safety_probe_cases(raw, filename):
    for operation in ("read", "write", "inspect"):
        for changed in ("owner", "permissions", "links", "size", "inode", "bytes"):
            if operation == "read" and changed in {"inode", "bytes"}:
                continue
            if operation == "inspect" and changed == "bytes":
                continue
            failure = KeyboardInterrupt("PRIVATE secondary close")
            closing = (PIN, DIRECTORY) if operation == "write" else (FILE, DIRECTORY)
            fs = _Filesystem(operation, close_errors={fd: failure for fd in closing})
            fs.changed = changed
            env = _namespace(raw, filename, fs)
            _value, error, _ = _invoke(env, fs, operation)
            yield _row(f"refusal/{operation}/{changed}", fs, error, dict(
                refusal=isinstance(error, PermissionError if operation == "read"
                                   and changed in {"permissions", "links"} else SafetyError),
                all_owned_closed=set(fs.closes) == set(fs.acquired),
                exactly_once=len(fs.closes) == len(fs.acquired),
                unpublished=not fs.published,
            ))


def contract_probe_cases(raw, filename):
    for operation in ("read", "write", "inspect"):
        stage = "open-file" if operation == "read" else "open-directory"
        for error_type in (OSError, PermissionError, FileNotFoundError):
            primary = error_type("PRIVATE open error")
            fs = _Filesystem(operation, stage, primary)
            env = _namespace(raw, filename, fs)
            _value, error, _ = _invoke(env, fs, operation)
            preserved = (isinstance(error, SafetyError) and error.__cause__ is primary
                         if operation == "read" else error is primary)
            yield _row(f"open-contract/{operation}/{error_type}", fs, error, dict(
                contract=preserved, not_acquired=not fs.acquired, not_closed=not fs.closes,
            ))
    for stage in ("open-file", "read"):
        for close_type in ERROR_TYPES:
            primary = FileNotFoundError("PRIVATE missing file")
            failure = close_type("PRIVATE close") if close_type else None
            fs = _Filesystem("inspect", stage, primary, {DIRECTORY: failure} if failure else {})
            env = _namespace(raw, filename, fs)
            value, error, _ = _invoke(env, fs, "inspect")
            preserved = (isinstance(error, SafetyError) and error.__cause__ is primary
                         if stage == "read" else error is failure and value is None)
            yield _row(f"missing-contract/{stage}/{close_type}", fs, error, dict(
                contract=preserved, all_owned_closed=set(fs.closes) == set(fs.acquired),
                exactly_once=len(fs.closes) == len(fs.acquired),
            ))
    for case in ("short-write", "occupied", "finalization"):
        primary = FileExistsError("PRIVATE occupied") if case == "occupied" else OSError("PRIVATE sync")
        stage = "publish" if case == "occupied" else "sync-directory" if case == "finalization" else None
        fs = _Filesystem("write", stage, primary)
        fs.short_write = case == "short-write"
        env = _namespace(raw, filename, fs)
        _value, error, _ = _invoke(env, fs, "write")
        checks = dict(
            all_owned_closed=fs.closes == ([FILE, DIRECTORY] if fs.short_write else [FILE, PIN, DIRECTORY]),
            publication=fs.published is (case == "finalization"),
        )
        if case == "finalization":
            checks["finalization_error"] = isinstance(error, env["EvidenceFinalizationError"]) and error.__cause__ is primary
            fs.operation, fs.stage, fs.primary, fs.offset = "inspect", None, None, 0
            value, second_error, _ = _invoke(env, fs, "inspect")
            checks["exact_published_state_resumable"] = value == (1, 2) and second_error is None
        elif case == "occupied":
            checks["no_replace"] = isinstance(error, FileExistsError) and (
                error is primary or error.__cause__ is primary
            )
        else:
            checks["refusal"] = isinstance(error, OSError)
        yield _row(f"publication-contract/{case}", fs, error, checks)


def collision_probe_cases(raw, filename):
    """Injected provenance contracts; real close returning EEXIST is unproved."""
    path = Path("/inert/evidence.json")

    def invoke(env):
        try:
            return env["_publish_or_accept_exact"](path, b"x"), None
        except BaseException as exc:
            return None, exc

    for fd in (FILE, PIN, DIRECTORY):
        for error_type in (FileExistsError, OSError, KeyboardInterrupt, SystemExit):
            failure = error_type("PRIVATE standalone close")
            fs = _Filesystem("write", close_errors={fd: failure})
            env = _namespace(raw, filename, fs)
            env["_exact_private_file"] = lambda *_args: (1, 2) if fs.published else None
            _value, error = invoke(env)
            yield _row(f"collision-close/{fd}/{error_type}", fs, error, dict(
                identity=error is failure, all_closed_once=fs.closes == [FILE, PIN, DIRECTORY],
                publication=fs.published is (fd != FILE),
            ))

    for state in ("exact", "absent", "different"):
        for fd in (None, FILE, PIN, DIRECTORY):
            collision = FileExistsError(errno.EEXIST, "PRIVATE publication-stage collision", "inert-destination")
            collision.filename2 = "inert-source"
            setattr(collision, "winerror", 183)
            failure = FileExistsError("PRIVATE close")
            unsafe = SafetyError("PRIVATE different existing file")
            fs = _Filesystem("write", close_errors={fd: failure} if fd is not None else {})
            env = _namespace(raw, filename, fs)
            lookups = []

            def existing(*_args):
                lookups.append("inspect-existing")
                if len(lookups) == 1 or state == "absent":
                    return None
                if state == "different":
                    raise unsafe
                return 1, 2

            def collide(*_args):
                fs.events.append(("publish-collision",))
                raise collision

            env["_exact_private_file"] = existing
            env["_rename_noreplace"] = collide
            value, error = invoke(env)
            expected = (failure if fd == FILE
                        else collision if state == "absent"
                        else unsafe if state == "different" else None)
            preserved = error is expected
            if expected is collision and error is not None:
                preserved = isinstance(error, FileExistsError) and (
                    error is collision or error.__cause__ is collision
                ) and all(getattr(error, field, None) == getattr(collision, field, None)
                          for field in ("args", "errno", "strerror", "filename", "filename2", "winerror"))
            yield _row(f"collision-resume/{state}/{fd}", fs, error, dict(
                identity_or_collision_cause=preserved,
                exact_success=value == (1, 2) if expected is None else value is None,
                lookups=len(lookups) == (1 if fd == FILE else 2),
                all_closed_once=fs.closes == [FILE, PIN, DIRECTORY],
                no_own_publication=not fs.published,
            ))

    for stage in ("open-directory", "token", "open-file", "write", "dup-file", "stat-pin"):
        failure = FileExistsError("PRIVATE non-publication failure")
        fs = _Filesystem("write", stage, failure)
        env = _namespace(raw, filename, fs)
        lookups = []

        def unrelated_exact(*_args):
            lookups.append("inspect-existing")
            return None if len(lookups) == 1 else (1, 2)

        env["_exact_private_file"] = unrelated_exact
        _value, error = invoke(env)
        yield _row(f"collision-origin/{stage}", fs, error, dict(
            identity=error is failure, no_collision_recovery=len(lookups) == 1,
            all_closed_once=len(fs.closes) == len(fs.acquired)
            and set(fs.closes) == set(fs.acquired),
        ))

    fs = _Filesystem("write")
    env = _namespace(raw, filename, fs)
    env["_exact_private_file"] = lambda *_args: (1, 2)
    value, error = invoke(env)
    yield _row("collision-resume/preexisting-exact", fs, error, dict(
        exact_success=value == (1, 2) and error is None, no_write=not fs.events,
    ))

    for error_type in (None, FileExistsError, OSError, KeyboardInterrupt, SystemExit):
        failure = error_type("PRIVATE injected writer failure") if error_type else None
        fs = _Filesystem("write")
        env = _namespace(raw, filename, fs)
        original = env["_atomic_write_bytes"]
        calls = []

        def two_argument_writer(path, data):
            calls.append((path, data))
            if failure is not None:
                raise failure
            return original(path, data)

        env["_atomic_write_bytes"] = two_argument_writer
        env["_exact_private_file"] = lambda *_args: None
        value, error = invoke(env)
        yield _row(f"collision-wrapper/{error_type}", fs, error, dict(
            two_argument_injection=len(calls) == 1,
            identity=error is failure,
            normal_success=value == (1, 2) if failure is None else value is None,
        ))


def test_evidence_cleanup_error_matrix():
    for row in cleanup_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_acquisition_is_owned_before_next_line():
    for row in acquisition_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_close_chain_preserves_first_failure_and_attempts_every_close():
    for row in close_chain_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_callers_and_ambient_exceptions():
    for row in caller_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_inspector_directory_acquisition_line_boundaries():
    for row in boundary_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_cleanup_preserves_safety_refusals():
    for row in safety_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_open_and_publication_contracts():
    for row in contract_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row


def test_evidence_collision_recovery_preserves_close_failure_provenance():
    for row in collision_probe_cases(SOURCE.read_bytes(), str(SOURCE)):
        assert row["passed"], row
