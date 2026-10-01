"""Portable source inspection and lock cleanup use only temporary fixtures."""

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def builder():
    path = Path(__file__).resolve().parents[1] / "scripts/build_desktop.py"
    spec = importlib.util.spec_from_file_location("portable_desktop_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WindowsOSProxy:
    name = "nt"

    def __getattr__(self, name):
        return getattr(os, name)


@pytest.mark.parametrize("changed_during_read", [False, True])
@pytest.mark.parametrize("host", ["nt", "posix"])
def test_source_ctime_compares_platform_apis(
    builder, tmp_path, monkeypatch, changed_during_read, host
):
    source = tmp_path / "main.go"
    source.write_bytes(b"package main\r\n// exact bytes\x1a\r\n")
    path_ctime = source.lstat().st_ctime_ns

    class SourceOSProxy(WindowsOSProxy):
        reads = 0

        def fstat(self, fd):
            info = os.fstat(fd)
            self.reads += 1
            fields = {
                name: getattr(info, name)
                for name in ("st_mode", "st_dev", "st_ino", "st_size", "st_mtime_ns")
            }
            # Model Windows APIs returning creation time versus change time.
            fields["st_ctime_ns"] = path_ctime + 100
            if changed_during_read and self.reads == 2:
                fields["st_ctime_ns"] += 1
            return SimpleNamespace(**fields)

    proxy = SourceOSProxy()
    proxy.name = host
    monkeypatch.setattr(builder, "os", proxy)
    if changed_during_read or host == "posix":
        with pytest.raises(RuntimeError, match="source input changed or unsafe"):
            builder._read_regular_source(source)
    else:
        assert builder._read_regular_source(source) == source.read_bytes()


@pytest.mark.parametrize("replacement", ["none", "lock", "output"])
def test_native_cleanup_closes_handle_and_preserves_replacement(
    builder, tmp_path, monkeypatch, replacement
):
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    (desktop / "go.mod").write_text("module fixture\n")
    (desktop / "main.go").write_text("package main\n")
    output = tmp_path / "output with spaces"
    lock = output / ".build.lock"

    def fake_output(argv, **kwargs):
        if argv[1:] == ["version"]:
            return "go version go1.26.8 windows/amd64\n"
        return "a" * 40 if argv[1:] == ["rev-parse", "HEAD"] else ""

    def fake_build(argv, **kwargs):
        Path(argv[argv.index("-o") + 1]).write_bytes(kwargs["env"]["GOOS"].encode())

    class CleanupOSProxy(WindowsOSProxy):
        released = False

        def close(self, fd):
            owned = os.fstat(fd)
            current = lock.lstat()
            assert (owned.st_dev, owned.st_ino) == (current.st_dev, current.st_ino)
            os.close(fd)
            self.released = True
            if replacement == "lock":
                lock.rename(output / "original-lock")
                lock.write_text("foreign lock")
            elif replacement == "output":
                original = tmp_path / "original-output"
                output.rename(original)
                output.mkdir()
                # A matching lock file ID does not authorize a different directory.
                os.link(original / ".build.lock", lock)

    proxy = CleanupOSProxy()
    monkeypatch.setattr(builder, "os", proxy)
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder.subprocess, "check_output", fake_output)
    monkeypatch.setattr(builder.subprocess, "check_call", fake_build)
    builder.build(output)
    assert proxy.released
    if replacement == "none":
        assert not lock.exists()
        # The output is immediately reusable after a successful build.
        builder.build(output)
        assert not lock.exists()
    elif replacement == "lock":
        assert lock.read_text() == "foreign lock"
    else:
        assert lock.exists()
        assert (tmp_path / "original-output/.build.lock").exists()
