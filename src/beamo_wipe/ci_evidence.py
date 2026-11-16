# SPDX-License-Identifier: GPL-3.0-or-later
"""Collect execution receipts on CI and finalize provenance after QEMU."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import stat
import subprocess
import sys

from beamo_wipe import __version__
from beamo_wipe.verification_evidence import (
    KNOWN_GATES, build_gate_receipt, build_package_inventory,
    _hide_host_paths, parse_dpkg_status, parse_junit_xml, utc_now_s,
    verify_gate_receipt,
)


def _write(path: Path, data: dict) -> None:
    """Create one JSON file without following or losing its parent path."""
    from beamo_wipe.release_signing import _write_new_file

    payload = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_new_file(Path(path), payload, 0o644)


def _unique_json_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeError("duplicate CI evidence field")
        result[key] = value
    return result


_DIRECTORY_ID_FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid")
_FILE_ID_FIELDS = (
    "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
    "st_mtime_ns", "st_ctime_ns",
)


def _metadata_values(metadata, fields):
    return tuple(getattr(metadata, field, None) for field in fields)


def _close_reader_fds(primary, owned, *names) -> None:
    """Consume each owned descriptor once, retaining an operation's primary error."""
    first_error = None
    for name in names or tuple(owned):
        fd = owned.pop(name, None)
        if fd is None:
            continue
        try:
            os.close(fd)
        except BaseException as exc:
            if first_error is None:
                first_error = exc
    if primary is None and first_error is not None:
        raise first_error


def _open_evidence_directory(directory: Path, *, create: bool = False) -> int:
    """Open every directory component without links and return the final fd."""
    requested = Path(directory)
    if ".." in requested.parts:
        raise RuntimeError("unsafe CI evidence directory")
    path = Path(os.path.abspath(os.fspath(requested)))
    flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    owned = {}
    try:
        try:
            owned["directory"] = os.open(os.sep, flags)
            for component in path.parts[1:]:
                if create:
                    try:
                        os.mkdir(component, 0o700, dir_fd=owned["directory"])
                    except FileExistsError:
                        pass
                owned["pending"] = os.open(
                    component, flags, dir_fd=owned["directory"]
                )
                _close_reader_fds(None, owned, "directory")
                owned["directory"] = owned.pop("pending")
            if not stat.S_ISDIR(os.fstat(owned["directory"]).st_mode):
                raise RuntimeError("unsafe CI evidence directory")
            return owned["directory"]
        except OSError as exc:
            raise RuntimeError("unsafe CI evidence directory") from exc
    except BaseException as exc:
        _close_reader_fds(exc, owned)
        raise


def _require_evidence_directory(directory: Path, *, create: bool = False) -> None:
    """Reject a linked path component before writing or trusting CI receipts."""
    owned = {}
    try:
        owned["directory"] = _open_evidence_directory(directory, create=create)
        _close_reader_fds(None, owned)
    except BaseException as exc:
        _close_reader_fds(exc, owned)
        raise


def _require_evidence_binding(directory: Path, directory_fd: int) -> None:
    """Require the requested path to still name the opened evidence directory."""
    current_fd = None
    primary = None
    try:
        try:
            current_fd = _open_evidence_directory(directory)
        except RuntimeError as exc:
            raise RuntimeError("CI evidence directory changed while in use") from exc
        if _metadata_values(
            os.fstat(directory_fd), _DIRECTORY_ID_FIELDS
        ) != _metadata_values(os.fstat(current_fd), _DIRECTORY_ID_FIELDS):
            raise RuntimeError("CI evidence directory changed while in use")
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": current_fd})


