"""PASS20 regressions for release-asset assembly path and byte binding."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from beamo_wipe.release_signing import (
    fingerprint,
    generate_keypair,
    key_id,
    sign_manifest_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


def load_assembler():
    spec = importlib.util.spec_from_file_location(
        "prepare_release_assets_pass20", ROOT / "scripts/prepare_release_assets.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class ReleaseFixture:
    assembler: object
    root: Path
    dist: Path
    stage: Path
    version: str
    build_id: str
    commit: str
    stem: str
    private_key: bytes
    manifest_bytes: bytes


def make_release_fixture(tmp_path: Path, monkeypatch) -> ReleaseFixture:
    assembler = load_assembler()
    private_key, public_key = generate_keypair()
    registry = {
        "schema": "beamo-wipe-release-keys/1",
        "keys": {
            key_id(public_key): {
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "fingerprint": fingerprint(public_key),
                "status": "active",
            }
        },
    }
    root = tmp_path / "source"
    dist = root / "dist"
    stage = tmp_path / "stage"
    (root / "packaging/release-keys").mkdir(parents=True)
    dist.mkdir()
    stage.mkdir()
    (root / "packaging/release-keys/keys.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    monkeypatch.setattr(assembler, "ROOT", root)
    monkeypatch.setattr(assembler, "_read_signing_key", lambda: private_key)

    version = "0.2.11"
    build_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    commit = "b" * 40
    stem = f"beamo-wipe-{version}-amd64"
    iso_bytes = b"PASS20 exact ISO bytes"
    raw_bytes = b"PASS20 exact raw USB bytes"
    iso_path = dist / f"{stem}.iso"
    raw_path = dist / f"{stem}.img"
    iso_path.write_bytes(iso_bytes)
    raw_path.write_bytes(raw_bytes)
    manifest = {
        "beamo_wipe_version": version,
        "source": {"commit": commit},
        "build": {"release_build_id": build_id},
        "artifact": {"iso_sha256": sha(iso_bytes)},
        "test_evidence": {"gates": {"pass20": "passed"}},
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    manifest_path = dist / f"{stem}.manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    signature_path = dist / f"{stem}.manifest.json.sig"
    signature_path.write_text(
        json.dumps(sign_manifest_bytes(manifest_bytes, private_key)), encoding="utf-8"
    )
    monkeypatch.setattr(assembler, "verify_manifest", lambda _path: manifest_bytes)
    (dist / f"{stem}.img.json").write_text(
        json.dumps({"sha256": sha(raw_bytes), "iso_sha256": sha(iso_bytes)}),
        encoding="utf-8",
    )
    for name in (
        f"{stem}.iso.sha256",
        f"{stem}.img.sha256",
        f"{stem}.manifest.json.sha256",
        "SHA256SUMS",
    ):
        (dist / name).write_text("fixture\n", encoding="ascii")
    compressed_path = stage / f"{stem}.img.gz"
    compressed_path.write_bytes(gzip.compress(raw_bytes, mtime=0))
    (stage / f"{stem}.img.gz.sha256").write_text(
        f"{sha(compressed_path.read_bytes())}  {compressed_path.name}\n",
        encoding="ascii",
    )
    (stage / "verification-evidence.tar.gz").write_bytes(
        b"PASS20 exact verification evidence"
    )
    (stage / "RELEASE_COMPLETE.txt").write_text(
        "\n".join(
            [
                "release_complete=true",
                f"build_id={build_id}",
                f"version={version}",
                f"source_commit={commit}",
                f"{sha(iso_bytes)}  {iso_path.name}",
                f"{sha(raw_bytes)}  {raw_path.name}",
                f"{sha(manifest_bytes)}  {manifest_path.name}",
                f"{sha(signature_path.read_bytes())}  {signature_path.name}",
            ]
        )
        + "\n",
        encoding="ascii",
    )
    return ReleaseFixture(
        assembler,
        root,
        dist,
        stage,
        version,
        build_id,
        commit,
        stem,
        private_key,
        manifest_bytes,
    )


def replace_on_digest(monkeypatch, assembler, *, trigger: bytes, target: Path) -> dict:
    """Replace target with an equal-byte new inode during hexdigest()."""
    real_sha256 = hashlib.sha256
    trigger_digest = real_sha256(trigger).digest()
    state = {"replaced": False}

    class ReplacingHash:
        def __init__(self, data=b""):
            self._inner = real_sha256(data)

        def update(self, data):
            self._inner.update(data)

        def digest(self):
            return self._inner.digest()

        def hexdigest(self):
            result = self._inner.hexdigest()
            if not state["replaced"] and self._inner.digest() == trigger_digest:
                replacement = target.with_name(target.name + ".replacement")
                replacement.write_bytes(target.read_bytes())
                os.replace(replacement, target)
                state["replaced"] = True
            return result

        def __getattr__(self, name):
            return getattr(self._inner, name)

    monkeypatch.setattr(assembler.hashlib, "sha256", ReplacingHash)
    return state


def run_prepare(fixture: ReleaseFixture, *, stage: Path | None = None) -> None:
    fixture.assembler.prepare(
        stage or fixture.stage,
        fixture.version,
        fixture.build_id,
        fixture.commit,
    )


def test_digest_rejects_linked_parent(tmp_path):
    assembler = load_assembler()
    real = tmp_path / "real"
    real.mkdir()
    (real / "asset").write_bytes(b"asset")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(RuntimeError):
        assembler.digest(alias / "asset")


def test_digest_rejects_same_byte_inode_replacement(tmp_path, monkeypatch):
    assembler = load_assembler()
    asset = tmp_path / "asset"
    payload = b"same bytes on a replacement inode"
    asset.write_bytes(payload)
    state = replace_on_digest(monkeypatch, assembler, trigger=payload, target=asset)
    with pytest.raises(RuntimeError):
        assembler.digest(asset)
    assert state["replaced"]


def test_file_record_rejects_linked_parent(tmp_path):
    assembler = load_assembler()
    real = tmp_path / "real"
    real.mkdir()
    (real / "asset").write_bytes(b"asset")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(RuntimeError):
        assembler.file_record(alias / "asset")


def test_file_record_rejects_hard_linked_input(tmp_path):
    assembler = load_assembler()
    asset = tmp_path / "asset"
    asset.write_bytes(b"asset")
    os.link(asset, tmp_path / "second-name")
    with pytest.raises(RuntimeError, match="not uniquely linked"):
        assembler.file_record(asset)


def test_write_json_rejects_linked_parent_without_writing_outside(tmp_path):
    assembler = load_assembler()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(RuntimeError):
        assembler.write_json(alias / "output.json", {"ok": True})
    assert not (real / "output.json").exists()


def test_prepare_rejects_stage_beneath_linked_parent(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    fixture.stage.rename(real_parent / "stage")
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(RuntimeError):
        run_prepare(fixture, stage=alias_parent / "stage")


def test_prepare_rejects_duplicate_image_metadata_fields(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    raw_sha = sha((fixture.dist / f"{fixture.stem}.img").read_bytes())
    iso_sha = sha((fixture.dist / f"{fixture.stem}.iso").read_bytes())
    (fixture.dist / f"{fixture.stem}.img.json").write_text(
        '{"sha256":"'
        + "0" * 64
        + '","sha256":"'
        + raw_sha
        + '","iso_sha256":"'
        + iso_sha
        + '"}',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="duplicate JSON field"):
        run_prepare(fixture)


def test_prepare_rejects_duplicate_signed_manifest_fields(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    manifest_path = fixture.dist / f"{fixture.stem}.manifest.json"
    duplicate = b'{"beamo_wipe_version":"9.9.9",' + fixture.manifest_bytes.lstrip()[1:]
    manifest_path.write_bytes(duplicate)
    signature_path = fixture.dist / f"{fixture.stem}.manifest.json.sig"
    signature_path.write_text(
        json.dumps(sign_manifest_bytes(duplicate, fixture.private_key)),
        encoding="utf-8",
    )
    monkeypatch.setattr(fixture.assembler, "verify_manifest", lambda _path: duplicate)
    iso = fixture.dist / f"{fixture.stem}.iso"
    raw = fixture.dist / f"{fixture.stem}.img"
    (fixture.stage / "RELEASE_COMPLETE.txt").write_text(
        "\n".join(
            [
                "release_complete=true",
                f"build_id={fixture.build_id}",
                f"version={fixture.version}",
                f"source_commit={fixture.commit}",
                f"{sha(iso.read_bytes())}  {iso.name}",
                f"{sha(raw.read_bytes())}  {raw.name}",
                f"{sha(duplicate)}  {manifest_path.name}",
                f"{sha(signature_path.read_bytes())}  {signature_path.name}",
            ]
        )
        + "\n",
        encoding="ascii",
    )
    with pytest.raises(RuntimeError, match="duplicate JSON field"):
        run_prepare(fixture)


def test_prepare_rejects_marker_replaced_after_snapshot(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    marker = fixture.stage / "RELEASE_COMPLETE.txt"
    state = replace_on_digest(
        monkeypatch, fixture.assembler, trigger=marker.read_bytes(), target=marker
    )
    with pytest.raises(RuntimeError):
        run_prepare(fixture)
    assert state["replaced"]


def test_prepare_rejects_public_asset_replaced_while_recorded(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    evidence = fixture.stage / "verification-evidence.tar.gz"
    state = replace_on_digest(
        monkeypatch, fixture.assembler, trigger=evidence.read_bytes(), target=evidence
    )
    with pytest.raises(RuntimeError):
        run_prepare(fixture)
    assert state["replaced"]


def test_prepare_rejects_public_asset_replaced_during_signing(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    evidence = fixture.stage / "verification-evidence.tar.gz"
    state = {"replaced": False}

    def replacing_key_read():
        replacement = evidence.with_name(evidence.name + ".replacement")
        replacement.write_bytes(evidence.read_bytes())
        os.replace(replacement, evidence)
        state["replaced"] = True
        return fixture.private_key

    monkeypatch.setattr(fixture.assembler, "_read_signing_key", replacing_key_read)
    with pytest.raises(RuntimeError):
        run_prepare(fixture)
    assert state["replaced"]
    assert not (fixture.stage / "release-downloads.json.sig").exists()


def test_prepare_rejects_stage_replacement_after_inventory_write(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    original_write_json = fixture.assembler._write_json_snapshot
    held_stage = tmp_path / "held-stage"
    state = {"replaced": False}

    def replacing_write_json(path, value, **kwargs):
        result = original_write_json(path, value, **kwargs)
        if path.name == "release-downloads.json":
            fixture.stage.rename(held_stage)
            fixture.stage.mkdir()
            state["replaced"] = True
        return result

    monkeypatch.setattr(fixture.assembler, "_write_json_snapshot", replacing_write_json)
    with pytest.raises(RuntimeError):
        run_prepare(fixture)
    assert state["replaced"]
    assert (held_stage / "release-downloads.json").is_file()
    assert not (fixture.stage / "release-downloads.json.sig").exists()


def test_prepare_positive_inventory_binds_exact_inputs(tmp_path, monkeypatch):
    fixture = make_release_fixture(tmp_path, monkeypatch)
    run_prepare(fixture)
    inventory = json.loads(
        (fixture.stage / "release-downloads.json").read_text(encoding="utf-8")
    )
    files = inventory["files"]
    for name in (
        "RELEASE_COMPLETE.txt",
        "BUILD-RECEIPT.json",
        "verification-evidence.tar.gz",
        f"{fixture.stem}.img",
        f"{fixture.stem}.img.gz",
        f"{fixture.stem}.manifest.json",
    ):
        path = (
            fixture.stage / name
            if (fixture.stage / name).exists()
            else fixture.dist / name
        )
        assert files[name] == {
            "bytes": path.stat().st_size,
            "sha256": sha(path.read_bytes()),
        }
