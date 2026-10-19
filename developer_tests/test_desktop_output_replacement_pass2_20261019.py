"""Compiler latency cannot authorize replacing newly appeared launcher files."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


class WindowsOSProxy:
    name = "nt"

    def __getattr__(self, name):
        return getattr(os, name)


@pytest.fixture
def builder():
    path = Path(__file__).resolve().parents[1] / "scripts/build_desktop.py"
    spec = importlib.util.spec_from_file_location("output_replacement_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setup(builder, tmp_path, monkeypatch, host, prior):
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    (desktop / "go.mod").write_text("module fixture\n")
    (desktop / "main.go").write_text("package main\nfunc main() {}\n")
    output = tmp_path / "output with spaces"
    output.mkdir()
    if prior:
        for name in builder.LAUNCHERS:
            (output / name).write_bytes(b"prior compiled launcher")
        (output / "desktop-build.json").write_text(
            json.dumps(
                {
                    "version": "0.2.13",
                    "source_commit": "a" * 40,
                    "source_sha256": "b" * 64,
                    "source_dirty": False,
                    "go": builder.GO_VERSION,
                    "files": {
                        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                        for name in builder.LAUNCHERS
                    },
                }
            )
        )

    def fake_output(argv, **kwargs):
        if argv[1:] == ["version"]:
            return f"go version {builder.GO_VERSION} {host}/amd64\n"
        if argv[1:] == ["rev-parse", "HEAD"]:
            return "a" * 40 + "\n"
        if argv[1:] == ["status", "--porcelain"]:
            return ""
        raise AssertionError(argv)

    def fake_build(argv, **kwargs):
        Path(argv[argv.index("-o") + 1]).write_bytes(b"new compiled launcher")

    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder.subprocess, "check_output", fake_output)
    monkeypatch.setattr(builder.subprocess, "check_call", fake_build)
    if host == "nt":
        monkeypatch.setattr(builder, "os", WindowsOSProxy())
    return output


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("prior", [False, True])
def test_unchanged_output_remains_rebuildable(
    builder, tmp_path, monkeypatch, host, prior
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    builder.build(output)
    builder.build(output)
    manifest = json.loads((output / "desktop-build.json").read_text())
    assert all(
        manifest["files"][name]
        == hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in builder.LAUNCHERS
    )
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize(
    "phase,target_index",
    [
        ("compile-first", 0),
        ("compile-first", 1),
        ("compile-second", 0),
        ("compile-second", 1),
        ("publish-first", 0),
        ("publish-second", 1),
        ("copy-first", 0),
        ("copy-second", 1),
    ],
)
def test_build_preserves_foreign_launcher_replacement(
    builder, tmp_path, monkeypatch, host, prior, phase, target_index
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    target = output / builder.LAUNCHERS[target_index]
    foreign_bytes = b"foreign user output appeared during the build"
    original_build = builder.subprocess.check_call
    original_publish = builder._publish_launcher
    original_copy = builder.shutil.copyfileobj
    counts = {"compile": 0, "publish": 0, "copy": 0}

    def inject(step):
        counts[step] += 1
        ordinal = "first" if counts[step] == 1 else "second"
        if phase == f"{step}-{ordinal}":
            target.write_bytes(foreign_bytes)

    def compile_then_replace(*args, **kwargs):
        original_build(*args, **kwargs)
        inject("compile")

    def replace_then_publish(*args, **kwargs):
        inject("publish")
        return original_publish(*args, **kwargs)

    def copy_then_replace(*args, **kwargs):
        result = original_copy(*args, **kwargs)
        inject("copy")
        return result

    monkeypatch.setattr(builder.subprocess, "check_call", compile_then_replace)
    monkeypatch.setattr(builder, "_publish_launcher", replace_then_publish)
    monkeypatch.setattr(builder.shutil, "copyfileobj", copy_then_replace)
    with pytest.raises(RuntimeError, match="launcher bytes changed"):
        builder.build(output)
    assert target.read_bytes() == foreign_bytes
    assert not (output / "desktop-build.json").exists()
    assert not (output / ".build.lock").exists()
    if phase.startswith("compile") and target_index == 1:
        first = output / builder.LAUNCHERS[0]
        assert (
            first.read_bytes() == b"prior compiled launcher"
            if prior
            else not first.exists()
        )


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("kind", ["symlink", "directory"])
def test_build_preserves_nonregular_output_appearing_during_compilation(
    builder, tmp_path, monkeypatch, host, prior, kind
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    target = output / builder.LAUNCHERS[0]
    outside = tmp_path / "foreign file"
    outside.write_bytes(b"foreign bytes")
    original_build = builder.subprocess.check_call
    calls = 0

    def compile_then_insert(*args, **kwargs):
        nonlocal calls
        original_build(*args, **kwargs)
        calls += 1
        if calls == 1:
            target.unlink(missing_ok=True)
            if kind == "symlink":
                target.symlink_to(outside)
            else:
                target.mkdir()
                (target / "user-data").write_bytes(b"owned directory content")

    monkeypatch.setattr(builder.subprocess, "check_call", compile_then_insert)
    with pytest.raises((RuntimeError, OSError)):
        builder.build(output)
    assert outside.read_bytes() == b"foreign bytes"
    if kind == "symlink":
        assert target.is_symlink()
    else:
        assert (target / "user-data").read_bytes() == b"owned directory content"
    assert not (output / "desktop-build.json").exists()
