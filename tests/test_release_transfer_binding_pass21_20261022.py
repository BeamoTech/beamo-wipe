"""PASS21 regressions for the measured release-transfer boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_transfer():
    spec = importlib.util.spec_from_file_location(
        "release_transfer_pass21", ROOT / "scripts/release_transfer.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class TransferFixture:
    transfer: object
    root: Path
    dist: Path
    evidence: Path
    staged: Path
    version: str
    build_id: str
    commit: str
    stem: str
    iso: Path
    image: Path
    sidecar: Path
    log: Path

    def ready_to_restore(self, monkeypatch) -> None:
        manifest = self.staged / "transfer-manifest.json"
        monkeypatch.setenv("TRANSFER_MANIFEST_SHA256", sha(manifest.read_bytes()))
        shutil.rmtree(self.dist)
        shutil.rmtree(self.evidence)


def make_source_fixture(tmp_path: Path, monkeypatch) -> TransferFixture:
    transfer = load_transfer()
    root = tmp_path / "source"
    dist = root / "dist"
    evidence = root / "qemu-evidence"
    dist.mkdir(parents=True)
    evidence.mkdir()
    version = "0.2.11"
    build_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    commit = "b" * 40
    stem = f"beamo-wipe-{version}-amd64"
    iso = dist / f"{stem}.iso"
    image = dist / f"{stem}.img"
    sidecar = dist / f"{stem}.img.sha256"
    log = evidence / "bios.log"
    iso.write_bytes(b"I")
    image.write_bytes(b"PASS21 exact raw USB bytes")
    sidecar.write_text(f"{sha(image.read_bytes())}  {image.name}\n", encoding="ascii")
    log.write_bytes(b"PASS21 qualified evidence")
    monkeypatch.setattr(transfer, "ROOT", root)
    monkeypatch.setattr(transfer, "identity", lambda: (version, commit, build_id))
    monkeypatch.setattr(
        transfer,
        "release_inputs",
        lambda _version: [iso, image, sidecar, log],
    )
    return TransferFixture(
        transfer,
        root,
        dist,
        evidence,
        root / "release-transfer",
        version,
        build_id,
        commit,
        stem,
        iso,
        image,
        sidecar,
        log,
    )


def make_packed_fixture(tmp_path: Path, monkeypatch) -> TransferFixture:
    fixture = make_source_fixture(tmp_path, monkeypatch)
    assert fixture.transfer.pack() == fixture.staged
    return fixture


def rewrite_manifest(fixture: TransferFixture, monkeypatch, value: dict) -> None:
    path = fixture.staged / "transfer-manifest.json"
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    monkeypatch.setenv("TRANSFER_MANIFEST_SHA256", sha(path.read_bytes()))


def replace_on_hexdigest(
    monkeypatch, transfer, *, trigger: bytes, target: Path
) -> dict:
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

    monkeypatch.setattr(transfer.hashlib, "sha256", ReplacingHash)
    return state


def test_pack_rejects_source_beneath_linked_parent(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    real_evidence = tmp_path / "real-evidence"
    fixture.evidence.rename(real_evidence)
    fixture.evidence.symlink_to(real_evidence, target_is_directory=True)
    linked_log = fixture.evidence / fixture.log.name
    monkeypatch.setattr(
        fixture.transfer,
        "release_inputs",
        lambda _version: [fixture.iso, fixture.image, fixture.sidecar, linked_log],
    )
    with pytest.raises(RuntimeError):
        fixture.transfer.pack()


def test_pack_rejects_checkout_beneath_linked_parent(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    fixture.root.rename(real_parent / "source")
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    alias_root = alias_parent / "source"
    alias_dist = alias_root / "dist"
    alias_evidence = alias_root / "qemu-evidence"
    monkeypatch.setattr(fixture.transfer, "ROOT", alias_root)
    monkeypatch.setattr(
        fixture.transfer,
        "release_inputs",
        lambda _version: [
            alias_dist / fixture.iso.name,
            alias_dist / fixture.image.name,
            alias_dist / fixture.sidecar.name,
            alias_evidence / fixture.log.name,
        ],
    )
    with pytest.raises(RuntimeError):
        fixture.transfer.pack()


def test_pack_rejects_hard_linked_source(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    os.link(fixture.iso, tmp_path / "second-iso-name")
    with pytest.raises(RuntimeError, match="linked|bound|safe"):
        fixture.transfer.pack()


def test_pack_rejects_duplicate_source_name(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        fixture.transfer,
        "release_inputs",
        lambda _version: [
            fixture.iso,
            fixture.image,
            fixture.sidecar,
            fixture.log,
            fixture.log,
        ],
    )
    with pytest.raises(RuntimeError, match="duplicate"):
        fixture.transfer.pack()


def test_pack_rejects_same_byte_raw_image_replacement(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    state = replace_on_hexdigest(
        monkeypatch,
        fixture.transfer,
        trigger=fixture.image.read_bytes(),
        target=fixture.image,
    )
    with pytest.raises(RuntimeError):
        fixture.transfer.pack()
    assert state["replaced"]


def test_pack_rejects_whole_transfer_replacement(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    original_digest = fixture.transfer.digest
    held = fixture.root / "held-release-transfer"
    state = {"replaced": False}

    def replacing_digest(path):
        if not state["replaced"] and fixture.staged in path.parents:
            fixture.staged.rename(held)
            shutil.copytree(held, fixture.staged)
            state["replaced"] = True
        return original_digest(path)

    monkeypatch.setattr(fixture.transfer, "digest", replacing_digest)
    with pytest.raises(RuntimeError):
        fixture.transfer.pack()
    assert state["replaced"]


def test_pack_rejects_copy_that_differs_from_measured_source(tmp_path, monkeypatch):
    fixture = make_source_fixture(tmp_path, monkeypatch)
    original_copy = fixture.transfer._copy
    state = {"corrupted": False}

    def corrupting_copy(source, destination):
        result = original_copy(source, destination)
        if not state["corrupted"] and destination.name == fixture.iso.name:
            destination.write_bytes(b"X")
            state["corrupted"] = True
        return result

    monkeypatch.setattr(fixture.transfer, "_copy", corrupting_copy)
    with pytest.raises(RuntimeError, match="copy differs"):
        fixture.transfer.pack()
    assert state["corrupted"]


def test_release_workflow_uses_digest_retained_by_pack_process():
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert 'manifest_sha256="$(python3 scripts/release_transfer.py pack)"' in workflow
    assert 'echo "manifest_sha256=$manifest_sha256"' in workflow
    assert "sha256sum release-transfer/transfer-manifest.json" not in workflow


def test_pack_retains_digest_of_its_bound_manifest(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    manifest = fixture.staged / "transfer-manifest.json"
    assert getattr(fixture.transfer, "PACKED_MANIFEST_SHA256", None) == sha(
        manifest.read_bytes()
    )


def test_restore_rejects_duplicate_manifest_fields(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    path = fixture.staged / "transfer-manifest.json"
    original = path.read_text(encoding="utf-8").lstrip()
    path.write_text('{"schema":"wrong",' + original[1:], encoding="utf-8")
    fixture.ready_to_restore(monkeypatch)
    with pytest.raises(RuntimeError, match="duplicate JSON field"):
        fixture.transfer.restore()


def test_restore_rejects_boolean_file_size(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    manifest = json.loads(
        (fixture.staged / "transfer-manifest.json").read_text(encoding="utf-8")
    )
    manifest["files"][f"dist/{fixture.stem}.iso"]["bytes"] = True
    rewrite_manifest(fixture, monkeypatch, manifest)
    shutil.rmtree(fixture.dist)
    shutil.rmtree(fixture.evidence)
    with pytest.raises(RuntimeError, match="record|manifest|size"):
        fixture.transfer.restore()


def test_restore_rejects_extra_manifest_fields(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    manifest = json.loads(
        (fixture.staged / "transfer-manifest.json").read_text(encoding="utf-8")
    )
    manifest["unqualified"] = "ignored by the old reader"
    rewrite_manifest(fixture, monkeypatch, manifest)
    shutil.rmtree(fixture.dist)
    shutil.rmtree(fixture.evidence)
    with pytest.raises(RuntimeError, match="manifest"):
        fixture.transfer.restore()


def test_restore_rejects_oversized_manifest(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    path = fixture.staged / "transfer-manifest.json"
    limit = getattr(fixture.transfer, "MAX_MANIFEST_BYTES", 4 * 1024 * 1024)
    payload = path.read_bytes() + b" " * (limit + 1)
    path.write_bytes(payload)
    fixture.ready_to_restore(monkeypatch)
    with pytest.raises(RuntimeError, match="size limit|exceeds"):
        fixture.transfer.restore()


def test_restore_rejects_hard_linked_transfer_file(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    os.link(
        fixture.staged / "dist" / f"{fixture.stem}.iso",
        tmp_path / "second-transfer-name",
    )
    fixture.ready_to_restore(monkeypatch)
    with pytest.raises(RuntimeError, match="linked|bound|safe"):
        fixture.transfer.restore()


def test_restore_rejects_same_byte_manifest_replacement(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    manifest = fixture.staged / "transfer-manifest.json"
    fixture.ready_to_restore(monkeypatch)
    state = replace_on_hexdigest(
        monkeypatch,
        fixture.transfer,
        trigger=manifest.read_bytes(),
        target=manifest,
    )
    with pytest.raises(RuntimeError):
        fixture.transfer.restore()
    assert state["replaced"]


def test_restore_rejects_same_byte_input_replacement(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    transferred_iso = fixture.staged / "dist" / f"{fixture.stem}.iso"
    fixture.ready_to_restore(monkeypatch)
    state = replace_on_hexdigest(
        monkeypatch,
        fixture.transfer,
        trigger=transferred_iso.read_bytes(),
        target=transferred_iso,
    )
    with pytest.raises(RuntimeError):
        fixture.transfer.restore()
    assert state["replaced"]


def test_restore_rejects_whole_transfer_replacement_before_copy(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    fixture.ready_to_restore(monkeypatch)
    original_copy = fixture.transfer._copy
    held = fixture.root / "held-release-transfer"
    state = {"replaced": False}

    def replacing_copy(source, destination):
        if not state["replaced"]:
            fixture.staged.rename(held)
            shutil.copytree(held, fixture.staged)
            state["replaced"] = True
        return original_copy(source, destination)

    monkeypatch.setattr(fixture.transfer, "_copy", replacing_copy)
    with pytest.raises(RuntimeError):
        fixture.transfer.restore()
    assert state["replaced"]


def test_restore_rejects_linked_output_parent_without_escape(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    fixture.ready_to_restore(monkeypatch)
    original_copy = fixture.transfer._copy
    outside = tmp_path / "outside"
    outside.mkdir()
    held_parent = tmp_path / "held-output-parent"
    state = {"linked": False}

    def linking_copy(source, destination):
        if not state["linked"]:
            if destination.parent.exists():
                destination.parent.rename(held_parent)
            destination.parent.symlink_to(outside, target_is_directory=True)
            state["linked"] = True
        return original_copy(source, destination)

    monkeypatch.setattr(fixture.transfer, "_copy", linking_copy)
    with pytest.raises(RuntimeError):
        fixture.transfer.restore()
    assert state["linked"]
    assert not list(outside.iterdir())


def test_restore_does_not_publish_partial_outputs_for_bad_gzip(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    compressed = fixture.staged / "dist" / f"{fixture.stem}.img.gz"
    compressed.write_bytes(b"not a gzip stream")
    manifest = json.loads(
        (fixture.staged / "transfer-manifest.json").read_text(encoding="utf-8")
    )
    manifest["files"][f"dist/{fixture.stem}.img.gz"] = {
        "bytes": compressed.stat().st_size,
        "sha256": sha(compressed.read_bytes()),
    }
    rewrite_manifest(fixture, monkeypatch, manifest)
    shutil.rmtree(fixture.dist)
    shutil.rmtree(fixture.evidence)
    with pytest.raises((RuntimeError, OSError, EOFError)):
        fixture.transfer.restore()
    assert not fixture.dist.exists()
    assert not fixture.evidence.exists()


def test_restore_rejects_unexpected_staged_file_without_publication(
    tmp_path, monkeypatch
):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    fixture.ready_to_restore(monkeypatch)
    original_copy = fixture.transfer._copy
    state = {"inserted": False}

    def inserting_copy(source, destination):
        result = original_copy(source, destination)
        if not state["inserted"]:
            (destination.parent / "unexpected").write_bytes(b"not qualified")
            state["inserted"] = True
        return result

    monkeypatch.setattr(fixture.transfer, "_copy", inserting_copy)
    with pytest.raises(RuntimeError, match="unexpected"):
        fixture.transfer.restore()
    assert state["inserted"]
    assert not fixture.dist.exists()
    assert not fixture.evidence.exists()


def test_restore_rolls_back_first_directory_if_second_publish_fails(
    tmp_path, monkeypatch
):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    fixture.ready_to_restore(monkeypatch)
    real_rename = os.rename
    state = {"failed": False}

    def failing_rename(source, destination, *args, **kwargs):
        if (
            not state["failed"]
            and source == "qemu-evidence"
            and kwargs.get("src_dir_fd") is not None
        ):
            state["failed"] = True
            raise OSError("injected second-directory publication failure")
        return real_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(fixture.transfer.os, "rename", failing_rename)
    with pytest.raises(OSError, match="injected"):
        fixture.transfer.restore()
    assert state["failed"]
    assert not fixture.dist.exists()
    assert not fixture.evidence.exists()


def test_transfer_positive_round_trip_binds_exact_bytes(tmp_path, monkeypatch):
    fixture = make_packed_fixture(tmp_path, monkeypatch)
    expected = {
        fixture.iso.name: fixture.iso.read_bytes(),
        fixture.image.name: fixture.image.read_bytes(),
        fixture.sidecar.name: fixture.sidecar.read_bytes(),
        fixture.log.name: fixture.log.read_bytes(),
    }
    fixture.ready_to_restore(monkeypatch)
    fixture.transfer.restore()
    assert fixture.iso.read_bytes() == expected[fixture.iso.name]
    assert fixture.image.read_bytes() == expected[fixture.image.name]
    assert fixture.sidecar.read_bytes() == expected[fixture.sidecar.name]
    assert fixture.log.read_bytes() == expected[fixture.log.name]
