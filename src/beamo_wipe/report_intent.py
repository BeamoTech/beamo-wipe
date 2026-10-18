# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal volatile preference recovery for kiosk process restarts.

This is neither a report nor an export receipt. The live /tmp filesystem is
lost on shutdown. No device identifier, report content or erase authorization
is stored here. Invalid state raises so the controller keeps shutdown guarded.
"""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path

from beamo_wipe.safety import SafetyError, default_log_dir


class ReportIntentStore:
    NAME = "report-intent"

    def __init__(self, directory: Path | None = None):
        self.directory = directory

    def _verify_directory(self, fd: int) -> None:
        from beamo_wipe import safety

        path = self.directory if self.directory is not None else safety.DEFAULT_LOG_DIR
        opened = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        if (
            (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino)
            or not stat.S_ISDIR(named.st_mode)
            or named.st_uid != os.getuid()
            or stat.S_IMODE(named.st_mode) != 0o700
        ):
            raise SafetyError("Unsafe report preference directory")

    def _directory_fd(self) -> int:
        path = self.directory if self.directory is not None else default_log_dir()
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            st = os.fstat(fd)
            if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700:
                raise SafetyError("Unsafe report preference directory")
            self._verify_directory(fd)
        except BaseException:
            os.close(fd)
            raise
        return fd

    def load(self) -> bool:
        directory = self._directory_fd()
        try:
            try:
                fd = os.open(
                    self.NAME,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
            except FileNotFoundError:
                self._verify_directory(directory)
                return False
            try:
                st = os.fstat(fd)
                if (
                    not stat.S_ISREG(st.st_mode)
                    or st.st_uid != os.getuid()
                    or stat.S_IMODE(st.st_mode) != 0o600
                    or st.st_nlink != 1
                ):
                    raise SafetyError("Unsafe report preference file")
                data = b""
                while len(data) < 32:
                    chunk = os.read(fd, 32 - len(data))
                    if not chunk:
                        break
                    data += chunk
                if data not in {b"wanted\n", b"not-wanted\n"}:
                    raise SafetyError("Invalid report preference")
                after = os.fstat(fd)
                named = os.stat(self.NAME, dir_fd=directory, follow_symlinks=False)
                if (
                    (after.st_dev, after.st_ino) != (named.st_dev, named.st_ino)
                    or (st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_mode, st.st_nlink)
                    != (after.st_size, after.st_mtime_ns, after.st_ctime_ns,
                        after.st_mode, after.st_nlink)
                    or len(data) != st.st_size
                ):
                    raise SafetyError("Unsafe report preference file")
                self._verify_directory(directory)
                return data == b"wanted\n"
            finally:
                os.close(fd)
        finally:
            os.close(directory)

    def save(self, wanted: bool) -> None:
        if type(wanted) is not bool:
            raise ValueError("Report intent must be boolean")
        directory = self._directory_fd()
        temporary = ".report-intent-" + secrets.token_hex(12)
        created = False
        try:
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            created = True
            try:
                data = b"wanted\n" if wanted else b"not-wanted\n"
                while data:
                    size = os.write(fd, data)
                    if size <= 0:
                        raise OSError("Incomplete report preference write")
                    data = data[size:]
                os.fsync(fd)
            finally:
                os.close(fd)
            self._verify_directory(directory)
            os.replace(temporary, self.NAME, src_dir_fd=directory, dst_dir_fd=directory)
            created = False
            os.fsync(directory)
            self._verify_directory(directory)
        finally:
            try:
                if created:
                    os.unlink(temporary, dir_fd=directory)
            finally:
                os.close(directory)
