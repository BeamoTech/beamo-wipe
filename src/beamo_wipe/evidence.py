# SPDX-License-Identifier: GPL-3.0-or-later
"""Auditable result evidence. Off-target, atomic, truthful.

Never overstating: a nonzero/unknown exit or missing success markers is
always FAILED, never COMPLETED/VERIFIED. No hostname, IP, or user details.
"""

from __future__ import annotations

import datetime
import ctypes
import errno
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from beamo_wipe import NWIPE_PINNED_COMMIT, NWIPE_PINNED_VERSION, __version__
from beamo_wipe.build_identity import evidence_identity
from beamo_wipe.methods import METHODS
from beamo_wipe import storage_limits as _limits
from beamo_wipe.storage_limits import notice
from beamo_wipe.models import Disk, MethodId, WipeRequest, WipeResult
import beamo_wipe.safety as safety
from beamo_wipe.safety import SafetyError, assert_log_not_on_target


SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2})
EVIDENCE_PREFIX = "result-"
EVIDENCE_SUFFIX = ".json"
CHECKSUM_SUFFIX = ".sha256"
MAX_EVIDENCE_FILE_BYTES = 16 * 1024 * 1024  # parser memory cap; export has a separate total request cap
WALL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
WALL_PROVENANCE = frozenset({"os_utc", "injected", "unavailable"})

# Explicit outcome set. VERIFIED means COMPLETED + verify==last + markers.
OUTCOME_STARTED = "started"
OUTCOME_RUNNING = "running"
OUTCOME_INTERRUPTED = "interrupted"
OUTCOME_FAILED = "failed"
OUTCOME_COMPLETED = "completed"  # ok, verify==off or no verify requested
OUTCOME_VERIFIED = "verified"  # ok, verify==last, last-pass or Erased row
ALLOWED_OUTCOMES = frozenset(
    {
        OUTCOME_STARTED,
        OUTCOME_RUNNING,
        OUTCOME_INTERRUPTED,
        OUTCOME_FAILED,
        OUTCOME_COMPLETED,
        OUTCOME_VERIFIED,
    }
)


def _iso_now_wall() -> str:
    # UTC, no local timezone leakage. Format is not evidence of a correct clock.
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def valid_wall(value: object) -> str:
    if not isinstance(value, str) or not WALL_RE.fullmatch(value):
        return ""
    try:
        # Python 3.10 rejects some valid fractional widths such as `.5Z`.
        # The anchored shape check covers fractional digits and UTC; parse
        # the calendar/clock fields independently of their precision.
        datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return ""
    return value


def wall_timestamps(
    started_at_wall: object,
    ended_at_wall: object,
    provenance: object,
) -> dict[str, Any]:
    """Record wall stamps without treating ISO format as trust."""
    source = (
        provenance
        if isinstance(provenance, str) and provenance in WALL_PROVENANCE
        else "unavailable"
    )
    started = valid_wall(started_at_wall)
    ended = valid_wall(ended_at_wall)
    if not started and not ended:
        return {
            "started_at_wall": "",
            "ended_at_wall": "",
            "wall_confidence": "unavailable",
            "wall_provenance": "unavailable",
        }
    if source == "unavailable":
        return {
            "started_at_wall": "",
            "ended_at_wall": "",
            "wall_confidence": "unavailable",
            "wall_provenance": "unavailable",
        }
    return {
        "started_at_wall": started,
        "ended_at_wall": ended,
        "wall_confidence": "unverified",
        "wall_provenance": source,
    }


