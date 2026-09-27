#!/usr/bin/env python3
"""Move only measured release inputs between unprivileged and publisher jobs."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publish_release_gcs import _release_inputs  # noqa: E402

SCHEMA = "beamo-wipe-blacksmith-transfer/1"
CHUNK = 8 * 1024 * 1024


def identity() -> tuple[str, str, str]:
    version = os.environ.get("BEAMO_WIPE_VERSION", "")
    commit = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("invalid transfer source identity")
    if os.environ.get("GITHUB_REPOSITORY") != "BeamoTech/beamo-wipe":
        raise RuntimeError("transfer repository differs from release repository")
    key = "/".join(os.environ[k] for k in ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"))
    build_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/" + key))
    return version, commit, build_id


def release_inputs(version: str) -> list[Path]:
    return _release_inputs(version)


def input_names(version: str) -> set[str]:
    stem = f"beamo-wipe-{version}-amd64"
    excluded = {f"dist/{stem}.img", f"dist/{stem}.manifest.json.sig"}
    names = {p.relative_to(ROOT).as_posix() for p in release_inputs(version)} - excluded
    names.add(f"dist/{stem}.img.gz")
    return names


def digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError(f"unsafe transfer file: {path.name}")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            h.update(chunk)
            size += len(chunk)
    return size, h.hexdigest()


def _copy(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file() or source.stat().st_uid != os.getuid():
        raise RuntimeError(f"unsafe transfer source: {source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, destination.open("xb") as copy:
        shutil.copyfileobj(original, copy, CHUNK)


def pack() -> Path:
    version, commit, build_id = identity()
    transfer = ROOT / "release-transfer"
    if transfer.exists() or transfer.is_symlink():
        raise RuntimeError("release transfer directory already exists")
    transfer.mkdir(mode=0o700)
    stem = f"beamo-wipe-{version}-amd64"
    raw = ROOT / "dist" / f"{stem}.img"
    raw_size, raw_sha = digest(raw)
    sidecar = (ROOT / "dist" / f"{stem}.img.sha256").read_text(encoding="ascii")
    if sidecar != f"{raw_sha}  {raw.name}\n":
        raise RuntimeError("tested USB image checksum sidecar differs")
    for name in sorted(input_names(version) - {f"dist/{stem}.img.gz"}):
        _copy(ROOT / name, transfer / name)
    compressed = transfer / "dist" / f"{stem}.img.gz"
    with raw.open("rb") as source, compressed.open("xb") as target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0, compresslevel=1) as zip_stream:
            shutil.copyfileobj(source, zip_stream, CHUNK)
    if digest(raw) != (raw_size, raw_sha):
        raise RuntimeError("USB image changed during release transfer")
    records = {}
    for name in sorted(input_names(version)):
        size, sha = digest(transfer / name)
        records[name] = {"bytes": size, "sha256": sha}
    manifest = {"schema": SCHEMA, "version": version, "source_commit": commit,
                "build_id": build_id, "raw_image": {"bytes": raw_size, "sha256": raw_sha},
                "files": records}
    with (transfer / "transfer-manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return transfer


def restore() -> None:
    version, commit, build_id = identity()
    transfer = ROOT / "release-transfer"
    if transfer.is_symlink() or not transfer.is_dir() or transfer.stat().st_uid != os.getuid():
        raise RuntimeError("unsafe release transfer directory")
    manifest_path = transfer / "transfer-manifest.json"
    expected_sha = os.environ.get("TRANSFER_MANIFEST_SHA256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or digest(manifest_path)[1] != expected_sha:
        raise RuntimeError("transfer manifest differs from qualification job")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_names = input_names(version)
    if (manifest.get("schema") != SCHEMA or manifest.get("version") != version
            or manifest.get("source_commit") != commit or manifest.get("build_id") != build_id
            or not isinstance(manifest.get("files"), dict)
            or set(manifest["files"]) != expected_names):
        raise RuntimeError("transfer manifest has wrong source or inputs")
    actual_names = set()
    for path in transfer.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("linked transfer entry")
        if path.is_file():
            actual_names.add(path.relative_to(transfer).as_posix())
        elif not path.is_dir():
            raise RuntimeError("special transfer entry")
    if actual_names != expected_names | {"transfer-manifest.json"}:
        raise RuntimeError("transfer contains missing or unexpected files")
    for name in expected_names:
        size, sha = digest(transfer / name)
        if manifest["files"][name] != {"bytes": size, "sha256": sha}:
            raise RuntimeError(f"transfer checksum mismatch: {name}")
    if (ROOT / "dist").exists() or (ROOT / "qemu-evidence").exists():
        raise RuntimeError("release output directory already exists")
    stem = f"beamo-wipe-{version}-amd64"
    for name in sorted(expected_names - {f"dist/{stem}.img.gz"}):
        _copy(transfer / name, ROOT / name)
    raw_info = manifest.get("raw_image")
    if not isinstance(raw_info, dict) or type(raw_info.get("bytes")) is not int or not 0 < raw_info["bytes"] <= 3 * 1024**3:
        raise RuntimeError("invalid raw USB size in transfer")
    raw = ROOT / "dist" / f"{stem}.img"
    h = hashlib.sha256()
    size = 0
    with gzip.open(transfer / "dist" / f"{stem}.img.gz", "rb") as source, raw.open("xb") as target:
        for chunk in iter(lambda: source.read(CHUNK), b""):
            size += len(chunk)
            if size > raw_info["bytes"]:
                raise RuntimeError("compressed USB image exceeds declared size")
            h.update(chunk)
            target.write(chunk)
    if size != raw_info["bytes"] or h.hexdigest() != raw_info.get("sha256"):
        raise RuntimeError("transferred USB image differs from qualified bytes")


if __name__ == "__main__":
    if sys.argv[1:] == ["pack"]:
        pack()
    elif sys.argv[1:] == ["restore"]:
        restore()
    else:
        raise SystemExit("usage: release_transfer.py {pack|restore}")