def _name_exists(directory_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def _read_descriptor(fd: int, limit: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    remaining = limit + 1
    while remaining:
        chunk = os.read(fd, min(1024 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _regular_file_is_bound(opened, current) -> bool:
    return (
        stat.S_ISREG(opened.st_mode)
        and opened.st_nlink == 1
        and _metadata_values(opened, _FILE_ID_FIELDS)
        == _metadata_values(current, _FILE_ID_FIELDS)
    )


class _OptionalImageInputMissing(Exception):
    """Approved operation-level absence, pending successful owned cleanup."""


def _read_regular_at(
    directory_fd: int, name: str, *, limit: int, what: str, missing_ok: bool = False,
) -> bytes:
    """Read bounded stable bytes from one regular file in a pinned directory."""
    fd = None
    primary = None
    try:
        try:
            fd = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            opened = os.fstat(fd)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size > limit
            ):
                raise RuntimeError(f"cannot safely read {what}; unsafe file or symlink")
            first = _read_descriptor(fd, limit)
            middle = os.fstat(fd)
            second = _read_descriptor(fd, limit)
            final = os.fstat(fd)
            named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            if missing_ok:
                raise _OptionalImageInputMissing from exc
            raise
        except OSError as exc:
            raise RuntimeError(
                f"cannot safely read {what}; unsafe file or symlink"
            ) from exc
    except _OptionalImageInputMissing:
        # Optional absence is normal only if the leaf close below succeeds.
        raise
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"file": fd})
    if (
        len(first) > limit
        or first != second
        or len(first) != opened.st_size
        or not _regular_file_is_bound(opened, middle)
        or not _regular_file_is_bound(opened, final)
        or not _regular_file_is_bound(opened, named)
    ):
        raise RuntimeError(f"{what} changed while being read")
    return first


def _hash_regular_at(
    directory_fd: int, name: str, *, what: str,
    metadata: list[os.stat_result] | None = None,
) -> str:
    """Hash one stable regular file in a pinned directory."""
    fd = None
    primary = None
    try:
        try:
            fd = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise RuntimeError(f"unsafe {what}")
            first = hashlib.sha256()
            first_size = 0
            for chunk in iter(lambda: os.read(fd, 1024 * 1024), b""):
                first.update(chunk)
                first_size += len(chunk)
            middle = os.fstat(fd)
            os.lseek(fd, 0, os.SEEK_SET)
            second = hashlib.sha256()
            second_size = 0
            for chunk in iter(lambda: os.read(fd, 1024 * 1024), b""):
                second.update(chunk)
                second_size += len(chunk)
            final = os.fstat(fd)
            named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise RuntimeError(f"unsafe {what}") from exc
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"file": fd})
    if (
        first_size != opened.st_size
        or second_size != first_size
        or second.digest() != first.digest()
        or not _regular_file_is_bound(opened, middle)
        or not _regular_file_is_bound(opened, final)
        or not _regular_file_is_bound(opened, named)
    ):
        raise RuntimeError(f"{what} changed while being hashed")
    if metadata is not None:
        metadata.append(opened)
    return first.hexdigest()


def _create_regular_at(directory_fd: int, name: str, mode: int = 0o644) -> int:
    flags = (
        os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = None
    try:
        fd = os.open(name, flags, mode, dir_fd=directory_fd)
        if os.name == "posix":
            os.fchmod(fd, mode)
        return fd
    except BaseException as exc:
        _close_reader_fds(exc, {"file": fd})
        raise


def _write_bytes_at(directory_fd: int, name: str, payload: bytes) -> None:
    """Exclusively create and verify bytes within a pinned directory."""
    fd = None
    data = bytes(payload)
    primary = None
    try:
        try:
            fd = _create_regular_at(directory_fd, name)
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("short write")
                view = view[written:]
            os.fsync(fd)
            opened = os.fstat(fd)
            named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if (
                not _regular_file_is_bound(opened, named)
                or opened.st_size != len(data)
                or _read_descriptor(fd, len(data)) != data
                or _read_descriptor(fd, len(data)) != data
            ):
                raise RuntimeError("CI evidence output changed while being written")
            os.fsync(directory_fd)
            if (
                not _regular_file_is_bound(opened, os.fstat(fd))
                or not _regular_file_is_bound(
                    opened,
                    os.stat(name, dir_fd=directory_fd, follow_symlinks=False),
                )
                or _read_descriptor(fd, len(data)) != data
            ):
                raise RuntimeError("CI evidence output changed while being written")
        except FileExistsError:
            raise
        except OSError as exc:
            raise RuntimeError("CI evidence output cannot be safely written") from exc
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"file": fd})