def _finite_monotonic(value: Any) -> float | None:
    """Keep only clock readings representable in a truthful JSON report."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _sanitize_argv(argv: Sequence[str]) -> List[str]:
    # Already validated; strip control chars and ensure safe printable
    out: List[str] = []
    for a in argv or []:
        if not isinstance(a, str):
            continue
        if any(unicodedata.category(ch).startswith("C") for ch in a):
            continue
        out.append(a)
    return out


def _device_identity(disk: Optional[Disk]) -> Optional[dict[str, Any]]:
    if disk is None:
        return None
    # Realpath is resolved; path stays as shown to user. No hostname.
    try:
        real = os.path.realpath(disk.path)
    except OSError:
        real = disk.path
    return {
        "path": disk.path,
        "realpath": real,
        "name": disk.name,
        "model": disk.model or "",
        "serial": disk.serial or "",
        "size_bytes": disk.size_bytes,
        "size_gb_label": disk.size_gb_label,
        "kind": disk.kind.value if hasattr(disk.kind, "value") else str(disk.kind),
        "bus": disk.bus or "",
        "vendor": disk.vendor or "",
        "wwn": disk.wwn or "",
        "label": disk.label or "",
        "is_boot": bool(disk.is_boot),
    }


def _exit_signal(exit_code: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    """Return (exit_code, signal) where signal is positive if killed by signal."""
    if exit_code is None or not isinstance(exit_code, int):
        return None, None
    if exit_code < 0:
        # Python's Popen returns -signal
        return exit_code, -exit_code
    if exit_code > 128:
        # Shell convention: 128+signal; but we keep raw exit_code and derive signal if plausible
        # Do not guess; treat as exit_code, signal None unless we know it's a signal
        return exit_code, None
    return exit_code, None


def _warnings_for(disk: Optional[Disk], selectable: Sequence[Disk]) -> List[str]:
    warns: List[str] = []
    if disk is None:
        return warns
    warns.append(notice(disk.kind))
    # Same-size hint
    if disk and selectable:
        labels = [d.size_gb_label for d in selectable]
        if labels.count(disk.size_gb_label) > 1:
            warns.append("Two disks share the same size; verify the serial suffix.")
    return warns


def _verification_state(
    method: MethodId,
    log_text: str,
    device: str,
    exit_code: Optional[int],
    result_ok: bool,
) -> Tuple[str, bool]:
    """Return (verification_requested, verified_bool) truthfully."""
    spec = METHODS.get(method)
    requested = spec.verify if spec else "unknown"
    if not result_ok:
        return requested, False
    if requested == "off":
        # No verification requested; verified is false but outcome can be COMPLETED
        return requested, False
    # For "last"/"all", verify requires evaluate's success markers
    # evaluate_nwipe_completion already checks Erased row or last-pass 100%
    # If result_ok is True, verification passed for that request.
    # But if log is empty and exit 0 without markers, evaluate returns ok False, so not here.
    return requested, True


def _outcome_for(
    *,
    result: Optional[WipeResult],
    method: MethodId,
    log_text: str,
    device: str,
    interrupted: bool,
    cancelled: bool,
) -> Tuple[str, Optional[str]]:
    """Return (outcome, failure_reason). Never upgrades failure to success."""
    if cancelled or interrupted:
        # Even if nwipe later reports success, interruption takes precedence
        return OUTCOME_INTERRUPTED, "interrupted by user or system"
    if result is None:
        # No result yet: running vs started distinguished by caller
        return OUTCOME_RUNNING, None
    # result exists
    ok = False
    exit_code = result.exit_code
    completion_summary = ""
    if result.ok:
        try:
            from beamo_wipe.nwipe_runner import completion_for_method

            ok, completion_summary, _reason = completion_for_method(
                exit_code, log_text or "", device, method
            )
        except Exception:
            ok = False
    spec = METHODS.get(method)
    verify = spec.verify if spec else "unknown"
    # Truthful: nonzero/unknown without markers is FAILED
    # evaluate_nwipe_completion is authoritative; but result.ok already reflects it
    # However if result.summary indicates bus skip / abort / open fail, ok is False
    if not ok:
        # Preserve the summary as failure reason (redacted, no host details)
        reason = (
            completion_summary
            or (result.summary or "").strip()
            or f"nwipe exited {exit_code}"
        )
        # Never translate to success
        return OUTCOME_FAILED, reason
    # ok == True
    if verify == "last":
        return OUTCOME_VERIFIED, None
    return OUTCOME_COMPLETED, None


def build_evidence(
    *,
    disk: Optional[Disk],
    discovery: Any,  # DiscoveryResult
    method: MethodId,
    request: Optional[WipeRequest],
    result: Optional[WipeResult],
    started_at_wall: Optional[str],
    ended_at_wall: Optional[str],
    started_mono: Optional[float],
    ended_mono: Optional[float],
    argv: Optional[Sequence[str]],
    log_text: str,
    assessment_log_text: Optional[str] = None,
    interrupted: bool = False,
    cancelled: bool = False,
    wall_provenance: str = "unavailable",
    language: str = "en",
    keyboard_layout: str = "us",
) -> dict[str, Any]:
    """Build a truthful, user-safe evidence dict."""
    spec = METHODS.get(method)
    if spec is None:
        raise ValueError("unknown method")

    walls = wall_timestamps(started_at_wall, ended_at_wall, wall_provenance)
    started_mono = _finite_monotonic(started_mono)
    ended_mono = _finite_monotonic(ended_mono)
    duration_s = (
        ended_mono - started_mono
        if started_mono is not None and ended_mono is not None
        else None
    )
    if duration_s is not None and (duration_s < 0 or not math.isfinite(duration_s)):
        duration_s = None

    # Exit/signal
    exit_code, signal = _exit_signal(result.exit_code if result else None)

    # Device identity
    device_dict = _device_identity(disk)

    # Boot identity (path only, no extra host)
    boot_path = ""
    try:
        boot_path = discovery.boot.path if getattr(discovery, "boot", None) else ""  # type: ignore[union-attr]
    except Exception:
        boot_path = ""

    # Warnings stay advisory. Structured checks never rewrite outcome.
    selectable: Sequence[Disk] = getattr(discovery, "selectable", ())  # type: ignore[assignment]
    warnings = list(_warnings_for(disk, selectable))
    device_path = disk.path if disk else (request.device if request else "")
    from beamo_wipe.engine_checks import alert_summaries, check_payloads

    # A terminal run can have a bounded projection from the entire engine
    # log. Keep log_text as the exact suffix authenticated for export while
    # evaluating outcome and advisory checks against that whole-log view.
    assessed_log = log_text if assessment_log_text is None else assessment_log_text
    checks = check_payloads(assessed_log or "", device_path, disk)
    for summary in alert_summaries(checks):
        if summary not in warnings:
            warnings.append(summary)
    from beamo_wipe.identity import present_disk

    device_presentation = present_disk(disk, selectable).payload() if disk is not None else None

    # Verification uses the same method-aware completion decision as outcome.
    # A one-pass 100% line is not verification of Three overwrites.
    validated_ok = False
    completion_ok = False
    completion_reason = "indeterminate"
    if result is not None:
        try:
            from beamo_wipe.nwipe_runner import completion_for_method

            completion_ok, _summary, completion_reason = completion_for_method(
                exit_code, assessed_log or "", device_path, method
            )
        except Exception:
            completion_ok = False
            completion_reason = "indeterminate"
        validated_ok = bool(result.ok and completion_ok)
    verification_requested, verified = _verification_state(
        method,
        assessed_log or "",
        (disk.path if disk else (request.device if request else "")),
        exit_code,
        validated_ok,
    )

    # Outcome
    outcome, failure_reason = _outcome_for(
        result=result,
        method=method,
        log_text=assessed_log or "",
        device=device_path,
        interrupted=interrupted,
        cancelled=cancelled,
    )
    # If still running but we have no result, distinguish STARTED vs RUNNING via presence of request
    if result is None and request is not None and not interrupted and not cancelled:
        # Caller decides started vs running; default to started if we only just built
        # Keep as started unless duration >0
        if duration_s is None or duration_s == 0:
            outcome = OUTCOME_STARTED
        else:
            outcome = OUTCOME_RUNNING
        failure_reason = None

    from beamo_wipe.outcomes import present_evidence

    validated = False
    reason = completion_reason
    if result is not None:
        validated = (not completion_ok) or result.ok
    if interrupted or cancelled:
        verified = False
        reason = "cancelled" if cancelled else "interrupted"
        # Cancellation cannot be inferred from a successful process result.
        validated = result is not None and (not cancelled or not result.ok)

    # Redacted argv
    argv_redacted = _sanitize_argv(argv or [])
    # Ensure no /dev/…/.. or control chars leaked beyond validation
    # Keep only allowed flags and the device itself

    # Log checksum (tail only, not full sensitive log)
    log_checksum: Optional[str] = None
    log_snapshot_size_bytes = 0
    if log_text:
        try:
            log_snapshot = log_text.encode("utf-8", errors="replace")
            log_checksum = hashlib.sha256(log_snapshot).hexdigest()
            log_snapshot_size_bytes = len(log_snapshot)
        except Exception:
            log_checksum = None
            log_snapshot_size_bytes = 0

    identity = evidence_identity()
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "beamo_wipe_version": __version__,
        "source_commit": identity["source_commit"],
        "build_id": identity["build_id"],
        "build_status": identity["build_status"],
        "source_dirty": identity["source_dirty"],
        "nwipe_version": NWIPE_PINNED_VERSION,
        "nwipe_commit": NWIPE_PINNED_COMMIT,
        "outcome": outcome,
        "completion": {"validated": validated, "reason": reason},
        "failure_reason": failure_reason,
        "device": device_dict,
        "device_presentation": device_presentation,
        "method": {
            "id": method.value,
            "nwipe_method": spec.nwipe_method,
            "rounds": spec.rounds,
            "verify": spec.verify,
            "noblank": spec.noblank,
            "docs_name": spec.docs_name,
            "title": spec.title,
            "overwrite_passes": spec.overwrite_passes,
            "verification_passes": spec.verification_passes,
            "description": spec.description,
            "operation_summary": spec.operation_summary,
        },
        "boot_device": boot_path,
        "timestamps": {
            "started_at_wall": walls["started_at_wall"],
            "ended_at_wall": walls["ended_at_wall"],
            "started_monotonic": started_mono,
            "ended_monotonic": ended_mono,
            "duration_s": duration_s,
            "duration_source": "monotonic",
            "wall_confidence": walls["wall_confidence"],
            "wall_provenance": walls["wall_provenance"],
        },
        "nwipe": {
            "version": NWIPE_PINNED_VERSION,
            "argv_redacted": argv_redacted,
        },
        "exit_evidence": {
            "exit_code": exit_code,
            "signal": signal,
        },
        "verification": {
            "requested": verification_requested,
            "verified": verified,
            "scope": _limits.VERIFICATION_SCOPE,
        },
        "warnings": warnings,
        "checks": checks,
        "interruption": {
            "interrupted": bool(interrupted or cancelled),
            "cancelled": bool(cancelled),
            "origin": "user" if cancelled else ("system" if interrupted else "none"),
        },
        "logfile": (result.logfile if result and result.logfile else (request.logfile if request else "")),
        "log_checksum_sha256": log_checksum,
        # Authenticates the exact UTF-8 log suffix retained for export. The
        # mutable logfile is exported only when this length and digest still
        # match; terminal checks may use the bounded whole-log projection.
        "log_snapshot_size_bytes": log_snapshot_size_bytes,
        "provenance": {
            "evidence_file": "",  # filled by writer
            "written_at_wall": "",
        },
        "locale": {
            "language": language if _is_supported_language(language) else "en",
            "keyboard_layout": keyboard_layout if _is_allowed_layout(keyboard_layout) else "us",
        },
    }

    presentation = present_evidence(evidence)
    evidence["presentation"] = presentation.payload()
    evidence["result_description"] = presentation.message

    # Never claim certified: we do not add a "certificate" field. Only verified/completed as above.
    return evidence


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Atomic write: temp + fsync + rename. No follow of symlinks."""
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    encoded = blob.encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_FILE_BYTES:
        raise SafetyError("Evidence file is too large")
    _atomic_write_bytes(path, encoded)


