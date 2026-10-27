#!/usr/bin/env python3
"""Copy private CI outputs into new, exclusively claimed destination names.

The isolated CI worker and its gate containers are trusted cooperating peers.
They must leave another invocation's private stage untouched. File-descriptor
checks detect changes to observed objects; they do not establish atomic mkdir
provenance or isolate a hostile process with the same UID.
"""

from __future__ import annotations

import os
import ctypes
from pathlib import Path
import re
import stat
import sys
import tempfile

from build_desktop import LAUNCHERS, _read_output_file, _require_output_directory


def _close_handoff_fds(primary: BaseException | None, *descriptors: int | None) -> None:
    """Attempt each owned close once without replacing an operation failure."""
    first_error = None
    for descriptor in descriptors:
        if descriptor is None:
            continue
        try:
            os.close(descriptor)
        except BaseException as error:
            if first_error is None:
                first_error = error
    if primary is None and first_error is not None:
        raise first_error


def _same_directory(path: Path, descriptor: int) -> None:
    current = None
    primary = None
    try:
        current = _require_output_directory(path)
        assert current is not None
        before, after = os.fstat(descriptor), os.fstat(current)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise RuntimeError("CI output directory changed during handoff")
    except BaseException as error:
        primary = error
        raise
    finally:
        _close_handoff_fds(primary, current)


def _write_new_file(directory_fd: int, name: str, raw: bytes, mode: int) -> None:
    descriptor = None
    primary = None
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_fd,
        )
        pending = memoryview(raw)
        while pending:
            written = os.write(descriptor, pending)
            if written <= 0:
                raise OSError("CI output handoff write made no progress")
            pending = pending[written:]
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    except BaseException as error:
        primary = error
        raise
    finally:
        _close_handoff_fds(primary, descriptor)


def _rename_new(directory_fd: int, source: str, destination: str) -> None:
    """Linux atomic directory publication; an existing name is always refused."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise RuntimeError("CI handoff requires renameat2 without replacement")
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if (
        rename(
            directory_fd, os.fsencode(source), directory_fd, os.fsencode(destination), 1
        )
        != 0
    ):  # RENAME_NOREPLACE
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), destination)


def _state(directory_fd: int, name: str) -> tuple[int, ...]:
    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    return tuple(
        getattr(info, field)
        for field in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def handoff(source: Path, destination: Path, gate: str, desktop: bool) -> None:
    if os.name != "posix" or re.fullmatch(r"[a-z][a-z-]*", gate) is None:
        raise RuntimeError("invalid CI output handoff")
    source_fd = parent_fd = destination_fd = None
    primary = None
    output = destination
    try:
        source_fd = _require_output_directory(source)
        assert source_fd is not None
        if desktop:
            parent_fd = _require_output_directory(destination.parent, create=True)
            assert parent_fd is not None
            _same_directory(destination.parent, parent_fd)
            # Copy into an owned private stage. The final name is never opened
            # for writing and cannot substitute another owner's directory.
            output = Path(
                tempfile.mkdtemp(prefix=".desktop-handoff-", dir=destination.parent)
            )
            destination_fd = _require_output_directory(output)
            assert destination_fd is not None
            named = os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
            opened = os.fstat(destination_fd)
            if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                raise RuntimeError("CI staging parent changed")
        else:
            destination_fd = _require_output_directory(destination, create=True)
        assert destination_fd is not None
        names = sorted(os.listdir(source_fd))
        source_names = set(names)
        if desktop:
            if source_names != {*LAUNCHERS, "desktop-build.json"}:
                raise RuntimeError("a complete desktop bundle is required")
            if os.listdir(destination_fd):
                raise RuntimeError("CI staging directory contains unidentified output")
        if not desktop:
            names = [name for name in names if name.startswith(gate + ".")]
        # The success receipt is copied after the launchers it describes.
        names.sort(key=lambda name: (name == "desktop-build.json", name))
        expected: dict[str, tuple[bytes, tuple[int, ...]]] = {}

        def verify_copied() -> None:
            if set(os.listdir(source_fd)) != source_names:
                raise RuntimeError("private CI output inventory changed")
            observed = set(os.listdir(destination_fd))
            if not desktop:
                observed = {name for name in observed if name.startswith(gate + ".")}
            if observed != set(expected):
                raise RuntimeError("CI output inventory changed during handoff")
            for copied_name, (copied_raw, copied_state) in expected.items():
                if (
                    _read_output_file(
                        output, destination_fd, copied_name, len(copied_raw)
                    )
                    != copied_raw
                    or _state(destination_fd, copied_name) != copied_state
                    or _read_output_file(
                        source, source_fd, copied_name, len(copied_raw)
                    )
                    != copied_raw
                ):
                    raise RuntimeError("CI output changed before complete handoff")

        for name in names:
            if desktop and name == "desktop-build.json":
                verify_copied()
            raw = _read_output_file(source, source_fd, name, 64 * 1024 * 1024)
            metadata = os.stat(name, dir_fd=source_fd, follow_symlinks=False)
            _same_directory(source, source_fd)
            _same_directory(output, destination_fd)
            _write_new_file(
                destination_fd, name, raw, stat.S_IMODE(metadata.st_mode) & 0o777
            )
            if _read_output_file(output, destination_fd, name, len(raw)) != raw:
                raise RuntimeError("CI output handoff readback mismatch")
            if _read_output_file(source, source_fd, name, len(raw)) != raw:
                raise RuntimeError("private CI output changed during handoff")
            expected[name] = (raw, _state(destination_fd, name))
        verify_copied()
        _same_directory(source, source_fd)
        _same_directory(output, destination_fd)
        os.fsync(destination_fd)
        if desktop:
            assert parent_fd is not None
            _same_directory(destination.parent, parent_fd)
            os.fchmod(destination_fd, 0o755)
            _rename_new(parent_fd, output.name, destination.name)
            output = destination
            _same_directory(destination, destination_fd)
            verify_copied()
            os.fsync(parent_fd)
    except BaseException as error:
        primary = error
        raise
    finally:
        _close_handoff_fds(primary, destination_fd, parent_fd, source_fd)


if __name__ == "__main__":
    mode, source_name, destination_name, phase = sys.argv[1:]
    if mode not in {"receipts", "desktop"}:
        raise SystemExit("invalid CI output handoff mode")
    handoff(Path(source_name), Path(destination_name), phase, mode == "desktop")