def _write_json_at(directory_fd: int, name: str, data: dict) -> None:
    payload = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_bytes_at(directory_fd, name, payload)


def qemu_evidence_hashes(directory: Path) -> dict[str, str]:
    """Hash copied QEMU evidence files, excluding the private staging path."""
    directory_fd = None
    primary = None
    try:
        try:
            try:
                directory_fd = _open_evidence_directory(directory)
            except (OSError, RuntimeError) as exc:
                raise RuntimeError("QEMU evidence cannot be read") from exc
            opened_directory = os.fstat(directory_fd)
            files = {}
            names = sorted(os.listdir(directory_fd))
            identities = {}
            for name in names:
                if name == "PATH":
                    continue
                named_member = os.stat(
                    name, dir_fd=directory_fd, follow_symlinks=False
                )
                if (
                    not stat.S_ISREG(named_member.st_mode)
                    or getattr(named_member, "st_nlink", 1) != 1
                ):
                    raise RuntimeError("QEMU evidence contains a non-regular file")
                member_metadata: list[os.stat_result] = []
                files[name] = _hash_regular_at(
                    directory_fd, name, what="QEMU evidence",
                    metadata=member_metadata,
                )
                # Bind the directory recheck to the inode actually hashed,
                # rather than to an earlier pathname stat that could change.
                opened = member_metadata[0]
                identities[name] = (
                    opened.st_dev, opened.st_ino, opened.st_size,
                    opened.st_mtime_ns, opened.st_ctime_ns,
                )
            if sorted(os.listdir(directory_fd)) != names:
                raise RuntimeError("QEMU evidence files changed while hashing")
            for name, identity in identities.items():
                current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if (
                    not stat.S_ISREG(current.st_mode)
                    or getattr(current, "st_nlink", 1) != 1
                    or (current.st_dev, current.st_ino, current.st_size,
                        current.st_mtime_ns, current.st_ctime_ns) != identity
                ):
                    raise RuntimeError("QEMU evidence file changed while hashing")
            named_directory = os.stat(directory, follow_symlinks=False)
            if (
                not stat.S_ISDIR(named_directory.st_mode)
                or (named_directory.st_dev, named_directory.st_ino,
                    named_directory.st_mtime_ns, named_directory.st_ctime_ns)
                != (opened_directory.st_dev, opened_directory.st_ino,
                    opened_directory.st_mtime_ns, opened_directory.st_ctime_ns)
            ):
                raise RuntimeError("QEMU evidence directory changed while hashing")
            _require_evidence_binding(directory, directory_fd)
        except OSError as exc:
            raise RuntimeError("QEMU evidence cannot be read") from exc
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})
    if not files:
        raise RuntimeError("QEMU evidence is empty")
    return files


def qemu_evidence_digest(files: dict[str, str]) -> str:
    """Bind both evidence filenames and contents in one stable digest."""
    blob = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _completed_qemu_evidence_digest(directory: Path) -> str:
    files = qemu_evidence_hashes(directory)
    if "summary.txt" not in files:
        raise RuntimeError("QEMU evidence is missing its completion summary")
    return qemu_evidence_digest(files)


