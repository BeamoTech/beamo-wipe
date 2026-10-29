#!/usr/bin/env python3
"""Explicit, no-overwrite GCS publisher for verified Beamo Wipe releases."""

from __future__ import annotations

import hashlib
import http.client
import io
import json
import os
from contextlib import contextmanager
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, BinaryIO, Iterator, Protocol
from urllib.parse import quote, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "beamo-wipe_cloudbuild"
RELEASE_PREFIX = "releases"
STORAGE_HOST = "storage.googleapis.com"
METADATA_HOST = "metadata.google.internal"
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
BUILD_ID_RE = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
CHUNK_SIZE = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_QEMU_LOG_LINE_BYTES = 1024 * 1024
MAX_KEY_REGISTRY_BYTES = 1024 * 1024
_REGULAR_BIND_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_uid",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)
_PARENT_BIND_FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid")


class PublishError(RuntimeError):
    """A release precondition or authenticated upload failed."""


class _OwnedBinding:
    """Identity of one owned regular file beneath one pinned parent path."""

    __slots__ = ("path", "fields", "parent_fields")

    def __init__(
        self,
        path: Path,
        fields: tuple[Any, ...],
        parent_fields: tuple[Any, ...],
    ) -> None:
        self.path = path
        self.fields = fields
        self.parent_fields = parent_fields

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, _OwnedBinding)
            and self.path == other.path
            and self.fields == other.fields
            and self.parent_fields == other.parent_fields
        )

    @property
    def size(self) -> int:
        return int(self.fields[_REGULAR_BIND_FIELDS.index("st_size")])


class _OwnedSnapshot:
    """Digest and retained identity of bytes accepted for publication."""

    __slots__ = ("binding", "fd", "sha256")

    def __init__(self, binding: _OwnedBinding, sha256: str, fd: int) -> None:
        self.binding = binding
        self.sha256 = sha256
        self.fd = fd

    @property
    def size(self) -> int:
        return self.binding.size

    def close(self) -> None:
        fd, self.fd = self.fd, -1
        if fd >= 0:
            os.close(fd)

    def __del__(self) -> None:
        try:
            self.close()
        except OSError:
            pass


class _ReadableBinary(Protocol):
    def read(self, size: int = -1) -> bytes: ...


def _unique_json_fields(pairs):
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise PublishError(f"duplicate JSON field in release input: {key}")
        fields[key] = value
    return fields


def _response_bytes(response: http.client.HTTPResponse) -> bytes:
    try:
        data = response.read(MAX_RESPONSE_BYTES + 1)
    finally:
        response.close()
    if len(data) > MAX_RESPONSE_BYTES:
        raise PublishError("Google API response exceeded the safety limit")
    return data


