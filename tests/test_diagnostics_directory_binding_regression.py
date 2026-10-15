"""Diagnostic paths stay bound to their private directory; fixtures only."""

import json
import os

import pytest

from beamo_wipe import diagnostics


@pytest.mark.parametrize("operation", ["write", "read"])
@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_directory_replacement_during_file_open_is_refused(
    tmp_path, monkeypatch, operation, replacement
):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    logfile = directory / "diagnostics.log"
    logfile.write_text('{"code":"original"}\n')
    logfile.chmod(0o600)
    (outside / "diagnostics.log").write_text('{"code":"outside"}\n')
    (outside / "diagnostics.log").chmod(0o600)
    before = (outside / "diagnostics.log").read_bytes()
    original_open = os.open
    swapped = False

    def swap_before_open(path, *args, **kwargs):
        nonlocal swapped
        if not swapped and os.fspath(path) in {str(logfile), "diagnostics.log"}:
            swapped = True
            directory.rename(tmp_path / "retired")
            if replacement == "symlink":
                directory.symlink_to(outside, target_is_directory=True)
            else:
                directory.mkdir(mode=0o700)
                (directory / "diagnostics.log").write_text('{"code":"replacement"}\n')
                (directory / "diagnostics.log").chmod(0o600)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(diagnostics.os, "open", swap_before_open)
    if operation == "write":
        assert diagnostics.log_diag("audit", "test", log_dir=directory) is False
    else:
        assert diagnostics.read_diagnostics(directory) == []
    assert swapped
    assert (outside / "diagnostics.log").read_bytes() == before


def test_normal_private_directory_write_and_read(tmp_path):
    assert diagnostics.log_diag("audit", "normal", log_dir=tmp_path)
    entries = diagnostics.read_diagnostics(tmp_path)
    assert len(entries) == 1
    assert entries[0]["code"] == "normal"
    assert json.loads((tmp_path / "diagnostics.log").read_text()) == entries[0]


@pytest.mark.parametrize("operation", ["write", "read"])
def test_symlink_log_directory_is_refused(tmp_path, operation):
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (outside / "diagnostics.log").write_text('{"code":"outside"}\n')
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)
    if operation == "write":
        assert diagnostics.log_diag("audit", "test", log_dir=link) is False
    else:
        assert diagnostics.read_diagnostics(link) == []
