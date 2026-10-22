"""Evidence publication retains the exact private bytes across every boundary."""

import errno
import os
import stat

import pytest

from beamo_wipe import evidence
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize("data", [b"", b"original"])
@pytest.mark.parametrize(
    "boundary",
    ["file_fsync", "before_link", "after_link", "temp_unlink", "directory_fsync"],
)
@pytest.mark.parametrize(
    "mutation", ["normal", "same_size", "different_size", "mode", "hardlink", "replacement"],
)
def test_atomic_publication_checks_private_bytes_at_each_boundary(
    tmp_path, monkeypatch, data, boundary, mutation
):
    destination = tmp_path / "result.json"
    real_open, real_fsync, real_link, real_unlink = os.open, os.fsync, os.link, os.unlink
    created = []
    altered = []
    replacement_bytes = b"another writer owns this entry"

    def mutate(name):
        if altered:
            return
        path = tmp_path / str(name)
        altered.append(path)
        if mutation == "same_size":
            path.write_bytes(b"x" * len(data) if data else b"x")
        elif mutation == "different_size":
            path.write_bytes(data + b"changed")
        elif mutation == "mode":
            path.chmod(0o644)
        elif mutation == "hardlink":
            real_link(path, tmp_path / "extra-link")
        elif mutation == "replacement":
            replacement = tmp_path / "replacement"
            replacement.write_bytes(replacement_bytes)
            replacement.chmod(0o600)
            os.replace(replacement, path)

    def track_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if flags & os.O_CREAT and str(path).startswith(".result.json.tmp."):
            created.append(str(path))
        return fd

    def sync(fd):
        result = real_fsync(fd)
        is_directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        if created and boundary == "file_fsync" and not is_directory:
            mutate(created[0])
        elif created and boundary == "directory_fsync" and is_directory:
            mutate(destination.name)
        return result

    def link(source, target, *args, **kwargs):
        if boundary == "before_link":
            mutate(source)
        result = real_link(source, target, *args, **kwargs)
        if boundary == "after_link":
            mutate(target)
        return result

    def unlink(name, *args, **kwargs):
        result = real_unlink(name, *args, **kwargs)
        if boundary == "temp_unlink" and str(name).startswith(".result.json.tmp."):
            mutate(destination.name)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", track_open)
        patch.setattr(os, "fsync", sync)
        patch.setattr(os, "link", link)
        patch.setattr(os, "unlink", unlink)
        if mutation == "normal":
            identity = evidence._atomic_write_bytes(destination, data)
            metadata = destination.stat()
            assert identity == (metadata.st_dev, metadata.st_ino)
            assert destination.read_bytes() == data
            assert stat.S_IMODE(metadata.st_mode) == 0o600
            assert metadata.st_nlink == 1
        else:
            with pytest.raises((SafetyError, OSError)):
                evidence._atomic_write_bytes(destination, data)
    assert created and altered
    if mutation == "replacement":
        assert altered[0].read_bytes() == replacement_bytes
    elif mutation != "normal":
        assert not destination.exists()
    assert not any(tmp_path.glob(".result.json.tmp.*")) or mutation == "replacement"
    # A refused publication does not prevent a clean, separately named retry.
    retry = tmp_path / "retry.json"
    evidence._atomic_write_bytes(retry, data)
    assert retry.read_bytes() == data


@pytest.mark.parametrize("occupied", ["destination", "temporary"])
def test_atomic_publication_preserves_preexisting_entries(tmp_path, monkeypatch, occupied):
    monkeypatch.setattr(evidence.time, "time_ns", lambda: 654321)
    destination = tmp_path / "result.json"
    existing = (
        destination if occupied == "destination"
        else tmp_path / f".result.json.tmp.{os.getpid()}.654321"
    )
    existing.write_bytes(b"existing owner")
    with pytest.raises(FileExistsError):
        evidence._atomic_write_bytes(destination, b"new data")
    assert existing.read_bytes() == b"existing owner"
    if occupied == "temporary":
        assert not destination.exists()


def test_atomic_publication_close_failure_keeps_inode_pinned_and_closes_once(
    tmp_path, monkeypatch
):
    real_open, real_close = os.open, os.close
    opened = []
    closed = []
    failed = False

    def track(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        opened.append(fd)
        return fd

    def close(fd):
        nonlocal failed
        closed.append(fd)
        real_close(fd)
        if len(opened) > 1 and fd == opened[1] and not failed:
            failed = True
            raise OSError(errno.EIO, "ambiguous original close")

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", track)
        patch.setattr(os, "close", close)
        with pytest.raises(OSError, match="ambiguous original close"):
            evidence._atomic_write_bytes(tmp_path / "result.json", b"data")
    assert failed
    assert all(closed.count(fd) == 1 for fd in opened)
    assert not (tmp_path / "result.json").exists()
    assert not any(tmp_path.glob(".result.json.tmp.*"))
    for fd in set(closed):
        with pytest.raises(OSError) as caught:
            os.fstat(fd)
        assert caught.value.errno == errno.EBADF
