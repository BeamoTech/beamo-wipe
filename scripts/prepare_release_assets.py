#!/usr/bin/env python3
"""Assemble the public download inventory from the signed, tested bytes."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Iterable, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from beamo_wipe.release_manifest import (  # noqa: E402
    _REGULAR_BIND_FIELDS,
    _RegularBinding,
    _binding,
    _hash_regular_snapshot,
    _metadata_values,
    _named_metadata,
    _open_bound_regular,
    _open_pinned_parent,
    _read_regular_snapshot,
    _require_parent_binding,
    _require_regular_binding as _require_regular_binding_raw,
    verify_manifest,
)
from beamo_wipe.release_signing import (  # noqa: E402
    _unique_json_fields,
    _write_new_file,
    detached_verification_metadata,
    load_key_registry,
    sign_manifest_bytes,
    verify_with_registry,
)
from publish_release_gcs import _read_signing_key  # noqa: E402


MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_MARKER_BYTES = 1024 * 1024


class _StageBinding:
    """An owned staging directory retained open for the whole assembly."""

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


def _require_regular_binding(binding: _RegularBinding) -> None:
    try:
        _require_regular_binding_raw(binding)
    except OSError as exc:
        raise RuntimeError(
            f"{binding.path.name} is no longer bound to its release path"
        ) from exc


def _open_stage_binding(stage: Path) -> _StageBinding:
    probe, directory_fd, fields = _open_pinned_parent(
        stage / ".release-assets-stage-binding"
    )
    try:
        metadata = (
            os.fstat(directory_fd)
            if directory_fd is not None
            else os.lstat(probe.parent)
        )
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise RuntimeError("unsafe release staging directory")
        _require_parent_binding(probe, directory_fd, fields)
        return _StageBinding(probe.parent, probe, directory_fd, fields)
    except Exception:
        if directory_fd is not None:
            os.close(directory_fd)
        raise


def _require_stage_binding(stage: _StageBinding) -> None:
    _require_parent_binding(stage.probe, stage.directory_fd, stage.fields)
    metadata = (
        os.fstat(stage.directory_fd)
        if stage.directory_fd is not None
        else os.lstat(stage.path)
    )
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise RuntimeError("release staging directory changed while in use")


def _read_descriptor(fd: int, size: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    remaining = size + 1
    while remaining:
        chunk = os.read(fd, min(1024 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _write_new_stage_file(
    stage: _StageBinding, path: Path, payload: bytes, mode: int
) -> _RegularBinding:
    """Create an output through the retained staging-directory descriptor."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    if absolute.parent != stage.path or not absolute.name:
        raise RuntimeError("release output is outside the bound staging directory")
    _require_stage_binding(stage)
    if stage.directory_fd is None:
        _write_new_file(absolute, payload, mode)
        _require_stage_binding(stage)
        written_bytes, binding = _read_regular_snapshot(
            absolute, limit=len(payload), what="release output"
        )
        if written_bytes != payload:
            raise RuntimeError(f"release output changed while written: {absolute.name}")
        return binding

    flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = None
    try:
        fd = os.open(absolute.name, flags, mode, dir_fd=stage.directory_fd)
        os.fchmod(fd, mode)
        remaining = memoryview(bytes(payload))
        while remaining:
            written_count = os.write(fd, remaining)
            if written_count <= 0:
                raise OSError("short write")
            remaining = remaining[written_count:]
        os.fsync(fd)
        opened = os.fstat(fd)
        named = os.stat(absolute.name, dir_fd=stage.directory_fd, follow_symlinks=False)
        expected = _metadata_values(opened, _REGULAR_BIND_FIELDS)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or _metadata_values(named, _REGULAR_BIND_FIELDS) != expected
            or opened.st_size != len(payload)
            or stat.S_IMODE(opened.st_mode) != mode
            or _read_descriptor(fd, len(payload)) != payload
            or _read_descriptor(fd, len(payload)) != payload
        ):
            raise RuntimeError(f"release output changed while written: {absolute.name}")
        os.fsync(stage.directory_fd)
        _require_stage_binding(stage)
        final = os.fstat(fd)
        current = os.stat(
            absolute.name, dir_fd=stage.directory_fd, follow_symlinks=False
        )
        if (
            _metadata_values(final, _REGULAR_BIND_FIELDS) != expected
            or _metadata_values(current, _REGULAR_BIND_FIELDS) != expected
            or _read_descriptor(fd, len(payload)) != payload
        ):
            raise RuntimeError(f"release output changed while written: {absolute.name}")
        return _binding(absolute, final, stage.fields)
    except FileExistsError:
        raise
    except OSError as exc:
        raise RuntimeError(
            f"release output cannot be safely written: {absolute.name}"
        ) from exc
    finally:
        if fd is not None:
            os.close(fd)


