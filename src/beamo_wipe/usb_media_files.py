# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic file list for a Beamo Wipe USB FAT tree. Read-only, stdlib only.

The USB image builder records this list in ``.img.json`` so the stick check can
compare a mounted stick with the signed release file for file. This module only
reads regular files; links, junctions and special files fail closed.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Any, Dict, List
import unicodedata

CHUNK = 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
# Characters FAT cannot store, plus controls. A signed list naming one of
# these is not a list of files that a FAT stick could actually hold.
_UNSAFE_NAME_RE = re.compile(r'[\x00-\x1f"*:<>?\\|]')
MAX_PATH_CHARS = 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class MediaListError(RuntimeError):
    """The tree or list is not a safe, deterministic set of regular files."""


def is_link_like(metadata: os.stat_result) -> bool:
    """True for symlinks and Windows reparse points (junctions, mount folders)."""
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE
    )


def media_path_key(path: str) -> str:
    """Comparison key: FAT names are case-insensitive; macOS may decompose."""
    return unicodedata.normalize("NFC", path).casefold()


def check_media_path(path: object) -> str:
    """Return ``path`` if it is a safe relative POSIX path, else raise."""
    if not isinstance(path, str) or not path or len(path) > MAX_PATH_CHARS:
        raise MediaListError(f"unsafe media path: {path!r}")
    parts = path.split("/")
    for part in parts:
        if (
            part in {"", ".", ".."}
            or _UNSAFE_NAME_RE.search(part)
            or part != part.rstrip(". ")
        ):
            raise MediaListError(f"unsafe media path: {path!r}")
    return path


def validate_media_files(value: object) -> List[Dict[str, Any]]:
    """Validate a ``files`` list: exact fields, safe paths, strictly sorted.

    Paths must be unique even when compared case-insensitively, because a FAT
    volume cannot hold two names that differ only in case.
    """
    if not isinstance(value, list) or not value:
        raise MediaListError("media file list must be a non-empty list")
    keys = set()
    previous = None
    clean = []
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise MediaListError(
                "media file entries need exactly path, bytes and sha256"
            )
        path = check_media_path(entry["path"])
        size, digest = entry["bytes"], entry["sha256"]
        if type(size) is not int or size < 0:
            raise MediaListError(f"invalid size for {path!r}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise MediaListError(f"invalid SHA256 for {path!r}")
        if previous is not None and path <= previous:
            raise MediaListError("media file list is not strictly sorted by path")
        key = media_path_key(path)
        if key in keys:
            raise MediaListError(
                f"media file list has a case-insensitive duplicate: {path!r}"
            )
        keys.add(key)
        previous = path
        clean.append({"path": path, "bytes": size, "sha256": digest})
    # A file and a folder cannot share one name on the stick.
    for key in keys:
        parts = key.split("/")
        for depth in range(1, len(parts)):
            if "/".join(parts[:depth]) in keys:
                raise MediaListError(f"media path is both a file and a folder: {key!r}")
    return clean


def _hash_regular(path: Path, expected: os.stat_result) -> tuple[int, str]:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_size != expected.st_size:
            raise MediaListError(f"file changed while listing: {path}")
        digest = hashlib.sha256()
        count = 0
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            count += len(chunk)
            digest.update(chunk)
    if count != expected.st_size:
        raise MediaListError(f"file changed while listing: {path}")
    return count, digest.hexdigest()


def list_media_files(root: Path) -> List[Dict[str, Any]]:
    """Walk ``root`` without following links; return sorted path/bytes/sha256.

    Raises :class:`MediaListError` for a link, junction, special file or any
    name that the stick check could not compare unambiguously.
    """
    root = Path(root)
    try:
        top = os.lstat(root)
    except OSError as exc:
        raise MediaListError(f"media tree is unreadable: {root}") from exc
    if is_link_like(top) or not stat.S_ISDIR(top.st_mode):
        raise MediaListError(f"media tree root is not a real directory: {root}")
    entries: List[Dict[str, Any]] = []
    pending = [(root, "")]
    while pending:
        directory, prefix = pending.pop()
        with os.scandir(directory) as scan:
            children = sorted(scan, key=lambda item: item.name)
        for child in children:
            rel = prefix + child.name
            metadata = child.stat(follow_symlinks=False)
            if is_link_like(metadata):
                raise MediaListError(f"linked media entry is not allowed: {rel}")
            if stat.S_ISDIR(metadata.st_mode):
                check_media_path(rel)
                pending.append((Path(child.path), rel + "/"))
            elif stat.S_ISREG(metadata.st_mode):
                size, digest = _hash_regular(Path(child.path), metadata)
                entries.append(
                    {"path": check_media_path(rel), "bytes": size, "sha256": digest}
                )
            else:
                raise MediaListError(f"special media entry is not allowed: {rel}")
    if not entries:
        raise MediaListError(f"media tree has no files: {root}")
    entries.sort(key=lambda entry: entry["path"])
    return validate_media_files(entries)
