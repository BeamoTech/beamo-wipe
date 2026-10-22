"""Interrupted exports and report readback stay bound to the named bytes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys

import pytest

from beamo_wipe import evidence, support_export
from beamo_wipe.safety import SafetyError


def _source(root: Path) -> tuple[Path, bytes]:
    source = root / "result-fixture-1.json"
    data = b'{"outcome":"failed"}\n'
    source.write_bytes(data)
    source.chmod(0o600)
    sidecar = Path(str(source) + evidence.CHECKSUM_SUFFIX)
    sidecar.write_bytes(
        f"{hashlib.sha256(data).hexdigest()}  {source.name}\n".encode("ascii")
    )
    sidecar.chmod(0o600)
    return source, data


def _export_bytes(source: Path, data: bytes) -> tuple[bytes, bytes]:
    return data, (
        f"{hashlib.sha256(data).hexdigest()}  {source.name}\n".encode("ascii")
    )


@pytest.mark.parametrize(
    "victim", ["result.json", "result.json.sha256", "nwipe.log", "COMPLETE"]
)
def test_report_readback_rejects_path_replaced_after_open(
    tmp_path, monkeypatch, victim
):
    session, files = support_export.write_report_bundle(
        tmp_path,
        b'{"outcome":"failed"}\n',
        b"bounded engine log\n",
        "complete",
        session_name="report-0123456789abcdef01234567",
    )
    directory = tmp_path / support_export.REPORTS_DIR / session
    real_open = os.open
    replaced = False

    def replace_after_open(name, flags, *args, **kwargs):
        nonlocal replaced
        fd = real_open(name, flags, *args, **kwargs)
        if name == victim and not replaced:
            replaced = True
            replacement = directory / "replacement"
            replacement.write_bytes(b"foreign replacement\n")
            os.replace(replacement, directory / victim)
        return fd

    monkeypatch.setattr(support_export.os, "open", replace_after_open)
    with pytest.raises(SafetyError, match="unsafe|read-back|changed"):
        support_export.verify_report_bundle(tmp_path, session, files)
    assert replaced
    assert (directory / victim).read_bytes() == b"foreign replacement\n"


def test_report_readback_normal_control(tmp_path):
    session, files = support_export.write_report_bundle(
        tmp_path,
        b'{"outcome":"failed"}\n',
        b"bounded engine log\n",
        "complete",
        session_name="report-0123456789abcdef01234567",
    )
    support_export.verify_report_bundle(tmp_path, session, files)


@pytest.mark.parametrize("unsafe", ["public", "hardlink"])
def test_report_readback_rejects_nonprivate_member(tmp_path, unsafe):
    session, files = support_export.write_report_bundle(
        tmp_path,
        b'{"outcome":"failed"}\n',
        b"bounded engine log\n",
        "complete",
        session_name="report-0123456789abcdef01234567",
    )
    member = tmp_path / support_export.REPORTS_DIR / session / "result.json"
    if unsafe == "public":
        member.chmod(0o644)
    else:
        os.link(member, tmp_path / "second-report-link")

    with pytest.raises(SafetyError, match="unsafe|read-back|changed"):
        support_export.verify_report_bundle(tmp_path, session, files)


def test_atomic_finalization_never_unlinks_replaced_final_name(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.json"
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign owner bytes")
    real_fsync = os.fsync
    real_unlink = os.unlink

    def fail_directory_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("directory sync failed")
        return real_fsync(fd)

    def swap_before_final_unlink(name, *args, **kwargs):
        if name == destination.name:
            os.replace(foreign, destination)
        return real_unlink(name, *args, **kwargs)

    monkeypatch.setattr(evidence.os, "fsync", fail_directory_sync)
    monkeypatch.setattr(evidence.os, "unlink", swap_before_final_unlink)
    with pytest.raises(evidence.EvidenceFinalizationError):
        evidence._atomic_write_bytes(destination, b"owned evidence")

    assert destination.read_bytes() == b"owned evidence"
    assert foreign.read_bytes() == b"foreign owner bytes"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux publication")
def test_atomic_linux_noreplace_preserves_existing_final(tmp_path):
    destination = tmp_path / "result.json"
    destination.write_bytes(b"foreign owner bytes")

    with pytest.raises(FileExistsError):
        evidence._atomic_write_bytes(destination, b"owned evidence")

    assert destination.read_bytes() == b"foreign owner bytes"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux publication")
def test_atomic_linux_without_renameat2_fails_closed(tmp_path, monkeypatch):
    class LibcWithoutRenameat2:
        pass

    source = tmp_path / "source"
    source.write_bytes(b"owned evidence")
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    monkeypatch.setattr(evidence.ctypes, "CDLL", lambda *_args, **_kwargs: LibcWithoutRenameat2())
    try:
        with pytest.raises(OSError) as caught:
            evidence._rename_noreplace(directory_fd, source.name, "result.json")
    finally:
        os.close(directory_fd)

    assert caught.value.errno == evidence.errno.ENOSYS
    assert source.read_bytes() == b"owned evidence"
    assert not (tmp_path / "result.json").exists()


def test_portable_fallback_never_rolls_back_published_final(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "result.json"
    source.write_bytes(b"owned evidence")
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    monkeypatch.setattr(evidence.sys, "platform", "portable-test")

    def fail_cleanup(*_args, **_kwargs):
        raise OSError("cleanup failed")

    monkeypatch.setattr(evidence.os, "unlink", fail_cleanup)
    try:
        with pytest.raises(evidence.EvidenceFinalizationError):
            evidence._rename_noreplace(directory_fd, source.name, destination.name)
    finally:
        os.close(directory_fd)

    assert source.read_bytes() == b"owned evidence"
    assert destination.read_bytes() == b"owned evidence"


def test_atomic_failure_never_unlinks_temp_replaced_after_identity_check(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.json"
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign owner bytes")
    real_stat = os.stat
    swapped = False

    def swap_after_stat(name, *args, **kwargs):
        nonlocal swapped
        result = real_stat(name, *args, **kwargs)
        if str(name).startswith(".result.json.tmp.") and not swapped:
            swapped = True
            directory_fd = kwargs["dir_fd"]
            os.replace(
                foreign.name,
                name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
        return result

    def fail_write(*_args):
        raise OSError("write failed")

    monkeypatch.setattr(evidence.os, "write", fail_write)
    monkeypatch.setattr(evidence.os, "stat", swap_after_stat)
    with pytest.raises(OSError, match="write failed"):
        evidence._atomic_write_bytes(destination, b"owned evidence")

    assert not swapped
    assert foreign.read_bytes() == b"foreign owner bytes"


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
def test_interrupted_export_resumes_exact_sidecar_without_orphaned_json(
    tmp_path, monkeypatch, interruption
):
    source, data = _source(tmp_path)
    destination = tmp_path / "usb"
    destination.mkdir()
    original = evidence._atomic_write_bytes
    calls = 0

    def stop_second(path, blob):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise interruption("fixture interruption")
        return original(path, blob)

    monkeypatch.setattr(evidence, "_atomic_write_bytes", stop_second)
    with pytest.raises(interruption):
        evidence.export_evidence(source, destination)

    exported = destination / source.name
    exported_sidecar = Path(str(exported) + evidence.CHECKSUM_SUFFIX)
    _, sidecar_data = _export_bytes(source, data)
    assert not exported.exists()
    assert exported_sidecar.read_bytes() == sidecar_data

    monkeypatch.setattr(evidence, "_atomic_write_bytes", original)
    assert evidence.export_evidence(source, destination) == exported
    assert evidence.verify_evidence_checksum(exported)


def test_export_failure_never_unlinks_a_foreign_replacement(
    tmp_path, monkeypatch
):
    source, _data = _source(tmp_path)
    destination = tmp_path / "usb"
    destination.mkdir()
    exported = destination / source.name
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign owner bytes")
    original_writer = evidence._atomic_write_bytes
    original_unlink = Path.unlink
    calls = 0

    def fail_second(path, blob):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("second publication failed")
        return original_writer(path, blob)

    def replace_immediately_before_unlink(path, *args, **kwargs):
        if path == exported:
            os.replace(foreign, exported)
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(evidence, "_atomic_write_bytes", fail_second)
    monkeypatch.setattr(Path, "unlink", replace_immediately_before_unlink)
    with pytest.raises(OSError, match="second publication failed"):
        evidence.export_evidence(source, destination)

    assert foreign.read_bytes() == b"foreign owner bytes"
    assert not exported.exists()


@pytest.mark.parametrize("state", ["json-only", "sidecar-only", "complete"])
def test_export_resumes_only_exact_private_partial_states(
    tmp_path, monkeypatch, state
):
    source, data = _source(tmp_path)
    destination = tmp_path / "usb"
    destination.mkdir()
    exported = destination / source.name
    exported_sidecar = Path(str(exported) + evidence.CHECKSUM_SUFFIX)
    json_data, sidecar_data = _export_bytes(source, data)
    if state in {"json-only", "complete"}:
        exported.write_bytes(json_data)
        exported.chmod(0o600)
    if state in {"sidecar-only", "complete"}:
        exported_sidecar.write_bytes(sidecar_data)
        exported_sidecar.chmod(0o600)

    original = evidence._atomic_write_bytes
    writes = []

    def record(path, blob):
        writes.append(Path(path).name)
        return original(path, blob)

    monkeypatch.setattr(evidence, "_atomic_write_bytes", record)
    assert evidence.export_evidence(source, destination) == exported
    assert evidence.verify_evidence_checksum(exported)
    assert len(writes) == (0 if state == "complete" else 1)


def test_export_preserves_and_refuses_a_different_existing_entry(
    tmp_path, monkeypatch
):
    source, _data = _source(tmp_path)
    destination = tmp_path / "usb"
    destination.mkdir()
    exported = destination / source.name
    exported.write_bytes(b"foreign owner bytes")
    exported.chmod(0o600)
    monkeypatch.setattr(
        evidence,
        "_atomic_write_bytes",
        lambda *_args, **_kwargs: pytest.fail("foreign entry reached publication"),
    )

    with pytest.raises(SafetyError, match="unsafe evidence|different evidence"):
        evidence.export_evidence(source, destination)
    assert exported.read_bytes() == b"foreign owner bytes"