def digest(path: Path) -> str:
    result, _size, binding = _hash_regular_snapshot(path)
    _require_regular_binding(binding)
    return result


def _snapshot_record(path: Path) -> tuple[dict[str, Any], _RegularBinding]:
    result, size, binding = _hash_regular_snapshot(path)
    _require_regular_binding(binding)
    nlink = binding.fields[_REGULAR_BIND_FIELDS.index("st_nlink")]
    if nlink != 1:
        raise RuntimeError(f"release input is not uniquely linked: {path.name}")
    return {"bytes": size, "sha256": result}, binding


def file_record(path: Path) -> dict[str, Any]:
    record, binding = _snapshot_record(path)
    _require_regular_binding(binding)
    return record


def _write_json_snapshot(
    path: Path,
    value: Mapping[str, Any],
    *,
    stage_binding: Optional[_StageBinding] = None,
) -> tuple[bytes, _RegularBinding]:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    created_binding = None
    if stage_binding is None:
        _write_new_file(path, payload, 0o644)
    else:
        created_binding = _write_new_stage_file(stage_binding, path, payload, 0o644)
    try:
        written, binding = _read_regular_snapshot(
            path, limit=len(payload), what="release JSON output"
        )
    except OSError as exc:
        raise RuntimeError(
            f"release JSON output is no longer bound to its path: {path.name}"
        ) from exc
    if written != payload:
        raise RuntimeError(f"release JSON output changed after writing: {path.name}")
    if created_binding is not None and binding != created_binding:
        raise RuntimeError(
            f"release JSON output path changed after writing: {path.name}"
        )
    nlink = binding.fields[_REGULAR_BIND_FIELDS.index("st_nlink")]
    if nlink != 1:
        raise RuntimeError(f"release JSON output is not uniquely linked: {path.name}")
    _require_regular_binding(binding)
    if stage_binding is not None:
        _require_stage_binding(stage_binding)
    return payload, binding


def write_json(path: Path, value: Mapping[str, Any]) -> bytes:
    payload, _binding_value = _write_json_snapshot(path, value)
    return payload


