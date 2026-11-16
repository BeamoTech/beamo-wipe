"""Cached desktop verification stays bound to the named artifact bytes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def builder():
    spec = importlib.util.spec_from_file_location(
        "desktop_builder_output_snapshot_pass14", ROOT / "scripts/build_desktop.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WindowsOSProxy:
    name = "nt"

    def __getattr__(self, name):
        return getattr(os, name)


def _bundle(builder, tmp_path):
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    (desktop / "go.mod").write_text("module fixture\n")
    (desktop / "main.go").write_text("package main\n")
    output = tmp_path / "output"
    output.mkdir()
    files = {}
    for name in builder.LAUNCHERS:
        payload = ("verified " + name).encode()
        (output / name).write_bytes(payload)
        files[name] = hashlib.sha256(payload).hexdigest()
    manifest = {
        "version": "0.2.14",
        "source_commit": "a" * 40,
        "source_sha256": builder.desktop_source_digest(tmp_path),
        "source_dirty": False,
        "go": builder.GO_VERSION,
        "files": files,
    }
    (output / "desktop-build.json").write_text(json.dumps(manifest))
    return output


def _mutation(path, kind, original, metadata):
    if kind == "replace":
        path.rename(path.with_name(path.name + ".old"))
        path.write_bytes(b"foreign replacement")
    elif kind == "restored-mtime":
        path.write_bytes(b"X" * len(original))
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    elif kind == "mode":
        path.chmod(0o400)
    else:
        raise AssertionError(kind)


class MutatingStream:
    def __init__(self, stream, mutate):
        self.stream = stream
        self.mutate = mutate

    def __enter__(self):
        self.stream.__enter__()
        return self

    def __exit__(self, *args):
        return self.stream.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def read(self, *args):
        data = self.stream.read(*args)
        self.mutate()
        return data


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize(
    "artifact", ["desktop-build.json", "Start Beamo Wipe.exe", "Start Beamo Wipe Linux"]
)
@pytest.mark.parametrize("kind", ["replace", "restored-mtime", "mode"])
def test_verifier_refuses_artifact_changed_during_bounded_read(
    builder, tmp_path, monkeypatch, host, artifact, kind
):
    output = _bundle(builder, tmp_path)
    target = output / artifact
    target_metadata = target.stat()
    target_identity = (target_metadata.st_dev, target_metadata.st_ino)
    target_bytes = target.read_bytes()
    changed = False

    def mutate_once():
        nonlocal changed
        if not changed:
            changed = True
            _mutation(target, kind, target_bytes, target_metadata)

    if host == "nt":
        monkeypatch.setattr(builder, "os", WindowsOSProxy())
    if builder.os.name == "posix":
        real_fdopen = builder.os.fdopen

        def fdopen(fd, mode="r", *args, **kwargs):
            identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            stream = real_fdopen(fd, mode, *args, **kwargs)
            if mode == "rb" and identity == target_identity:
                return MutatingStream(stream, mutate_once)
            return stream

        monkeypatch.setattr(builder.os, "fdopen", fdopen)
    else:
        real_open = Path.open

        def path_open(path, mode="r", *args, **kwargs):
            stream = real_open(path, mode, *args, **kwargs)
            if path == target and mode == "rb":
                return MutatingStream(stream, mutate_once)
            return stream

        monkeypatch.setattr(Path, "open", path_open)

    with pytest.raises(RuntimeError, match="manifest|checksum"):
        builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
    assert changed


@pytest.mark.parametrize("host", ["posix", "nt"])
def test_verifier_accepts_unchanged_bounded_bundle(
    builder, tmp_path, monkeypatch, host
):
    output = _bundle(builder, tmp_path)
    if host == "nt":
        monkeypatch.setattr(builder, "os", WindowsOSProxy())
    builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
