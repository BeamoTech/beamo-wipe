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
from typing import Callable

from beamo_wipe.safety import SafetyError, default_log_dir


def _cleanup_report_handles(
    directory: int | None,
    fd: int | None,
    temporary: str | None = None,
    *,
    primary: BaseException | None = None,
) -> None:
    """Attempt each owned cleanup once without replacing an operation failure."""
    failures: list[BaseException] = []

    def attempt(stage: str, action: Callable[[], object]) -> None:
        try:
            action()
        except BaseException as error:
            failures.append(error)
            try:
                from beamo_wipe.diagnostics import log_diag

                log_diag("report_intent", stage, type(error).__name__)
            except BaseException:
                pass

    if directory is not None and fd is not None and temporary is not None:
        file_handle, directory_handle, name = fd, directory, temporary

        def remove_owned_temporary() -> None:
            opened = os.fstat(file_handle)
            try:
                named = os.stat(name, dir_fd=directory_handle, follow_symlinks=False)
            except FileNotFoundError:
                return
            # Keep the descriptor open through this check; preserve replacements.
            if (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino):
                os.unlink(name, dir_fd=directory_handle)

        attempt("temporary_cleanup", remove_owned_temporary)
    if fd is not None:
        attempt("file_close", lambda: os.close(fd))
    if directory is not None:
        attempt("directory_close", lambda: os.close(directory))
    if primary is None and failures:
        raise failures[0]


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
        fd = None
        try:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            st = os.fstat(fd)
            if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700:
                raise SafetyError("Unsafe report preference directory")
            self._verify_directory(fd)
            return fd
        except BaseException as error:
            _cleanup_report_handles(None, fd, primary=error)
            raise

    def load(self) -> bool:
        directory = fd = None
        primary = None
        try:
            try:
                directory = self._directory_fd()
                fd = os.open(
                    self.NAME,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
            except FileNotFoundError:
                if directory is None:
                    raise
                self._verify_directory(directory)
                return False
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
            fields = (
                "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
                "st_mtime_ns", "st_ctime_ns",
            )
            if (
                any(getattr(after, key) != getattr(named, key) for key in fields)
                or (st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_mode, st.st_nlink)
                != (after.st_size, after.st_mtime_ns, after.st_ctime_ns,
                    after.st_mode, after.st_nlink)
                or len(data) != st.st_size
            ):
                raise SafetyError("Unsafe report preference file")
            self._verify_directory(directory)
            return data == b"wanted\n"
        except BaseException as error:
            primary = error
            raise
        finally:
            _cleanup_report_handles(directory, fd, primary=primary)

    def _verify_publication(self, directory: int, fd: int, name: str, data: bytes) -> None:
        """Bind the named private file to our still-open inode and exact bytes."""
        fields = (
            "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
            "st_mtime_ns", "st_ctime_ns",
        )
        opened = os.fstat(fd)
        named = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (
            any(getattr(opened, key) != getattr(named, key) for key in fields)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(opened.st_mode) != 0o600
            or opened.st_nlink != 1
            or opened.st_size != len(data)
        ):
            raise SafetyError("Unsafe report preference file")
        received = b""
        while len(received) <= len(data):
            chunk = os.pread(fd, len(data) + 1 - len(received), len(received))
            if not chunk:
                break
            received += chunk
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if received != data or any(
            getattr(opened, key) != getattr(after, key)
            or getattr(after, key) != getattr(named, key)
            for key in fields
        ):
            raise SafetyError("Unsafe report preference file")

    def save(self, wanted: bool) -> None:
        if type(wanted) is not bool:
            raise ValueError("Report intent must be boolean")
        directory = fd = None
        temporary = None
        primary = None
        try:
            directory = self._directory_fd()
            temporary = ".report-intent-" + secrets.token_hex(12)
            fd = os.open(
                temporary,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            data = b"wanted\n" if wanted else b"not-wanted\n"
            pending = data
            while pending:
                size = os.write(fd, pending)
                if size <= 0:
                    raise OSError("Incomplete report preference write")
                pending = pending[size:]
            os.fsync(fd)
            self._verify_directory(directory)
            self._verify_publication(directory, fd, temporary, data)
            os.replace(temporary, self.NAME, src_dir_fd=directory, dst_dir_fd=directory)
            temporary = None
            os.fsync(directory)
            self._verify_directory(directory)
            self._verify_publication(directory, fd, self.NAME, data)
        except BaseException as error:
            primary = error
            raise
        finally:
            _cleanup_report_handles(directory, fd, temporary, primary=primary)
