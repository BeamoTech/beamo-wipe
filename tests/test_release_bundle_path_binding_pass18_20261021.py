"""Release verification must stay bound to one link-free bundle snapshot."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

import pytest

from beamo_wipe import NWIPE_PINNED_COMMIT, release_manifest as rm


VERSION = "0.2.9"
ISO_NAME = f"beamo-wipe-{VERSION}-amd64.iso"
MANIFEST_NAME = f"beamo-wipe-{VERSION}-amd64.manifest.json"


def _bundle(directory: Path) -> Path:
    directory.mkdir()
    iso = directory / ISO_NAME
    iso.write_bytes(b"disposable release ISO fixture")
    iso_sha = hashlib.sha256(iso.read_bytes()).hexdigest()
    manifest = {
        "schema_version": rm.SCHEMA_VERSION,
        "beamo_wipe_version": VERSION,
        "source": {"commit": "a" * 40, "dirty": False},
        "build": {"release_build_id": "local"},
        "nwipe": {
            "version": "0.42",
            "commit": NWIPE_PINNED_COMMIT,
            "pinned_path": "/usr/lib/beamo-wipe/nwipe",
        },
        "artifact": {
            "iso_name": ISO_NAME,
            "iso_path": ISO_NAME,
            "iso_size_bytes": iso.stat().st_size,
            "iso_sha256": iso_sha,
        },
    }
    canonical = json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    manifest["_manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    manifest_path = directory / MANIFEST_NAME
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(raw)
    (directory / f"{ISO_NAME}.sha256").write_text(
        f"{iso_sha}  {ISO_NAME}\n", encoding="ascii"
    )
    (directory / f"{MANIFEST_NAME}.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest()}  {MANIFEST_NAME}\n", encoding="ascii"
    )
    return manifest_path


def _replace_with_same_bytes(path: Path) -> None:
    replacement = path.with_name(f".{path.name}.replacement")
    replacement.write_bytes(path.read_bytes())
    os.replace(replacement, path)


def test_iso_hash_rejects_a_symlinked_parent(tmp_path: Path) -> None:
    release = tmp_path / "release"
    release.mkdir()
    artifact = release / "artifact.iso"
    artifact.write_bytes(b"fixture")
    alias = tmp_path / "alias"
    alias.symlink_to(release, target_is_directory=True)

    with pytest.raises(RuntimeError, match="parent|safely"):
        rm.sha256_file_with_stat(alias / artifact.name)


def test_manifest_verification_rejects_a_symlinked_parent(tmp_path: Path) -> None:
    release = tmp_path / "release"
    manifest = _bundle(release)
    alias = tmp_path / "alias"
    alias.symlink_to(release, target_is_directory=True)

    with pytest.raises(RuntimeError, match="parent|safely"):
        rm.verify_build_manifest(alias / manifest.name)


@pytest.mark.parametrize("target_name", [MANIFEST_NAME, ISO_NAME])
def test_verification_rejects_bundle_member_replacement_after_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target_name: str,
) -> None:
    release = tmp_path / "release"
    manifest = _bundle(release)
    target = release / target_name
    real_verify_sidecar = rm._verify_sidecar
    changed = False

    def replace_then_verify(path: Path, sha: str, name: str):
        nonlocal changed
        if not changed:
            changed = True
            _replace_with_same_bytes(target)
        return real_verify_sidecar(path, sha, name)

    monkeypatch.setattr(rm, "_verify_sidecar", replace_then_verify)
    with pytest.raises(RuntimeError, match="changed|bound|snapshot"):
        rm.verify_build_manifest(manifest)
    assert changed


@pytest.mark.parametrize(
    ("sidecar_name", "replace_on_call"),
    [
        (f"{ISO_NAME}.sha256", 1),
        (f"{MANIFEST_NAME}.sha256", 2),
    ],
)
def test_verification_rejects_sidecar_replacement_after_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sidecar_name: str,
    replace_on_call: int,
) -> None:
    release = tmp_path / "release"
    manifest = _bundle(release)
    target = release / sidecar_name
    real_verify_sidecar = rm._verify_sidecar
    calls = 0

    def verify_then_replace(path: Path, sha: str, name: str):
        nonlocal calls
        calls += 1
        result = real_verify_sidecar(path, sha, name)
        if calls == replace_on_call:
            _replace_with_same_bytes(target)
        return result

    monkeypatch.setattr(rm, "_verify_sidecar", verify_then_replace)
    with pytest.raises(RuntimeError, match="changed|bound|snapshot"):
        rm.verify_build_manifest(manifest)


def test_verification_rejects_parent_directory_replacement_after_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "release"
    manifest = _bundle(release)
    real_verify_sidecar = rm._verify_sidecar
    calls = 0

    def verify_then_replace_parent(path: Path, sha: str, name: str):
        nonlocal calls
        calls += 1
        result = real_verify_sidecar(path, sha, name)
        if calls == 2:
            retired = tmp_path / "retired-release"
            shutil.copytree(release, tmp_path / "replacement-release")
            release.rename(retired)
            (tmp_path / "replacement-release").rename(release)
        return result

    monkeypatch.setattr(rm, "_verify_sidecar", verify_then_replace_parent)
    with pytest.raises(RuntimeError, match="parent|changed|bound|snapshot"):
        rm.verify_build_manifest(manifest)
