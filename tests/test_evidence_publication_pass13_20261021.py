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
    [
        "file_fsync",
        "before_publish",
        "after_publish",
        "post_publish_readback",
        "directory_fsync",
    ],
)
@pytest.mark.parametrize(
    "mutation", ["normal", "same_size", "different_size", "mode", "hardlink", "replacement"],
)
def test_atomic_publication_checks_private_bytes_at_each_boundary(
    tmp_path, monkeypatch, data, boundary, mutation
):
    destination = tmp_path / "result.json"
    real_open, real_fsync, real_link = os.open, os.fsync, os.link
    real_publish = evidence._rename_noreplace
    real_stat = os.stat
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

    def publish(directory_fd, source, target):
        if boundary == "before_publish":
            mutate(source)
        result = real_publish(directory_fd, source, target)
        if boundary == "after_publish":
            mutate(target)
        return result

    def inspect(name, *args, **kwargs):
        result = real_stat(name, *args, **kwargs)
        if boundary == "post_publish_readback" and name == destination.name:
            mutate(name)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", track_open)
        patch.setattr(os, "fsync", sync)
        patch.setattr(os, "stat", inspect)
        patch.setattr(evidence, "_rename_noreplace", publish)
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
        replacement_path = altered[0] if boundary == "file_fsync" else destination
        assert replacement_path.read_bytes() == replacement_bytes
    elif mutation != "normal" and boundary == "file_fsync":
        assert not destination.exists()
    leftovers = list(tmp_path.glob(".result.json.tmp.*"))
    assert not leftovers or (mutation != "normal" and boundary == "file_fsync")
    # A refused publication does not prevent a clean, separately named retry.
    retry = tmp_path / "retry.json"
    evidence._atomic_write_bytes(retry, data)
    assert retry.read_bytes() == data


@pytest.mark.parametrize("occupied", ["destination", "temporary"])
def test_atomic_publication_preserves_preexisting_entries(tmp_path, monkeypatch, occupied):
    token = "65" * 16
    monkeypatch.setattr(evidence.secrets, "token_hex", lambda _size: token)
    destination = tmp_path / "result.json"
    existing = (
        destination if occupied == "destination"
        else tmp_path / f".result.json.tmp.{token}"
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
    leftovers = list(tmp_path.glob(".result.json.tmp.*"))
    assert len(leftovers) == 1
    assert leftovers[0].read_bytes() == b"data"
    assert stat.S_IMODE(leftovers[0].stat().st_mode) == 0o600
    for fd in set(closed):
        with pytest.raises(OSError) as caught:
            os.fstat(fd)
        assert caught.value.errno == errno.EBADF
