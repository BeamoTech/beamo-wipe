"""The compatibility export must not remove another writer's file on failure."""

import hashlib
import os
from pathlib import Path

import pytest

from beamo_wipe import evidence


def test_sidecar_failure_preserves_replaced_destination(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    data = b'{"test":true}\n'
    source.write_bytes(data)
    Path(str(source) + ".sha256").write_text(
        f"{hashlib.sha256(data).hexdigest()}  {source.name}\n", encoding="ascii"
    )
    destination = tmp_path / "usb"
    destination.mkdir()
    exported = destination / source.name
    replacement_data = b"a different writer's file"
    replacement = destination / "replacement.json"
    replacement.write_bytes(replacement_data)
    original_writer = evidence._atomic_write_bytes
    calls = 0

    def replace_before_sidecar_error(path, contents):
        nonlocal calls
        calls += 1
        if calls == 1:
            return original_writer(path, contents)
        os.replace(replacement, exported)
        raise OSError("sidecar write failed")

    monkeypatch.setattr(evidence, "_atomic_write_bytes", replace_before_sidecar_error)
    with pytest.raises(OSError, match="sidecar write failed"):
        evidence.export_evidence(source, destination)

    assert exported.read_bytes() == replacement_data


def test_atomic_writer_finalization_preserves_replaced_destination(tmp_path, monkeypatch):
    """A failed post-publication check cannot delete a new owner of the path."""
    dest = tmp_path / "result.json"
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"replacement")
    original_publish = evidence._rename_noreplace

    def replace_after_publish(directory_fd, source, destination):
        original_publish(directory_fd, source, destination)
        os.replace(replacement, dest)

    monkeypatch.setattr(evidence, "_rename_noreplace", replace_after_publish)
    with pytest.raises(evidence.EvidenceFinalizationError):
        evidence._atomic_write_bytes(dest, b"original")
    assert dest.read_bytes() == b"replacement"
