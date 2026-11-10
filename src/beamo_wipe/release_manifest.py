# SPDX-License-Identifier: GPL-3.0-or-later
"""Machine-readable release manifest. Fails closed on dirty/placeholder."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from beamo_wipe import NWIPE_PINNED_COMMIT, NWIPE_PINNED_VERSION, __version__
from beamo_wipe.build_identity import BUILD_ID_RE
from beamo_wipe.release_signing import detached_verification_metadata
from beamo_wipe.verification_evidence import (
    build_test_evidence,
    verify_package_inventory,
    verify_release_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 2
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MANIFEST_NAME_TEMPLATE = "beamo-wipe-{version}-amd64.manifest.json"
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
EXPECTED_REMOTE = "https://github.com/BeamoTech/beamo-wipe"
# Measured SHA-256 of the signed, published v0.2.11 ISO. Do not copy-forward.
PRIOR_STABLE = {
    "version": "0.2.11",
    "iso_name": "beamo-wipe-0.2.11-amd64.iso",
    "sha256": "9694068e4d70824b316f12da9bd4c0ee964809d15ce5ad4d406333f710176305",
    "commit": "662cf470f9fcedf710d897591560267575745fea",
}

PLACEHOLDER_RE = re.compile(r"PLACEHOLDER|TODO|XXX|CHANGEME", re.I)

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


@dataclass(frozen=True)
class _RegularBinding:
    """Identity of one regular file and its requested link-free parent path."""

    path: Path
    fields: tuple[Any, ...]
    parent_fields: tuple[Any, ...]


def _run(cmd: List[str], **kw: Any) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, text=True, **kw).strip()  # noqa: S603


def git_commit() -> str:
    try:
        return _run(["git", "rev-parse", "HEAD"])
    except Exception:
        raise RuntimeError("untraceable source state: git rev-parse HEAD failed")


def git_tag_for_commit(commit: str) -> Optional[str]:
    try:
        tags = _run(["git", "tag", "--points-at", commit]).splitlines()
        tags = [t.strip() for t in tags if t.strip()]
        release_tag = f"v{__version__}"
        return release_tag if release_tag in tags else (tags[0] if tags else None)
    except Exception:
        return None


def git_dirty() -> tuple[bool, List[str]]:
    try:
        out = _run(["git", "status", "--porcelain"])
        files = [line for line in out.splitlines() if line.strip()]
        return (len(files) > 0, files)
    except Exception:
        return (True, ["unknown"])


def git_remote_url() -> str:
    try:
        raw = _run(["git", "config", "--get", "remote.origin.url"])
    except Exception:
        raise RuntimeError("untraceable source state: origin URL unavailable")
    # GitHub's organization rename preserves the old URL as a redirect.
    # Accept only these exact identities and record the canonical repository.
    allowed = {
        remote
        for owner in ("BeamoTech", "BeamoINT")
        for remote in (
            f"https://github.com/{owner}/beamo-wipe",
            f"https://github.com/{owner}/beamo-wipe.git",
            f"git@github.com:{owner}/beamo-wipe.git",
            f"ssh://git@github.com/{owner}/beamo-wipe.git",
        )
    }
    if raw not in allowed:
        # Do not echo the raw value: a malformed HTTPS remote can contain a
        # credential in its userinfo or query string.
        raise RuntimeError("untraceable source state: unexpected origin URL")
    return EXPECTED_REMOTE


def _validate_version(version: str) -> str:
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise RuntimeError("invalid Beamo Wipe version")
    return version


def _metadata_values(
    metadata: os.stat_result, fields: tuple[str, ...]
) -> tuple[Any, ...]:
    return tuple(getattr(metadata, field) for field in fields)


def _validate_nonposix_parent(path: Path) -> os.stat_result:
    """Reject links and reparse points in a non-POSIX parent path."""
    current = Path(path.anchor)
    try:
        for component in path.parent.parts[1:]:
            current /= component
            metadata = os.lstat(current)
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if not stat.S_ISDIR(metadata.st_mode) or attributes & reparse:
                raise RuntimeError(f"cannot safely open parent of {path.name}")
        metadata = os.lstat(path.parent)
    except OSError as exc:
        raise RuntimeError(f"cannot safely open parent of {path.name}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError(f"cannot safely open parent of {path.name}")
    return metadata


def _open_pinned_parent(path: Path) -> tuple[Path, Optional[int], tuple[Any, ...]]:
    """Open every parent component without following a link."""
    absolute = Path(os.path.abspath(os.fspath(Path(path))))
    if not absolute.name or absolute.name in {".", ".."}:
        raise RuntimeError("release input has no safe file name")
    if os.name != "posix":
        metadata = _validate_nonposix_parent(absolute)
        return (
            absolute,
            None,
            _metadata_values(metadata, _PARENT_BIND_FIELDS),
        )

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        directory_fd = os.open(os.sep, flags)
    except OSError as exc:
        raise RuntimeError(f"cannot safely open parent of {absolute.name}") from exc
    try:
        for component in absolute.parent.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        metadata = os.fstat(directory_fd)
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"cannot safely open parent of {absolute.name}")
        return (
            absolute,
            directory_fd,
            _metadata_values(metadata, _PARENT_BIND_FIELDS),
        )
    except (OSError, RuntimeError) as exc:
        os.close(directory_fd)
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"cannot safely open parent of {absolute.name}") from exc


def _named_metadata(path: Path, directory_fd: Optional[int]) -> os.stat_result:
    if directory_fd is None:
        return os.lstat(path)
    return os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)


def _require_parent_binding(
    path: Path, directory_fd: Optional[int], parent_fields: tuple[Any, ...]
) -> None:
    """Require the requested parent path to still name the opened directory."""
    _, current_fd, current_fields = _open_pinned_parent(path)
    try:
        if current_fields != parent_fields:
            raise RuntimeError(f"parent of {path.name} changed while being verified")
        if directory_fd is not None and current_fd is not None:
            opened_fields = _metadata_values(
                os.fstat(directory_fd), _PARENT_BIND_FIELDS
            )
            if opened_fields != current_fields:
                raise RuntimeError(
                    f"parent of {path.name} changed while being verified"
                )
    finally:
        if current_fd is not None:
            os.close(current_fd)


def _open_bound_regular(
    path: Path,
) -> tuple[Path, Optional[int], tuple[Any, ...], int, os.stat_result]:
    """Open one regular leaf relative to its pinned, link-free parent."""
    absolute, directory_fd, parent_fields = _open_pinned_parent(path)
    fd = -1
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        if directory_fd is None:
            fd = os.open(absolute, flags)
        else:
            fd = os.open(absolute.name, flags, dir_fd=directory_fd)
        opened = os.fstat(fd)
        named = _named_metadata(absolute, directory_fd)
        if not stat.S_ISREG(opened.st_mode) or _metadata_values(
            opened, _REGULAR_BIND_FIELDS
        ) != _metadata_values(named, _REGULAR_BIND_FIELDS):
            raise RuntimeError(f"cannot safely read {absolute.name}")
        _require_parent_binding(absolute, directory_fd, parent_fields)
        return absolute, directory_fd, parent_fields, fd, opened
    except Exception:
        if fd >= 0:
            os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)
        raise


def _open_regular_nofollow(path: Path) -> int:
    try:
        # A planted FIFO cannot block because _open_bound_regular uses NONBLOCK.
        _absolute, directory_fd, _parent_fields, fd, _opened = _open_bound_regular(path)
        if directory_fd is not None:
            os.close(directory_fd)
        return fd
    except (OSError, RuntimeError) as exc:
        raise RuntimeError(f"cannot safely read {path.name}") from exc


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


def _binding(
    path: Path, opened: os.stat_result, parent_fields: tuple[Any, ...]
) -> _RegularBinding:
    return _RegularBinding(
        path,
        _metadata_values(opened, _REGULAR_BIND_FIELDS),
        parent_fields,
    )


def _read_regular_snapshot(
    path: Path, *, limit: int, what: str
) -> tuple[bytes, _RegularBinding]:
    """Read stable bounded bytes and retain their path identity."""
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(path)
    try:
        if opened.st_size > limit:
            raise RuntimeError(f"{what} exceeds size limit")
        first = _read_descriptor(fd, limit)
        middle = os.fstat(fd)
        second = _read_descriptor(fd, limit)
        final = os.fstat(fd)
        named = _named_metadata(absolute, directory_fd)
        requested = os.lstat(absolute)
        _require_parent_binding(absolute, directory_fd, parent_fields)
        expected = _metadata_values(opened, _REGULAR_BIND_FIELDS)
        if (
            len(first) > limit
            or first != second
            or len(first) != opened.st_size
            or any(
                _metadata_values(item, _REGULAR_BIND_FIELDS) != expected
                for item in (middle, final, named, requested)
            )
        ):
            raise RuntimeError(f"{what} changed while being verified")
        return first, _binding(absolute, opened, parent_fields)
    finally:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _hash_regular_snapshot(path: Path) -> tuple[str, int, _RegularBinding]:
    """Hash one stable regular inode and retain its path identity."""
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(path)
    try:
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        final = os.fstat(fd)
        named = _named_metadata(absolute, directory_fd)
        requested = os.lstat(absolute)
        _require_parent_binding(absolute, directory_fd, parent_fields)
        expected = _metadata_values(opened, _REGULAR_BIND_FIELDS)
        if any(
            _metadata_values(item, _REGULAR_BIND_FIELDS) != expected
            for item in (final, named, requested)
        ):
            raise RuntimeError(f"{absolute.name} changed while it was being verified")
        return (
            digest.hexdigest(),
            int(opened.st_size),
            _binding(absolute, opened, parent_fields),
        )
    finally:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _require_regular_binding(binding: _RegularBinding) -> None:
    """Require a previously verified file and parent to keep their identities."""
    absolute, directory_fd, parent_fields, fd, opened = _open_bound_regular(
        binding.path
    )
    try:
        named = _named_metadata(absolute, directory_fd)
        _require_parent_binding(absolute, directory_fd, parent_fields)
        if (
            parent_fields != binding.parent_fields
            or _metadata_values(opened, _REGULAR_BIND_FIELDS) != binding.fields
            or _metadata_values(named, _REGULAR_BIND_FIELDS) != binding.fields
        ):
            raise RuntimeError(
                f"{absolute.name} changed after its release snapshot was verified"
            )
    finally:
        os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def sha256_file(path: Path) -> str:
    return sha256_file_with_stat(path)[0]


def sha256_file_with_stat(path: Path) -> tuple[str, int]:
    """Hash and size one opened inode, rejecting pathname replacement."""
    digest, size, _snapshot = _hash_regular_snapshot(path)
    return digest, size


def file_sha256_or_none(path: Path) -> Optional[str]:
    try:
        if path.is_file():
            return sha256_file(path)
    except Exception:
        pass
    return None


def _reject_symlinked_input(path: Path) -> None:
    """Reject any linked component of a release input below the checkout."""
    current = ROOT
    for component in path.relative_to(ROOT).parts:
        current = current / component
        if current.is_symlink():
            raise RuntimeError(f"release input contains a symlink: {path.relative_to(ROOT)}")


def live_build_inputs() -> Dict[str, Any]:
    cfg = ROOT / "packaging" / "live" / "config"
    for ancestor in (ROOT / "packaging", ROOT / "packaging" / "live", cfg):
        if ancestor.is_symlink():
            raise RuntimeError("live-build config contains a symlinked parent")
    inputs: Dict[str, Any] = {}
    for rel in [
        "bootstrap",
        "binary",
        "chroot",
        "common",
        "source",
        "apt",
        "archives",
        "binary",
        "bootloaders",
        "debian-installer",
        "hooks",
        "includes.chroot",
        "includes.binary",
        "package-lists/beamo.list.chroot",
        "package-lists/live.list.chroot",
        "hooks/normal/0500-build-nwipe.hook.chroot",
    ]:
        p = cfg
        for component in Path(rel).parts:
            p = p / component
            if p.is_symlink():
                raise RuntimeError(f"live-build input is a symlink: {rel}")
        if p.is_file():
            inputs[rel] = file_sha256_or_none(p)
        elif p.is_dir():
            # hash directory contents
            h = hashlib.sha256()
            for sub in sorted(p.rglob("*")):
                rel2 = str(sub.relative_to(cfg))
                if sub.is_symlink():
                    # Hash the link itself, never a file outside the tree.
                    rel_blob = rel2.encode()
                    target = os.readlink(sub).encode("utf-8", errors="surrogateescape")
                    h.update(f"{len(rel_blob)}:".encode() + rel_blob)
                    h.update(b"S")
                    h.update(f"{len(target)}:".encode() + target)
                elif sub.is_file():
                    rel_blob = rel2.encode()
                    digest = sha256_file(sub).encode()
                    h.update(f"{len(rel_blob)}:".encode() + rel_blob)
                    h.update(b"F")
                    h.update(f"{len(digest)}:".encode() + digest)
            inputs[rel + "/"] = h.hexdigest()
    # Also hash src/beamo_wipe. rglob follows a linked starting directory,
    # even though a later child may itself be a regular file.
    _reject_symlinked_input(ROOT / "src" / "beamo_wipe")
    src_h = hashlib.sha256()
    source_files = []
    for sub in sorted((ROOT / "src" / "beamo_wipe").rglob("*")):
        if sub.is_symlink():
            raise RuntimeError("source tree contains a symlink")
        if not sub.is_file() or "__pycache__" in sub.parts or sub.suffix in {".pyc", ".pyo"}:
            continue
        source_files.append(sub)
        rel_blob = str(sub.relative_to(ROOT)).encode()
        digest = sha256_file(sub).encode()
        src_h.update(f"{len(rel_blob)}:".encode() + rel_blob)
        src_h.update(f"{len(digest)}:".encode() + digest)
    if not source_files:
        raise RuntimeError("missing shipped wrapper source")
    inputs["src/beamo_wipe/"] = src_h.hexdigest()
    _reject_symlinked_input(ROOT / "desktop")
    desktop_h = hashlib.sha256()
    for sub in sorted((ROOT / "desktop").rglob("*")):
        if sub.is_symlink():
            raise RuntimeError("desktop source contains a symlink")
        if sub.is_file():
            rel_blob = str(sub.relative_to(ROOT)).encode()
            desktop_h.update(f"{len(rel_blob)}:".encode() + rel_blob)
            desktop_h.update(sha256_file(sub).encode())
    inputs["desktop/"] = desktop_h.hexdigest()
    for rel in (
        "helper/index.html",
        "helper/fr.html",
        "helper/de.html",
        "helper/es.html",
        "helper/it.html",
        "scripts/build-iso.sh",
        "scripts/build-desktop.sh",
        "scripts/build-usb-image.sh",
        "scripts/ci-desktop.sh",
        "scripts/fetch-ci-go.sh",
        "packaging/live/inside-docker.sh",
    ):
        path = ROOT / rel
        _reject_symlinked_input(path)
        if path.is_file():
            inputs[rel] = sha256_file(path)
    return inputs


def dependency_locks(*, strict: bool = False) -> Dict[str, Any]:
    locks: Dict[str, Any] = {}
    locks["pyproject.toml"] = file_sha256_or_none(ROOT / "pyproject.toml")
    locks["THIRD_PARTY.md"] = file_sha256_or_none(ROOT / "THIRD_PARTY.md")
    locks["NOTICE"] = file_sha256_or_none(ROOT / "NOTICE")
    if strict and any(not digest for digest in locks.values()):
        raise RuntimeError("missing required release dependency input")
    # live-build package lists already in live_build_inputs but duplicate for drift check
    return locks


def build_env() -> Dict[str, Any]:
    env: Dict[str, Any] = {}
    # Container/runner image
    try:
        # The hosted ISO builder uses pinned Debian bookworm
        env["container_image"] = (
            "debian:bookworm@sha256:"
            "6ebd97fa83deb272194a2cf015b3d26a4d538e9ad3a7a79d544c8af5b0a01443"
        )
    except Exception:
        env["container_image"] = "unknown"
    # Runner
    env["runner"] = os.environ.get("BEAMO_CI_RUNNER", os.environ.get("RUNNER_OS", "unknown"))
    env["github_runner_image"] = os.environ.get("ImageOS", "unknown")
    # Build commands
    env["build_commands"] = [
        "./scripts/build-iso.sh",
        "packaging/live/inside-docker.sh lb config && lb build",
    ]
    env["built_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    build_id = os.environ.get("BUILD_ID", "local")
    if not BUILD_ID_RE.fullmatch(build_id):
        raise RuntimeError("invalid release build identity")
    if (
        os.environ.get("PROJECT_ID") == "beamo-wipe"
        and build_id == "local"
        and os.environ.get("ALLOW_DIRTY") != "1"
    ):
        raise RuntimeError("hosted production image requires BUILD_ID")
    env["release_build_id"] = build_id
    return env


def iso_info(version: str = __version__) -> Dict[str, Any]:
    version = _validate_version(version)
    iso_name = f"beamo-wipe-{version}-amd64.iso"
    iso_path = ROOT / "dist" / iso_name
    if not iso_path.is_file():
        raise RuntimeError(f"missing checksum: ISO not found at {iso_path}")
    sha, size = sha256_file_with_stat(iso_path)
    if not sha or size == 0:
        raise RuntimeError("missing checksum")
    # Verify nwipe version inside ISO via hook pins (not by mounting, just pins)
    if NWIPE_PINNED_VERSION != "0.42":
        raise RuntimeError(f"unexpected nwipe version {NWIPE_PINNED_VERSION}, expected 0.42")
    if not re.fullmatch(r"[0-9a-f]{40}", NWIPE_PINNED_COMMIT):
        raise RuntimeError("placeholder provenance: nwipe commit not a 40-hex SHA")
    return {
        "iso_name": iso_name,
        # Public manifests must be relocatable. Record only the canonical bare
        # filename; write/verify resolve it in their trusted release directory.
        "iso_path": iso_name,
        "iso_size_bytes": size,
        "iso_sha256": sha,
        "iso_sha256_sidecar": f"{iso_name}.sha256",
    }


def hardware_limits() -> Dict[str, Any]:
    # From docs/compatibility-matrix.md and docs/claims.md
    return {
        "supported": [
            "x64 PCs (UEFI + Legacy BIOS) via USB-A/C, boot menu F12/Esc/F9",
            "SATA HDD, SATA SSD, NVMe, virtio (QEMU), eMMC (mmcblk0)",
            "Resolutions 800x600–1920x1080 including 1280x720 @72 DPI, keyboard-only",
        ],
        "unsupported": [
            "Apple Silicon, Chromebooks, RAID/dm-raid, network bdevs (nbd/iscsi/fc/nvmeof)",
            "In-OS erase from Windows/macOS; automatic execution on USB insertion",
        ],
        "degraded": [
            "SSD overwrite is controller-dependent (not a lab cert)",
            "800x600 requires scroll, HiDPI 144 un-gated",
            "USB-SATA bridges may present as sata",
            "Secure Boot depends on firmware trust and revocations; signed Debian EFI components are included",
            "Desktop restart requires one exact existing USB boot entry; otherwise use the boot menu",
        ],
    }


def known_issues() -> List[str]:
    return [
        "Physical Windows/Linux desktop-to-USB handoff and hardware Secure Boot acceptance remain required (see docs/desktop-entry-design.md)",
        "QEMU TCG on Apple silicon is slow; use Blacksmith x86_64 KVM (see docs/vm-test.md)",
        "eMMC boot partitions (mmcblk0boot0) hidden; eMMC-only recycle shows single selectable",
    ]


def unmeasured_test_evidence(reason: str) -> Dict[str, Any]:
    """Development-only marker. verify_manifest rejects it: script paths are
    not execution evidence, so a manifest without measured gate receipts can
    never verify as a release."""
    return {
        "schema": "beamo-wipe-test-evidence/1",
        "measured": False,
        "reason": reason,
        "gates": {},
    }


def unmeasured_package_inventory(reason: str) -> Dict[str, Any]:
    """Development-only marker. verify_manifest rejects it."""
    return {
        "schema": "beamo-wipe-package-inventory/1",
        "measured": False,
        "reason": reason,
        "package_count": 0,
        "packages": [],
    }


def generate_manifest(
    version: str = __version__,
    strict: bool = True,
    gate_receipts: Optional[List[Dict[str, Any]]] = None,
    package_inventory: Optional[Dict[str, Any]] = None,
    build_only: bool = False,
) -> Dict[str, Any]:
    version = _validate_version(version)
    commit = git_commit()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("untraceable source state: commit not 40-hex")
    tag = git_tag_for_commit(commit)
    dirty, dirty_files = git_dirty()
    if strict and dirty:
        # File names can themselves contain customer or secret material.
        raise RuntimeError("uncommitted source state")
    # Placeholder check
    for f in [ROOT / "src" / "beamo_wipe" / "__init__.py", ROOT / "packaging" / "live" / "config" / "binary"]:
        if f.is_file():
            txt = f.read_text(encoding="utf-8", errors="replace")
            if PLACEHOLDER_RE.search(txt):
                raise RuntimeError(f"placeholder provenance in {f}")

    iso = iso_info(version)
    # Dependency drift: if pyproject version != wrapper version, fail
    try:
        try:
            import tomllib  # type: ignore[import-not-found, no-redef]
        except ImportError:
            import tomli as tomllib  # type: ignore[import-not-found, no-redef]

        with open(ROOT / "pyproject.toml", "rb") as fh:
            pyproject = tomllib.load(fh)
        py_ver = pyproject.get("project", {}).get("version", "")
        if not py_ver:
            raise RuntimeError("missing project version")
        if py_ver != __version__:
            raise RuntimeError(f"unapproved dependency drift: pyproject version {py_ver} != wrapper {__version__}")
        if strict and version != __version__:
            raise RuntimeError(
                f"artifact version {version} != wrapper {__version__}"
            )
    except RuntimeError:
        raise
    except Exception as exc:
        if strict:
            raise RuntimeError("cannot validate pyproject version") from exc

    manifest: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "beamo_wipe_version": version,
        "source": {
            "commit": commit,
            "tag": tag,
            "dirty": dirty,
            "dirty_count": len(dirty_files),
            "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) if not dirty else "dirty",
            "remote_url": git_remote_url(),
        },
        "build": build_env(),
        "dependencies": dependency_locks(strict=strict),
        "live_build_inputs": live_build_inputs(),
        "nwipe": {
            "version": NWIPE_PINNED_VERSION,
            "commit": NWIPE_PINNED_COMMIT,
            "source": "https://github.com/martijnvanbrummelen/nwipe",
            "pinned_path": "/usr/lib/beamo-wipe/nwipe",
        },
        "artifact": iso,
        "test_evidence": (
            build_test_evidence(gate_receipts)
            if gate_receipts is not None
            else unmeasured_test_evidence(
                "no gate receipts collected"
                if strict
                else "development manifest without gate receipts"
            )
        ),
        "installed_packages": (
            verify_package_inventory(package_inventory)
            if package_inventory is not None
            else unmeasured_package_inventory(
                "no package inventory collected"
                if strict
                else "development manifest without package inventory"
            )
        ),
        "hardware_limits": hardware_limits(),
        "known_issues": known_issues(),
        "license": {
            "wrapper": "GPL-3.0-or-later",
            "nwipe": "GPL-2.0",
            "source": EXPECTED_REMOTE,
            "notice": "NOTICE",
            "third_party": "THIRD_PARTY.md",
        },
        "prior_stable": PRIOR_STABLE,
        "rollback": f"git checkout {PRIOR_STABLE['commit']} or git revert <commit> to prior ISO {PRIOR_STABLE['iso_name']}",
        "verification": {
            **detached_verification_metadata(MANIFEST_NAME_TEMPLATE.format(version=version), version),
            "checksum_instructions": (
                "After verifying the detached signature and comparing artifact hashes "
                "with the authenticated manifest/inventory: "
                f"cd dist && sha256sum -c {iso['iso_name']}.sha256"
            ),
            "artifact_immutability": "verification is ephemeral unless the explicit post-QEMU release gate writes a unique build path",
            "reproducibility": "live-build is not bit-reproducible due to apt timestamps; use SHA256 and source commit for traceability",
        },
    }
    if strict:
        final_commit = git_commit()
        final_dirty, _final_files = git_dirty()
        if final_commit != commit or final_dirty:
            raise RuntimeError("source state changed during manifest generation")
        missing = []
        if gate_receipts is None:
            missing.append("gate receipts (measured gate results)")
        if package_inventory is None:
            missing.append("package inventory (installed image packages)")
        if missing and not build_only:
            raise RuntimeError(f"missing release evidence: {', '.join(missing)}")
    # Top-level checksum (of manifest without itself)
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    manifest["_manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return manifest


_SNAPSHOT_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_uid",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


@dataclass(frozen=True)
class _OutputSnapshot:
    fields: tuple[int, ...]
    contents: bytes | str
    kind: str = "regular"


def _stat_fields(value: os.stat_result) -> tuple[int, ...]:
    return tuple(int(getattr(value, field)) for field in _SNAPSHOT_FIELDS)


def _regular_fd_snapshot(fd: int, limit: int) -> _OutputSnapshot:
    """Read one pinned descriptor twice and bind it to complete metadata."""
    opened = os.fstat(fd)

    def read_once() -> bytes:
        contents = bytearray()
        while len(contents) <= limit:
            chunk = os.pread(
                fd, min(65536, limit + 1 - len(contents)), len(contents)
            )
            if not chunk:
                break
            contents.extend(chunk)
        return bytes(contents)

    first = read_once()
    middle = os.fstat(fd)
    second = read_once()
    finished = os.fstat(fd)
    snapshots = (opened, middle, finished)
    if (
        len(first) > limit
        or first != second
        or len(first) != opened.st_size
        or any(not stat.S_ISREG(item.st_mode) for item in snapshots)
        or any(item.st_uid != os.getuid() for item in snapshots)
        or any(_stat_fields(item) != _stat_fields(opened) for item in snapshots)
    ):
        raise RuntimeError("unverified prior manifest output")
    return _OutputSnapshot(_stat_fields(opened), first)


def _regular_output_snapshot(path: Path, limit: int) -> _OutputSnapshot | None:
    """Bind a bounded read to one unchanged, named regular file."""
    path = Path(path)
    try:
        named_before = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(named_before.st_mode) or named_before.st_uid != os.getuid():
        raise RuntimeError("unverified prior manifest output")
    fd = -1
    try:
        fd = _open_regular_nofollow(path)
        pinned = _regular_fd_snapshot(fd, limit)
        named_after = path.lstat()
        confirmed = _regular_fd_snapshot(fd, limit)
    except OSError as exc:
        raise RuntimeError("unverified prior manifest output") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    if (
        not stat.S_ISREG(named_after.st_mode)
        or named_after.st_uid != os.getuid()
        or _stat_fields(named_before) != pinned.fields
        or _stat_fields(named_after) != pinned.fields
        or confirmed != pinned
    ):
        raise RuntimeError("unverified prior manifest output")
    return pinned


def _regular_snapshot_bytes(snapshot: _OutputSnapshot) -> bytes:
    """Return bytes only for a snapshot created from a regular file."""
    if snapshot.kind != "regular" or not isinstance(snapshot.contents, bytes):
        raise RuntimeError("unverified prior manifest output")
    return snapshot.contents


def _path_snapshot(
    path: Path, limit: int, *, allow_symlink: bool = False
) -> _OutputSnapshot | None:
    """Snapshot a replaceable output; links are allowed only for generic replacement."""
    path = Path(path)
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISREG(before.st_mode):
        return _regular_output_snapshot(path, limit)
    if allow_symlink and stat.S_ISLNK(before.st_mode) and before.st_uid == os.getuid():
        target = os.readlink(path)
        after = path.lstat()
        if _stat_fields(before) != _stat_fields(after):
            raise RuntimeError("unverified prior manifest output")
        return _OutputSnapshot(_stat_fields(before), target, "symlink")
    raise RuntimeError("unverified prior manifest output")


def _snapshot_matches(
    path: Path,
    expected: _OutputSnapshot,
    *,
    allow_changed_ctime: bool = False,
) -> bool:
    try:
        current = _path_snapshot(
            path,
            len(expected.contents) if isinstance(expected.contents, bytes) else 0,
            allow_symlink=expected.kind == "symlink",
        )
    except (OSError, RuntimeError):
        return False
    if current is None or current.kind != expected.kind or current.contents != expected.contents:
        return False
    for index, (actual, wanted) in enumerate(zip(current.fields, expected.fields)):
        if index == 7 and allow_changed_ctime:
            continue
        if actual != wanted:
            return False
    return True


_CAPTURE_CURRENT = object()
_RENAME_NOREPLACE = 1
_RENAME_EXCHANGE = 2


def _renameat2(
    source_dirfd: int,
    source: str,
    destination_dirfd: int,
    destination: str,
    flags: int,
) -> None:
    """Call Linux renameat2; release publication has no safe emulation."""
    import ctypes
    import sys

    if not sys.platform.startswith("linux"):
        raise RuntimeError("atomic release publication requires Linux renameat2")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise RuntimeError("atomic release publication requires Linux renameat2")
    rename.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    rename.restype = ctypes.c_int
    result = rename(
        source_dirfd,
        os.fsencode(source),
        destination_dirfd,
        os.fsencode(destination),
        flags,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _snapshot_digest(snapshot: _OutputSnapshot | None) -> str:
    if snapshot is None:
        return "absent"
    contents = snapshot.contents
    if isinstance(contents, str):
        raw = contents.encode("utf-8", errors="surrogateescape")
    else:
        raw = contents
    return hashlib.sha256(raw).hexdigest()


def _atomic_write(
    path: Path,
    blob: bytes,
    *,
    expected: _OutputSnapshot | None | object = _CAPTURE_CURRENT,
) -> None:
    """Publish bytes atomically while retaining every displaced pathname."""
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    if expected is _CAPTURE_CURRENT:
        expected = _path_snapshot(
            path, max(MAX_MANIFEST_BYTES, len(blob)), allow_symlink=True
        )
    if isinstance(expected, _OutputSnapshot) and expected.contents == blob:
        if not _snapshot_matches(path, expected):
            raise RuntimeError("manifest output changed before publication")
        existing_dirfd = os.open(
            str(directory), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        try:
            os.fsync(existing_dirfd)
        finally:
            os.close(existing_dirfd)
        if not _snapshot_matches(path, expected):
            raise RuntimeError("manifest output changed during finalization")
        return
    dirfd = os.open(str(directory), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    name = path.name
    suffix = secrets.token_hex(16)
    new_digest = hashlib.sha256(blob).hexdigest()
    prior_digest = _snapshot_digest(
        expected if isinstance(expected, _OutputSnapshot) else None
    )
    tmp_name = (
        f".{name}.publish.{new_digest}.retired-{prior_digest}.{suffix}"
    )
    tmp_path = directory / tmp_name
    fd = -1
    staged: _OutputSnapshot | None = None

    try:
        fd = os.open(
            tmp_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=dirfd,
        )
        view = memoryview(blob)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short manifest write")
            view = view[written:]
        os.fsync(fd)
        pinned_stage = _regular_fd_snapshot(fd, len(blob))
        if (
            pinned_stage.contents != blob
            or pinned_stage.fields[4] != 1
            or stat.S_IMODE(pinned_stage.fields[2]) != 0o600
        ):
            raise RuntimeError("manifest staging changed")
        staged = pinned_stage
        if not _snapshot_matches(tmp_path, staged):
            raise RuntimeError("manifest staging changed")

        if isinstance(expected, _OutputSnapshot):
            _renameat2(dirfd, tmp_name, dirfd, name, _RENAME_EXCHANGE)
        else:
            _renameat2(dirfd, tmp_name, dirfd, name, _RENAME_NOREPLACE)

        published_matches = _snapshot_matches(
            path, staged, allow_changed_ctime=True
        )
        displaced: _OutputSnapshot | None = None
        if isinstance(expected, _OutputSnapshot):
            try:
                displaced = _path_snapshot(
                    tmp_path,
                    max(MAX_MANIFEST_BYTES, len(expected.contents)),
                    allow_symlink=True,
                )
            except RuntimeError:
                pass
        displaced_matches = not isinstance(
            expected, _OutputSnapshot
        ) or _snapshot_matches(tmp_path, expected, allow_changed_ctime=True)
        if isinstance(expected, _OutputSnapshot) and not displaced_matches:
            if published_matches:
                # The entry at the final name changed after preflight but
                # before EXCHANGE. Swap it back atomically: the foreign entry
                # keeps its pathname and our intended bytes stay retained at
                # the cryptographically identified staging name.
                _renameat2(dirfd, tmp_name, dirfd, name, _RENAME_EXCHANGE)
                os.fsync(dirfd)
                if displaced is not None and not _snapshot_matches(
                    path, displaced, allow_changed_ctime=True
                ):
                    raise RuntimeError(
                        f"manifest output changed; entries retained at {path} and {tmp_path}"
                    )
                if not _snapshot_matches(
                    tmp_path, staged, allow_changed_ctime=True
                ):
                    raise RuntimeError(
                        f"manifest output changed; entries retained at {path} and {tmp_path}"
                    )
            raise RuntimeError(
                f"manifest output changed; intended bytes retained at {tmp_path}"
            )
        if not published_matches:
            raise RuntimeError("manifest publication changed")
        os.fsync(dirfd)
        if not _snapshot_matches(path, staged, allow_changed_ctime=True):
            raise RuntimeError("manifest publication changed")
        if isinstance(expected, _OutputSnapshot) and not _snapshot_matches(
            tmp_path, expected, allow_changed_ctime=True
        ):
            raise RuntimeError(
                f"displaced manifest output changed; retained at {tmp_path}"
            )
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(dirfd)


def _sidecar_blob(sha: str, name: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", sha) or not name or name != os.path.basename(name):
        raise RuntimeError("invalid checksum sidecar fields")
    return f"{sha}  {name}\n".encode("ascii")


def _prior_output_bytes(path: Path, limit: int) -> bytes | None:
    """Read an existing output without treating a link or partial file as ours."""
    snapshot = _regular_output_snapshot(path, limit)
    return None if snapshot is None else _regular_snapshot_bytes(snapshot)


def _require_replaceable_manifest_outputs(
    dest: Path,
    iso_path: Path,
    iso_name: str,
    iso_sha: str,
    manifest_blob: bytes,
) -> dict[Path, _OutputSnapshot | None]:
    """Preserve unfamiliar files before publishing any release output."""
    try:
        dest = Path(dest)
        manifest_sidecar = Path(str(dest) + ".sha256")
        iso_sidecar = Path(str(iso_path) + ".sha256")
        intended_manifest_sidecar = _sidecar_blob(
            hashlib.sha256(manifest_blob).hexdigest(), dest.name
        )
        intended_iso_sidecar = _sidecar_blob(iso_sha, iso_name)
        snapshots = {
            dest: _regular_output_snapshot(dest, MAX_MANIFEST_BYTES),
            manifest_sidecar: _regular_output_snapshot(manifest_sidecar, 512),
            iso_sidecar: _regular_output_snapshot(iso_sidecar, 512),
        }
        prior_snapshot = snapshots[dest]
        sidecar_snapshot = snapshots[manifest_sidecar]
        prior = (
            None
            if prior_snapshot is None
            else _regular_snapshot_bytes(prior_snapshot)
        )
        prior_sidecar = (
            None
            if sidecar_snapshot is None
            else _regular_snapshot_bytes(sidecar_snapshot)
        )
        prior_is_intended = prior == manifest_blob
        prior_is_verified = False
        if prior is not None and not prior_is_intended:
            data = json.loads(prior, object_pairs_hook=_unique_manifest_fields)
            if not isinstance(data, dict):
                raise RuntimeError("invalid prior manifest")
            recorded = data.pop("_manifest_sha256", None)
            canonical = json.dumps(
                data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            artifact = data.get("artifact")
            version = iso_name.removeprefix("beamo-wipe-").removesuffix("-amd64.iso")
            if (
                recorded != hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                or data.get("schema_version") != SCHEMA_VERSION
                or data.get("beamo_wipe_version") != version
                or not isinstance(artifact, dict)
                or artifact.get("iso_name") != iso_name
                or artifact.get("iso_path") != iso_name
                or artifact.get("iso_sha256") != iso_sha
            ):
                raise RuntimeError("prior manifest does not match this ISO")
            prior_is_verified = True

        if prior is None:
            if prior_sidecar not in (None, intended_manifest_sidecar):
                raise RuntimeError("incomplete prior manifest bundle")
        elif prior_is_intended:
            if prior_sidecar not in (None, intended_manifest_sidecar):
                raise RuntimeError("incomplete prior manifest bundle")
        elif prior_is_verified:
            verified_prior_sidecar = _sidecar_blob(
                hashlib.sha256(prior).hexdigest(), dest.name
            )
            if prior_sidecar not in (
                verified_prior_sidecar,
                intended_manifest_sidecar,
            ):
                raise RuntimeError("incomplete prior manifest bundle")

        iso_sidecar_snapshot = snapshots[iso_sidecar]
        iso_sidecar_blob = (
            None
            if iso_sidecar_snapshot is None
            else _regular_snapshot_bytes(iso_sidecar_snapshot)
        )
        if iso_sidecar_blob not in (None, intended_iso_sidecar):
            raise RuntimeError("prior ISO checksum does not match this ISO")
        return snapshots
    except (OSError, ValueError, TypeError, UnicodeError, RuntimeError) as exc:
        raise RuntimeError("unverified prior manifest output") from exc


def require_verified_prior_checksum_list(dist: Path, *, replace_link: bool = False) -> None:
    """Preserve an unfamiliar SHA256SUMS before regenerating a release bundle."""
    dist = Path(dist)
    try:
        # The finalizer publishes with os.replace, so a planted link can be
        # replaced safely without reading or writing its destination.
        if replace_link and (dist / "SHA256SUMS").is_symlink():
            return
        raw = _prior_output_bytes(dist / "SHA256SUMS", 1024)
        if raw is None:
            return
        lines = raw.decode("ascii").splitlines(keepends=True)
        if len(lines) != 2:
            raise ValueError("unexpected checksum entries")
        first = re.fullmatch(
            r"([0-9a-f]{64})  (beamo-wipe-([0-9]+\.[0-9]+\.[0-9]+)-amd64\.iso)\n",
            lines[0],
        )
        if first is None:
            raise ValueError("invalid ISO checksum entry")
        iso_sha, iso_name, version = first.groups()
        manifest_name = MANIFEST_NAME_TEMPLATE.format(version=version)
        second = re.fullmatch(
            rf"([0-9a-f]{{64}})  {re.escape(manifest_name)}\n", lines[1]
        )
        if second is None:
            raise ValueError("invalid manifest checksum entry")
        manifest_sha = second.group(1)
        actual_iso_sha, iso_size = sha256_file_with_stat(dist / iso_name)
        manifest_raw = _prior_output_bytes(dist / manifest_name, MAX_MANIFEST_BYTES)
        if manifest_raw is None:
            raise ValueError("missing prior manifest")
        data = json.loads(manifest_raw, object_pairs_hook=_unique_manifest_fields)
        if not isinstance(data, dict):
            raise ValueError("invalid prior manifest")
        internal_sha = data.pop("_manifest_sha256", None)
        canonical = json.dumps(
            data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        artifact = data.get("artifact")
        schema = data.get("schema_version")
        old_schema = (
            type(schema) is int
            and schema == 1
            and tuple(map(int, version.split(".")))
            < tuple(map(int, __version__.split(".")))
        )
        recorded_path = artifact.get("iso_path") if isinstance(artifact, dict) else None
        path_matches = (
            recorded_path == iso_name
            if type(schema) is int and schema == SCHEMA_VERSION
            else old_schema
            and isinstance(recorded_path, str)
            and recorded_path.rsplit("/", 1)[-1] == iso_name
        )
        if (
            actual_iso_sha != iso_sha
            or hashlib.sha256(manifest_raw).hexdigest() != manifest_sha
            or internal_sha != hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            or not ((type(schema) is int and schema == SCHEMA_VERSION) or old_schema)
            or data.get("beamo_wipe_version") != version
            or not isinstance(artifact, dict)
            or artifact.get("iso_name") != iso_name
            or not path_matches
            or artifact.get("iso_sha256") != iso_sha
            or type(artifact.get("iso_size_bytes")) is not int
            or artifact["iso_size_bytes"] != iso_size
            or _prior_output_bytes(dist / f"{iso_name}.sha256", 512)
            != _sidecar_blob(iso_sha, iso_name)
            or _prior_output_bytes(dist / f"{manifest_name}.sha256", 512)
            != _sidecar_blob(manifest_sha, manifest_name)
        ):
            raise ValueError("prior bundle does not match its checksums")
    except (OSError, ValueError, TypeError, UnicodeError, RuntimeError) as exc:
        raise RuntimeError("unverified prior checksum list") from exc


def write_manifest(manifest: Dict[str, Any], dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    artifact = manifest.get("artifact", {})
    iso_name = str(artifact.get("iso_name", ""))
    if not re.fullmatch(r"beamo-wipe-[0-9]+\.[0-9]+\.[0-9]+-amd64\.iso", iso_name):
        raise RuntimeError("invalid ISO artifact name")
    if artifact.get("iso_path") != iso_name:
        raise RuntimeError("ISO path escapes the release directory")
    iso_path = ROOT / "dist" / iso_name
    try:
        if iso_path.resolve(strict=True) != (ROOT / "dist" / iso_name).resolve(strict=True):
            raise RuntimeError("ISO path escapes the release directory")
    except OSError as exc:
        raise RuntimeError("ISO referenced by manifest is missing") from exc
    recorded_iso_sha = str(artifact.get("iso_sha256", ""))
    if sha256_file(iso_path) != recorded_iso_sha:
        raise RuntimeError("ISO checksum mismatch")
    blob = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    sidecar = Path(str(dest) + ".sha256")
    iso_sidecar = iso_path.parent / f"{iso_name}.sha256"
    manifest_sidecar_blob = _sidecar_blob(hashlib.sha256(blob).hexdigest(), dest.name)
    iso_sidecar_blob = _sidecar_blob(recorded_iso_sha, iso_name)
    expected = _require_replaceable_manifest_outputs(
        dest, iso_path, iso_name, recorded_iso_sha, blob
    )
    # Publish the checksum entries first.  If a later write is interrupted,
    # every visible new byte is the exact intended retry input; the manifest
    # itself is the final commit point.
    _atomic_write(
        iso_sidecar,
        iso_sidecar_blob,
        expected=expected[iso_sidecar],
    )
    _atomic_write(sidecar, manifest_sidecar_blob, expected=expected[sidecar])
    _atomic_write(dest, blob, expected=expected[dest])
    return dest


def verify_manifest(path: Path, allow_dirty: bool = False) -> bytes:
    """Verify measured gates and return the exact accepted manifest bytes."""
    return _verify_manifest(path, allow_dirty=allow_dirty, require_evidence=True)


def verify_build_manifest(path: Path, allow_dirty: bool = False) -> bytes:
    """Return exact verified pre-QEMU bytes; never sufficient for publication."""
    return _verify_manifest(path, allow_dirty=allow_dirty, require_evidence=False)


def _unique_manifest_fields(pairs):
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise RuntimeError("duplicate JSON field in manifest")
        fields[key] = value
    return fields


def _verify_manifest(path: Path, *, allow_dirty: bool, require_evidence: bool) -> bytes:
    path = Path(path)
    raw_bytes, manifest_binding = _read_regular_snapshot(
        path, limit=MAX_MANIFEST_BYTES, what="release manifest"
    )
    try:
        raw_manifest = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("release manifest is not UTF-8") from exc
    data = json.loads(raw_manifest, object_pairs_hook=_unique_manifest_fields)
    if not isinstance(data, dict):
        raise RuntimeError("invalid release manifest root")
    # Recompute checksum (exclude sidecar)
    expected = data.pop("_manifest_sha256", None)
    if expected is None:
        raise RuntimeError("missing checksum: manifest has no _manifest_sha256")
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    got = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if expected != got:
        raise RuntimeError(f"manifest checksum mismatch: expected {expected}, got {got}")
    for field in ("source", "build", "nwipe", "artifact"):
        if not isinstance(data.get(field), dict):
            raise RuntimeError(f"invalid release manifest {field}")
    source = data["source"]
    nwipe = data["nwipe"]
    artifact = data["artifact"]
    if type(source.get("dirty")) is not bool or not isinstance(source.get("commit"), str):
        raise RuntimeError("invalid release manifest source")
    if not isinstance(nwipe.get("commit"), str):
        raise RuntimeError("invalid release manifest nwipe")
    if type(artifact.get("iso_size_bytes")) is not int or artifact["iso_size_bytes"] <= 0:
        raise RuntimeError("invalid release manifest artifact")
    # Placeholder check
    blob = json.dumps(data)
    if PLACEHOLDER_RE.search(blob):
        raise RuntimeError("placeholder provenance in manifest")
    # Dirty check (skipped only for explicit local-dev ALLOW_DIRTY runs; every
    # other structural check still applies)
    if not allow_dirty and data.get("source", {}).get("dirty"):
        raise RuntimeError("uncommitted source state")
    # Missing checksum
    if not data.get("artifact", {}).get("iso_sha256"):
        raise RuntimeError("missing checksum")
    # Unexpected nwipe version
    if data.get("nwipe", {}).get("version") != "0.42":
        raise RuntimeError(f"unexpected nwipe version {data['nwipe']['version']}")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("nwipe", {}).get("commit", "")):
        raise RuntimeError("placeholder nwipe commit")
    if require_evidence and (
        nwipe.get("commit") != NWIPE_PINNED_COMMIT
        or nwipe.get("pinned_path") != "/usr/lib/beamo-wipe/nwipe"
    ):
        raise RuntimeError("release manifest nwipe pin differs from the shipped engine")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("unsupported release manifest schema")
    build_id = data.get("build", {}).get("release_build_id", "")
    if not isinstance(build_id, str) or not BUILD_ID_RE.fullmatch(build_id):
        raise RuntimeError("missing release build identity")
    if not re.fullmatch(r"[0-9a-f]{40}", str(data.get("source", {}).get("commit", ""))):
        raise RuntimeError("untraceable source state: commit not 40-hex")
    if require_evidence:
        # Measured release evidence: script paths are not execution evidence, so
        # a manifest without verified gate receipts and package inventory fails.
        evidence = data.get("test_evidence")
        if not isinstance(evidence, dict) or evidence.get("measured") is not True:
            raise RuntimeError("missing measured gate evidence")
        verified_gates = verify_release_evidence(evidence)
        manifest_commit = str(data.get("source", {}).get("commit", ""))
        manifest_build = str(data.get("build", {}).get("release_build_id", ""))
        for gate_name, receipt in verified_gates.items():
            if receipt["source_commit"] != manifest_commit:
                raise RuntimeError(
                    f"gate {gate_name!r} evidence is for another source commit"
                )
            if receipt["build_id"] != manifest_build:
                raise RuntimeError(
                    f"gate {gate_name!r} evidence is for another build identity"
                )
        inventory = data.get("installed_packages")
        if not isinstance(inventory, dict) or inventory.get("measured") is not True:
            raise RuntimeError("missing measured package inventory")
        verified_inventory = verify_package_inventory(inventory)
        if verified_inventory["source_commit"] != manifest_commit:
            raise RuntimeError("package inventory is for another source commit")
    artifact = data.get("artifact", {})
    version = _validate_version(data.get("beamo_wipe_version", ""))
    iso_name = f"beamo-wipe-{version}-amd64.iso"
    if artifact.get("iso_name") != iso_name:
        raise RuntimeError("unexpected ISO name in manifest")
    if artifact.get("iso_path") != iso_name:
        raise RuntimeError("ISO path escapes the release directory")
    iso_path = path.parent / iso_name
    recorded_iso_sha = str(artifact.get("iso_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", recorded_iso_sha):
        raise RuntimeError("missing checksum")
    try:
        actual_sha, actual_size, iso_binding = _hash_regular_snapshot(iso_path)
        if actual_sha != recorded_iso_sha:
            raise RuntimeError("ISO checksum mismatch")
        if actual_size != artifact["iso_size_bytes"]:
            raise RuntimeError("ISO size mismatch")
    except OSError as exc:
        raise RuntimeError("ISO referenced by manifest is missing") from exc
    iso_sidecar_binding = _verify_sidecar(
        Path(str(iso_path) + ".sha256"), recorded_iso_sha, iso_name
    )
    manifest_sidecar_binding = _verify_sidecar(
        Path(str(path) + ".sha256"),
        hashlib.sha256(raw_manifest.encode("utf-8")).hexdigest(),
        path.name,
    )
    for binding in (
        manifest_binding,
        iso_binding,
        iso_sidecar_binding,
        manifest_sidecar_binding,
    ):
        _require_regular_binding(binding)
    return raw_bytes


def _verify_sidecar(path: Path, sha: str, name: str) -> _RegularBinding:
    raw, binding = _read_regular_snapshot(path, limit=512, what="checksum sidecar")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"checksum sidecar mismatch for {name}") from exc
    if text != f"{sha}  {name}\n":
        raise RuntimeError(f"checksum sidecar mismatch for {name}")
    return binding