def _parse_json_bytes(data: bytes, *, what: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_json_fields,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError(f"{what} is not JSON") from exc


def _read_json_snapshot(path: Path, *, what: str) -> tuple[Any, _RegularBinding]:
    data, binding = _read_regular_snapshot(path, limit=MAX_JSON_BYTES, what=what)
    return _parse_json_bytes(data, what=what), binding


def _read_text_snapshot(
    path: Path, *, encoding: str, limit: int, what: str
) -> tuple[str, _RegularBinding]:
    data, binding = _read_regular_snapshot(path, limit=limit, what=what)
    try:
        return data.decode(encoding), binding
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{what} is not valid {encoding} text") from exc


def _require_bindings(bindings: Iterable[_RegularBinding]) -> None:
    for binding in bindings:
        _require_regular_binding(binding)


def _gzip_content_digest(
    binding: _RegularBinding, *, expected_size: int
) -> tuple[str, int]:
    """Hash decompressed bytes while keeping the compressed path bound."""
    _require_regular_binding(binding)
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(
        binding.path
    )
    try:
        if _binding(absolute, opened, parent_fields) != binding:
            raise RuntimeError("compressed USB download changed before validation")
        result = hashlib.sha256()
        total = 0
        with os.fdopen(os.dup(fd), "rb") as source:
            with gzip.GzipFile(fileobj=source, mode="rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    total += len(chunk)
                    if total > expected_size:
                        raise RuntimeError(
                            "compressed USB download expands beyond the tested image"
                        )
                    result.update(chunk)
        final = os.fstat(fd)
        named = _named_metadata(absolute, directory_fd)
        _require_parent_binding(absolute, directory_fd, parent_fields)
        if (
            _metadata_values(final, _REGULAR_BIND_FIELDS) != binding.fields
            or _metadata_values(named, _REGULAR_BIND_FIELDS) != binding.fields
        ):
            raise RuntimeError("compressed USB download changed during validation")
        return result.hexdigest(), total
    except (EOFError, gzip.BadGzipFile, OSError) as exc:
        raise RuntimeError("compressed USB download is not a valid gzip file") from exc
    finally:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)
        _require_regular_binding(binding)


def _collect_records(
    paths: Iterable[Path], bindings: list[_RegularBinding]
) -> dict[str, dict[str, Any]]:
    records = {}
    for path in paths:
        if path.name in records:
            raise RuntimeError(f"duplicate release asset name: {path.name}")
        record, binding = _snapshot_record(path)
        records[path.name] = record
        bindings.append(binding)
    return records


def prepare(stage: Path, version: str, build_id: str, commit: str) -> None:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise RuntimeError("invalid release version")
    if not re.fullmatch(
        r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", build_id
    ) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("invalid release source identity")

    stage_binding = _open_stage_binding(stage)
    bindings: list[_RegularBinding] = []
    try:
        stage = stage_binding.path
        stem = f"beamo-wipe-{version}-amd64"
        dist = ROOT / "dist"
        manifest_path = dist / f"{stem}.manifest.json"
        manifest_bytes = verify_manifest(manifest_path)
        manifest_disk, manifest_binding = _read_regular_snapshot(
            manifest_path, limit=MAX_JSON_BYTES, what="release manifest"
        )
        if manifest_disk != manifest_bytes:
            raise RuntimeError("release manifest changed after verification")
        bindings.append(manifest_binding)
        manifest = _parse_json_bytes(manifest_bytes, what="release manifest")
        if not isinstance(manifest, dict):
            raise RuntimeError("release manifest is not an object")
        if (
            manifest["beamo_wipe_version"] != version
            or manifest["source"]["commit"] != commit
            or manifest["build"]["release_build_id"] != build_id
        ):
            raise RuntimeError("release manifest does not match qualified source")

        registry_data, registry_binding = _read_json_snapshot(
            ROOT / "packaging/release-keys/keys.json", what="release key registry"
        )
        bindings.append(registry_binding)
        registry = load_key_registry(registry_data)
        signature, signature_binding = _read_json_snapshot(
            dist / f"{stem}.manifest.json.sig", what="release manifest signature"
        )
        bindings.append(signature_binding)
        verify_with_registry(manifest_bytes, signature, registry)

        raw_image = dist / f"{stem}.img"
        raw_record, raw_binding = _snapshot_record(raw_image)
        bindings.append(raw_binding)
        raw_sha = raw_record["sha256"]
        image_meta, image_meta_binding = _read_json_snapshot(
            dist / f"{stem}.img.json", what="USB image metadata"
        )
        bindings.append(image_meta_binding)
        if not isinstance(image_meta, dict):
            raise RuntimeError("USB image metadata is not an object")
        if (
            image_meta.get("sha256") != raw_sha
            or image_meta.get("iso_sha256") != manifest["artifact"]["iso_sha256"]
        ):
            raise RuntimeError("USB image differs from signed ISO provenance")

        # GCS writes this marker only after each immutable object has been read
        # back and checked. Require this exact build and its customer bytes.
        marker_path = stage / "RELEASE_COMPLETE.txt"
        marker_text, marker_text_binding = _read_text_snapshot(
            marker_path,
            encoding="ascii",
            limit=MAX_MARKER_BYTES,
            what="remote completion marker",
        )
        bindings.append(marker_text_binding)
        marker = marker_text.splitlines()
        if marker[:4] != [
            "release_complete=true",
            f"build_id={build_id}",
            f"version={version}",
            f"source_commit={commit}",
        ]:
            raise RuntimeError("remote completion marker has the wrong identity")
        remote = {}
        for line in marker[4:]:
            match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
            if not match or match[2] in remote:
                raise RuntimeError("malformed remote completion marker")
            remote[match[2]] = match[1]
        remote_paths = (
            dist / f"{stem}.iso",
            raw_image,
            manifest_path,
            dist / f"{stem}.manifest.json.sig",
        )
        for path in remote_paths:
            record, binding = _snapshot_record(path)
            bindings.append(binding)
            if remote.get(path.name) != record["sha256"]:
                raise RuntimeError(f"remote release does not match {path.name}")

        compressed = stage / f"{stem}.img.gz"
        compressed_record, compressed_binding = _snapshot_record(compressed)
        bindings.append(compressed_binding)
        decompressed_sha, decompressed_size = _gzip_content_digest(
            compressed_binding, expected_size=raw_record["bytes"]
        )
        if decompressed_sha != raw_sha or decompressed_size != raw_record["bytes"]:
            raise RuntimeError("compressed USB download differs from tested image")
        sidecar_path = stage / f"{stem}.img.gz.sha256"
        sidecar, sidecar_binding = _read_text_snapshot(
            sidecar_path,
            encoding="ascii",
            limit=MAX_MARKER_BYTES,
            what="compressed USB checksum sidecar",
        )
        bindings.append(sidecar_binding)
        if sidecar != f"{compressed_record['sha256']}  {compressed.name}\n":
            raise RuntimeError("compressed USB checksum sidecar differs")

        public = [
            dist / f"{stem}.iso",
            dist / f"{stem}.iso.sha256",
            dist / f"{stem}.img.sha256",
            dist / f"{stem}.img.json",
            manifest_path,
            dist / f"{stem}.manifest.json.sha256",
            dist / f"{stem}.manifest.json.sig",
            dist / "SHA256SUMS",
            ROOT / "packaging/release-keys/keys.json",
            compressed,
            sidecar_path,
            stage / "verification-evidence.tar.gz",
        ]
        public_records = _collect_records(public, bindings)
        expected_manifest_record = {
            "bytes": len(manifest_bytes),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        }
        if public_records[manifest_path.name] != expected_manifest_record:
            raise RuntimeError("public manifest differs from verified manifest bytes")

        marker_record, marker_binding = _snapshot_record(marker_path)
        bindings.append(marker_binding)
        _require_bindings(bindings)
        _require_stage_binding(stage_binding)

        build_receipt = {
            "version": version,
            "source_commit": commit,
            "build_id": build_id,
            "public_release": False,
            "raw_usb_sha256": raw_sha,
            "gates": manifest["test_evidence"]["gates"],
            "artifacts": public_records,
        }
        receipt_path = stage / "BUILD-RECEIPT.json"
        receipt_bytes, receipt_binding = _write_json_snapshot(
            receipt_path, build_receipt, stage_binding=stage_binding
        )
        _require_regular_binding(receipt_binding)
        bindings.append(receipt_binding)
        receipt_record = {
            "bytes": len(receipt_bytes),
            "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        }

        inventory_files = dict(public_records)
        for name, record in (
            (receipt_path.name, receipt_record),
            (raw_image.name, raw_record),
            (marker_path.name, marker_record),
        ):
            if name in inventory_files:
                raise RuntimeError(f"duplicate release asset name: {name}")
            inventory_files[name] = record
        inventory = {
            "schema": "beamo-wipe-release-downloads/1",
            "beamo_wipe_version": version,
            "source_commit": commit,
            "qualified_build_id": build_id,
            "verification": detached_verification_metadata(
                "release-downloads.json", version
            ),
            "files": inventory_files,
        }
        _require_bindings(bindings)
        _require_stage_binding(stage_binding)
        inventory_path = stage / "release-downloads.json"
        inventory_bytes, inventory_binding = _write_json_snapshot(
            inventory_path, inventory, stage_binding=stage_binding
        )
        _require_regular_binding(inventory_binding)
        bindings.append(inventory_binding)
        _require_bindings(bindings)
        _require_stage_binding(stage_binding)

        signed = sign_manifest_bytes(inventory_bytes, _read_signing_key())
        verify_with_registry(inventory_bytes, signed, registry)
        _require_bindings(bindings)
        _require_stage_binding(stage_binding)
        signature_path = stage / "release-downloads.json.sig"
        signature_bytes, signature_output_binding = _write_json_snapshot(
            signature_path, signed, stage_binding=stage_binding
        )
        if (
            _parse_json_bytes(signature_bytes, what="release download signature")
            != signed
        ):
            raise RuntimeError("release download signature changed while written")
        _require_regular_binding(signature_output_binding)
        bindings.append(signature_output_binding)
        _require_bindings(bindings)
        _require_stage_binding(stage_binding)
    finally:
        if stage_binding.directory_fd is not None:
            os.close(stage_binding.directory_fd)


if __name__ == "__main__":
    prepare(
        Path(sys.argv[1]),
        os.environ["BEAMO_WIPE_VERSION"],
        os.environ["BUILD_ID"],
        os.environ["GITHUB_SHA"],
    )
