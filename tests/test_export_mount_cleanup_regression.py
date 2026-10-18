"""Every owned mount-state descriptor is released after a cleanup I/O error."""

import errno
import os
from types import SimpleNamespace

import pytest

from beamo_wipe import support_export as export
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize("failure", ["lock_close", "unmount"])
def test_cleanup_error_still_removes_owned_mount_directory_and_closes_root(
    tmp_path, monkeypatch, failure
):
    root = tmp_path / "run"
    monkeypatch.setattr(export, "MOUNT_ROOT", root)
    real_open, real_close = os.open, os.close
    opened = {}

    def record_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        opened[str(path)] = fd
        return fd

    def close_with_error(fd):
        real_close(fd)
        if failure == "lock_close" and fd == opened.get(".lock"):
            # Linux releases the descriptor even when close reports EIO.
            raise OSError(errno.EIO, "fake cleanup failure")

    def refuse_mount(*_args, **_kwargs):
        raise SafetyError("fake mount refusal")

    def fail_unmount(*_args, **_kwargs):
        raise OSError(errno.EIO, "fake cleanup failure")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", record_open)
            patch.setattr(os, "close", close_with_error)
            patch.setattr(export, "_run_command", refuse_mount)
            if failure == "unmount":
                patch.setattr(export, "_run_command", lambda *_a, **_kw: SimpleNamespace(returncode=0))
                patch.setattr(export, "_mounted_exact", lambda *_a: True)
                patch.setattr(export, "_verify_mount", refuse_mount)
                patch.setattr(export, "_ordinary_unmount", fail_unmount)
            with pytest.raises(OSError, match="fake cleanup failure"):
                export._persist_and_verify_report(
                    SimpleNamespace(fstype="vfat"), None, b"", "unavailable", 0
                )
        with pytest.raises(OSError) as error:
            os.fstat(opened[str(root)])
        assert error.value.errno == errno.EBADF
        assert list(root.iterdir()) == [root / ".lock"]
    finally:
        # The original implementation leaks this FD; keep the proof isolated.
        for fd in set(opened.values()):
            try:
                real_close(fd)
            except OSError:
                pass


@pytest.mark.parametrize("close_error", [False, True])
def test_worker_closes_parent_after_volume_close_error(tmp_path, monkeypatch, close_error):
    import io

    parent, child = tmp_path / "fake-parent", tmp_path / "fake-volume"
    parent.write_bytes(b"parent")
    child.write_bytes(b"volume")
    volume = SimpleNamespace(path=str(child), rdev=0, parent=SimpleNamespace(path=str(parent), rdev=0))
    monkeypatch.setattr(export.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"fake request")))
    monkeypatch.setattr(export, "_decode_worker_request", lambda _: (None, volume, [], set(), b"", "unavailable", False))
    monkeypatch.setattr(export, "_emit_export_marker", lambda *_: None)
    monkeypatch.setattr(export, "run_lsblk", lambda: {})
    monkeypatch.setattr(export, "select_export_volume", lambda *_: volume)
    monkeypatch.setattr(export, "_same_volume", lambda *_a, **_kw: True)
    monkeypatch.setattr(export, "_protected_rdevs", lambda *_: set())
    monkeypatch.setattr(export, "_volume_with_rdev", lambda value: value)
    monkeypatch.setattr(export, "_assert_partition_parent", lambda *_: None)

    def refuse_export(*_a, **_kw):
        raise SafetyError("fake export refusal")

    monkeypatch.setattr(export, "_persist_and_verify_report", refuse_export)
    real_open, real_close = os.open, os.close
    opened = {}

    def record_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        opened[str(path)] = fd
        return fd

    def close(fd):
        real_close(fd)
        if close_error and fd == opened[str(child)]:
            raise OSError(errno.EIO, "fake volume close failure")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", record_open)
            patch.setattr(os, "close", close)
            error = OSError if close_error else SafetyError
            with pytest.raises(error, match="fake (volume close failure|export refusal)"):
                export._worker()
        for fd in opened.values():
            with pytest.raises(OSError) as caught:
                os.fstat(fd)
            assert caught.value.errno == errno.EBADF
    finally:
        for fd in opened.values():
            try:
                real_close(fd)
            except OSError:
                pass