def _metadata_token() -> str:
    # GitHub OIDC credentials are written by google-github-actions/auth only
    # after the full release gate. gcloud refreshes short-lived tokens for
    # large uploads; never pass a long-lived service-account key to CI.
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        if (os.environ.get("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE")
                != os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
            raise PublishError("workload identity credentials are not selected by gcloud")
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                check=True, capture_output=True, text=True, timeout=45,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PublishError("workload identity authentication failed") from exc
        token = result.stdout.strip()
        if not isinstance(token, str) or not 20 <= len(token) <= 8192 or any(ch.isspace() for ch in token):
            raise PublishError("workload identity returned an invalid token")
        return token
    connection = http.client.HTTPConnection(METADATA_HOST, timeout=10)
    try:
        try:
            connection.request(
                "GET",
                "/computeMetadata/v1/instance/service-accounts/default/token",
                headers={"Metadata-Flavor": "Google"},
            )
            response = connection.getresponse()
            body = _response_bytes(response)
            if response.status != 200:
                raise PublishError(f"metadata authentication failed with status {response.status}")
        except (OSError, http.client.HTTPException) as exc:
            raise PublishError("metadata authentication transport failed") from exc
    finally:
        connection.close()
    try:
        payload = json.loads(body, object_pairs_hook=_unique_json_fields)
        token = payload["access_token"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PublishError("metadata authentication returned an invalid response") from exc
    if not isinstance(token, str) or not 20 <= len(token) <= 8192 or any(ch.isspace() for ch in token):
        raise PublishError("metadata authentication returned an invalid token")
    return token


def _object_name(build_id: str, filename: str) -> str:
    if not BUILD_ID_RE.fullmatch(build_id):
        raise PublishError("missing or invalid release build ID")
    if not filename or filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise PublishError("invalid release filename")
    return f"{RELEASE_PREFIX}/{build_id}/{filename}"


def _start_resumable_upload(object_name: str, size: int, token: str) -> str:
    if type(size) is not int or size < 0:
        raise PublishError("invalid upload size")
    query = urlencode(
        {
            "uploadType": "resumable",
            "name": object_name,
            "ifGenerationMatch": "0",
        }
    )
    connection = http.client.HTTPSConnection(STORAGE_HOST, timeout=30)
    try:
        try:
            connection.request(
                "POST",
                f"/upload/storage/v1/b/{quote(BUCKET, safe='')}/o?{query}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Length": "0",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Length": str(size),
                    "X-Upload-Content-Type": "application/octet-stream",
                },
            )
            response = connection.getresponse()
            location = response.getheader("Location", "")
            _response_bytes(response)
            if response.status == 412:
                raise PublishError("release object already exists")
            if response.status not in {200, 201}:
                raise PublishError(f"upload initialization failed with status {response.status}")
        except (OSError, http.client.HTTPException) as exc:
            raise PublishError("upload initialization transport failed") from exc
    finally:
        connection.close()
    try:
        parsed = urlsplit(location)
        valid_endpoint = (
            parsed.scheme == "https"
            and parsed.hostname == STORAGE_HOST
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
            and not parsed.fragment
        )
    except ValueError as exc:
        raise PublishError(
            "upload initialization returned an invalid endpoint"
        ) from exc
    if not valid_endpoint:
        raise PublishError("upload initialization returned an invalid endpoint")
    return parsed.path + (f"?{parsed.query}" if parsed.query else "")


def _send_upload(
    location: str, stream: _ReadableBinary, size: int, token: str
) -> None:
    if type(size) is not int or size < 0:
        raise PublishError("invalid upload size")
    connection = http.client.HTTPSConnection(STORAGE_HOST, timeout=120)
    try:
        try:
            connection.putrequest("PUT", location)
            connection.putheader("Authorization", f"Bearer {token}")
            connection.putheader("Content-Length", str(size))
            connection.putheader("Content-Type", "application/octet-stream")
            connection.endheaders()
            remaining = size
            while remaining:
                chunk = stream.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    raise PublishError("release input ended before its declared size")
                connection.send(chunk)
                remaining -= len(chunk)
            if stream.read(1):
                raise PublishError("release input grew during upload")
            response = connection.getresponse()
            _response_bytes(response)
            if response.status not in {200, 201}:
                raise PublishError(f"release upload failed with status {response.status}")
        except (OSError, http.client.HTTPException) as exc:
            # Never include the resumable session URI: it is an upload credential.
            raise PublishError("release upload transport failed") from exc
    finally:
        connection.close()


def _upload_stream(
    object_name: str, stream: _ReadableBinary, size: int
) -> None:
    token = _metadata_token()
    location = _start_resumable_upload(object_name, size, token)
    _send_upload(location, stream, size, token)


class _DigestingReader:
    """Record the exact bytes consumed by the resumable upload."""

    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.digest = hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        chunk = self.stream.read(size)
        self.digest.update(chunk)
        return chunk


def _descriptor_sha256(fd: int, size: int, name: str) -> str:
    """Hash exactly one retained descriptor without changing its offset."""
    digest = hashlib.sha256()
    offset = 0
    while offset < size:
        chunk = os.pread(fd, min(CHUNK_SIZE, size - offset), offset)
        if not chunk:
            raise PublishError(f"release input changed during upload: {name}")
        digest.update(chunk)
        offset += len(chunk)
    if os.pread(fd, 1, size):
        raise PublishError(f"release input changed during upload: {name}")
    return digest.hexdigest()


def _upload_file(
    path: Path, object_name: str, expected: _OwnedSnapshot | None = None
) -> str:
    snapshot = expected if expected is not None else _snapshot_owned_file(path)
    try:
        with _open_owned_descriptor(
            path, expected=snapshot.binding
        ) as (named_fd, _binding):
            retained = os.fstat(snapshot.fd)
            named = os.fstat(named_fd)
            if (
                _metadata_values(retained, _REGULAR_BIND_FIELDS)
                != snapshot.binding.fields
                or retained.st_dev != named.st_dev
                or retained.st_ino != named.st_ino
            ):
                raise PublishError(
                    f"release input changed after verification: {path.name}"
                )
            os.lseek(snapshot.fd, 0, os.SEEK_SET)
            with os.fdopen(os.dup(snapshot.fd), "rb", buffering=0) as stream:
                measured = _DigestingReader(stream)
                _upload_stream(object_name, measured, snapshot.size)
        uploaded_sha = measured.digest.hexdigest()
        final_sha = _descriptor_sha256(snapshot.fd, snapshot.size, path.name)
        if uploaded_sha != snapshot.sha256 or final_sha != snapshot.sha256:
            raise PublishError("release input changed during upload")
        return uploaded_sha
    finally:
        snapshot.close()


def _remote_sha256(object_name: str, *, expected_size: int | None = None) -> str:
    if expected_size is not None and (
        type(expected_size) is not int or expected_size < 0
    ):
        raise PublishError("invalid remote verification size")
    token = _metadata_token()
    encoded_object = quote(object_name, safe="")
    connection = http.client.HTTPSConnection(STORAGE_HOST, timeout=120)
    digest = hashlib.sha256()
    total = 0
    try:
        try:
            connection.request(
                "GET",
                f"/storage/v1/b/{quote(BUCKET, safe='')}/o/{encoded_object}?alt=media",
                headers={"Authorization": f"Bearer {token}"},
            )
            response = connection.getresponse()
            if response.status != 200:
                _response_bytes(response)
                raise PublishError(f"uploaded-byte verification failed with status {response.status}")
            try:
                while True:
                    read_size = CHUNK_SIZE
                    if expected_size is not None:
                        read_size = min(CHUNK_SIZE, expected_size - total + 1)
                    chunk = response.read(read_size)
                    if not chunk:
                        break
                    total += len(chunk)
                    if expected_size is not None and total > expected_size:
                        raise PublishError("remote object size verification failed")
                    digest.update(chunk)
            finally:
                response.close()
        except (OSError, http.client.HTTPException) as exc:
            raise PublishError("uploaded-byte verification transport failed") from exc
    finally:
        connection.close()
    if expected_size is not None and total != expected_size:
        raise PublishError("remote object size verification failed")
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    snapshot = _snapshot_owned_file(path)
    try:
        return snapshot.sha256
    finally:
        snapshot.close()


def _metadata_values(
    metadata: os.stat_result, fields: tuple[str, ...]
) -> tuple[Any, ...]:
    return tuple(getattr(metadata, field) for field in fields)


def _open_owned_parent(
    path: Path,
) -> tuple[Path, int, tuple[Any, ...]]:
    """Pin every release-input parent without following an ancestor link."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    if not absolute.name or absolute.name in {".", ".."}:
        raise PublishError(f"unsafe release directory for {path.name}")
    parts = absolute.parts
    fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in parts[1:-1]:
            next_fd = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            os.close(fd)
            fd = next_fd
        opened = os.fstat(fd)
        if not stat.S_ISDIR(opened.st_mode) or opened.st_uid != os.getuid():
            raise PublishError(f"unsafe release directory for {path.name}")
        return absolute, fd, _metadata_values(opened, _PARENT_BIND_FIELDS)
    except Exception:
        os.close(fd)
        raise


def _require_parent_binding(
    path: Path, retained_fd: int, parent_fields: tuple[Any, ...]
) -> None:
    absolute, current_fd, current_fields = _open_owned_parent(path)
    try:
        if (
            current_fields != parent_fields
            or _metadata_values(os.fstat(retained_fd), _PARENT_BIND_FIELDS)
            != parent_fields
        ):
            raise PublishError(
                f"release directory changed while using {absolute.name}"
            )
    finally:
        os.close(current_fd)


def _named_metadata(path: Path, parent_fd: int) -> os.stat_result:
    return os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)


@contextmanager
def _open_owned_descriptor(
    path: Path, *, expected: _OwnedBinding | None = None
) -> Iterator[tuple[int, _OwnedBinding]]:
    """Open and retain one requested owned, single-link regular inode."""
    try:
        absolute, parent_fd, parent_fields = _open_owned_parent(path)
    except (OSError, PublishError) as exc:
        raise PublishError(f"unsafe release directory for {path.name}") from exc
    fd = -1
    try:
        try:
            fd = os.open(
                absolute.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )
        except OSError as exc:
            raise PublishError(f"unsafe release input: {path.name}") from exc
        opened = os.fstat(fd)
        named = _named_metadata(absolute, parent_fd)
        fields = _metadata_values(opened, _REGULAR_BIND_FIELDS)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or opened.st_nlink != 1
            or fields != _metadata_values(named, _REGULAR_BIND_FIELDS)
        ):
            raise PublishError(f"unsafe release input: {path.name}")
        binding = _OwnedBinding(absolute, fields, parent_fields)
        if expected is not None and binding != expected:
            raise PublishError(
                f"release input changed after verification: {path.name}"
            )
        _require_parent_binding(absolute, parent_fd, parent_fields)
        yield fd, binding
        after = os.fstat(fd)
        named = _named_metadata(absolute, parent_fd)
        _require_parent_binding(absolute, parent_fd, parent_fields)
        if (
            _metadata_values(after, _REGULAR_BIND_FIELDS) != fields
            or _metadata_values(named, _REGULAR_BIND_FIELDS) != fields
        ):
            raise PublishError(f"release input changed while open: {path.name}")
    except PublishError:
        raise
    except OSError as exc:
        raise PublishError(f"release input changed while open: {path.name}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)


@contextmanager
def _open_owned_file(path: Path) -> Iterator[BinaryIO]:
    with _open_owned_descriptor(path) as (fd, _binding):
        with os.fdopen(os.dup(fd), "rb") as stream:
            yield stream


def _regular_owned_file(path: Path) -> _OwnedBinding:
    with _open_owned_descriptor(path) as (_fd, binding):
        return binding


def _snapshot_owned_file(
    path: Path, expected: _OwnedBinding | None = None
) -> _OwnedSnapshot:
    digest = hashlib.sha256()
    total = 0
    retained_fd = -1
    try:
        with _open_owned_descriptor(path, expected=expected) as (fd, binding):
            while True:
                chunk = os.read(fd, CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                digest.update(chunk)
            if total != binding.size:
                raise PublishError(
                    f"release input changed while hashing: {path.name}"
                )
            retained_fd = os.dup(fd)
        return _OwnedSnapshot(binding, digest.hexdigest(), retained_fd)
    except BaseException:
        if retained_fd >= 0:
            os.close(retained_fd)
        raise


def _read_owned_bytes(
    path: Path,
    *,
    limit: int,
    label: str,
    expected: _OwnedBinding | None = None,
) -> tuple[bytes, _OwnedBinding]:
    with _open_owned_descriptor(path, expected=expected) as (fd, binding):
        if binding.size > limit:
            raise PublishError(f"{label} exceeded the safety limit")
        chunks = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(fd, min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > limit:
            raise PublishError(f"{label} exceeded the safety limit")
        if len(raw) != binding.size:
            raise PublishError(f"{label} changed while being read")
        return raw, binding


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublishError("source identity verification failed") from exc
    return result.stdout.strip()


def _verify_source(version: str) -> str:
    if _git("status", "--porcelain"):
        raise PublishError("refusing release publication from a dirty source tree")
    commit = _git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise PublishError("source commit is invalid")
    tags = _git("tag", "--points-at", commit).splitlines()
    if f"v{version}" not in tags:
        raise PublishError(f"release tag v{version} does not point at the source commit")
    return commit


def _verify_sha256sums(dist: Path, version: str) -> None:
    iso_name = f"beamo-wipe-{version}-amd64.iso"
    manifest_name = f"beamo-wipe-{version}-amd64.manifest.json"
    sums_path = dist / "SHA256SUMS"
    try:
        with _open_owned_file(sums_path) as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            raise PublishError("SHA256SUMS exceeded the safety limit")
        lines = raw.decode("ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise PublishError("SHA256SUMS is unreadable") from exc
    expected_names = [iso_name, manifest_name]
    if len(lines) != len(expected_names):
        raise PublishError("SHA256SUMS has an unexpected number of entries")
    for line, name in zip(lines, expected_names, strict=True):
        expected = f"{_sha256(dist / name)}  {name}"
        if line != expected:
            raise PublishError(f"SHA256SUMS mismatch for {name}")


def _verify_usb_image(dist: Path, version: str) -> tuple[str, str]:
    """Bind the desktop-readable image to the verified ISO before uploading."""
    image = dist / f"beamo-wipe-{version}-amd64.img"
    iso = dist / f"beamo-wipe-{version}-amd64.iso"
    try:
        with _open_owned_file(Path(f"{image}.json")) as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            raise PublishError("USB image metadata exceeded the safety limit")
        metadata = json.loads(raw, object_pairs_hook=_unique_json_fields)
        with _open_owned_file(Path(f"{image}.sha256")) as stream:
            sidecar = stream.read(4097).decode("ascii")
        with _open_owned_file(image) as stream:
            size = os.fstat(stream.fileno()).st_size
    except (OSError, UnicodeError, ValueError) as exc:
        raise PublishError("USB image metadata is unreadable") from exc
    image_sha = _sha256(image)
    expected = {
        "schema_version": 1,
        "image": image.name,
        "sha256": image_sha,
        "iso": iso.name,
        "iso_sha256": _sha256(iso),
        "layout": "MBR, one active FAT32 partition at sector 2048",
        "size": size,
    }
    if (
        not isinstance(metadata, dict)
        or metadata != expected
        or type(metadata.get("schema_version")) is not int
        or type(metadata.get("size")) is not int
        or size <= 0
        or sidecar != f"{image_sha}  {image.name}\n"
    ):
        raise PublishError("USB image does not match its ISO, metadata, or checksum")
    return image_sha, hashlib.sha256(raw).hexdigest()


def _qemu_tested_usb_sha(root: Path) -> str:
    """Read the image digest retained in the signed QEMU gate log."""
    log_path = root / "dist" / "evidence" / "qemu.log"
    prefix = b"[qemu-verify] usb_image_sha256="
    found = []
    with _open_owned_file(log_path) as stream:
        while line := stream.readline(MAX_QEMU_LOG_LINE_BYTES + 1):
            if len(line) > MAX_QEMU_LOG_LINE_BYTES:
                raise PublishError("QEMU execution log line exceeded the safety limit")
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                if not re.fullmatch(rb"[0-9a-f]{64}", value):
                    raise PublishError("invalid QEMU-tested USB image digest")
                found.append(value.decode("ascii"))
    if len(found) != 1:
        raise PublishError("missing or ambiguous QEMU-tested USB image digest")
    return found[0]


def _verified_json_input_sha(
    path: Path, expected: object, *, limit: int, label: str
) -> str:
    """Bind a separate JSON evidence file to the signed manifest contents."""
    with _open_owned_file(path) as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise PublishError(f"{label} exceeded the safety limit")
    try:
        actual = json.loads(raw, object_pairs_hook=_unique_json_fields)
        canonical_actual = json.dumps(
            actual, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
        canonical_expected = json.dumps(
            expected, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
        if not isinstance(actual, dict) or canonical_actual != canonical_expected:
            raise PublishError(f"{label} differs from verified manifest")
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise PublishError(f"{label} is unreadable") from exc
    return hashlib.sha256(raw).hexdigest()


def _qemu_evidence_names() -> list[str]:
    """Complete flat output inventory of scripts/qemu-verify.sh."""
    names = [
        "run.txt",
        "untested-physical.txt",
        "qemu-version.txt",
        "source-commit.txt",
        "checksums.txt",
        "isoinfo.txt",
        "iso-extraction.txt",
        "nwipe-version.txt",
        "fixed-vulnerabilities.txt",
        "accessible-runtime.txt",
        "keyboard-layouts.txt",
        "secure-boot-signers.txt",
        "report-image.txt",
        "report-helper-crash.txt",
        "fake-disk-e2e.txt",
        "qemu-img.txt",
        "nwipe-invalid-target.txt",
        "summary.txt",
    ]
    for label in (
        "uefi",
        "bios-usb",
        "uefi-usb",
        "secureboot-usb",
        "bios-speech-usb",
        "uefi-speech-usb",
        "bios-troubleshoot-usb",
        "uefi-troubleshoot-usb",
        "bios-sata-usb",
        "uefi-nvme-usb",
    ):
        names.extend(f"{label}-{suffix}.txt" for suffix in ("serial", "qemu", "cmdline"))
    # SATA (FAT32 report) and NVMe (exFAT report, checked without a worker
    # mount) erase journeys from the writable USB image.
    names.extend(
        f"guest-bios-sata-usb-{suffix}.txt" for suffix in ("readback", "bundle", "fsck", "mount")
    )
    names.extend(f"guest-uefi-nvme-usb-{suffix}.txt" for suffix in ("readback", "bundle", "fsck"))
    for method in ("everyday", "extra", "quick_zero"):
        for case in (method, f"{method}-repeat"):
            names.extend(
                (
                    f"host-{case}.log",
                    f"host-{case}-nwipe.txt",
                    f"bios-{case}-serial.txt",
                    f"bios-{case}-qemu.txt",
                    f"bios-{case}-cmdline.txt",
                    f"guest-{case}-readback.txt",
                    f"guest-{case}-bundle.txt",
                    f"guest-{case}-fsck.txt",
                    f"guest-{case}-mount.txt",
                )
            )
    return names


def _require_complete_qemu_inputs(hashes: dict[str, str], paths: list[Path]) -> None:
    """Do not mark a release complete with omitted or extra QEMU evidence."""
    names = [path.name for path in paths]
    if len(names) != len(set(names)) or set(names) != set(hashes):
        raise PublishError("QEMU evidence inventory differs from release inputs")


def _release_inputs(version: str) -> list[Path]:
    iso = ROOT / "dist" / f"beamo-wipe-{version}-amd64.iso"
    image = ROOT / "dist" / f"beamo-wipe-{version}-amd64.img"
    manifest = ROOT / "dist" / f"beamo-wipe-{version}-amd64.manifest.json"
    return [
        iso,
        Path(f"{iso}.sha256"),
        image,
        Path(f"{image}.sha256"),
        Path(f"{image}.json"),
        manifest,
        Path(f"{manifest}.sha256"),
        Path(f"{manifest}.sig"),
        ROOT / "dist" / "SHA256SUMS",
        *[ROOT / "qemu-evidence" / name for name in _qemu_evidence_names()],
        *[
            ROOT / "dist" / "evidence" / name
            for gate in (
                "lint",
                "tests",
                "preview",
                "desktop-launchers",
                "negative",
                "iso",
                "qemu",
            )
            for name in (f"{gate}.receipt.json", f"{gate}.log")
        ],
        ROOT / "dist" / "evidence" / "packages.json",
    ]


def _read_signing_key() -> bytes:
    """Load the publisher key from the operator-provided file, fail closed.

    The key file arrives only via an operator-invoked release submission
    (Secret Manager); trigger builds never carry it, so its absence here
    refuses publication instead of publishing unsigned.
    """
    key_path = os.environ.get("BEAMO_WIPE_SIGNING_KEY_FILE", "")
    if not key_path:
        raise PublishError("refusing release publication without signing material")
    path = Path(key_path)
    try:
        raw, binding = _read_owned_bytes(
            path, limit=32, label="signing material"
        )
    except PublishError as exc:
        if "exceeded the safety limit" in str(exc):
            raise PublishError("signing material must hold 32 raw bytes") from exc
        raise PublishError("unsafe signing material") from exc
    mode = int(binding.fields[_REGULAR_BIND_FIELDS.index("st_mode")])
    if stat.S_IMODE(mode) not in (0o600, 0o400):
        raise PublishError("signing material must be mode 0600 or 0400")
    if len(raw) != 32:
        raise PublishError("signing material must hold 32 raw bytes")
    return raw


def _sign_release_manifest(
    dist: Path, version: str, *, manifest_bytes: bytes | None = None
) -> tuple[Path, str]:
    """Sign the verified manifest and verify the sidecar before upload."""
    sys.path.insert(0, str(ROOT / "src"))
    from beamo_wipe.release_signing import (  # type: ignore[import-untyped]
        load_key_registry,
        sign_manifest_bytes,
        verify_with_registry,
    )

    manifest = dist / f"beamo-wipe-{version}-amd64.manifest.json"
    if manifest_bytes is None:
        manifest_bytes, _manifest_binding = _read_owned_bytes(
            manifest,
            limit=16 * 1024 * 1024,
            label="manifest",
        )
    if len(manifest_bytes) > 16 * 1024 * 1024:
        raise PublishError("manifest exceeded the safety limit")
    sidecar = sign_manifest_bytes(manifest_bytes, _read_signing_key())
    registry_path = ROOT / "packaging" / "release-keys" / "keys.json"
    try:
        registry_raw, _registry_binding = _read_owned_bytes(
            registry_path,
            limit=MAX_KEY_REGISTRY_BYTES,
            label="publisher key registry",
        )
    except PublishError as exc:
        raise PublishError("publisher key registry is unsafe") from exc
    try:
        registry = load_key_registry(
            json.loads(
                registry_raw,
                object_pairs_hook=_unique_json_fields,
            )
        )
    except (UnicodeError, ValueError) as exc:
        raise PublishError("publisher key registry is unreadable") from exc
    try:
        result = verify_with_registry(manifest_bytes, sidecar, registry)
    except RuntimeError as exc:
        raise PublishError(f"fresh manifest signature rejected: {exc}") from exc
    sig_path = Path(f"{manifest}.sig")
    payload = (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        absolute_sig, parent_fd, parent_fields = _open_owned_parent(sig_path)
    except (OSError, PublishError) as exc:
        raise PublishError("signature sidecar directory is unsafe") from exc
    fd = -1
    owned = None

    def remove_owned_partial() -> None:
        if owned is None:
            return
        try:
            current = os.stat(
                absolute_sig.name, dir_fd=parent_fd, follow_symlinks=False
            )
        except OSError:
            return
        if stat.S_ISREG(current.st_mode) and (
            current.st_dev,
            current.st_ino,
        ) == (owned.st_dev, owned.st_ino):
            try:
                os.unlink(absolute_sig.name, dir_fd=parent_fd)
            except OSError:
                pass

    try:
        try:
            fd = os.open(absolute_sig.name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError as exc:
            raise PublishError("stale signature sidecar already exists") from exc
        except OSError as exc:
            raise PublishError("signature sidecar cannot be written") from exc
        owned = os.fstat(fd)
        try:
            with os.fdopen(fd, "wb", closefd=False) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            remove_owned_partial()
            raise PublishError("signature sidecar cannot be written") from exc
        try:
            final = os.fstat(fd)
            named = _named_metadata(absolute_sig, parent_fd)
            _require_parent_binding(absolute_sig, parent_fd, parent_fields)
            final_fields = _metadata_values(final, _REGULAR_BIND_FIELDS)
            if (
                not stat.S_ISREG(final.st_mode)
                or final.st_uid != os.getuid()
                or final.st_nlink != 1
                or final.st_size != len(payload)
                or final_fields != _metadata_values(named, _REGULAR_BIND_FIELDS)
            ):
                raise PublishError("signature sidecar changed while being written")
            os.fsync(parent_fd)
            _require_parent_binding(absolute_sig, parent_fd, parent_fields)
        except (OSError, PublishError) as exc:
            remove_owned_partial()
            if isinstance(exc, PublishError):
                raise
            raise PublishError("signature sidecar changed while being written") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)
    print(f"Signed manifest with publisher key {result['key_id']}")
    return sig_path, hashlib.sha256(payload).hexdigest()


def publish() -> str | None:
    if os.environ.get("PUBLISH_RELEASE", "false") != "true":
        print("Release publication disabled; verified artifacts remain ephemeral.")
        return None
    if os.environ.get("SKIP_ISO", "false") == "true" or os.environ.get("SKIP_QEMU", "false") == "true":
        raise PublishError("refusing release publication with a skipped ISO or QEMU gate")

    version = os.environ.get("BEAMO_WIPE_VERSION", "0.2.14")
    build_id = os.environ.get("BUILD_ID", "")
    if not VERSION_RE.fullmatch(version):
        raise PublishError("invalid BEAMO_WIPE_VERSION")
    if not BUILD_ID_RE.fullmatch(build_id):
        raise PublishError("missing or invalid release build ID")

    inputs = _release_inputs(version)
    sig_name = f"beamo-wipe-{version}-amd64.manifest.json.sig"
    if (
        len(inputs) != len(set(inputs))
        or len(inputs) != len({path.name for path in inputs})
    ):
        raise PublishError("release inputs contain a duplicate path or object name")
    bindings: dict[Path, _OwnedBinding] = {}
    for path in inputs:
        if path.name == sig_name:
            continue  # created by signing below, after manifest verification
        bindings[path] = _regular_owned_file(path)
    commit = _verify_source(version)

    sys.path.insert(0, str(ROOT / "src"))
    from beamo_wipe.release_manifest import verify_manifest  # type: ignore[import-untyped]
    from beamo_wipe.ci_evidence import (  # type: ignore[import-untyped]
        load_receipts, qemu_evidence_digest, qemu_evidence_hashes,
    )

    manifest_path = ROOT / "dist" / f"beamo-wipe-{version}-amd64.manifest.json"
    validated_manifest = verify_manifest(manifest_path)
    validated_sha = hashlib.sha256(validated_manifest).hexdigest()
    manifest_data = json.loads(
        validated_manifest, object_pairs_hook=_unique_json_fields
    )
    if (manifest_data["source"]["commit"] != commit
            or manifest_data["build"]["release_build_id"] != build_id):
        raise PublishError("manifest does not match the release source and build")
    receipts = {r["gate"]: r for r in load_receipts(ROOT / "dist" / "evidence")}
    if receipts != manifest_data["test_evidence"]["gates"]:
        raise PublishError("execution receipts do not match the verified manifest")
    package_path = ROOT / "dist" / "evidence" / "packages.json"
    package_sha = (
        _verified_json_input_sha(
            package_path, manifest_data.get("installed_packages"),
            limit=32 * 1024 * 1024, label="package inventory",
        )
        if package_path in inputs else None
    )
    receipt_sha = {
        ROOT / "dist" / "evidence" / f"{gate}.receipt.json":
            _verified_json_input_sha(
                ROOT / "dist" / "evidence" / f"{gate}.receipt.json",
                receipt, limit=4 * 1024 * 1024, label="gate receipt",
            )
        for gate, receipt in receipts.items()
        if ROOT / "dist" / "evidence" / f"{gate}.receipt.json" in inputs
    }
    qemu_paths = [path for path in inputs if path.parent == ROOT / "qemu-evidence"]
    qemu_hashes = {}
    if qemu_paths:
        expected_qemu_digest = receipts.get("qemu", {}).get("environment", {}).get(
            "qemu_evidence_sha256"
        )
        if not isinstance(expected_qemu_digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected_qemu_digest
        ):
            raise PublishError("QEMU receipt does not bind its copied evidence")
        try:
            qemu_hashes = qemu_evidence_hashes(ROOT / "qemu-evidence")
        except RuntimeError as exc:
            raise PublishError("QEMU evidence changed after gate") from exc
        if qemu_evidence_digest(qemu_hashes) != expected_qemu_digest:
            raise PublishError("QEMU evidence changed after gate")
        _require_complete_qemu_inputs(qemu_hashes, qemu_paths)
    expected_log_sha = {
        ROOT / "dist" / "evidence" / f"{gate}.log": receipt["log_sha256"]
        for gate, receipt in receipts.items()
        if receipt["status"] != "skip"
    }
    if _sha256(manifest_path) != validated_sha:
        raise PublishError("manifest changed after verification")
    _verify_sha256sums(ROOT / "dist", version)
    tested_usb_sha = _qemu_tested_usb_sha(ROOT)
    verified_usb_sha, metadata_sha = _verify_usb_image(ROOT / "dist", version)
    if verified_usb_sha != tested_usb_sha:
        raise PublishError("USB image differs from QEMU-tested USB image")

    iso_name = f"beamo-wipe-{version}-amd64.iso"
    image_name = f"beamo-wipe-{version}-amd64.img"
    manifest_name = manifest_path.name
    iso_sha = manifest_data["artifact"]["iso_sha256"]
    expected_sidecars = {
        ROOT / "dist" / f"{iso_name}.sha256": f"{iso_sha}  {iso_name}\n".encode("ascii"),
        ROOT / "dist" / f"{image_name}.sha256": f"{tested_usb_sha}  {image_name}\n".encode("ascii"),
        ROOT / "dist" / f"{manifest_name}.sha256": f"{validated_sha}  {manifest_name}\n".encode("ascii"),
        ROOT / "dist" / "SHA256SUMS": (
            f"{iso_sha}  {iso_name}\n{validated_sha}  {manifest_name}\n"
        ).encode("ascii"),
    }
    # Finish all artifact checks before creating the one-use signature file.
    # A failed preflight can then be repaired and retried without stale output.
    signature_path, signature_sha = _sign_release_manifest(
        ROOT / "dist", version, manifest_bytes=validated_manifest
    )
    if signature_path != ROOT / "dist" / sig_name:
        raise PublishError("signature sidecar path changed during signing")
    bindings[signature_path] = _regular_owned_file(signature_path)

    receipt_lines = [
        "release_complete=true",
        f"build_id={build_id}",
        f"version={version}",
        f"source_commit={commit}",
    ]
    for path in inputs:
        object_name = _object_name(build_id, path.name)
        try:
            snapshot = _snapshot_owned_file(path, bindings[path])
        except KeyError as exc:
            raise PublishError(f"release input was not bound: {path.name}") from exc
        except PublishError as exc:
            if path == manifest_path:
                message = "manifest changed after verification"
            elif path.name == iso_name:
                message = "ISO differs from the verified manifest"
            elif path.name == image_name:
                message = "USB image differs from QEMU-tested USB image"
            elif path in expected_log_sha:
                message = "execution log changed after verification"
            elif path in qemu_paths:
                message = "QEMU evidence changed after gate"
            elif path == package_path:
                message = "package inventory changed after verification"
            elif path in receipt_sha:
                message = "gate receipt changed after verification"
            elif path in expected_sidecars:
                message = "checksum sidecar changed after verification"
            elif path == ROOT / "dist" / f"{image_name}.json":
                message = "USB image metadata changed after verification"
            elif path == signature_path:
                message = "signature changed after signing"
            else:
                message = f"release input changed after verification: {path.name}"
            raise PublishError(message) from exc
        local_sha = snapshot.sha256
        if path == manifest_path and local_sha != validated_sha:
            raise PublishError("manifest changed after verification")
        if (
            path.name == f"beamo-wipe-{version}-amd64.iso"
            and local_sha != manifest_data["artifact"]["iso_sha256"]
        ):
            raise PublishError("ISO differs from the verified manifest")
        if path.name == f"beamo-wipe-{version}-amd64.img" and local_sha != tested_usb_sha:
            raise PublishError("USB image differs from QEMU-tested USB image")
        if path in expected_log_sha and local_sha != expected_log_sha[path]:
            raise PublishError("execution log changed after verification")
        if path in qemu_paths and local_sha != qemu_hashes[path.name]:
            raise PublishError("QEMU evidence changed after gate")
        if path == package_path and local_sha != package_sha:
            raise PublishError("package inventory changed after verification")
        if path in receipt_sha and local_sha != receipt_sha[path]:
            raise PublishError("gate receipt changed after verification")
        if path in expected_sidecars and local_sha != hashlib.sha256(expected_sidecars[path]).hexdigest():
            raise PublishError("checksum sidecar changed after verification")
        if path == ROOT / "dist" / f"{image_name}.json" and local_sha != metadata_sha:
            raise PublishError("USB image metadata changed after verification")
        if path == signature_path and local_sha != signature_sha:
            raise PublishError("signature changed after signing")
        if _upload_file(path, object_name, snapshot) != local_sha:
            raise PublishError(f"uploaded byte verification failed for {path.name}")
        if _remote_sha256(object_name, expected_size=snapshot.size) != local_sha:
            raise PublishError(f"uploaded byte verification failed for {path.name}")
        receipt_lines.append(f"{local_sha}  {path.name}")

    receipt = ("\n".join(receipt_lines) + "\n").encode("ascii")
    receipt_object = _object_name(build_id, "RELEASE_COMPLETE.txt")
    _upload_stream(receipt_object, io.BytesIO(receipt), len(receipt))
    if _remote_sha256(
        receipt_object, expected_size=len(receipt)
    ) != hashlib.sha256(receipt).hexdigest():
        raise PublishError("release completion receipt verification failed")

    release_uri = f"gs://{BUCKET}/{RELEASE_PREFIX}/{build_id}/"
    print(f"Published and verified release path: {release_uri}")
    return release_uri


def main() -> int:
    try:
        publish()
    except PublishError as exc:
        print(f"Release publication failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
