# SPDX-License-Identifier: GPL-3.0-or-later
"""Recovery reads must remain bound to the regular file named by the journal."""

import os

import pytest

from beamo_wipe import session_recovery as recovery
from beamo_wipe.safety import SafetyError
from beamo_wipe.session_recovery import NAME, SessionStore


BOOT = "00000000-0000-0000-0000-000000000001"
BUILD = "a" * 64
NAMES = (NAME, "result-sda-1.json", "result-sda-1.json.sha256")
CHANGES = ("replace", "symlink", "directory", "remove")


@pytest.fixture(autouse=True)
def no_native_effects(monkeypatch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native device, process or power action reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
    ):
        monkeypatch.setattr(target, forbidden)
    yield
    assert not effects


def open_store(tmp_path):
    return SessionStore(tmp_path / "private", boot=BOOT, build=BUILD).open()


def mutate_name(path, archive, foreign, change):
    path.rename(archive)
    if change == "replace":
        path.write_bytes(foreign.read_bytes())
        path.chmod(0o600)
    elif change == "symlink":
        path.symlink_to(foreign)
    elif change == "directory":
        path.mkdir(mode=0o700)
        (path / "foreign-content").write_bytes(foreign.read_bytes())


def assert_preserved(path, foreign, change):
    if change == "remove":
        assert not path.exists()
    elif change == "directory":
        assert (path / "foreign-content").read_bytes() == foreign.read_bytes()
    else:
        assert path.read_bytes() == foreign.read_bytes()
        assert path.is_symlink() is (change == "symlink")
    assert foreign.read_bytes() == b"foreign replacement must survive"


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("timing", ("open", "read", "final-metadata"))
@pytest.mark.parametrize("change", CHANGES)
def test_named_recovery_read_rejects_replacement_and_closes_file(
    tmp_path, monkeypatch, name, timing, change
):
    store = open_store(tmp_path)
    path = store.directory / name
    if name != NAME:
        path.write_bytes(b"original ordinary fixture bytes")
        path.chmod(0o600)
    original = path.read_bytes()
    archive = tmp_path / "old-file"
    foreign = tmp_path / "foreign-file"
    foreign.write_bytes(b"foreign replacement must survive")
    foreign.chmod(0o600)
    target_inode = path.stat().st_ino
    real_open, real_read, real_fstat = os.open, os.read, os.fstat
    opened = []
    changed = []
    stat_calls = 0

    def mutate():
        if not changed:
            changed.append(True)
            mutate_name(path, archive, foreign, change)

    def open_then_change(value, *args, **kwargs):
        fd = real_open(value, *args, **kwargs)
        if value == name:
            opened.append(fd)
            if timing == "open":
                mutate()
        return fd

    def read_then_change(fd, amount):
        data = real_read(fd, amount)
        if timing == "read" and fd in opened and data:
            mutate()
        return data

    def metadata_then_change(fd):
        nonlocal stat_calls
        info = real_fstat(fd)
        if fd in opened and info.st_ino == target_inode:
            stat_calls += 1
            # _file validates once, then read captures before/after snapshots.
            if timing == "final-metadata" and stat_calls == 3:
                mutate()
        return info

    monkeypatch.setattr(recovery.os, "open", open_then_change)
    monkeypatch.setattr(recovery.os, "read", read_then_change)
    monkeypatch.setattr(recovery.os, "fstat", metadata_then_change)
    try:
        with pytest.raises(SafetyError):
            store.read(name)
        assert changed and len(opened) == 1
        assert archive.read_bytes() == original
        assert_preserved(path, foreign, change)
        with pytest.raises(OSError):
            real_fstat(opened[0])
    finally:
        store.close()


@pytest.mark.parametrize("change", CHANGES)
def test_journal_change_after_open_is_invalid_and_corrected_retry_releases_owner(
    tmp_path, monkeypatch, change
):
    first = open_store(tmp_path)
    expected = first.record
    first.close()
    path = first.directory / NAME
    archive = tmp_path / "old-journal"
    foreign = tmp_path / "foreign-file"
    foreign.write_bytes(b"foreign replacement must survive")
    foreign.chmod(0o600)
    real_open = os.open
    changed = []

    def open_then_change(value, *args, **kwargs):
        fd = real_open(value, *args, **kwargs)
        if value == NAME and not changed:
            changed.append(True)
            mutate_name(path, archive, foreign, change)
        return fd

    second = SessionStore(first.directory, boot=BOOT, build=BUILD)
    monkeypatch.setattr(recovery.os, "open", open_then_change)
    try:
        second.open()
        assert second.previous and second.invalid and second.record is None
        assert_preserved(path, foreign, change)
    finally:
        second.close()
    monkeypatch.setattr(recovery.os, "open", real_open)
    if change == "directory":
        (path / "foreign-content").unlink()
        path.rmdir()
    else:
        path.unlink(missing_ok=True)
    archive.rename(path)
    third = SessionStore(first.directory, boot=BOOT, build=BUILD).open()
    try:
        assert third.previous and not third.invalid
        assert third.record == expected
    finally:
        third.close()


def test_read_rechecks_name_after_file_validation_returns(tmp_path, monkeypatch):
    store = open_store(tmp_path)
    path = store.directory / NAME
    foreign = tmp_path / "foreign-file"
    foreign.write_bytes(b"foreign replacement must survive")
    foreign.chmod(0o600)
    original_file = store._file

    def validated_then_changed(*args, **kwargs):
        fd = original_file(*args, **kwargs)
        mutate_name(path, tmp_path / "old-journal", foreign, "replace")
        return fd

    monkeypatch.setattr(store, "_file", validated_then_changed)
    try:
        with pytest.raises(SafetyError):
            store.read(NAME)
        assert_preserved(path, foreign, "replace")
    finally:
        store.close()


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("chunk_size", (1, 7))
def test_unchanged_named_reads_keep_short_read_and_repeated_read_support(
    tmp_path, monkeypatch, name, chunk_size
):
    store = open_store(tmp_path)
    path = store.directory / name
    if name != NAME:
        path.write_bytes(b"ordinary verified bytes")
        path.chmod(0o600)
    expected = path.read_bytes()
    real_read = os.read
    monkeypatch.setattr(recovery.os, "read", lambda fd, size: real_read(fd, min(size, chunk_size)))
    try:
        assert store.read(name) == expected
        assert store.read(name) == expected
    finally:
        store.close()
