"""Executable suffixes must not look like output replacement on Windows."""

import importlib.util
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from test_desktop_output_replacement_pass2_20261019 import _setup


@pytest.fixture
def builder():
    path = Path(__file__).resolve().parents[1] / "scripts/build_desktop.py"
    spec = importlib.util.spec_from_file_location("windows_output_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("suffix", [".exe", ".com", ".bat", ".cmd", ""])
def test_unchanged_output_with_executable_suffix(builder, tmp_path, suffix):
    path = tmp_path / ("launcher" + suffix)
    data = b"ordinary owned output fixture\r\n"
    path.write_bytes(data)
    assert builder._read_output_file(tmp_path, None, path.name, 1024) == data


def test_native_manifest_keeps_canonical_line_endings(builder, tmp_path, monkeypatch):
    output = _setup(builder, tmp_path, monkeypatch, "nt", False)
    builder.build(output)
    assert b"\r\n" not in (output / "desktop-build.json").read_bytes()
    builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)


@pytest.mark.parametrize("api", ["path", "handle"])
def test_execute_mode_changes_within_one_stat_api_are_refused(
    builder, tmp_path, monkeypatch, api
):
    path = tmp_path / "launcher.exe"
    path.write_bytes(b"owned output fixture")

    def changed_mode(info):
        fields = {
            name: getattr(info, name) for name in dir(info) if name.startswith("st_")
        }
        fields["st_mode"] ^= stat.S_IXUSR
        return SimpleNamespace(**fields)

    if api == "path":
        original = Path.lstat
        reads = 0

        def lstat(current, *args, **kwargs):
            nonlocal reads
            info = original(current, *args, **kwargs)
            if current == path:
                reads += 1
                if reads == 2:
                    return changed_mode(info)
            return info

        monkeypatch.setattr(Path, "lstat", lstat)
    else:

        class OSProxy:
            reads = 0

            def __getattr__(self, name):
                return getattr(os, name)

            def fstat(self, fd):
                self.reads += 1
                info = os.fstat(fd)
                return changed_mode(info) if self.reads == 2 else info

        monkeypatch.setattr(builder, "os", OSProxy())

    with pytest.raises(OSError, match="output file changed during read"):
        builder._read_output_file(tmp_path, None, path.name, 1024)