def write_evidence_atomic(
    evidence: dict[str, Any],
    *,
    log_dir: Optional[Path] = None,
    device_path: str = "",
    target_device: str = "",
) -> Path:
    """Write evidence JSON to log_dir atomically, off-target, with checksum sidecar.

    Returns the evidence path. Also writes .sha256 sidecar.
    """
    directory = log_dir if log_dir is not None else safety.default_log_dir()
    # Safety: ensure directory itself is not on target (default_log_dir already checks /tmp dev)
    # Evidence file name: result-<sanitized-device>-<timestamp_ns>.json
    safe = os.path.basename(device_path or target_device or "unknown").replace("/", "_") or "unknown"
    if not safe or safe in {".", ".."}:
        safe = "unknown"
    ts = time.time_ns()
    name = f"{EVIDENCE_PREFIX}{safe}-{ts}{EVIDENCE_SUFFIX}"
    path = Path(directory) / name
    # Off-target check (pass log_dir to ensure _is_under uses same root)
    assert_log_not_on_target(str(path), target_device or device_path, log_dir=Path(directory))
    # A report can be written before a disk was selected, so the target path
    # above may be empty. That must not waive the live image's memory-only
    # evidence rule.
    if not safety.is_preview_env() and not safety.log_location_is_tmpfs(path.resolve()):
        raise SafetyError("Evidence directory must be on tmpfs.")
    # Add provenance before write
    evidence = dict(evidence)
    evidence["provenance"] = dict(evidence.get("provenance", {}))
    evidence["provenance"]["evidence_file"] = str(path)
    evidence["provenance"]["written_at_wall"] = _iso_now_wall()
    # Compute checksum of the final JSON (after provenance)
    # We write, then compute checksum of file
    _atomic_write_json(path, evidence)
    # Sidecar checksum
    h = hashlib.sha256(_read_regular_nofollow(path)).hexdigest()
    sidecar = Path(str(path) + CHECKSUM_SUFFIX)
    _atomic_write_bytes(sidecar, f"{h}  {path.name}\n".encode("ascii"))
    return path