def _verify_execution_log(
    path: Path, directory_fd: int, logged, size: int, digest: str
) -> None:
    """Bind retained regular-file bytes to the output actually collected."""
    fields = (
        "st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_nlink",
        "st_mtime_ns", "st_ctime_ns",
    )

    def matches(metadata):
        return stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and all(
            getattr(metadata, key) == getattr(logged, key) for key in fields
        )

    try:
        _require_evidence_binding(path.parent, directory_fd)
        if logged.st_size != size or not matches(os.stat(path, follow_symlinks=False)):
            raise RuntimeError("execution log changed during gate")
        if not matches(os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)):
            raise RuntimeError("execution log changed during gate")
        fd = None
        primary = None
        try:
            fd = os.open(
                path.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fd,
            )
            if not matches(os.fstat(fd)):
                raise RuntimeError("execution log changed during gate")
            actual = hashlib.sha256()
            total = 0
            while total <= size:
                chunk = os.read(fd, min(65536, size + 1 - total))
                if not chunk:
                    break
                total += len(chunk)
                actual.update(chunk)
            if (
                total != size or actual.hexdigest() != digest
                or not matches(os.fstat(fd))
                or not matches(
                    os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
                )
            ):
                raise RuntimeError("execution log changed during gate")
        except BaseException as exc:
            primary = exc
            raise
        finally:
            _close_reader_fds(primary, {"directory": fd})
        _require_evidence_binding(path.parent, directory_fd)
    except OSError as exc:
        raise RuntimeError("execution log changed during gate") from exc


def run_gate(gate, command, *, root, evidence_dir, build_id):
    """Run once, retaining the exit status and exact combined output."""
    if gate not in KNOWN_GATES:
        raise RuntimeError("unknown CI gate")
    requested_evidence_dir = Path(evidence_dir)
    evidence_dir = Path(os.path.abspath(os.fspath(requested_evidence_dir)))
    receipt_name = f"{gate}.receipt.json"
    log_name = f"{gate}.log"
    junit_name = f"{gate}.xml"
    orca_junit_name = junit_name + ".orca.xml"
    log_path = evidence_dir / log_name
    junit = evidence_dir / junit_name
    directory_fd = None
    primary = None
    try:
        directory_fd = _open_evidence_directory(evidence_dir, create=True)
        _require_evidence_binding(evidence_dir, directory_fd)
        if any(
            _name_exists(directory_fd, name)
            for name in (receipt_name, log_name, junit_name, orca_junit_name)
        ):
            raise RuntimeError(
                f"stale evidence for {gate}; use a fresh build workspace"
            )
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        proc_directory = Path(f"/proc/self/fd/{directory_fd}")
        if not Path("/proc/self/fd").is_dir():
            raise RuntimeError("pinned CI evidence paths are unavailable")
        pinned_junit = str(proc_directory / junit_name)
        original_junit_paths = {
            str(junit),
            str(requested_evidence_dir / junit_name),
        }
        child_command = []
        replace_next = False
        for argument in command:
            text = os.fspath(argument)
            if replace_next and text in original_junit_paths:
                text = pinned_junit
            replace_next = text == "--junitxml"
            if text in original_junit_paths:
                text = pinned_junit
            else:
                for original_junit in original_junit_paths:
                    if text == "--junitxml=" + original_junit:
                        text = "--junitxml=" + pinned_junit
                        break
            child_command.append(text)
        env = dict(
            os.environ,
            BEAMO_GATE_CHILD="1",
            BEAMO_GATE_JUNIT=pinned_junit,
        )
        started = utc_now_s()
        log_digest = hashlib.sha256()
        log_size = 0
        with os.fdopen(_create_regular_at(directory_fd, log_name), "wb") as log:
            with subprocess.Popen(
                child_command,
                cwd=root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                pass_fds=(directory_fd,),
            ) as proc:
                assert proc.stdout is not None
                for chunk in iter(lambda: proc.stdout.read1(65536), b""):
                    log.write(chunk)
                    log_digest.update(chunk)
                    log_size += len(chunk)
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                code = proc.wait()
            log.flush()
            os.fsync(log.fileno())
            logged = os.fstat(log.fileno())
        _verify_execution_log(
            log_path, directory_fd, logged, log_size, log_digest.hexdigest()
        )
        ended = utc_now_s()
        measured = dict(
            passed=int(code == 0), failed=int(code != 0), errors=0,
            skipped=0, xfailed=0, deselected=0, total=1,
        )
        skips = []
        status = "pass" if code == 0 else "fail"
        reason = ""
        if gate in ("iso", "qemu") and env.get(f"SKIP_{gate.upper()}") == "true":
            if code == 0:
                status = "skip"
                reason = f"SKIP_{gate.upper()}=true"
                measured.update(passed=0, skipped=1)
                skips = [dict(id=gate, kind="skip", reason=reason)]
        if gate == "tests":
            report_names = [
                name for name in (junit_name, orca_junit_name)
                if _name_exists(directory_fd, name)
            ]
            if not report_names or (code == 0 and junit_name not in report_names):
                raise RuntimeError(
                    "test gate did not produce its JUnit execution report"
                )
            measured = dict.fromkeys(measured, 0)
            for report_name in report_names:
                junit_bytes = _read_regular_at(
                    directory_fd,
                    report_name,
                    limit=16 * 1024 * 1024,
                    what="JUnit execution report",
                )
                try:
                    parsed = parse_junit_xml(junit_bytes.decode("utf-8"))
                except UnicodeDecodeError as exc:
                    raise RuntimeError(
                        "JUnit execution report is not UTF-8"
                    ) from exc
                skips.extend(parsed.pop("skips"))
                for key, value in parsed.items():
                    measured[key] += value
        environment = dict(
            platform=sys.platform,
            arch=platform.machine(),
            python=platform.python_version(),
            runner="cloudbuild" if build_id != "local" else "local",
        )
        if os.environ.get("BEAMO_CI_RUNNER") == "blacksmith":
            environment.update(runner="blacksmith", **{
                key: os.environ[name] for key, name in (
                    ("github_run_id", "GITHUB_RUN_ID"),
                    ("github_run_attempt", "GITHUB_RUN_ATTEMPT"),
                    ("github_repository", "GITHUB_REPOSITORY"),
                )
            })
        if gate == "qemu" and status == "pass":
            environment["qemu_evidence_sha256"] = _completed_qemu_evidence_digest(
                root / "qemu-evidence"
            )
        receipt = build_gate_receipt(
            gate=gate,
            status=status,
            command=_hide_host_paths(shlex.join(command)),
            source_commit=commit,
            build_id=build_id,
            environment=environment,
            measured=measured,
            skips=skips,
            log_sha256="" if status == "skip" else log_digest.hexdigest(),
            reason=reason,
            started_at=started,
            ended_at=ended,
        )
        _require_evidence_binding(evidence_dir, directory_fd)
        _write_json_at(directory_fd, receipt_name, receipt)
        _require_evidence_binding(evidence_dir, directory_fd)
        return receipt
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})


