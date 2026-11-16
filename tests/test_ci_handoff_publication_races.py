"""Direct, regular-file regressions for CI desktop publication races.

No subprocesses, symlinks, devices or native Windows execution are involved.
The parent owns execution and retention of the failing/passing evidence.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Linux dir_fd publication boundaries"
)
FIRST = "Start Beamo Wipe Linux"
SECOND = "Start Beamo Wipe.exe"
RECEIPT = "desktop-build.json"


@pytest.fixture
def helper(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("handoff_ci_outputs")


def _desktop(tmp_path):
    source = tmp_path / "private-desktop"
    source.mkdir()
    content = {FIRST: b"launcher-A\n", SECOND: b"launcher-B\n"}
    content[RECEIPT] = (
        json.dumps(
            {name: hashlib.sha256(raw).hexdigest() for name, raw in content.items()},
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")
    for name, raw in content.items():
        (source / name).write_bytes(raw)
    (source / SECOND).chmod(0o755)
    parent = tmp_path / "public"
    parent.mkdir()
    return source, parent / "desktop", content


def _snapshot(directory):
    """Names, identities, permissions and bytes; rename may change ctime."""
    directory_info = directory.stat()
    entries = {}
    for path in directory.iterdir():
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode)
        entries[path.name] = (info.st_dev, info.st_ino, info.st_mode, path.read_bytes())
    return (
        directory_info.st_dev,
        directory_info.st_ino,
        directory_info.st_mode,
    ), entries


def test_desktop_rejects_first_launcher_changed_while_copying_second(
    tmp_path, monkeypatch, helper
):
    source, destination, _ = _desktop(tmp_path)
    source_before = _snapshot(source)
    original_read = helper._read_output_file
    first_readback = []
    mutations = []

    def read_and_mutate(output, output_fd, name, limit):
        raw = original_read(output, output_fd, name, limit)
        if output != source and name == FIRST and not first_readback:
            # Remember the actual output FD, including a future private stage.
            first_readback.append((output, output_fd))
        if output == source and name == SECOND and first_readback and not mutations:
            output_path, first_fd = first_readback[0]
            assert original_read(output_path, first_fd, FIRST, 1024) == (
                b"launcher-A\n"
            )
            before = os.stat(FIRST, dir_fd=first_fd, follow_symlinks=False)
            descriptor = os.open(FIRST, os.O_WRONLY | os.O_NOFOLLOW, dir_fd=first_fd)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(b"tampered-A\n")
                stream.flush()
                os.fsync(stream.fileno())
            after = os.stat(FIRST, dir_fd=first_fd, follow_symlinks=False)
            assert (before.st_dev, before.st_ino, before.st_size) == (
                after.st_dev,
                after.st_ino,
                after.st_size,
            )
            assert original_read(output_path, first_fd, FIRST, 1024) == (
                b"tampered-A\n"
            )
            mutations.append(True)
        return raw

    monkeypatch.setattr(helper, "_read_output_file", read_and_mutate)
    refusal = None
    try:
        helper.handoff(source, destination, "desktop-launchers", True)
    except (OSError, RuntimeError) as exc:
        refusal = exc

    assert mutations == [True], "race must occur after the first output readback"
    assert _snapshot(source) == source_before
    assert refusal is not None, "changed launcher must refuse desktop publication"
    assert not (destination / RECEIPT).exists(), (
        "bad bytes must not have a success receipt"
    )


def test_desktop_refuses_same_uid_directory_planted_at_creation_boundary(
    tmp_path, monkeypatch, helper
):
    source, destination, _ = _desktop(tmp_path)
    source_before = _snapshot(source)
    unidentified = tmp_path / "unidentified"
    unidentified.mkdir()
    (unidentified / "sentinel").write_bytes(b"unidentified owner data\n")
    (unidentified / "previous-launcher").write_bytes(b"previous unrelated bytes\n")
    original_directory = _snapshot(unidentified)
    parent_info = destination.parent.stat()
    parent_identity = (parent_info.st_dev, parent_info.st_ino)
    original_mkdir = os.mkdir
    displaced = tmp_path / "displaced-created-directory"
    injections = []
    displaced_identity = []

    def mkdir_and_plant(path, mode=0o777, *, dir_fd=None):
        result = original_mkdir(path, mode, dir_fd=dir_fd)
        if injections:
            return result
        candidate = Path(path)
        if dir_fd is not None:
            info = os.fstat(dir_fd)
            directly_under_parent = (
                (info.st_dev, info.st_ino) == parent_identity
                and not candidate.is_absolute()
                and len(candidate.parts) == 1
            )
            created = destination.parent / candidate
        else:
            created = candidate.absolute()
            directly_under_parent = created.parent == destination.parent
        if directly_under_parent:
            if created == destination:
                # Old direct-publication implementation: replace immediately
                # after mkdir succeeds, before its first directory open.
                info = created.stat()
                displaced_identity.append((info.st_dev, info.st_ino, info.st_mode))
                created.rename(displaced)
            # With private staging, leave the stage alone and plant the same
            # unidentified final directory before its no-replace publication.
            unidentified.rename(destination)
            assert destination.stat().st_uid == os.getuid()
            assert _snapshot(destination) == original_directory
            injections.append(True)
        return result

    monkeypatch.setattr(helper.os, "mkdir", mkdir_and_plant)
    refusal = None
    try:
        helper.handoff(source, destination, "desktop-launchers", True)
    except (OSError, RuntimeError) as exc:
        refusal = exc

    assert injections == [True], "must exercise an actual output creation boundary"
    assert _snapshot(source) == source_before
    assert _snapshot(destination) == original_directory, (
        "unidentified directory changed"
    )
    if displaced_identity:
        assert _snapshot(displaced) == (displaced_identity[0], {})
    assert refusal is not None, "an unidentified same-UID destination must be refused"
    assert not (destination / RECEIPT).exists()


def test_clean_desktop_handoff_preserves_source_and_copies_complete_bundle(
    tmp_path, helper
):
    source, destination, expected = _desktop(tmp_path)
    source_before = _snapshot(source)
    sentinel = destination.parent / "unrelated-sentinel"
    sentinel.write_bytes(b"parent data\n")
    sentinel_before = (sentinel.stat().st_ino, sentinel.read_bytes())

    helper.handoff(source, destination, "desktop-launchers", True)

    assert _snapshot(source) == source_before
    assert (sentinel.stat().st_ino, sentinel.read_bytes()) == sentinel_before
    assert destination.is_dir() and not destination.is_symlink()
    assert {path.name for path in destination.iterdir()} == set(expected)
    for name, raw in expected.items():
        output = destination / name
        assert stat.S_ISREG(output.lstat().st_mode)
        assert output.read_bytes() == raw
        assert stat.S_IMODE(output.stat().st_mode) == stat.S_IMODE(
            (source / name).stat().st_mode
        )


@pytest.mark.parametrize("missing", [RECEIPT, FIRST, "all"])
def test_incomplete_source_cannot_be_published_as_desktop_bundle(
    tmp_path, helper, missing
):
    source, destination, _ = _desktop(tmp_path)
    for path in list(source.iterdir()):
        if missing == "all" or path.name == missing:
            path.unlink()
    before = _snapshot(source)
    with pytest.raises(RuntimeError, match="complete desktop"):
        helper.handoff(source, destination, "desktop-launchers", True)
    assert _snapshot(source) == before
    assert not destination.exists()


def test_replaced_private_stage_is_refused_without_populating_foreign_directory(
    tmp_path, monkeypatch, helper
):
    source, destination, _ = _desktop(tmp_path)
    foreign = tmp_path / "foreign-stage"
    foreign.mkdir()
    (foreign / "sentinel").write_bytes(b"unidentified stage data")
    before = _snapshot(foreign)
    original = helper.tempfile.mkdtemp
    stages = []

    def substituted_stage(*args, **kwargs):
        name = original(*args, **kwargs)
        path = Path(name)
        path.rename(tmp_path / "retained-created-stage")
        foreign.rename(path)
        stages.append(path)
        return name

    monkeypatch.setattr(helper.tempfile, "mkdtemp", substituted_stage)
    refusal = None
    try:
        helper.handoff(source, destination, "desktop-launchers", True)
    except (OSError, RuntimeError) as exc:
        refusal = exc
    assert len(stages) == 1
    assert refusal is not None, "foreign staging content must refuse the handoff"
    assert _snapshot(stages[0]) == before
    assert not destination.exists()
