"""Release output reads and publication stay bound to the verified bytes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from beamo_wipe import release_manifest as rm


VERSION = "0.2.9"
ISO_NAME = f"beamo-wipe-{VERSION}-amd64.iso"
MANIFEST_NAME = f"beamo-wipe-{VERSION}-amd64.manifest.json"
ROOT = Path(__file__).resolve().parents[1]


def _manifest_fixture(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(rm, "ROOT", tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    iso = dist / ISO_NAME
    iso.write_bytes(b"disposable ISO fixture")
    iso_sha = hashlib.sha256(iso.read_bytes()).hexdigest()
    manifest = {
        "artifact": {
            "iso_name": ISO_NAME,
            "iso_path": ISO_NAME,
            "iso_sha256": iso_sha,
        },
        "schema_version": 2,
        "beamo_wipe_version": VERSION,
    }
    canonical = json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    manifest["_manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return dist / MANIFEST_NAME, manifest


def _updated_manifest(manifest):
    updated = {**manifest, "test_evidence": {"measured": True}}
    unsigned = {key: value for key, value in updated.items() if key != "_manifest_sha256"}
    canonical = json.dumps(
        unsigned, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    updated["_manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return updated


def test_prior_output_read_rejects_same_inode_rewrite_after_read(tmp_path, monkeypatch):
    path = tmp_path / "prior.json"
    original = b"owned receipt"
    foreign = b"foreign bytes"
    assert len(original) == len(foreign)
    path.write_bytes(original)
    before = path.stat()
    real_lstat = Path.lstat
    calls = 0

    def rewrite_before_final_lstat(candidate, *args, **kwargs):
        nonlocal calls
        result = real_lstat(candidate, *args, **kwargs)
        if candidate == path:
            calls += 1
            if calls == 2:
                path.write_bytes(foreign)
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                result = real_lstat(candidate, *args, **kwargs)
        return result

    monkeypatch.setattr(Path, "lstat", rewrite_before_final_lstat)
    with pytest.raises(RuntimeError, match="unverified prior manifest output"):
        rm._prior_output_bytes(path, 512)
    assert path.read_bytes() == foreign


def test_manifest_publication_retires_foreign_replacement_at_final_exchange(
    tmp_path, monkeypatch
):
    output, manifest = _manifest_fixture(tmp_path, monkeypatch)
    rm.write_manifest(manifest, output)
    updated = _updated_manifest(manifest)
    foreign = b"another writer owns this manifest name"
    real_renameat2 = rm._renameat2
    replaced = False

    def replace_before_exchange(source_dirfd, source, destination_dirfd, destination, flags):
        nonlocal replaced
        if destination == output.name and flags == rm._RENAME_EXCHANGE and not replaced:
            replaced = True
            output.write_bytes(foreign)
        return real_renameat2(
            source_dirfd, source, destination_dirfd, destination, flags
        )

    monkeypatch.setattr(rm, "_renameat2", replace_before_exchange)
    intended_blob = (
        json.dumps(updated, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    with pytest.raises(RuntimeError, match="intended bytes retained"):
        rm.write_manifest(updated, output)

    assert replaced
    assert output.read_bytes() == foreign
    retired = list(output.parent.glob(f".{output.name}.publish.*"))
    assert [entry.read_bytes() for entry in retired] == [intended_blob]


def test_interrupted_intended_sidecars_are_retryable(tmp_path, monkeypatch):
    output, manifest = _manifest_fixture(tmp_path, monkeypatch)
    real_atomic_write = rm._atomic_write
    calls = 0

    def interrupt_manifest(path, blob, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise KeyboardInterrupt
        return real_atomic_write(path, blob, **kwargs)

    monkeypatch.setattr(rm, "_atomic_write", interrupt_manifest)
    with pytest.raises(KeyboardInterrupt):
        rm.write_manifest(manifest, output)

    assert not output.exists()
    assert Path(str(output) + ".sha256").is_file()
    monkeypatch.setattr(rm, "_atomic_write", real_atomic_write)
    rm.write_manifest(manifest, output)
    assert output.is_file()
    assert Path(str(output) + ".sha256").read_bytes() == rm._sidecar_blob(
        hashlib.sha256(output.read_bytes()).hexdigest(), output.name
    )


def test_interruption_immediately_after_exchange_is_retryable(tmp_path, monkeypatch):
    output, manifest = _manifest_fixture(tmp_path, monkeypatch)
    rm.write_manifest(manifest, output)
    updated = _updated_manifest(manifest)
    real_renameat2 = rm._renameat2
    interrupted = False

    def interrupt_after_exchange(
        source_dirfd, source, destination_dirfd, destination, flags
    ):
        nonlocal interrupted
        real_renameat2(source_dirfd, source, destination_dirfd, destination, flags)
        if (
            destination == output.name
            and flags == rm._RENAME_EXCHANGE
            and not interrupted
        ):
            interrupted = True
            raise KeyboardInterrupt

    monkeypatch.setattr(rm, "_renameat2", interrupt_after_exchange)
    with pytest.raises(KeyboardInterrupt):
        rm.write_manifest(updated, output)

    assert interrupted
    monkeypatch.setattr(rm, "_renameat2", real_renameat2)
    rm.write_manifest(updated, output)
    assert json.loads(output.read_text())["test_evidence"] == {"measured": True}


def test_atomic_publication_preserves_mutated_temp_at_unsafe_result(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.json"
    intended = b"owned receipt"
    foreign = b"foreign bytes"
    real_renameat2 = rm._renameat2
    changed_temp = None

    def mutate_before_publication(source_dirfd, source, destination_dirfd, target, flags):
        nonlocal changed_temp
        if target == destination.name:
            changed_temp = tmp_path / str(source)
            before = changed_temp.stat()
            changed_temp.write_bytes(foreign)
            os.utime(changed_temp, ns=(before.st_atime_ns, before.st_mtime_ns))
        return real_renameat2(source_dirfd, source, destination_dirfd, target, flags)

    monkeypatch.setattr(rm, "_renameat2", mutate_before_publication)
    with pytest.raises(RuntimeError, match="publication changed"):
        rm._atomic_write(destination, intended, expected=None)

    assert destination.read_bytes() == foreign
    assert changed_temp is not None
    assert not changed_temp.exists()


def test_atomic_publication_preserves_destination_that_appears(tmp_path, monkeypatch):
    destination = tmp_path / "result.json"
    foreign = b"another writer arrived"
    real_renameat2 = rm._renameat2
    planted = False

    def plant_before_publication(source_dirfd, source, destination_dirfd, target, flags):
        nonlocal planted
        if target == destination.name and not planted:
            planted = True
            destination.write_bytes(foreign)
        return real_renameat2(source_dirfd, source, destination_dirfd, target, flags)

    monkeypatch.setattr(rm, "_renameat2", plant_before_publication)
    with pytest.raises(FileExistsError):
        rm._atomic_write(destination, b"intended bytes", expected=None)

    assert planted
    assert destination.read_bytes() == foreign
    retained = list(tmp_path.glob(".result.json.publish.*"))
    assert [entry.read_bytes() for entry in retained] == [b"intended bytes"]


def _complete_iso_bundle(out: Path):
    iso_blob = b"owned prior ISO fixture"
    iso = out / ISO_NAME
    iso.write_bytes(iso_blob)
    iso_sha = hashlib.sha256(iso_blob).hexdigest()
    fields = {
        "schema_version": 2,
        "beamo_wipe_version": VERSION,
        "artifact": {
            "iso_name": ISO_NAME,
            "iso_path": ISO_NAME,
            "iso_size_bytes": len(iso_blob),
            "iso_sha256": iso_sha,
            "iso_sha256_sidecar": f"{ISO_NAME}.sha256",
        },
    }
    canonical = json.dumps(
        fields, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    fields["_manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    manifest_blob = (
        json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    (out / MANIFEST_NAME).write_bytes(manifest_blob)
    manifest_sha = hashlib.sha256(manifest_blob).hexdigest()
    (out / f"{ISO_NAME}.sha256").write_text(f"{iso_sha}  {ISO_NAME}\n")
    (out / f"{MANIFEST_NAME}.sha256").write_text(
        f"{manifest_sha}  {MANIFEST_NAME}\n"
    )
    (out / "SHA256SUMS").write_text(
        f"{iso_sha}  {ISO_NAME}\n{manifest_sha}  {MANIFEST_NAME}\n"
    )
    return iso, iso_blob


def test_embedded_iso_reader_rejects_late_same_inode_rewrite(tmp_path):
    out = tmp_path / "dist"
    out.mkdir()
    iso, original = _complete_iso_bundle(out)
    hook_dir = tmp_path / "hook"
    hook_dir.mkdir()
    (hook_dir / "sitecustomize.py").write_text(
        """import inspect