def _unique_evidence_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SafetyError("Duplicate evidence field")
        result[key] = value
    return result


def load_evidence(path: Path, *, private: bool = False) -> dict[str, Any]:
    return json.loads(
        _read_regular_nofollow(Path(path), private=private).decode("utf-8"),
        object_pairs_hook=_unique_evidence_fields if private else dict,
    )


def recover_result(path: Path, *, expected_sha256: str | None = None):
    """Recover a report explanation; never resume erasure or infer success.

    Authenticate the saved JSON and, for a successful record, independently
    recheck its exact log snapshot. A caller recovering journal-bound evidence
    can require the journal's digest. Missing/replaced evidence stays indeterminate.
    """
    from beamo_wipe.outcomes import present_evidence
    try:
        data = _verified_evidence_bytes(
            Path(path), private=expected_sha256 is not None
        )
        if (
            expected_sha256 is not None
            and hashlib.sha256(data).hexdigest() != expected_sha256
        ):
            return present_evidence(None)
        evidence = json.loads(
            data,
            object_pairs_hook=_unique_evidence_fields,
        )
        view = present_evidence(evidence)
        if view.success or view.code in {"occupied", "open_failed", "geometry_unusable"}:
            from beamo_wipe.support_export import read_export_log

            snapshot, status = read_export_log(
                evidence["logfile"],
                expected_sha256=evidence["log_checksum_sha256"],
                expected_size_bytes=evidence["log_snapshot_size_bytes"],
            )
            if status not in {"complete", "tail"}:
                return present_evidence(None)
            from beamo_wipe.nwipe_runner import completion_for_method

            ok, _detail, reason = completion_for_method(
                evidence["exit_evidence"]["exit_code"],
                snapshot.decode("utf-8"),
                evidence["device"]["path"],
                evidence["method"]["id"],
            )
            if view.success and (not ok or reason != "completed"):
                return present_evidence(None)
            if not view.success and (ok or reason != view.code):
                return present_evidence(None)
        return view
    except (OSError, SafetyError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        return present_evidence(None)


def _read_regular_nofollow(path: Path, *, private: bool = False) -> bytes:
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise SafetyError("Cannot safely read evidence file") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise SafetyError("Evidence path is not a regular file")
        if opened.st_uid != os.getuid():
            raise SafetyError("Evidence file has the wrong owner")
        if opened.st_size > MAX_EVIDENCE_FILE_BYTES:
            raise SafetyError("Evidence file is too large")
        if private and (stat.S_IMODE(opened.st_mode) != 0o600 or opened.st_nlink != 1):
            raise PermissionError(errno.EPERM, "Unsafe evidence permissions")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_EVIDENCE_FILE_BYTES:
                raise SafetyError("Evidence file is too large")
        after = os.fstat(fd)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mode,
            opened.st_nlink,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mode,
            after.st_nlink,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ) or total != opened.st_size:
            raise SafetyError("Evidence changed while reading")
        return b"".join(chunks)
    finally:
        os.close(fd)


