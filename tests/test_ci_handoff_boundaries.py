"""CI handoff refuses aliases, invalid sources, denied writes and duplicates."""

import errno
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _command(source, destination):
    return [
        sys.executable,
        str(ROOT / "scripts/handoff_ci_outputs.py"),
        "receipts",
        str(source),
        str(destination),
        "lint",
    ]


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_handoff_rejects_nonregular_source(tmp_path, kind):
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"unrelated")
    entry = source / "lint.json"
    if kind == "symlink":
        entry.symlink_to(outside)
    elif kind == "fifo":
        os.mkfifo(entry)
    else:
        entry.mkdir()
    destination = tmp_path / "destination"
    result = subprocess.run(
        _command(source, destination), capture_output=True, timeout=10
    )
    assert result.returncode != 0
    assert outside.read_bytes() == b"unrelated"
    assert not (destination / "lint.json").exists()


def test_handoff_rejects_linked_output_ancestor(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "lint.json").write_bytes(b"receipt")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"unrelated")
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)
    result = subprocess.run(
        _command(source, alias / "evidence"), capture_output=True, timeout=10
    )
    assert result.returncode != 0
    assert {p.name for p in outside.iterdir()} == {"sentinel"}
    assert (outside / "sentinel").read_bytes() == b"unrelated"


def test_handoff_propagates_denied_destination_creation(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    helper = importlib.import_module("handoff_ci_outputs")
    source = tmp_path / "source"
    source.mkdir()
    (source / "lint.json").write_bytes(b"receipt")
    destination = tmp_path / "destination"
    destination.mkdir()
    sentinel = destination / "sentinel"
    sentinel.write_bytes(b"unrelated")
    original = os.open
    attempted = []
    denied = PermissionError(errno.EACCES, "injected owned destination refusal")

    def open_with_denial(path, flags, *args, **kwargs):
        if path == "lint.json" and flags & os.O_WRONLY:
            attempted.append(True)
            raise denied
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(helper.os, "open", open_with_denial)
    with pytest.raises(PermissionError) as failure:
        helper.handoff(source, destination, "lint", False)
    assert failure.value is denied
    assert attempted == [True]
    assert {p.name for p in destination.iterdir()} == {"sentinel"}
    assert sentinel.read_bytes() == b"unrelated"


def test_concurrent_handoffs_have_one_exclusive_winner(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    receipt = source / "lint.json"
    receipt.write_bytes(b"one observed receipt")
    destination = tmp_path / "destination"
    destination.mkdir()
    processes = []
    try:
        for _ in range(2):
            processes.append(
                subprocess.Popen(
                    _command(source, destination),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )
        outputs = [p.communicate(timeout=15) for p in processes]
        assert sorted(p.returncode == 0 for p in processes) == [False, True], outputs
        assert (destination / "lint.json").read_bytes() == receipt.read_bytes()
        assert (destination / "lint.json").stat().st_nlink == 1
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
