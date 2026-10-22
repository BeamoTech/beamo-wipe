# SPDX-License-Identifier: GPL-3.0-or-later
"""Release-signing CLI files stay bound to one parent, inode, and payload."""

from __future__ import annotations

import os
import stat

import pytest

from beamo_wipe import release_signing


def test_signing_read_rejects_a_linked_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "manifest.json").write_bytes(b"outside manifest")
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="safely|parent"):
        release_signing._read_bytes_file(linked / "manifest.json", what="manifest")


def test_signing_write_rejects_a_linked_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="safely|parent"):
        release_signing._write_new_file(
            linked / "manifest.json.sig", b"signature bytes", 0o644
        )

    assert list(outside.iterdir()) == []


def test_signing_read_rejects_a_hardlinked_input(tmp_path):
    target = tmp_path / "manifest.json"
    target.write_bytes(b"manifest")
    os.link(target, tmp_path / "alias.json")

    with pytest.raises(RuntimeError, match="safely|bound"):
        release_signing._read_bytes_file(target, what="manifest")


def test_signing_read_detects_leaf_replacement_after_open(tmp_path, monkeypatch):
    target = tmp_path / "manifest.json"
    target.write_bytes(b"opened original")
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"path replacement")
    real_open = os.open
    real_replace = os.replace
    swapped = False

    def open_then_swap(path, flags, *args, **kwargs):
        nonlocal swapped
        fd = real_open(path, flags, *args, **kwargs)
        directory_fd = kwargs.get("dir_fd")
        opens_target = (
            os.fspath(path) == os.fspath(target)
            if directory_fd is None
            else os.fspath(path) == target.name
        )
        if opens_target and not swapped:
            swapped = True
            if directory_fd is None:
                real_replace(replacement, target)
            else:
                real_replace(
                    replacement.name,
                    target.name,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
        return fd

    monkeypatch.setattr(release_signing.os, "open", open_then_swap)
    with pytest.raises(RuntimeError, match="changed|safely"):
        release_signing._read_bytes_file(target, what="manifest")

    assert swapped
    assert target.read_bytes() == b"path replacement"


def test_signing_read_detects_an_in_place_rewrite(tmp_path, monkeypatch):
    target = tmp_path / "manifest.json"
    target.write_bytes(b"opened original")
    real_fstat = os.fstat
    changed = False

    def fstat_then_rewrite(fd):
        nonlocal changed
        metadata = real_fstat(fd)
        if stat.S_ISREG(metadata.st_mode) and not changed:
            changed = True
            target.write_bytes(b"mutated content")
        return metadata

    monkeypatch.setattr(release_signing.os, "fstat", fstat_then_rewrite)
    with pytest.raises(RuntimeError, match="changed|safely|bound"):
        release_signing._read_bytes_file(target, what="manifest")

    assert changed
    assert target.read_bytes() == b"mutated content"


def test_signing_read_detects_parent_replacement_after_open(tmp_path, monkeypatch):
    parent = tmp_path / "requested"
    parent.mkdir()
    target = parent / "manifest.json"
    target.write_bytes(b"opened original")
    moved = tmp_path / "moved"
    replacement_parent = tmp_path / "replacement-parent"
    replacement_parent.mkdir()
    real_open = os.open
    swapped = False

    def open_then_swap_parent(path, flags, *args, **kwargs):
        nonlocal swapped
        fd = real_open(path, flags, *args, **kwargs)
        directory_fd = kwargs.get("dir_fd")
        opens_target = (
            os.fspath(path) == os.fspath(target)
            if directory_fd is None
            else os.fspath(path) == target.name
        )
        if opens_target and not swapped:
            swapped = True
            parent.rename(moved)
            replacement_parent.rename(parent)
        return fd

    monkeypatch.setattr(release_signing.os, "open", open_then_swap_parent)
    with pytest.raises(RuntimeError, match="changed|safely|parent"):
        release_signing._read_bytes_file(target, what="manifest")

    assert swapped
    assert (moved / target.name).read_bytes() == b"opened original"
    assert not target.exists()


def test_signing_write_detects_post_sync_replacement(tmp_path, monkeypatch):
    target = tmp_path / "manifest.json.sig"
    foreign = tmp_path / "foreign.sig"
    foreign.write_bytes(b"foreign signature")
    real_fsync = os.fsync
    real_replace = os.replace
    swapped = False

    def sync_then_swap(fd):
        nonlocal swapped
        real_fsync(fd)
        if not swapped:
            swapped = True
            real_replace(foreign, target)

    monkeypatch.setattr(release_signing.os, "fsync", sync_then_swap)
    with pytest.raises(RuntimeError, match="changed|safely"):
        release_signing._write_new_file(target, b"intended signature", 0o644)

    assert swapped
    assert target.read_bytes() == b"foreign signature"


@pytest.mark.parametrize(
    "mutation", ["rewrite", "truncate", "mode", "hardlink", "symlink"]
)
def test_signing_write_detects_post_sync_mutation(tmp_path, monkeypatch, mutation):
    target = tmp_path / "manifest.json.sig"
    alias = tmp_path / "alias.sig"
    foreign = tmp_path / "foreign.sig"
    foreign.write_bytes(b"foreign signature")
    real_fsync = os.fsync
    changed = False

    def sync_then_mutate(fd):
        nonlocal changed
        real_fsync(fd)
        if changed:
            return
        changed = True
        if mutation == "rewrite":
            target.write_bytes(b"altered signature")
        elif mutation == "truncate":
            target.write_bytes(b"x")
        elif mutation == "mode":
            target.chmod(0o600)
        elif mutation == "hardlink":
            os.link(target, alias)
        else:
            target.unlink()
            target.symlink_to(foreign)

    monkeypatch.setattr(release_signing.os, "fsync", sync_then_mutate)
    with pytest.raises(RuntimeError, match="changed|safely"):
        release_signing._write_new_file(target, b"intended signature", 0o644)

    assert changed
    if mutation == "rewrite":
        assert target.read_bytes() == b"altered signature"
    elif mutation == "truncate":
        assert target.read_bytes() == b"x"
    elif mutation == "mode":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
    elif mutation == "hardlink":
        assert os.path.samefile(target, alias)
    else:
        assert target.is_symlink()
        assert foreign.read_bytes() == b"foreign signature"


def test_signing_regular_read_and_write_control(tmp_path):
    source = tmp_path / "manifest.json"
    source.write_bytes(b"exact manifest")
    assert (
        release_signing._read_bytes_file(source, what="manifest") == b"exact manifest"
    )

    output = tmp_path / "manifest.json.sig"
    release_signing._write_new_file(output, b"exact signature", 0o600)
    assert output.read_bytes() == b"exact signature"
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
