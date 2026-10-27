"""Log reads retain one descriptor owner across interruption and wrapping."""

import stat
import sys
from types import SimpleNamespace

import pytest

from beamo_wipe import nwipe_runner as module


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("close_error", [False, True])
@pytest.mark.parametrize("operation", ["_read_log_tail", "_scan_completion_log"])
@pytest.mark.parametrize("boundary", ["open", "wrapped", "normal"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_log_read_has_one_descriptor_owner(monkeypatch, active, close_error, operation, boundary, error_type):
    handles, closes = {}, []
    wrapped = False
    snapshot = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0,
                               st_dev=1, st_ino=2, st_size=4, st_mtime_ns=3)

    def open_file(*_args):
        handles[17] = "log"
        return 17

    def close_file(fd):
        closes.append(handles.pop(fd, "already-closed"))
        if close_error:
            raise OSError(5, "fake close failure")

    class Stream:
        cursor = 0

        def __init__(self, closefd):
            self.closefd = closefd

        def __enter__(self):
            nonlocal wrapped
            wrapped = True
            return self

        def __exit__(self, *_args):
            if self.closefd:
                close_file(17)
                # Another thread can reuse an FD once the wrapper closes it.
                handles[17] = "unrelated"
            return False

        def fileno(self):
            return 17

        def seek(self, offset, whence=0):
            self.cursor = 4 if whence == 2 else offset

        def read(self, count):
            data = b"data"[self.cursor:self.cursor + count]
            self.cursor += len(data)
            return data

        def readline(self, count):
            return self.read(count)

    monkeypatch.setattr(module, "os", SimpleNamespace(
        open=open_file, close=close_file, O_RDONLY=1, O_NOFOLLOW=2,
        O_NONBLOCK=4, SEEK_END=2, getuid=lambda: 0, fstat=lambda _fd: snapshot,
        fdopen=lambda _fd, _mode, closefd=True: Stream(closefd),
        path=SimpleNamespace(realpath=lambda path: path,
                             basename=lambda path: path.rsplit("/", 1)[-1]),
    ))
    monkeypatch.setattr(module, "_try_log_diag", lambda *_args: None)
    monkeypatch.setattr(module, "_named_private_log_matches", lambda *_args: True)
    monkeypatch.setattr(module, "_status_device_names", lambda _device: [])
    monkeypatch.setattr(module, "nwipe_status_device_field", lambda _device: "sda")
    monkeypatch.setattr(module, "_log_signature", lambda info: (
        info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
    ))
    owner = SimpleNamespace(_log_read_state=SimpleNamespace(),
                            _active_log_identity=("/inert/log", 1, 2) if active else None)
    function = getattr(module.NwipeRunner, operation)
    arguments = ((owner, "/inert/log", 100) if operation == "_read_log_tail"
                 else (owner, "/inert/log", "/dev/sda", (1, 2, 4, 3)))
    primary = error_type("fake read interruption")
    previous_trace = sys.gettrace()
    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if (not fired and boundary != "normal" and event == "line"
                and frame.f_code is function.__code__ and frame.f_locals.get("fd") == 17
                and ((boundary == "open" and not wrapped) or (boundary == "wrapped" and wrapped))):
            fired = True
            raise primary
        return interrupt

    try:
        sys.settrace(interrupt)
        if boundary == "normal":
            expected = ("" if close_error else "data") if operation == "_read_log_tail" else None
            assert function(*arguments) == expected
        else:
            with pytest.raises(error_type) as caught:
                function(*arguments)
            assert caught.value is primary
    finally:
        sys.settrace(previous_trace)
    assert fired is (boundary != "normal")
    assert closes == ["log"]
    assert not handles or handles == {17: "unrelated"}


def test_close_failure_is_not_hidden_by_an_unrelated_caller_exception(monkeypatch):
    close_error = OSError(5, "fake close failure")
    calls = []

    def close(fd):
        calls.append(fd)
        raise close_error

    monkeypatch.setattr(module, "os", SimpleNamespace(close=close))
    try:
        raise ValueError("unrelated caller exception")
    except ValueError:
        with pytest.raises(OSError) as caught:
            module._close_log_read_fd(17)
    assert caught.value is close_error
    assert calls == [17]
