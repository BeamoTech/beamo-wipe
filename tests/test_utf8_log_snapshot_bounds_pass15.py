"""Normalized terminal snapshots keep their verdict at UTF-8 byte boundaries."""

import copy
import hashlib
import os

import pytest

from beamo_wipe import evidence as evidence_module
from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.evidence import build_evidence, recover_result, write_evidence_atomic
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult, MethodId, WipeRequest
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.support_export import prepare_terminal_evidence, read_export_log


_RAW_LIMIT = runner_module.NWIPE_COMPLETION_LOG_BYTES
_STATUS = (
    runner_module.NWIPE_DRIVE_STATUS_HEADER
    + "\n sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
).encode()
_VALID_CASES = [
    pytest.param(character, cut, id=f"U{ord(character):04X}-cut{cut}")
    for character in ("A", "é", "€", "😀")
    for cut in range(len(character.encode("utf-8")))
]


@pytest.fixture(autouse=True)
def _fake_boundaries(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("a snapshot regression reached a native effect")

    monkeypatch.setattr(runner_module.subprocess, "Popen", forbidden)
    monkeypatch.setattr(runner_module.subprocess, "run", forbidden)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", forbidden)
    monkeypatch.setattr(runner_module, "_recheck_identity_under_lock", forbidden)
    monkeypatch.setattr(runner_module, "_reserve_target_under_lock", forbidden)
    monkeypatch.setattr(runner_module, "_try_log_diag", lambda *_args: None)
    monkeypatch.setattr(
        evidence_module,
        "evidence_identity",
        lambda: {
            "source_commit": "a" * 40,
            "build_id": "local",
            "build_status": "development",
            "source_dirty": False,
        },
    )
    realpath = os.path.realpath

    def fake_device_realpath(path, *args, **kwargs):
        if os.fsdecode(path).startswith("/dev/"):
            return os.fspath(path)
        return realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_device_realpath)
    native_open = os.open

    def ordinary_open(path, *args, **kwargs):
        if os.fsdecode(path).startswith(("/dev/", "/sys/", "/proc/")):
            forbidden()
        return native_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", ordinary_open)


def _padding(size, byte=b"x"):
    records, remainder = divmod(size, 65536)
    return (byte * 65535 + b"\n") * records + (
        byte * (remainder - 1) + b"\n" if remainder else b""
    )


def _evidence_from_raw(tmp_path, raw, method):
    logfile = tmp_path / "fake-nwipe.log"
    logfile.write_bytes(raw)
    logfile.chmod(0o600)
    request = WipeRequest("/dev/sda", method, "/dev/sr0", str(logfile))

    class Exited:
        returncode = 0

        def poll(self):
            return self.returncode

    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    runner._active_request = request
    runner._last_logfile = str(logfile)
    result = runner.poll(request)
    assert result is not None and result.ok and result.reason == "completed"
    assert runner._proc is None and runner._lock_fd is None and runner._log_fd is None
    expected_snapshot = raw[-_RAW_LIMIT:].decode("utf-8", errors="replace").encode("utf-8")
    assert runner._log_tail.encode("utf-8") == expected_snapshot
    disk = Disk(
        "/dev/sda", "sda", "FAKE DISK", "FAKE-SERIAL", 1_000_000_000,
        "1", DiskKind.HDD, "sata", "",
    )
    boot = Disk(
        "/dev/sr0", "sr0", "FAKE BOOT", "FAKE-BOOT", 2_000_000_000,
        "2", DiskKind.UNKNOWN, "usb", "BEAMO_WIPE", is_boot=True,
    )
    discovery = DiscoveryResult(
        disks=(disk, boot), selectable=(disk,), boot=boot, boot_identified=True
    )
    payload = build_evidence(
        disk=disk,
        discovery=discovery,
        method=method,
        request=request,
        result=result,
        started_at_wall="",
        ended_at_wall="",
        started_mono=0,
        ended_mono=1,
        argv=[],
        log_text=runner._log_tail,
        assessment_log_text=runner._assessment_log_text,
    )
    assert payload["log_snapshot_size_bytes"] == len(expected_snapshot)
    assert payload["log_checksum_sha256"] == hashlib.sha256(expected_snapshot).hexdigest()
    assert logfile.read_bytes() == raw
    return payload, expected_snapshot, logfile


def _assert_roundtrip(tmp_path, raw, method):
    payload, expected_snapshot, logfile = _evidence_from_raw(tmp_path, raw, method)
    code = "unverified" if method == MethodId.QUICK_ZERO else "verified"
    assert payload["outcome"] == ("completed" if code == "unverified" else "verified")
    assert payload["presentation"]["code"] == code
    assert present_evidence(payload).code == code
    snapshot, status = read_export_log(
        str(logfile),
        expected_sha256=payload["log_checksum_sha256"],
        expected_size_bytes=payload["log_snapshot_size_bytes"],
    )
    assert snapshot == expected_snapshot
    assert status == ("tail" if len(raw) > _RAW_LIMIT else "complete")
    path = write_evidence_atomic(
        payload, log_dir=tmp_path, device_path="/dev/sda", target_device="/dev/sda"
    )
    assert recover_result(path).code == code
    prepared = prepare_terminal_evidence(path, "/dev/sda")
    assert prepared.data == path.read_bytes()
    assert prepared.sha256 == hashlib.sha256(prepared.data).hexdigest()
    assert prepared.log_size_bytes == len(expected_snapshot)
    assert prepared.log_sha256 == hashlib.sha256(expected_snapshot).hexdigest()
    assert logfile.read_bytes() == raw


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize(("character", "cut"), _VALID_CASES)
def test_valid_utf8_tail_boundaries_preserve_terminal_roundtrip(
    tmp_path, method, character, cut
):
    first = character.encode("utf-8") + b"\n"
    raw = first + _padding(_RAW_LIMIT + cut - len(first) - len(_STATUS)) + _STATUS
    assert len(raw) == _RAW_LIMIT + cut
    raw.decode("utf-8")  # The complete original log is valid, including boundary failures.
    normalized = raw[-_RAW_LIMIT:].decode("utf-8", errors="replace").encode("utf-8")
    assert (len(normalized) > _RAW_LIMIT) == (cut > 0)
    _assert_roundtrip(tmp_path, raw, method)


@pytest.mark.parametrize("method", list(MethodId))
def test_bounded_invalid_utf8_capture_preserves_terminal_roundtrip(tmp_path, method):
    raw = _padding(_RAW_LIMIT - len(_STATUS), b"\xff") + _STATUS
    assert len(raw) == _RAW_LIMIT
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    normalized = raw.decode("utf-8", errors="replace").encode("utf-8")
    assert 2 * _RAW_LIMIT < len(normalized) < 3 * _RAW_LIMIT
    _assert_roundtrip(tmp_path, raw, method)


@pytest.mark.parametrize("size", [True, 0, -1, 3 * _RAW_LIMIT + 1, float(3 * _RAW_LIMIT)])
def test_snapshot_metadata_still_rejects_invalid_or_unbounded_sizes(tmp_path, size):
    payload, _snapshot, _logfile = _evidence_from_raw(tmp_path, _STATUS, MethodId.EVERYDAY)
    assert present_evidence(payload).code == "verified"
    changed = copy.deepcopy(payload)
    changed["log_snapshot_size_bytes"] = size
    assert present_evidence(changed).code == "indeterminate"