def _image_directory_fd(root: Path, relative: Path, *, missing_ok: bool = False) -> int:
    """Open a mounted-image directory without following any component link."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    owned = {}
    try:
        try:
            root_fd = owned["root"] = _open_evidence_directory(root)
        except RuntimeError as exc:
            raise RuntimeError("unsafe image inventory input") from exc
        fd = owned["directory"] = os.dup(root_fd)
        for component in relative.parts:
            try:
                next_fd = owned["pending"] = os.open(component, flags, dir_fd=fd)
            except FileNotFoundError as exc:
                if missing_ok:
                    raise _OptionalImageInputMissing from exc
                raise
            _close_reader_fds(None, owned, "directory")
            owned["directory"] = owned.pop("pending")
            fd = next_fd
        _require_evidence_binding(root, root_fd)
        _close_reader_fds(None, owned, "root")
        return fd
    except _OptionalImageInputMissing:
        # A close failure must not be mistaken for operation-level absence.
        try:
            _close_reader_fds(None, owned, "pending", "directory", "root")
        except OSError as cleanup:
            raise RuntimeError("unsafe image inventory input") from cleanup
        raise
    except BaseException as exc:
        _close_reader_fds(exc, owned, "pending", "directory", "root")
        raise


def _image_text(root: Path, relative: Path, *, required: bool, limit: int) -> str | None:
    """Read a regular image file, never a host file reached through a link."""
    parent_fd = None
    primary = None
    try:
        try:
            parent_fd = _image_directory_fd(root, relative.parent, missing_ok=not required)
            data = _read_regular_at(
                parent_fd,
                relative.name,
                limit=limit,
                what="image inventory input",
                missing_ok=not required,
            )
            return data.decode("utf-8")
        except _OptionalImageInputMissing:
            return None
        except FileNotFoundError as exc:
            if required:
                raise RuntimeError("missing image inventory input") from exc
            raise RuntimeError("unsafe image inventory input") from exc
        except (OSError, UnicodeDecodeError) as exc:
            raise RuntimeError("unsafe image inventory input") from exc
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": parent_fd})


def _image_source_names(root: Path) -> list[str]:
    directory_fd = None
    primary = None
    try:
        try:
            directory_fd = _image_directory_fd(
                root, Path("etc/apt/sources.list.d"), missing_ok=True
            )
            try:
                names = os.listdir(directory_fd)
            except FileNotFoundError:
                return []
            return sorted(
                name for name in names
                if name.endswith((".list", ".sources"))
            )
        except _OptionalImageInputMissing:
            return []
        except OSError as exc:
            raise RuntimeError("unsafe image inventory input") from exc
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})


def _active_apt_uris(path: Path, content: str) -> set[str]:
    """Extract only active APT entries, excluding comments and disabled stanzas."""
    sources = set()
    if path.suffix != ".sources":
        for raw_line in content.splitlines():
            line = raw_line.partition("#")[0].strip()
            match = re.match(r"deb(?:-src)?\s+", line)
            if not match:
                continue
            remainder = line[match.end():].lstrip()
            if remainder.startswith("["):
                closing = remainder.find("]")
                if closing < 0:
                    continue
                remainder = remainder[closing + 1:].lstrip()
            uri = remainder.split(maxsplit=1)[0] if remainder else ""
            if uri.startswith(("http://", "https://")):
                sources.add(uri)
        return sources

    for paragraph in re.split(r"\n\s*\n", content):
        fields: dict[str, str] = {}
        current = ""
        for raw_line in paragraph.splitlines():
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            if raw_line[0].isspace():
                if current:
                    fields[current] += " " + raw_line.strip()
                continue
            key, separator, value = raw_line.partition(":")
            if not separator:
                continue
            current = key.lower()
            fields[current] = value.partition("#")[0].strip()
        if fields.get("enabled", "yes").lower() == "no":
            continue
        sources.update(
            uri for uri in fields.get("uris", "").split()
            if uri.startswith(("http://", "https://"))
        )
    return sources


def collect_inventory(image_root: Path, dest: Path, commit: str) -> None:
    """Read package status and configured repositories from the mounted image."""
    dest = Path(os.path.abspath(os.fspath(dest)))
    directory_fd = None
    primary = None
    try:
        directory_fd = _open_evidence_directory(dest.parent)
        _require_evidence_binding(dest.parent, directory_fd)
        sources = set()
        paths = [Path("etc/apt/sources.list")]
        paths.extend(
            Path("etc/apt/sources.list.d") / name
            for name in _image_source_names(image_root)
        )
        for path in paths:
            content = _image_text(
                image_root, path, required=False, limit=1024 * 1024
            )
            if content is not None:
                sources.update(_active_apt_uris(path, content))
        status = _image_text(
            image_root,
            Path("var/lib/dpkg/status"),
            required=True,
            limit=16 * 1024 * 1024,
        )
        assert status is not None
        inventory = build_package_inventory(
            packages=parse_dpkg_status(status),
            collected_from="squashfs var/lib/dpkg/status",
            apt_sources=sorted(sources),
            source_commit=commit,
        )
        _require_evidence_binding(dest.parent, directory_fd)
        _write_json_at(directory_fd, dest.name, inventory)
        _require_evidence_binding(dest.parent, directory_fd)
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})


def _load_receipts_at(directory_fd: int) -> list[dict]:
    """Load receipts and logs relative to one already pinned directory."""
    names = sorted(os.listdir(directory_fd))
    receipts = []
    for name in (item for item in names if item.endswith(".receipt.json")):
        raw = _read_regular_at(
            directory_fd,
            name,
            limit=4 * 1024 * 1024,
            what="CI gate receipt",
        )
        receipt = verify_gate_receipt(
            json.loads(raw, object_pairs_hook=_unique_json_fields)
        )
        gate = receipt["gate"]
        if name != f"{gate}.receipt.json":
            raise RuntimeError("receipt filename does not match its gate")
        if receipt["status"] != "skip":
            if _hash_regular_at(
                directory_fd, f"{gate}.log", what="CI gate execution log"
            ) != receipt["log_sha256"]:
                raise RuntimeError(f"execution log digest mismatch for {gate}")
        receipts.append(receipt)
    if sorted(os.listdir(directory_fd)) != names:
        raise RuntimeError("CI evidence directory contents changed while in use")
    return receipts


def load_receipts(directory: Path) -> list[dict]:
    """Bind every receipt to the retained execution log before finalization."""
    directory = Path(os.path.abspath(os.fspath(directory)))
    directory_fd = None
    primary = None
    try:
        directory_fd = _open_evidence_directory(directory)
        receipts = _load_receipts_at(directory_fd)
        _require_evidence_binding(directory, directory_fd)
        return receipts
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})


def finalize(root: Path) -> None:
    from beamo_wipe import release_manifest as rm

    allow_dirty = os.environ.get("ALLOW_DIRTY") == "1"
    dist = root / "dist"
    dest = dist / f"beamo-wipe-{__version__}-amd64.manifest.json"
    verified_manifest = rm.verify_build_manifest(dest, allow_dirty=allow_dirty)
    previous = json.loads(verified_manifest, object_pairs_hook=_unique_json_fields)
    if (previous["source"]["commit"] != rm.git_commit()
            or previous["build"]["release_build_id"] != os.environ.get("BUILD_ID", "local")):
        raise RuntimeError("built artifact belongs to another source or build")
    checksum_snapshot = rm.require_verified_prior_checksum_list(dist, replace_link=True)
    evidence_dir = dist / "evidence"
    receipts = load_receipts(evidence_dir)
    evidence_fd = None
    primary = None
    try:
        evidence_fd = _open_evidence_directory(evidence_dir)
        pinned_receipts = _load_receipts_at(evidence_fd)
        if pinned_receipts != receipts:
            raise RuntimeError("CI evidence directory changed while in use")
        receipts = pinned_receipts
        raw_inventory = _read_regular_at(
            evidence_fd,
            "packages.json",
            limit=32 * 1024 * 1024,
            what="packages.json CI package inventory",
        )
        _require_evidence_binding(evidence_dir, evidence_fd)
    except BaseException as exc:
        primary = exc
        raise
    finally:
        if evidence_fd is not None:
            try:
                os.close(evidence_fd)
            except BaseException:
                if primary is None:
                    raise
    inventory = json.loads(raw_inventory, object_pairs_hook=_unique_json_fields)
    inventory_digest = hashlib.sha256(raw_inventory).hexdigest()
    manifest = rm.generate_manifest(strict=not allow_dirty, gate_receipts=receipts, package_inventory=inventory)
    if manifest["artifact"] != previous["artifact"]:
        raise RuntimeError("artifact changed during verification")
    for field in ("beamo_wipe_version", "source", "dependencies", "live_build_inputs", "nwipe"):
        if manifest[field] != previous[field]:
            raise RuntimeError("build inputs changed during verification")
    for receipt in receipts:
        if receipt["gate"] == "qemu" and receipt["status"] == "pass":
            expected = receipt["environment"].get("qemu_evidence_sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise RuntimeError("QEMU evidence is not bound by its gate receipt")
            if _completed_qemu_evidence_digest(root / "qemu-evidence") != expected:
                raise RuntimeError("QEMU evidence changed after its gate")
    rm.write_manifest(manifest, dest)
    verified_manifest = rm.verify_manifest(dest, allow_dirty=allow_dirty)
    verified_artifact = json.loads(
        verified_manifest, object_pairs_hook=_unique_json_fields
    )["artifact"]
    iso = dist / verified_artifact["iso_name"]
    iso_sha = verified_artifact["iso_sha256"]
    manifest_sha = hashlib.sha256(verified_manifest).hexdigest()
    # Bind checksums to the accepted bytes and the initially permitted output.
    rm._atomic_write(
        dist / "SHA256SUMS",
        f"{iso_sha}  {iso.name}\n{manifest_sha}  {dest.name}\n".encode("ascii"),
        expected=checksum_snapshot,
    )
    print("Final verified evidence: " + json.dumps({
        "source_commit": manifest["source"]["commit"],
        "build_id": manifest["build"]["release_build_id"],
        "iso_sha256": iso_sha,
        "manifest_sha256": manifest_sha,
        "gate_count": len(receipts),
        "packages_sha256": inventory_digest,
    }, sort_keys=True), flush=True)


def print_summary(evidence_dir: Path) -> None:
    """Print pass/fail/skip and elapsed seconds for every written receipt."""
    evidence_dir = Path(os.path.abspath(os.fspath(evidence_dir)))
    try:
        initial = os.lstat(evidence_dir)
    except FileNotFoundError:
        print("CI timing summary: no evidence directory")
        return
    if not stat.S_ISDIR(initial.st_mode) and not stat.S_ISLNK(initial.st_mode):
        print("CI timing summary: no evidence directory")
        return
    directory_fd = None
    primary = None
    try:
        directory_fd = _open_evidence_directory(evidence_dir)
        rows = []
        names = sorted(os.listdir(directory_fd))
        for name in (item for item in names if item.endswith(".receipt.json")):
            raw = _read_regular_at(
                directory_fd,
                name,
                limit=4 * 1024 * 1024,
                what="CI gate receipt",
            )
            receipt = verify_gate_receipt(
                json.loads(raw, object_pairs_hook=_unique_json_fields)
            )
            if name != f"{receipt['gate']}.receipt.json":
                raise RuntimeError("receipt filename does not match its gate")
            started = receipt.get("started_at", "")
            ended = receipt.get("ended_at", "")
            elapsed = "unknown"
            try:
                start = datetime.datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ")
                end = datetime.datetime.strptime(ended, "%Y-%m-%dT%H:%M:%SZ")
                elapsed = f"{int((end - start).total_seconds())}s"
            except (TypeError, ValueError):
                pass
            rows.append((receipt["gate"], receipt["status"], elapsed))
        if sorted(os.listdir(directory_fd)) != names:
            raise RuntimeError("CI evidence directory contents changed while in use")
        _require_evidence_binding(evidence_dir, directory_fd)
    except BaseException as exc:
        primary = exc
        raise
    finally:
        _close_reader_fds(primary, {"directory": directory_fd})
    print("CI timing summary")
    for gate, status, elapsed in rows:
        print(f"  {gate}: {status} {elapsed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=sorted(KNOWN_GATES) + ["inventory", "summary"])
    parser.add_argument("--image-root", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    evidence = root / "dist/evidence"
    if args.gate == "summary":
        print_summary(evidence)
        return 0
    if args.gate == "inventory":
        if args.image_root is None:
            parser.error("inventory requires --image-root")
        from beamo_wipe.release_manifest import git_commit
        _require_evidence_directory(evidence, create=True)
        collect_inventory(args.image_root, evidence / "packages.json", git_commit())
        return 0
    receipt = run_gate(args.gate, ["bash", "scripts/ci-hosted.sh", args.gate],
                       root=root, evidence_dir=evidence, build_id=os.environ.get("BUILD_ID", "local"))
    if receipt["status"] == "fail":
        return 1
    if args.gate == "qemu" and receipt["status"] == "pass":
        finalize(root)
        print_summary(evidence)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"CI evidence failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
