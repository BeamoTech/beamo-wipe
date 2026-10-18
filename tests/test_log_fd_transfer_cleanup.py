"""Ordinary-file transfer failure must not leak the unpublished validated FD."""
import os
import stat
import pytest
from beamo_wipe import safety


def test_directory_close_failure_retires_untransferred_log(tmp_path, monkeypatch):
    log = tmp_path / 'engine.log'
    real_open, real_close = os.open, os.close
    opened = {}
    closes = []

    def record_open(path, *args, **kwargs):
        fd = real_open(path, *args, **kwargs)
        opened['directory' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'log'] = fd
        return fd

    def close_directory_then_fail(fd):
        closes.append(fd)
        real_close(fd)
        if fd == opened.get('directory'):
            raise OSError('injected directory close failure')

    try:
        with monkeypatch.context() as patch:
            patch.setattr(safety, 'assert_log_not_on_target', lambda *_args: None)
            patch.setattr(safety.os, 'open', record_open)
            patch.setattr(safety.os, 'close', close_directory_then_fail)
            with pytest.raises(OSError, match='directory close failure'):
                safety.truncate_log_file(str(log), '/dev/sda', retain_fd=True)
        with pytest.raises(OSError):
            os.fstat(opened['log'])
        assert closes.count(opened['directory']) == 1
        assert closes.count(opened['log']) == 1
    finally:
        if 'log' in opened:
            try:
                os.fstat(opened['log'])
            except OSError:
                pass
            else:
                real_close(opened['log'])