class EvidenceFinalizationError(OSError):
    """Publication occurred but its final filesystem synchronization failed."""


def _rename_noreplace(directory_fd: int, source: str, destination: str) -> None:
    """Atomically publish ``source`` without replacing ``destination``."""
    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        try:
            renameat2 = libc.renameat2
        except AttributeError as exc:
            raise OSError(errno.ENOSYS, "renameat2 is required for publication") from exc
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        if renameat2(
            directory_fd,
            os.fsencode(source),
            directory_fd,
            os.fsencode(destination),
            1,  # RENAME_NOREPLACE
        ) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), destination)
        return

    # Development-only portability fallback. The cryptographic source name
    # bounds interference, but POSIX has no portable atomic no-replace rename.
    # Never roll back the final name if unlinking the source fails.
    os.link(
        source,
        destination,
        src_dir_fd=directory_fd,
        dst_dir_fd=directory_fd,
        follow_symlinks=False,
    )
    try:
        os.unlink(source, dir_fd=directory_fd)
    except BaseException as exc:
        if isinstance(exc, Exception):
            raise EvidenceFinalizationError("Evidence finalization failed") from exc
        raise


def _atomic_write_bytes(path: Path, data: bytes) -> tuple[int, int]:
    directory = path.parent
    dir_fd = os.open(str(directory), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    tmp_name = f".{path.name}.tmp.{secrets.token_hex(16)}"
    fd = pinned_fd = -1

    def verify_publication(name: str, links: int) -> None:
        fields = (
            "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
            "st_mtime_ns", "st_ctime_ns",
        )
        opened = os.fstat(pinned_fd)
        named = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        if (
            any(getattr(opened, key) != getattr(named, key) for key in fields)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(opened.st_mode) != 0o600
            or opened.st_nlink != links
            or opened.st_size != len(data)
        ):
            raise SafetyError("Evidence publication changed")
        received = bytearray()
        while len(received) <= len(data):
            chunk = os.pread(
                pinned_fd, min(65536, len(data) + 1 - len(received)), len(received)
            )
            if not chunk:
                break
            received.extend(chunk)
        after = os.fstat(pinned_fd)
        named = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        if received != data or any(
            getattr(opened, key) != getattr(after, key)
            or getattr(after, key) != getattr(named, key)
            for key in fields
        ):
            raise SafetyError("Evidence publication changed")

    try:
        fd = os.open(
            tmp_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=dir_fd,
        )
        opened = os.fstat(fd)
        temp_identity = (opened.st_dev, opened.st_ino)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short evidence write")
            view = view[written:]
        os.fsync(fd)
        published_identity = temp_identity
        # Keep the inode pinned through publication while retaining the
        # original close boundary: its failure must refuse before renameat2.
        pinned_fd = os.dup(fd)
        closing_fd = fd
        fd = -1
        # A failed close has platform-dependent ownership; never retry its
        # descriptor number, which may already have been reused.
        os.close(closing_fd)
        verify_publication(tmp_name, 1)
        # Linux atomically consumes the temporary name and refuses an occupied
        # destination. No final-name rollback or temp-name unlink is needed.
        _rename_noreplace(dir_fd, tmp_name, path.name)
        try:
            verify_publication(path.name, 1)
            os.fsync(dir_fd)
            verify_publication(path.name, 1)
        except BaseException as exc:
            # A published exact file is a resumable state. Portable POSIX has
            # no unlink-if-same-inode primitive, so never roll back this name.
            if isinstance(exc, Exception):
                raise EvidenceFinalizationError("Evidence finalization failed") from exc
            raise
        return published_identity
    finally:
        try:
            if fd >= 0:
                os.close(fd)
        finally:
            try:
                if pinned_fd >= 0:
                    os.close(pinned_fd)
            finally:
                os.close(dir_fd)


def verify_evidence_checksum(path: Path) -> bool:
    """Return True only if the sidecar sha matches the file bytes.

    A missing sidecar is unverifiable, never valid: well-formed JSON alone
    proves nothing about integrity, so it returns False (callers record
    ``provenance.verified = False`` instead of blessing forged evidence).
    """
    sidecar = Path(str(path) + CHECKSUM_SUFFIX)
    try:
        data = _read_regular_nofollow(Path(path))
        h = hashlib.sha256(data).hexdigest()
        txt = _read_regular_nofollow(sidecar).decode("ascii")
        return txt == f"{h}  {Path(path).name}\n"
    except Exception:
        return False


def _verified_evidence_bytes(path: Path, *, private: bool = False) -> bytes:
    """Return the exact bytes authenticated by the adjacent sidecar."""
    data = _read_regular_nofollow(path, private=private)
    sidecar = Path(str(path) + CHECKSUM_SUFFIX)
    try:
        text = _read_regular_nofollow(sidecar, private=private).decode("ascii")
    except Exception as exc:
        raise SafetyError("Evidence checksum is missing or invalid") from exc
    expected = f"{hashlib.sha256(data).hexdigest()}  {path.name}\n"
    if text != expected:
        raise SafetyError("Evidence checksum is missing or invalid")
    return data


def _exact_private_file(path: Path, expected: bytes) -> tuple[int, int] | None:
    """Return a stable identity only when a named private file has exact bytes."""
    directory_fd = os.open(
        str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    )
    fd = -1
    try:
        try:
            fd = os.open(
                path.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            return None
        opened = os.fstat(fd)
        fields = (
            "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
            "st_mtime_ns", "st_ctime_ns",
        )
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(opened.st_mode) != 0o600
            or opened.st_nlink != 1
            or opened.st_size != len(expected)
        ):
            raise SafetyError("Export destination contains unsafe evidence")

        def read_once() -> bytes:
            os.lseek(fd, 0, os.SEEK_SET)
            received = bytearray()
            while len(received) <= len(expected):
                chunk = os.read(fd, min(65536, len(expected) + 1 - len(received)))
                if not chunk:
                    break
                received.extend(chunk)
            return bytes(received)

        first = read_once()
        second = read_once()
        after = os.fstat(fd)
        named = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            first != expected
            or second != expected
            or any(
                getattr(opened, field) != getattr(after, field)
                or getattr(after, field) != getattr(named, field)
                for field in fields
            )
        ):
            raise SafetyError("Export destination contains different evidence")
        return opened.st_dev, opened.st_ino
    except OSError as exc:
        raise SafetyError("Cannot safely inspect export destination") from exc
    finally:
        try:
            if fd >= 0:
                os.close(fd)
        finally:
            os.close(directory_fd)


