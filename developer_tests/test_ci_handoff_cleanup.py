"""Exact handoff functions with fake descriptors; no devices or native publication."""

from __future__ import annotations

import ast
import io
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/handoff_ci_outputs.py"


def functions(**values):
    names = {"handoff", "_same_directory", "_close_handoff_fds", "_write_new_file"}
    nodes = [
        node
        for node in ast.parse(SOURCE.read_bytes()).body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    namespace = dict(Path=PurePosixPath, re=re, stat=stat, **values)
    tree = ast.Module(
        body=ast.parse("from __future__ import annotations").body + nodes,
        type_ignores=[],
    )
    exec(compile(tree, str(SOURCE), "exec"), namespace)
    return namespace


class FakeOS:
    name = "posix"
    O_WRONLY, O_CREAT, O_EXCL, O_NOFOLLOW = 1, 2, 4, 8

    def __init__(self, desktop, primary, bad_mask, error_type):
        self.desktop, self.primary = desktop, primary
        self.directory_fds = [12, 11, 10] if desktop else [12, 10]
        self.active = set()
        self.closes = []
        self.acquisitions = []
        self.close_errors = {
            fd: error_type("inert cleanup refusal")
            for index, fd in enumerate(self.directory_fds)
            if bad_mask & (1 << index)
        }
        self.files = {10: {}, 12: {}}
        self.writers = {}
        names = ("one", "two", "desktop-build.json") if desktop else ("lint.json",)
        self.files[10].update({name: b"fixture" for name in names})
        self.next_file = 20
        self.write_error = None

    def acquire(self, *args, **kwargs):
        choices = [10, 11, 12] if self.desktop else [10, 12]
        fd = choices[len(self.acquisitions)]
        self.acquisitions.append(fd)
        self.active.add(fd)
        return fd

    def listdir(self, fd):
        if self.primary is not None:
            raise self.primary
        return list(self.files[fd])

    def stat(self, name, *, dir_fd, **kwargs):
        return SimpleNamespace(
            st_dev=1,
            st_ino=12 if name == ".stage" else 42,
            st_mode=stat.S_IFREG | 0o600,
        )

    def fstat(self, fd):
        return SimpleNamespace(st_dev=1, st_ino=fd)

    def open(self, name, flags, mode, *, dir_fd):
        fd = self.next_file
        self.next_file += 1
        self.active.add(fd)
        self.writers[fd] = (dir_fd, name)
        self.files[dir_fd][name] = b""
        return fd

    def write(self, fd, raw):
        if self.write_error is not None:
            raise self.write_error
        directory, name = self.writers[fd]
        self.files[directory][name] += bytes(raw)
        return len(raw)

    def fdopen(self, fd, mode):
        owner = self

        class Stream(io.BytesIO):
            def write(self, raw):
                return owner.write(fd, raw)

            def fileno(self):
                return fd

            def close(self):
                if not self.closed:
                    try:
                        owner.close(fd)
                    finally:
                        super().close()

        return Stream()

    def fsync(self, fd):
        pass

    def fchmod(self, fd, mode):
        pass

    def close(self, fd):
        assert fd in self.active, "Close retried a released descriptor"
        self.active.remove(fd)
        self.closes.append(fd)
        if fd in self.close_errors:
            raise self.close_errors[fd]


def scenarios():
    for desktop in (False, True):
        width = 3 if desktop else 2
        for primary_type in (None, ValueError, KeyboardInterrupt, SystemExit):
            for error_type in (OSError, KeyboardInterrupt, SystemExit):
                for mask in range(1 << width):
                    yield desktop, primary_type, error_type, mask


@pytest.mark.parametrize("desktop,primary_type,error_type,mask", list(scenarios()))
def test_handoff_attempts_every_close_and_preserves_primary(
    desktop, primary_type, error_type, mask
):
    primary = primary_type("inert primary refusal") if primary_type else None
    fake = FakeOS(desktop, primary, mask, error_type)
    namespace = functions(
        os=fake,
        tempfile=SimpleNamespace(mkdtemp=lambda **kwargs: "/output/.stage"),
        LAUNCHERS=("one", "two"),
        _require_output_directory=fake.acquire,
        _read_output_file=lambda path, fd, name, limit: fake.files[fd][name],
        _state=lambda *args: (1,),
        _rename_new=lambda *args: None,
    )
    namespace["_same_directory"] = lambda *args: None
    observed = None
    try:
        namespace["handoff"](
            PurePosixPath("/source"), PurePosixPath("/output/desktop"), "lint", desktop
        )
    except BaseException as error:
        observed = error
    expected = primary
    if expected is None:
        expected = next(iter(fake.close_errors.values()), None)
    assert observed is expected
    assert [fd for fd in fake.closes if fd < 20] == fake.directory_fds
    assert not fake.active


@pytest.mark.parametrize("primary_type", [None, OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_type", [None, OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("directory_failures", [False, True])
def test_copy_failure_survives_member_and_directory_cleanup(
    primary_type, close_type, directory_failures
):
    primary = primary_type("inert write refusal") if primary_type else None
    fake = FakeOS(True, None, 7 if directory_failures else 0, OSError)
    fake.write_error = primary
    member_error = close_type("inert member close refusal") if close_type else None
    if member_error is not None:
        fake.close_errors[20] = member_error
    namespace = functions(
        os=fake,
        tempfile=SimpleNamespace(mkdtemp=lambda **kwargs: "/output/.stage"),
        LAUNCHERS=("one", "two"),
        _require_output_directory=fake.acquire,
        _read_output_file=lambda path, fd, name, limit: fake.files[fd][name],
        _state=lambda *args: (1,),
        _rename_new=lambda *args: None,
    )
    namespace["_same_directory"] = lambda *args: None
    observed = None
    try:
        namespace["handoff"](
            PurePosixPath("/source"), PurePosixPath("/output/desktop"), "lint", True
        )
    except BaseException as error:
        observed = error
    expected = primary if primary is not None else member_error
    if expected is None:
        expected = next(iter(fake.close_errors.values()), None)
    assert observed is expected
    assert [fd for fd in fake.closes if fd < 20] == [12, 11, 10]
    assert not fake.active


@pytest.mark.parametrize(
    "primary_type", [None, ValueError, KeyboardInterrupt, SystemExit]
)
@pytest.mark.parametrize("close_type", [None, OSError, KeyboardInterrupt, SystemExit])
def test_binding_check_preserves_primary(primary_type, close_type):
    primary = primary_type("inert binding refusal") if primary_type else None
    close_error = close_type("inert close refusal") if close_type else None
    closed = []

    def metadata(fd):
        if primary is not None:
            raise primary
        return SimpleNamespace(st_dev=1, st_ino=2)

    def close(fd):
        closed.append(fd)
        if close_error is not None:
            raise close_error

    namespace = functions(
        os=SimpleNamespace(fstat=metadata, close=close),
        _require_output_directory=lambda *args: 11,
    )
    observed = None
    try:
        namespace["_same_directory"](PurePosixPath("/fixture"), 10)
    except BaseException as error:
        observed = error
    assert observed is (primary if primary is not None else close_error)
    assert closed == [11]


@pytest.mark.parametrize("chunk", [1, 2, 100])
@pytest.mark.parametrize("raw", [b"", b"x", b"fixture\xffpayload"])
def test_exclusive_member_handles_short_writes(chunk, raw):
    fake = FakeOS(False, None, 0, OSError)
    original_write = fake.write
    fake.write = lambda fd, data: original_write(fd, data[:chunk])
    namespace = functions(os=fake)
    namespace["_write_new_file"](12, "lint.json", raw, 0o600)
    assert fake.files[12]["lint.json"] == raw
    assert fake.closes == [20]
    assert not fake.active


@pytest.mark.parametrize("stage", ["write", "fchmod", "fsync"])
@pytest.mark.parametrize("primary_type", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_fails", [False, True])
def test_member_failure_preserves_identity(stage, primary_type, close_fails):
    fake = FakeOS(False, None, 0, OSError)
    primary = primary_type("inert member failure")
    if close_fails:
        fake.close_errors[20] = OSError("inert cleanup failure")

    def fail(*args):
        raise primary

    setattr(fake, stage, fail)
    namespace = functions(os=fake)
    observed = None
    try:
        namespace["_write_new_file"](12, "lint.json", b"fixture", 0o600)
    except BaseException as error:
        observed = error
    assert observed is primary
    assert fake.closes == [20]
    assert not fake.active


def test_zero_length_write_is_a_failure():
    fake = FakeOS(False, None, 0, OSError)
    fake.write = lambda *args: 0
    namespace = functions(os=fake)
    with pytest.raises(OSError, match="made no progress"):
        namespace["_write_new_file"](12, "lint.json", b"fixture", 0o600)
    assert fake.files[12]["lint.json"] == b""
    assert fake.closes == [20]
    assert not fake.active


@pytest.mark.parametrize(
    "desktop,acquired", [(False, 1), (False, 2), (True, 1), (True, 2), (True, 3)]
)
@pytest.mark.parametrize("primary_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("close_fails", [False, True])
def test_interruption_after_directory_acquisition_is_owned(
    desktop, acquired, primary_type, close_fails
):
    fake = FakeOS(desktop, None, 7 if close_fails else 0, OSError)
    namespace = functions(
        os=fake,
        tempfile=SimpleNamespace(mkdtemp=lambda **kwargs: "/output/.stage"),
        LAUNCHERS=("one", "two"),
        _require_output_directory=fake.acquire,
        _read_output_file=lambda path, fd, name, limit: fake.files[fd][name],
        _state=lambda *args: (1,),
        _rename_new=lambda *args: None,
    )
    namespace["_same_directory"] = lambda *args: None
    handoff = namespace["handoff"]
    primary = primary_type("inert acquisition interruption")
    injected = []

    def trace(frame, event, argument):
        if frame.f_code is handoff.__code__ and event == "line":
            if len(fake.acquisitions) == acquired and not injected:
                injected.append(True)
                raise primary
        return trace

    previous = sys.gettrace()
    observed = None
    try:
        sys.settrace(trace)
        handoff(
            PurePosixPath("/source"), PurePosixPath("/output/desktop"), "lint", desktop
        )
    except BaseException as error:
        observed = error
    finally:
        sys.settrace(previous)
    assert injected == [True]
    assert observed is primary
    assert fake.closes == list(reversed(fake.acquisitions))
    assert not fake.active
    assert sys.gettrace() is previous
