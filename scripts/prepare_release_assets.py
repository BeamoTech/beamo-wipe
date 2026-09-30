#!/usr/bin/env python3
"""Assemble the public download inventory from the signed, tested bytes."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from beamo_wipe.release_manifest import verify_manifest  # noqa: E402
from beamo_wipe.release_signing import (  # noqa: E402
    detached_verification_metadata, load_key_registry, sign_manifest_bytes, verify_with_registry,
)
from publish_release_gcs import _read_signing_key  # noqa: E402


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def file_record(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing regular release input: {path.name}")
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def write_json(path: Path, value: dict) -> bytes:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
    return payload


def prepare(stage: Path, version: str, build_id: str, commit: str) -> None:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise RuntimeError("invalid release version")
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", build_id) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("invalid release source identity")
    if stage.is_symlink() or not stage.is_dir() or stage.stat().st_uid != os.getuid():
        raise RuntimeError("unsafe release staging directory")

    stem = f"beamo-wipe-{version}-amd64"
    dist = ROOT / "dist"
    manifest_path = dist / f"{stem}.manifest.json"
    manifest_bytes = verify_manifest(manifest_path)
    manifest = json.loads(manifest_bytes)
    if (manifest["beamo_wipe_version"] != version
            or manifest["source"]["commit"] != commit
            or manifest["build"]["release_build_id"] != build_id):
        raise RuntimeError("release manifest does not match qualified source")
    registry = load_key_registry(json.loads((ROOT / "packaging/release-keys/keys.json").read_text()))
    signature = json.loads((dist / f"{stem}.manifest.json.sig").read_text())
    verify_with_registry(manifest_bytes, signature, registry)

    raw_image = dist / f"{stem}.img"
    raw_sha = digest(raw_image)
    image_meta = json.loads((dist / f"{stem}.img.json").read_text())
    if image_meta["sha256"] != raw_sha or image_meta["iso_sha256"] != manifest["artifact"]["iso_sha256"]:
        raise RuntimeError("USB image differs from signed ISO provenance")

    # GCS writes this marker only after each immutable object has been read
    # back and checked. Require this exact build and its customer bytes.
    marker = (stage / "RELEASE_COMPLETE.txt").read_text(encoding="ascii").splitlines()
    if marker[:4] != ["release_complete=true", f"build_id={build_id}",
                       f"version={version}", f"source_commit={commit}"]:
        raise RuntimeError("remote completion marker has the wrong identity")
    remote = {}
    for line in marker[4:]:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if not match or match[2] in remote:
            raise RuntimeError("malformed remote completion marker")
        remote[match[2]] = match[1]
    for path in (dist / f"{stem}.iso", raw_image, manifest_path,
                 dist / f"{stem}.manifest.json.sig"):
        if remote.get(path.name) != digest(path):
            raise RuntimeError(f"remote release does not match {path.name}")

    compressed = stage / f"{stem}.img.gz"
    decompressed = hashlib.sha256()
    with gzip.open(compressed, "rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            decompressed.update(chunk)
    if decompressed.hexdigest() != raw_sha:
        raise RuntimeError("compressed USB download differs from tested image")
    if (stage / f"{stem}.img.gz.sha256").read_text(encoding="ascii") != f"{digest(compressed)}  {compressed.name}\n":
        raise RuntimeError("compressed USB checksum sidecar differs")

    public = [
        dist / f"{stem}.iso", dist / f"{stem}.iso.sha256",
        dist / f"{stem}.img.sha256", dist / f"{stem}.img.json",
        manifest_path, dist / f"{stem}.manifest.json.sha256",
        dist / f"{stem}.manifest.json.sig", dist / "SHA256SUMS",
        ROOT / "packaging/release-keys/keys.json", compressed,
        stage / f"{stem}.img.gz.sha256", stage / "verification-evidence.tar.gz",
    ]
    build_receipt = {
        "version": version, "source_commit": commit, "build_id": build_id,
        "public_release": False, "raw_usb_sha256": raw_sha,
        "gates": manifest["test_evidence"]["gates"],
        "artifacts": {p.name: file_record(p) for p in public},
    }
    receipt_path = stage / "BUILD-RECEIPT.json"
    write_json(receipt_path, build_receipt)
    inventory = {
        "schema": "beamo-wipe-release-downloads/1",
        "beamo_wipe_version": version, "source_commit": commit,
        "qualified_build_id": build_id,
        "verification": detached_verification_metadata("release-downloads.json", version),
        "files": {p.name: file_record(p) for p in [*public, receipt_path, raw_image]},
    }
    inventory_bytes = write_json(stage / "release-downloads.json", inventory)
    signed = sign_manifest_bytes(inventory_bytes, _read_signing_key())
    verify_with_registry(inventory_bytes, signed, registry)
    write_json(stage / "release-downloads.json.sig", signed)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), os.environ["BEAMO_WIPE_VERSION"],
            os.environ["BUILD_ID"], os.environ["GITHUB_SHA"])