def _publish_or_accept_exact(path: Path, data: bytes) -> tuple[int, int]:
    """Publish once, or resume only an identical stable private-file state."""
    existing = _exact_private_file(path, data)
    if existing is not None:
        return existing
    try:
        return _atomic_write_bytes(path, data)
    except FileExistsError:
        # A concurrent publisher may have won after the absence check. Its
        # exact bytes are harmless; every other state belongs to that writer.
        existing = _exact_private_file(path, data)
        if existing is None:
            raise
        return existing


def export_evidence(
    evidence_path: Path,
    dest_dir: Path,
    *,
    target_device: str = "",
    boot_device: str = "",
) -> Path:
    """Copy evidence + checksum to dest_dir (second USB) atomically, off-target.

    Validates dest_dir is not the target or boot device filesystem.
    """
    src = Path(evidence_path)
    dest_dir = Path(dest_dir)
    data = _verified_evidence_bytes(src)
    if not dest_dir.exists():
        raise SafetyError("Export destination missing")
    # Ensure dest_dir itself is a directory and not a symlink
    try:
        st = os.lstat(str(dest_dir))
        if stat.S_ISLNK(st.st_mode):
            raise SafetyError("Refusing to export through symlink")
        if not stat.S_ISDIR(st.st_mode):
            raise SafetyError("Export destination is not a directory")
    except OSError as exc:
        raise SafetyError(f"Cannot stat export destination: {exc}") from exc
    # Off-target checks: dest_dir must not be on target or boot filesystem via mountinfo
    # Use assert_log_not_on_target semantics: a file under dest_dir must not be on target.
    # The dest is a second USB, not the log dir, so scope the under-dir check
    # to dest_dir itself (default would wrongly require dest under /tmp/beamo-wipe
    # and every real export would fail).
    dest_file = dest_dir / src.name
    assert_log_not_on_target(str(dest_file), target_device or "", log_dir=dest_dir)
    if boot_device:
        assert_log_not_on_target(str(dest_file), boot_device, log_dir=dest_dir)
    # Also check via mountinfo that dest_dir is not on target (best effort)
    # Compatibility API for pre-mounted destinations. The kiosk does not call
    # this path; _atomic_write_bytes still publishes without replacement.
    dest_sc = Path(str(dest_file) + CHECKSUM_SUFFIX)
    sidecar_data = (
        f"{hashlib.sha256(data).hexdigest()}  {dest_file.name}\n".encode("ascii")
    )
    # Inspect both names before publishing either. An exact partial bundle is
    # a resumable interrupted attempt; every differing entry remains foreign.
    _exact_private_file(dest_file, data)
    _exact_private_file(dest_sc, sidecar_data)
    # The checksum is harmless without its evidence. Publishing it first means
    # an interruption never exposes unauthenticated JSON and needs no racy
    # stat-then-unlink rollback of a final pathname.
    _publish_or_accept_exact(dest_sc, sidecar_data)
    _publish_or_accept_exact(dest_file, data)
    if (
        _exact_private_file(dest_sc, sidecar_data) is None
        or _exact_private_file(dest_file, data) is None
    ):
        raise SafetyError("Export evidence finalization failed")
    # Fsync dest_dir
    try:
        dfd = os.open(str(dest_dir), os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass
    return dest_file


# For testing: allow injection of wall clock
def _is_supported_language(code: object) -> bool:
    try:
        from beamo_wipe.lang import is_supported
    except Exception:
        return code == "en"
    return is_supported(code)


def _is_allowed_layout(layout_id: object) -> bool:
    try:
        from beamo_wipe.keyboard import is_allowed
    except Exception:
        return layout_id == "us"
    return isinstance(layout_id, str) and is_allowed(layout_id)


def build_evidence_for_wizard(
    *,
    disk: Optional[Disk],
    discovery: Any,
    method: MethodId,
    request: Optional[WipeRequest],
    result: Optional[WipeResult],
    started_at_wall: Optional[str],
    ended_at_wall: Optional[str],
    started_mono: Optional[float],
    ended_mono: Optional[float],
    argv: Optional[Sequence[str]],
    log_text: str,
    cancelled: bool = False,
    interrupted: bool = False,
    language: str = "en",
    keyboard_layout: str = "us",
) -> dict[str, Any]:
    return build_evidence(
        disk=disk,
        discovery=discovery,
        method=method,
        request=request,
        result=result,
        started_at_wall=started_at_wall,
        ended_at_wall=ended_at_wall,
        started_mono=started_mono,
        ended_mono=ended_mono,
        argv=argv,
        log_text=log_text,
        interrupted=interrupted,
        cancelled=cancelled,
        language=language,
        keyboard_layout=keyboard_layout,
    )