import os

_real_lstat = os.lstat
_target = os.environ["BEAMO_MUTATE_PATH"]
_calls = 0

def _lstat(path, *args, **kwargs):
    global _calls
    caller = inspect.currentframe().f_back.f_code.co_name
    if os.fspath(path) == _target and caller == "read_regular":
        _calls += 1
        if _calls == 2:
            before = _real_lstat(path)
            with open(path, "r+b") as stream:
                stream.write(b"Z" * before.st_size)
                stream.flush()
                os.fsync(stream.fileno())
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    return _real_lstat(path, *args, **kwargs)

os.lstat = _lstat
"""
    )
    source = (ROOT / "scripts/build-iso.sh").read_text()
    helper = "verify_prior_bundle() {" + source.split(
        "verify_prior_bundle() {", 1
    )[1].split("\ncleanup() {", 1)[0]
    script = "#!/bin/sh\nset -eu\nVERSION=0.2.9\n" + helper
    script += '\nverify_prior_bundle "$1"\n'
    result = subprocess.run(
        ["sh", "-c", script, "verify", str(out)],
        env={
            **os.environ,
            "PYTHONPATH": str(hook_dir),
            "BEAMO_MUTATE_PATH": str(iso),
        },
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert "Unverified prior ISO bundle" in result.stderr
    assert iso.read_bytes() == b"Z" * len(original)
