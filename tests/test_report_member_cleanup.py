"""Member files and optional logs keep their own failure and handle ownership."""

import hashlib
import os
import stat
import sys
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostics, support_export as export


@pytest.fixture
def member_state(monkeypatch):
    state = SimpleNamespace(opened=[], closed=[], primary=None, close_error=None,
                            open_error=None, cursor=0, published=False, events=[])
    snapshot = SimpleNamespace(st_dev=1, st_ino=2, st_size=4, st_mode=stat.S_IFREG | 0o600,
                               st_uid=0, st_nlink=1, st_mtime_ns=3, st_ctime_ns=4)

    def open_file(*_args, **_kwargs):
        if state.open_error:
            raise state.open_error
        state.opened.append(17)
        return 17

    def close_file(fd):
        assert fd == 17 and not state.closed
        state.closed.append(fd)
        if state.close_error:
            raise state.close_error

    def read_file(_fd, count):
        if state.primary:
            raise state.primary
        data = b"data"[state.cursor:state.cursor + count]
        state.cursor += len(data)
        return data

    def write_file(_fd, data):
        if state.primary:
            raise state.primary
        return len(data)

    def seek_file(*_args):
        state.cursor = 0

    def rename_file(*_args, **_kwargs):
        state.published = True

    monkeypatch.setattr(export, "os", SimpleNamespace(
        O_WRONLY=os.O_WRONLY, O_CREAT=os.O_CREAT, O_EXCL=os.O_EXCL,
        O_RDONLY=os.O_RDONLY, O_NOFOLLOW=os.O_NOFOLLOW, O_NONBLOCK=os.O_NONBLOCK,
        SEEK_SET=os.SEEK_SET, open=open_file, close=close_file, read=read_file,
        write=write_file, fsync=lambda *_a: None, fstat=lambda *_a: snapshot,
        stat=lambda *_a, **_k: snapshot, getuid=lambda: 0, lseek=seek_file,
        rename=rename_file,
    ))
    monkeypatch.setattr(diagnostics, "log_diag", lambda *args: state.events.append(args))
    return state


def invoke(helper):
    if helper == "write":
        return export._write_exclusive(99, "DATA", b"data")
    if helper == "read":
        return export._read_at(99, "DATA", private=True)
    return export.read_export_log("/inert/log", expected_sha256=hashlib.sha256(b"data").hexdigest(), expected_size_bytes=4)


@pytest.mark.parametrize("helper", ["write", "read", "optional"])
@pytest.mark.parametrize("primary_type", [export.SafetyError, KeyboardInterrupt])
@pytest.mark.parametrize("close_type", [OSError, KeyboardInterrupt])
def test_member_primary_survives_close_failure(member_state, helper, primary_type, close_type):
    primary = primary_type("private I/O refusal")
    member_state.primary = primary
    member_state.close_error = close_type("private close detail")
    with pytest.raises(BaseException) as caught:
        invoke(helper)
    assert caught.value is primary
    assert member_state.closed == member_state.opened == [17]
    assert not member_state.published


@pytest.mark.parametrize("helper", ["write", "read", "optional"])
@pytest.mark.parametrize("close_type", [OSError, KeyboardInterrupt])
def test_member_close_failure_cannot_publish_or_return_trusted_bytes(member_state, helper, close_type):
    error = close_type("close failed")
    member_state.close_error = error
    if helper == "optional" and close_type is OSError:
        assert invoke(helper) == (b"", "unavailable")
    else:
        with pytest.raises(BaseException) as caught:
            invoke(helper)
        assert caught.value is error
    assert member_state.closed == member_state.opened == [17]
    assert not member_state.published


@pytest.mark.parametrize("helper", ["write", "read", "optional"])
def test_member_normal_control(member_state, helper):
    expected = None if helper == "write" else (b"data" if helper == "read" else (b"data", "complete"))
    assert invoke(helper) == expected
    assert member_state.closed == member_state.opened == [17]
    assert member_state.published is (helper == "write")


@pytest.mark.parametrize("helper", ["write", "read", "optional"])
def test_member_interrupted_acquisition_retires_handle(member_state, helper):
    function = {"write": export._write_exclusive, "read": export._read_at,
                "optional": export.read_export_log}[helper]
    primary = KeyboardInterrupt("interruption after member open")
    previous = sys.gettrace()
    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if not fired and event == "line" and frame.f_code is function.__code__ and member_state.opened:
            fired = True
            raise primary
        return interrupt

    try:
        sys.settrace(interrupt)
        with pytest.raises(KeyboardInterrupt) as caught:
            invoke(helper)
    finally:
        sys.settrace(previous)
    assert fired and caught.value is primary
    assert member_state.closed == member_state.opened == [17]
    assert not member_state.published


@pytest.mark.parametrize("helper", ["write", "read", "optional"])
def test_member_failed_open_closes_nothing(member_state, helper):
    error = OSError("open failed")
    member_state.open_error = error
    if helper == "optional":
        assert invoke(helper) == (b"", "unavailable")
    else:
        with pytest.raises(OSError) as caught:
            invoke(helper)
        assert caught.value is error
    assert member_state.opened == member_state.closed == []


def test_optional_log_io_and_close_errors_remain_unavailable(member_state):
    member_state.primary = OSError("read failed")
    member_state.close_error = OSError("close failed")
    assert invoke("optional") == (b"", "unavailable")
    assert member_state.closed == [17]
