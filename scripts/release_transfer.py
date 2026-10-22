#!/usr/bin/env python3
"""Move only measured release inputs between qualification and publication."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
from typing import Any, Iterable, Optional
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from beamo_wipe.release_manifest import (  # noqa: E402
    _REGULAR_BIND_FIELDS,
    _RegularBinding,
    _binding,
    _metadata_values,
    _named_metadata,
    _open_bound_regular,
    _open_pinned_parent,
    _read_regular_snapshot,
    _require_parent_binding,
    _require_regular_binding as _require_regular_binding_raw,
)
from beamo_wipe.release_signing import (  # noqa: E402
    _unique_json_fields,
    _write_new_file,
)
from publish_release_gcs import _release_inputs  # noqa: E402


SCHEMA = "beamo-wipe-blacksmith-transfer/1"
CHUNK = 8 * 1024 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_SIDECAR_BYTES = 1024 * 1024
MAX_RAW_IMAGE_BYTES = 3 * 1024**3
PACKED_MANIFEST_SHA256: Optional[str] = None
_DIRECTORY_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_uid",
    "st_nlink",
    "st_mtime_ns",
    "st_ctime_ns",
)
_DIRECTORY_IDENTITY_FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid", "st_nlink")


class _DirectoryBinding:
    """One owned, link-free directory retained open across an operation."""

    def __init__(
        self,
        path: Path,
        probe: Path,
        directory_fd: Optional[int],
        fields: tuple[Any, ...],
    ) -> None:
        self.path = path
        self.probe = probe
        self.directory_fd = directory_fd
        self.fields = fields


def identity() -> tuple[str, str, str]:
    version = os.environ.get("BEAMO_WIPE_VERSION", "")
    commit = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(
        r"[0-9a-f]{40}", commit
    ):
        raise RuntimeError("invalid transfer source identity")
    if os.environ.get("GITHUB_REPOSITORY") != "BeamoTech/beamo-wipe":
        raise RuntimeError("transfer repository differs from release repository")
    key = "/".join(
        os.environ[k]
        for k in ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")
    )
    build_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/" + key))
    return version, commit, build_id


def release_inputs(version: str) -> list[Path]:
    return _release_inputs(version)


def _source_paths(version: str) -> dict[str, Path]:
    """Return unique, lexical checkout-relative release source paths."""
    root = Path(os.path.abspath(os.fspath(ROOT)))
    sources: dict[str, Path] = {}
    for candidate in release_inputs(version):
        absolute = Path(os.path.abspath(os.fspath(candidate)))
        try:
            relative = absolute.relative_to(root)
        except ValueError as exc:
            raise RuntimeError("release input is outside the source checkout") from exc
        if (
            not relative.parts
            or relative.parts[0] not in {"dist", "qemu-evidence"}
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise RuntimeError("release input has an unsafe transfer name")
        name = relative.as_posix()
        if name in sources:
            raise RuntimeError(f"duplicate release input name: {name}")
        sources[name] = root.joinpath(*relative.parts)
    return sources


def _selected_names(version: str, sources: dict[str, Path]) -> set[str]:
    stem = f"beamo-wipe-{version}-amd64"
    raw_name = f"dist/{stem}.img"
    signature_name = f"dist/{stem}.manifest.json.sig"
    if raw_name not in sources:
        raise RuntimeError("release inputs omit the tested USB image")
    names = set(sources) - {raw_name, signature_name}
    names.add(f"dist/{stem}.img.gz")
    return names


def input_names(version: str) -> set[str]:
    sources = _source_paths(version)
    return _selected_names(version, sources)


def _binding_field(binding: _RegularBinding, name: str) -> Any:
    return binding.fields[_REGULAR_BIND_FIELDS.index(name)]


def _validate_file_binding(binding: _RegularBinding, *, what: str) -> None:
    if (
        not stat.S_ISREG(_binding_field(binding, "st_mode"))
        or _binding_field(binding, "st_uid") != os.getuid()
        or _binding_field(binding, "st_nlink") != 1
    ):
        raise RuntimeError(f"{what} is not a safely bound regular file")


def _require_file_binding(binding: _RegularBinding) -> None:
    try:
        _require_regular_binding_raw(binding)
    except OSError as exc:
        raise RuntimeError(
            f"{binding.path.name} is no longer bound to its transfer path"
        ) from exc
    _validate_file_binding(binding, what=binding.path.name)


def _snapshot_digest(path: Path, *, what: str) -> tuple[int, str, _RegularBinding]:
    """Hash one stable, owned, single-link regular file and retain its binding."""
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(path)
    try:
        binding = _binding(absolute, opened, parent_fields)
        _validate_file_binding(binding, what=what)
        result = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(fd, CHUNK)
            if not chunk:
                break
            result.update(chunk)
            size += len(chunk)
        digest_value = result.hexdigest()
        final = os.fstat(fd)
        named = _named_metadata(absolute, directory_fd)
        requested = os.lstat(absolute)
        _require_parent_binding(absolute, directory_fd, parent_fields)
        expected = binding.fields
        if size != opened.st_size or any(
            _metadata_values(item, _REGULAR_BIND_FIELDS) != expected
            for item in (final, named, requested)
        ):
            raise RuntimeError(f"{what} changed while it was measured")
        return size, digest_value, binding
    except OSError as exc:
        raise RuntimeError(f"{what} cannot be safely measured") from exc
    finally:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def digest(path: Path) -> tuple[int, str]:
    size, digest_value, binding = _snapshot_digest(path, what="transfer file")
    _require_file_binding(binding)
    return size, digest_value


def _read_snapshot(
    path: Path, *, limit: int, what: str
) -> tuple[bytes, _RegularBinding]:
    try:
        data, binding = _read_regular_snapshot(path, limit=limit, what=what)
    except OSError as exc:
        raise RuntimeError(f"{what} cannot be safely read") from exc
    _validate_file_binding(binding, what=what)
    return data, binding


def _open_directory_binding(path: Path, *, what: str) -> _DirectoryBinding:
    probe, directory_fd, fields = _open_pinned_parent(
        path / ".release-transfer-directory-binding"
    )
    try:
        metadata = (
            os.fstat(directory_fd)
            if directory_fd is not None
            else os.lstat(probe.parent)
        )
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise RuntimeError(f"unsafe {what}")
        _require_parent_binding(probe, directory_fd, fields)
        return _DirectoryBinding(probe.parent, probe, directory_fd, fields)
    except Exception:
        if directory_fd is not None:
            os.close(directory_fd)
        raise


def _require_directory_binding(binding: _DirectoryBinding) -> None:
    _require_parent_binding(binding.probe, binding.directory_fd, binding.fields)
    metadata = (
        os.fstat(binding.directory_fd)
        if binding.directory_fd is not None
        else os.lstat(binding.path)
    )
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise RuntimeError(f"unsafe transfer directory: {binding.path.name}")


def _close_directory_binding(binding: Optional[_DirectoryBinding]) -> None:
    if binding is not None and binding.directory_fd is not None:
        os.close(binding.directory_fd)


def _create_directory(path: Path, *, mode: int, what: str) -> _DirectoryBinding:
    absolute, parent_fd, parent_fields = _open_pinned_parent(path)
    try:
        if parent_fd is None:
            os.mkdir(absolute, mode)
        else:
            os.mkdir(absolute.name, mode, dir_fd=parent_fd)
        _require_parent_binding(absolute, parent_fd, parent_fields)
    except FileExistsError as exc:
        raise RuntimeError(f"{what} already exists") from exc
    except OSError as exc:
        raise RuntimeError(f"{what} cannot be safely created") from exc
    finally:
        if parent_fd is not None:
            os.close(parent_fd)
    binding = _open_directory_binding(absolute, what=what)
    if os.name == "posix":
        metadata = os.fstat(binding.directory_fd)  # type: ignore[arg-type]
        if stat.S_IMODE(metadata.st_mode) != mode:
            _close_directory_binding(binding)
            raise RuntimeError(f"{what} has an unsafe mode")
    return binding


def _safe_tree_names(root: _DirectoryBinding) -> set[str]:
    """Enumerate a tree through directory descriptors without following links."""
    _require_directory_binding(root)
    if root.directory_fd is None:
        names: set[str] = set()
        for path in root.path.rglob("*"):
            metadata = os.lstat(path)
            relative = path.relative_to(root.path).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                raise RuntimeError("linked transfer entry")
            if stat.S_ISREG(metadata.st_mode):
                names.add(relative)
            elif not stat.S_ISDIR(metadata.st_mode):
                raise RuntimeError("special transfer entry")
        _require_directory_binding(root)
        return names

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )

    def walk(directory_fd: int, prefix: str) -> set[str]:
        before = os.fstat(directory_fd)
        if not stat.S_ISDIR(before.st_mode) or before.st_uid != os.getuid():
            raise RuntimeError("unsafe transfer directory entry")
        result: set[str] = set()
        for name in os.listdir(directory_fd):
            if name in {"", ".", ".."} or "/" in name or "\\" in name:
                raise RuntimeError("unsafe transfer entry name")
            metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            relative = f"{prefix}/{name}" if prefix else name
            if stat.S_ISREG(metadata.st_mode):
                result.add(relative)
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                raise RuntimeError("linked or special transfer entry")
            child_fd = os.open(name, flags, dir_fd=directory_fd)
            try:
                opened = os.fstat(child_fd)
                if _metadata_values(opened, _DIRECTORY_FIELDS) != _metadata_values(
                    metadata, _DIRECTORY_FIELDS
                ):
                    raise RuntimeError("transfer directory changed while enumerated")
                result.update(walk(child_fd, relative))
                final = os.fstat(child_fd)
                named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if any(
                    _metadata_values(item, _DIRECTORY_FIELDS)
                    != _metadata_values(opened, _DIRECTORY_FIELDS)
                    for item in (final, named)
                ):
                    raise RuntimeError("transfer directory changed while enumerated")
            finally:
                os.close(child_fd)
        after = os.fstat(directory_fd)
        if _metadata_values(after, _DIRECTORY_FIELDS) != _metadata_values(
            before, _DIRECTORY_FIELDS
        ):
            raise RuntimeError("transfer directory changed while enumerated")
        return result

    names = walk(root.directory_fd, "")
    _require_directory_binding(root)
    return names


def _write_all(fd: int, data: bytes) -> None:
    remaining = memoryview(data)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("short write")
        remaining = remaining[written:]


def _open_bound_source(binding: _RegularBinding) -> tuple[Path, Optional[int], int]:
    _require_file_binding(binding)
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(
        binding.path
    )
    if _binding(absolute, opened, parent_fields) != binding:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)
        raise RuntimeError(f"transfer source changed: {binding.path.name}")
    return absolute, directory_fd, fd


def _open_new_output(
    path: Path, *, mode: int
) -> tuple[Path, Optional[int], tuple[Any, ...], int]:
    absolute, directory_fd, parent_fields = _open_pinned_parent(path)
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        fd = (
            os.open(absolute, flags, mode)
            if directory_fd is None
            else os.open(absolute.name, flags, mode, dir_fd=directory_fd)
        )
        if os.name == "posix":
            os.fchmod(fd, mode)
        return absolute, directory_fd, parent_fields, fd
    except Exception:
        if directory_fd is not None:
            os.close(directory_fd)
        raise


def _finish_output(
    absolute: Path,
    directory_fd: Optional[int],
    parent_fields: tuple[Any, ...],
    fd: int,
    *,
    mode: int,
) -> _RegularBinding:
    os.fsync(fd)
    opened = os.fstat(fd)
    named = _named_metadata(absolute, directory_fd)
    _require_parent_binding(absolute, directory_fd, parent_fields)
    binding = _binding(absolute, opened, parent_fields)
    _validate_file_binding(binding, what="transfer output")
    if _metadata_values(named, _REGULAR_BIND_FIELDS) != binding.fields or (
        os.name == "posix" and stat.S_IMODE(opened.st_mode) != mode
    ):
        raise RuntimeError(f"transfer output changed: {absolute.name}")
    if directory_fd is not None:
        os.fsync(directory_fd)
    return binding


def _copy(source: Path | _RegularBinding, destination: Path) -> _RegularBinding:
    """Copy one already-measured source to one exclusive, bound output."""
    if isinstance(source, _RegularBinding):
        source_binding = source
    else:
        _size, _sha, source_binding = _snapshot_digest(source, what="transfer source")
    _absolute_source, source_parent_fd, source_fd = _open_bound_source(source_binding)
    output_parent_fd: Optional[int] = None
    output_fd: Optional[int] = None
    try:
        absolute, output_parent_fd, parent_fields, output_fd = _open_new_output(
            destination, mode=0o644
        )
        while True:
            chunk = os.read(source_fd, CHUNK)
            if not chunk:
                break
            _write_all(output_fd, chunk)
        output_binding = _finish_output(
            absolute,
            output_parent_fd,
            parent_fields,
            output_fd,
            mode=0o644,
        )
        source_final = os.fstat(source_fd)
        if (
            _metadata_values(source_final, _REGULAR_BIND_FIELDS)
            != source_binding.fields
        ):
            raise RuntimeError(f"transfer source changed: {source_binding.path.name}")
    except FileExistsError as exc:
        raise RuntimeError(
            f"transfer output already exists: {destination.name}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"transfer copy failed: {destination.name}") from exc
    finally:
        if output_fd is not None:
            os.close(output_fd)
        if output_parent_fd is not None:
            os.close(output_parent_fd)
        os.close(source_fd)
        if source_parent_fd is not None:
            os.close(source_parent_fd)
    _require_file_binding(source_binding)
    _require_file_binding(output_binding)
    return output_binding


def _compress(source: _RegularBinding, destination: Path) -> _RegularBinding:
    _absolute_source, source_parent_fd, source_fd = _open_bound_source(source)
    output_parent_fd: Optional[int] = None
    output_fd: Optional[int] = None
    try:
        absolute, output_parent_fd, parent_fields, output_fd = _open_new_output(
            destination, mode=0o644
        )
        with os.fdopen(os.dup(source_fd), "rb") as source_stream:
            with os.fdopen(os.dup(output_fd), "wb") as output_stream:
                with gzip.GzipFile(
                    filename="",
                    mode="wb",
                    fileobj=output_stream,
                    mtime=0,
                    compresslevel=1,
                ) as zip_stream:
                    shutil.copyfileobj(source_stream, zip_stream, CHUNK)
                output_stream.flush()
        output_binding = _finish_output(
            absolute,
            output_parent_fd,
            parent_fields,
            output_fd,
            mode=0o644,
        )
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise RuntimeError("tested USB image cannot be safely compressed") from exc
    finally:
        if output_fd is not None:
            os.close(output_fd)
        if output_parent_fd is not None:
            os.close(output_parent_fd)
        os.close(source_fd)
        if source_parent_fd is not None:
            os.close(source_parent_fd)
    _require_file_binding(source)
    _require_file_binding(output_binding)
    return output_binding


def _decompress(
    source: _RegularBinding,
    destination: Path,
    *,
    expected_size: int,
    expected_sha: str,
) -> _RegularBinding:
    _absolute_source, source_parent_fd, source_fd = _open_bound_source(source)
    output_parent_fd: Optional[int] = None
    output_fd: Optional[int] = None
    try:
        absolute, output_parent_fd, parent_fields, output_fd = _open_new_output(
            destination, mode=0o644
        )
        result = hashlib.sha256()
        size = 0
        with os.fdopen(os.dup(source_fd), "rb") as source_stream:
            with gzip.GzipFile(fileobj=source_stream, mode="rb") as zip_stream:
                while True:
                    chunk = zip_stream.read(CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > expected_size:
                        raise RuntimeError(
                            "compressed USB image exceeds its qualified size"
                        )
                    result.update(chunk)
                    _write_all(output_fd, chunk)
        if size != expected_size or result.hexdigest() != expected_sha:
            raise RuntimeError("transferred USB image differs from qualified bytes")
        output_binding = _finish_output(
            absolute,
            output_parent_fd,
            parent_fields,
            output_fd,
            mode=0o644,
        )
    except RuntimeError:
        raise
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise RuntimeError("transferred USB image is not a valid gzip file") from exc
    finally:
        if output_fd is not None:
            os.close(output_fd)
        if output_parent_fd is not None:
            os.close(output_parent_fd)
        os.close(source_fd)
        if source_parent_fd is not None:
            os.close(source_parent_fd)
    _require_file_binding(source)
    _require_file_binding(output_binding)
    return output_binding


def _write_bytes(path: Path, payload: bytes) -> _RegularBinding:
    _write_new_file(path, payload, 0o644)
    written, binding = _read_snapshot(
        path, limit=len(payload), what="transfer manifest output"
    )
    if written != payload:
        raise RuntimeError("transfer manifest changed while it was written")
    _require_file_binding(binding)
    return binding


def _require_bindings(bindings: Iterable[_RegularBinding]) -> None:
    for binding in bindings:
        _require_file_binding(binding)


def _parse_manifest(data: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_json_fields,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("transfer manifest is not JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("transfer manifest is not an object")
    return value


def _validate_manifest(
    manifest: dict[str, Any],
    *,
    version: str,
    commit: str,
    build_id: str,
    expected_names: set[str],
) -> None:
    if set(manifest) != {
        "schema",
        "version",
        "source_commit",
        "build_id",
        "raw_image",
        "files",
    }:
        raise RuntimeError("transfer manifest has unexpected fields")
    if (
        manifest["schema"] != SCHEMA
        or manifest["version"] != version
        or manifest["source_commit"] != commit
        or manifest["build_id"] != build_id
    ):
        raise RuntimeError("transfer manifest has wrong source identity")
    raw = manifest["raw_image"]
    if (
        not isinstance(raw, dict)
        or set(raw) != {"bytes", "sha256"}
        or type(raw["bytes"]) is not int
        or not 0 < raw["bytes"] <= MAX_RAW_IMAGE_BYTES
        or not isinstance(raw["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", raw["sha256"])
    ):
        raise RuntimeError("transfer manifest has an invalid raw image record")
    files = manifest["files"]
    if not isinstance(files, dict) or set(files) != expected_names:
        raise RuntimeError("transfer manifest has wrong input names")
    for name, record in files.items():
        if (
            not isinstance(name, str)
            or not isinstance(record, dict)
            or set(record) != {"bytes", "sha256"}
            or type(record["bytes"]) is not int
            or record["bytes"] < 0
            or not isinstance(record["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
        ):
            raise RuntimeError(f"transfer manifest has an invalid file record: {name}")


def _ensure_parent_directories(root: Path, names: Iterable[str]) -> None:
    parents = sorted(
        {Path(name).parent for name in names if Path(name).parent != Path(".")},
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    for relative in parents:
        path = root.joinpath(*relative.parts)
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            metadata = os.lstat(path)
            if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
                raise RuntimeError("unsafe transfer output directory")


def _cleanup_owned_directory(binding: Optional[_DirectoryBinding]) -> None:
    if binding is None:
        return
    try:
        _require_directory_binding(binding)
    except (OSError, RuntimeError):
        return
    try:
        shutil.rmtree(binding.path)
    except OSError:
        return


def pack() -> Path:
    global PACKED_MANIFEST_SHA256
    PACKED_MANIFEST_SHA256 = None
    version, commit, build_id = identity()
    sources = _source_paths(version)
    expected_names = _selected_names(version, sources)
    transfer = ROOT / "release-transfer"
    transfer_binding: Optional[_DirectoryBinding] = None
    success = False
    try:
        transfer_binding = _create_directory(
            transfer, mode=0o700, what="release transfer directory"
        )
        _ensure_parent_directories(transfer, expected_names)
        stem = f"beamo-wipe-{version}-amd64"
        raw_name = f"dist/{stem}.img"
        raw = sources[raw_name]
        raw_size, raw_sha, raw_binding = _snapshot_digest(raw, what="tested USB image")
        if not 0 < raw_size <= MAX_RAW_IMAGE_BYTES:
            raise RuntimeError("tested USB image has an invalid size")
        sidecar_name = f"dist/{stem}.img.sha256"
        if sidecar_name not in sources:
            raise RuntimeError("release inputs omit the tested USB checksum")
        sidecar, sidecar_binding = _read_snapshot(
            sources[sidecar_name],
            limit=MAX_SIDECAR_BYTES,
            what="tested USB checksum sidecar",
        )
        if sidecar != f"{raw_sha}  {raw.name}\n".encode("ascii"):
            raise RuntimeError("tested USB image checksum sidecar differs")

        source_bindings = [raw_binding, sidecar_binding]
        output_bindings: list[_RegularBinding] = []
        source_records: dict[str, dict[str, Any]] = {}
        compressed_name = f"dist/{stem}.img.gz"
        for name in sorted(expected_names - {compressed_name}):
            source_size, source_sha, source_binding = _snapshot_digest(
                sources[name], what=f"release input {Path(name).name}"
            )
            source_records[name] = {"bytes": source_size, "sha256": source_sha}
            source_bindings.append(source_binding)
            output_bindings.append(_copy(source_binding, transfer / name))
        output_bindings.append(_compress(raw_binding, transfer / compressed_name))

        # Keep the small public digest helper exercised at the transfer root;
        # the retained directory binding makes a whole-tree swap fail closed.
        digest(transfer / sidecar_name)
        _require_directory_binding(transfer_binding)

        records: dict[str, dict[str, Any]] = {}
        measured_outputs: list[_RegularBinding] = []
        for name in sorted(expected_names):
            size, digest_value, binding = _snapshot_digest(
                transfer / name, what=f"transferred file {Path(name).name}"
            )
            records[name] = {"bytes": size, "sha256": digest_value}
            if name != compressed_name and records[name] != source_records[name]:
                raise RuntimeError(f"transfer copy differs from source: {name}")
            measured_outputs.append(binding)
        manifest = {
            "schema": SCHEMA,
            "version": version,
            "source_commit": commit,
            "build_id": build_id,
            "raw_image": {"bytes": raw_size, "sha256": raw_sha},
            "files": records,
        }
        manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode(
            "utf-8"
        )
        if len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise RuntimeError("transfer manifest exceeds the size limit")
        manifest_binding = _write_bytes(
            transfer / "transfer-manifest.json", manifest_bytes
        )
        actual_names = _safe_tree_names(transfer_binding)
        if actual_names != expected_names | {"transfer-manifest.json"}:
            raise RuntimeError("transfer contains missing or unexpected files")
        _require_bindings(source_bindings)
        _require_bindings(output_bindings)
        _require_bindings(measured_outputs)
        _require_file_binding(manifest_binding)
        _require_directory_binding(transfer_binding)
        PACKED_MANIFEST_SHA256 = hashlib.sha256(manifest_bytes).hexdigest()
        success = True
        return transfer
    finally:
        if not success:
            _cleanup_owned_directory(transfer_binding)
        _close_directory_binding(transfer_binding)


def _target_absent(root: _DirectoryBinding, name: str) -> None:
    _require_directory_binding(root)
    try:
        if root.directory_fd is None:
            os.lstat(root.path / name)
        else:
            os.stat(name, dir_fd=root.directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise RuntimeError("release output directory already exists")


def _directory_metadata(root: _DirectoryBinding, name: str) -> tuple[Any, ...]:
    metadata = (
        os.lstat(root.path / name)
        if root.directory_fd is None
        else os.stat(name, dir_fd=root.directory_fd, follow_symlinks=False)
    )
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise RuntimeError("unsafe staged release directory")
    return _metadata_values(metadata, _DIRECTORY_IDENTITY_FIELDS)


def _rename_directory(
    source_root: _DirectoryBinding,
    destination_root: _DirectoryBinding,
    name: str,
) -> tuple[Any, ...]:
    expected = _directory_metadata(source_root, name)
    _target_absent(destination_root, name)
    if source_root.directory_fd is None or destination_root.directory_fd is None:
        (source_root.path / name).rename(destination_root.path / name)
    else:
        os.rename(
            name,
            name,
            src_dir_fd=source_root.directory_fd,
            dst_dir_fd=destination_root.directory_fd,
        )
    return expected


def _rollback_directory(
    stage: _DirectoryBinding,
    root: _DirectoryBinding,
    name: str,
    expected: tuple[Any, ...],
) -> None:
    try:
        if _directory_metadata(root, name) != expected:
            return
        if stage.directory_fd is None or root.directory_fd is None:
            (root.path / name).rename(stage.path / name)
        else:
            os.rename(
                name,
                name,
                src_dir_fd=root.directory_fd,
                dst_dir_fd=stage.directory_fd,
            )
    except (FileExistsError, FileNotFoundError, OSError, RuntimeError):
        return


def restore() -> None:
    version, commit, build_id = identity()
    sources = _source_paths(version)
    expected_names = _selected_names(version, sources)
    transfer_path = ROOT / "release-transfer"
    transfer = _open_directory_binding(transfer_path, what="release transfer directory")
    root: Optional[_DirectoryBinding] = None
    stage: Optional[_DirectoryBinding] = None
    published: list[tuple[str, tuple[Any, ...]]] = []
    success = False
    try:
        if _safe_tree_names(transfer) != expected_names | {"transfer-manifest.json"}:
            raise RuntimeError("transfer contains missing or unexpected files")
        manifest_path = transfer_path / "transfer-manifest.json"
        manifest_bytes, manifest_binding = _read_snapshot(
            manifest_path,
            limit=MAX_MANIFEST_BYTES,
            what="transfer manifest",
        )
        expected_sha = os.environ.get("TRANSFER_MANIFEST_SHA256", "")
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        _require_file_binding(manifest_binding)
        if (
            not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
            or manifest_sha != expected_sha
        ):
            raise RuntimeError("transfer manifest differs from qualification job")
        manifest = _parse_manifest(manifest_bytes)
        _validate_manifest(
            manifest,
            version=version,
            commit=commit,
            build_id=build_id,
            expected_names=expected_names,
        )

        transfer_bindings: dict[str, _RegularBinding] = {}
        for name in sorted(expected_names):
            size, digest_value, binding = _snapshot_digest(
                transfer_path / name,
                what=f"transferred file {Path(name).name}",
            )
            if manifest["files"][name] != {
                "bytes": size,
                "sha256": digest_value,
            }:
                raise RuntimeError(f"transfer checksum mismatch: {name}")
            transfer_bindings[name] = binding
        _require_file_binding(manifest_binding)
        _require_bindings(transfer_bindings.values())
        _require_directory_binding(transfer)

        root = _open_directory_binding(ROOT, what="release checkout")
        for output_name in ("dist", "qemu-evidence"):
            _target_absent(root, output_name)
        stage_name = f".release-restore-{uuid.uuid4().hex}"
        stage = _create_directory(
            ROOT / stage_name, mode=0o700, what="release restore staging directory"
        )
        stem = f"beamo-wipe-{version}-amd64"
        compressed_name = f"dist/{stem}.img.gz"
        raw_name = f"dist/{stem}.img"
        staged_names = (expected_names - {compressed_name}) | {raw_name}
        _ensure_parent_directories(stage.path, staged_names)
        staged_bindings: list[_RegularBinding] = []
        for name in sorted(expected_names - {compressed_name}):
            staged_bindings.append(_copy(transfer_bindings[name], stage.path / name))
        raw_info = manifest["raw_image"]
        staged_bindings.append(
            _decompress(
                transfer_bindings[compressed_name],
                stage.path / raw_name,
                expected_size=raw_info["bytes"],
                expected_sha=raw_info["sha256"],
            )
        )
        _require_bindings(transfer_bindings.values())
        _require_bindings(staged_bindings)
        _require_file_binding(manifest_binding)
        _require_directory_binding(transfer)
        _require_directory_binding(stage)
        if _safe_tree_names(stage) != staged_names:
            raise RuntimeError("staged release contains missing or unexpected files")
        for output_name in ("dist", "qemu-evidence"):
            _target_absent(root, output_name)

        for output_name in ("dist", "qemu-evidence"):
            metadata = _rename_directory(stage, root, output_name)
            published.append((output_name, metadata))
            if _directory_metadata(root, output_name) != metadata:
                raise RuntimeError(
                    "published release directory changed during restoration"
                )

        final_bindings: list[_RegularBinding] = []
        for name in sorted(expected_names - {compressed_name}):
            size, digest_value, binding = _snapshot_digest(
                ROOT / name, what=f"restored file {Path(name).name}"
            )
            if manifest["files"][name] != {
                "bytes": size,
                "sha256": digest_value,
            }:
                raise RuntimeError(f"restored release file differs: {name}")
            final_bindings.append(binding)
        raw_size, raw_sha, raw_binding = _snapshot_digest(
            ROOT / raw_name, what="restored USB image"
        )
        if {"bytes": raw_size, "sha256": raw_sha} != raw_info:
            raise RuntimeError("restored USB image differs from qualified bytes")
        final_bindings.append(raw_binding)
        _require_bindings(final_bindings)
        _require_bindings(transfer_bindings.values())
        _require_file_binding(manifest_binding)
        _require_directory_binding(transfer)
        _require_directory_binding(root)
        if stage.directory_fd is None or root.directory_fd is None:
            os.rmdir(stage.path)
        else:
            os.rmdir(stage.path.name, dir_fd=root.directory_fd)
        success = True
    finally:
        if not success and stage is not None:
            for name, metadata in reversed(published):
                if root is not None:
                    _rollback_directory(stage, root, name, metadata)
            _cleanup_owned_directory(stage)
        _close_directory_binding(stage)
        _close_directory_binding(root)
        _close_directory_binding(transfer)


if __name__ == "__main__":
    if sys.argv[1:] == ["pack"]:
        pack()
        if PACKED_MANIFEST_SHA256 is None:
            raise RuntimeError("release transfer manifest digest was not retained")
        print(PACKED_MANIFEST_SHA256)
    elif sys.argv[1:] == ["restore"]:
        restore()
    else:
        raise SystemExit("usage: release_transfer.py {pack|restore}")
