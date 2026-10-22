# SPDX-License-Identifier: GPL-3.0-or-later
"""Build identity publication stays on one owned directory and inode."""

from __future__ import annotations

import json
import os

import pytest

from beamo_wipe import build_identity


ARGS = {
    "source_commit": "a" * 40,
    "source_sha256": "b" * 64,
    "build_id": "local",
    "source_dirty": False,
}


def test_leaf_symlink_is_replaced_without_writing_its_target(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"preserve outside bytes")
    target = tmp_path / "build-identity.json"
    target.symlink_to(outside)

    expected = build_identity.write_injected(target, **ARGS)

    assert outside.read_bytes() == b"preserve outside bytes"
    assert not target.is_symlink()
    assert json.loads(target.read_bytes()) == expected
    assert target.stat().st_mode & 0o777 == 0o644


def test_linked_parent_is_rejected_without_publishing_outside(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        build_identity.write_injected(linked / "build-identity.json", **ARGS)

    assert list(outside.iterdir()) == []


def test_repeated_publication_replaces_only_the_identity_entry(tmp_path):
    target = tmp_path / "nested/build-identity.json"
    expected = build_identity.write_injected(target, **ARGS)
    first = target.stat()
    assert build_identity.write_injected(target, **ARGS) == expected
    second = target.stat()

    assert (first.st_dev, first.st_ino) != (second.st_dev, second.st_ino)
    assert json.loads(target.read_bytes()) == expected
    assert not list(target.parent.glob(".build-identity-*"))


def test_replacement_after_publish_is_detected_and_preserved(tmp_path, monkeypatch):
    target = tmp_path / "build-identity.json"
    real_replace = os.replace
    replacement = b"foreign replacement"

    def replace_then_swap(src, dst, *args, **kwargs):
        real_replace(src, dst, *args, **kwargs)
        directory_fd = kwargs["dst_dir_fd"]
        planted = ".foreign-build-identity"
        fd = os.open(
            planted,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o644,
            dir_fd=directory_fd,
        )
        try:
            os.write(fd, replacement)
        finally:
            os.close(fd)
        real_replace(
            planted,
            dst,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )

    monkeypatch.setattr(build_identity.os, "replace", replace_then_swap)
    with pytest.raises(RuntimeError, match="changed during publication"):
        build_identity.write_injected(target, **ARGS)

    assert target.read_bytes() == replacement
    assert not list(tmp_path.glob(".build-identity-*"))


def test_failed_stage_is_retained_without_racy_pathname_cleanup(tmp_path, monkeypatch):
    target = tmp_path / "build-identity.json"

    def reject_stage(*_args, **_kwargs):
        raise RuntimeError("injected staging refusal")

    def forbidden_unlink(*_args, **_kwargs):
        raise AssertionError("failed staging attempted pathname deletion")

    monkeypatch.setattr(
        build_identity, "_verify_identity_publication", reject_stage, raising=False
    )
    monkeypatch.setattr(build_identity.os, "unlink", forbidden_unlink)
    with pytest.raises(RuntimeError, match="injected staging refusal"):
        build_identity.write_injected(target, **ARGS)

    retained = list(tmp_path.glob(".build-identity-*"))
    assert len(retained) == 1
    assert json.loads(retained[0].read_bytes()) == build_identity.injected_payload(
        **ARGS
    )
    assert not target.exists()
