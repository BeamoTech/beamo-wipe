"""The generator must publish against the checksum list it actually verified."""

import hashlib
import json
from pathlib import Path
import stat
import sys

import pytest

from beamo_wipe import __version__, ci_evidence, release_manifest as rm


pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="release publication requires Linux renameat2"
)
ROOT = Path(__file__).resolve().parents[1]
FOREIGN = b"unrelated owner bytes must survive\n"


def _manifest(iso_name, iso_bytes, generation):
    data = {
        "schema_version": rm.SCHEMA_VERSION,
        "beamo_wipe_version": __version__,
        "artifact": {
            "iso_name": iso_name,
            "iso_path": iso_name,
            "iso_sha256": hashlib.sha256(iso_bytes).hexdigest(),
            "iso_size_bytes": len(iso_bytes),
        },
        "fixture_generation": generation,
    }
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    data["_manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return data


def _fixture(tmp_path, monkeypatch, *, prior=False, build_only=True):
    dist = tmp_path / "dist"
    evidence = dist / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "packages.json").write_text("{}")
    iso_name = f"beamo-wipe-{__version__}-amd64.iso"
    iso_bytes = b"ordinary file fixture, never a disk image"
    (dist / iso_name).write_bytes(iso_bytes)
    output = dist / rm.MANIFEST_NAME_TEMPLATE.format(version=__version__)
    sums = dist / "SHA256SUMS"
    monkeypatch.setattr(rm, "ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setenv("ALLOW_DIRTY", "1")
    monkeypatch.setenv("BEAMO_BUILD_PROVENANCE_ONLY", "1" if build_only else "0")
    monkeypatch.setenv("BEAMO_WIPE_MANIFEST_VERSION", __version__)
    monkeypatch.setenv("BEAMO_WIPE_MANIFEST_DEST", str(output))
    if prior:
        rm.write_manifest(_manifest(iso_name, iso_bytes, "old"), output)
        sums.write_bytes(
            rm._sidecar_blob(hashlib.sha256(iso_bytes).hexdigest(), iso_name)
            + rm._sidecar_blob(hashlib.sha256(output.read_bytes()).hexdigest(), output.name)
        )
    current = _manifest(iso_name, iso_bytes, "new")

    def generate(**kwargs):
        assert kwargs["build_only"] is build_only
        assert kwargs["strict"] is False
        if not build_only:
            assert kwargs["gate_receipts"] == []
            assert kwargs["package_inventory"] == {}
        return current

    def verify(path, *, allow_dirty):
        assert allow_dirty is True
        raw = path.read_bytes()
        assert json.loads(raw) == current
        return raw

    def wrong_verifier(*_args, **_kwargs):
        raise AssertionError("build-only and release verification were conflated")

    monkeypatch.setattr(rm, "generate_manifest", generate)
    monkeypatch.setattr(ci_evidence, "load_receipts", lambda _path: [])
    monkeypatch.setattr(rm, "verify_build_manifest", verify if build_only else wrong_verifier)
    monkeypatch.setattr(rm, "verify_manifest", wrong_verifier if build_only else verify)
    return output, sums


def _run_generator_python():
    # Execute the real transaction, without a shell/build or real release inputs.
    script = (ROOT / "scripts/generate-release-manifest.sh").read_text()
    source = script.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    exec(compile(source, "generate-release-manifest.sh:Python", "exec"), {})  # noqa: S102 - checked-in transaction, owned fixtures


def _plant_foreign(sums, kind):
    # Only these fresh tmp_path fixture entries are replaced by the test.
    if sums.exists() or sums.is_symlink():
        sums.unlink()
    if kind == "regular":
        sums.write_bytes(FOREIGN)
    elif kind == "directory":
        sums.mkdir()
        (sums / "owner-notes").write_bytes(FOREIGN)
    else:
        outside = sums.parent / "owner-notes"
        outside.write_bytes(FOREIGN)
        sums.symlink_to(outside)
    metadata = sums.lstat()
    return metadata.st_dev, metadata.st_ino


def _assert_foreign_retained(sums, kind, identity):
    expected_mode = {
        "regular": stat.S_IFREG, "directory": stat.S_IFDIR, "symlink": stat.S_IFLNK
    }[kind]
    metadata = sums.lstat()
    assert stat.S_IFMT(metadata.st_mode) == expected_mode
    assert (metadata.st_dev, metadata.st_ino) == identity
    if kind == "symlink":
        assert sums.readlink() == sums.parent / "owner-notes"
    contents = sums / "owner-notes" if kind == "directory" else sums
    assert contents.read_bytes() == FOREIGN


@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("build_only", [False, True])
def test_checksum_publication_accepts_absence_and_verified_rerun(
    tmp_path, monkeypatch, prior, build_only
):
    output, sums = _fixture(tmp_path, monkeypatch, prior=prior, build_only=build_only)
    _run_generator_python()
    iso_name = f"beamo-wipe-{__version__}-amd64.iso"
    assert sums.read_bytes() == (
        rm._sidecar_blob(rm.sha256_file(sums.parent / iso_name), iso_name)
        + rm._sidecar_blob(hashlib.sha256(output.read_bytes()).hexdigest(), output.name)
    )


@pytest.mark.parametrize("kind", ["regular", "symlink", "directory"])
def test_checksum_publication_refuses_unknown_prior_before_manifest_write(
    tmp_path, monkeypatch, kind
):
    output, sums = _fixture(tmp_path, monkeypatch, prior=True)
    previous = output.read_bytes()
    identity = _plant_foreign(sums, kind)
    with pytest.raises(RuntimeError, match="^unverified prior checksum list$"):
        _run_generator_python()
    assert output.read_bytes() == previous
    _assert_foreign_retained(sums, kind, identity)


@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("boundary", ["after-preflight", "after-final-check"])
@pytest.mark.parametrize("kind", ["regular", "symlink", "directory"])
def test_checksum_publication_retains_concurrent_foreign_entry(
    tmp_path, monkeypatch, prior, boundary, kind
):
    _output, sums = _fixture(tmp_path, monkeypatch, prior=prior)
    injected = False
    identity = None
    original_write = rm.write_manifest
    original_rename = rm._renameat2

    def write(manifest, dest):
        nonlocal injected, identity
        if boundary == "after-preflight":
            identity = _plant_foreign(sums, kind)
            injected = True
        return original_write(manifest, dest)

    def rename(source_fd, source, dest_fd, destination, flags):
        nonlocal injected, identity
        if destination == "SHA256SUMS" and not injected:
            # _atomic_write has completed its last pre-rename stage check.
            identity = _plant_foreign(sums, kind)
            injected = True
        return original_rename(source_fd, source, dest_fd, destination, flags)

    monkeypatch.setattr(rm, "write_manifest", write)
    monkeypatch.setattr(rm, "_renameat2", rename)
    error_type = RuntimeError if prior else FileExistsError
    with pytest.raises(error_type):
        _run_generator_python()
    assert injected
    assert identity is not None
    _assert_foreign_retained(sums, kind, identity)


def test_checksum_publication_preserves_manifest_verification_failure(tmp_path, monkeypatch):
    _output, sums = _fixture(tmp_path, monkeypatch, prior=True)
    previous = sums.read_bytes()
    primary = RuntimeError("fixture manifest verification failure")

    def refuse(*_args, **_kwargs):
        raise primary

    monkeypatch.setattr(rm, "verify_build_manifest", refuse)
    with pytest.raises(RuntimeError, match="^fixture manifest verification failure$") as caught:
        _run_generator_python()
    assert caught.value is primary
    assert sums.read_bytes() == previous


def test_checksum_publication_hashes_the_exact_verified_manifest_bytes(tmp_path, monkeypatch):
    output, sums = _fixture(tmp_path, monkeypatch)
    original_verify = rm.verify_build_manifest
    accepted = None

    def verify_then_replace(path, **kwargs):
        nonlocal accepted
        accepted = original_verify(path, **kwargs)
        path.write_bytes(b"concurrent unverified manifest bytes")
        return accepted

    monkeypatch.setattr(rm, "verify_build_manifest", verify_then_replace)
    _run_generator_python()
    assert accepted is not None
    assert sums.read_bytes().splitlines()[1] == (
        f"{hashlib.sha256(accepted).hexdigest()}  {output.name}".encode("ascii")
    )
