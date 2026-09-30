"""Generated guidance and real detached verification with ephemeral test keys."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex

import pytest

from beamo_wipe import __version__
from beamo_wipe import release_manifest as rm
from beamo_wipe import release_signing as rs


@pytest.fixture
def generated(tmp_path, monkeypatch):
    """Real manifest serialization over a regular file, never a disk/image build."""
    monkeypatch.setattr(rm, "ROOT", tmp_path)
    monkeypatch.setattr(rm, "git_commit", lambda: "a" * 40)
    monkeypatch.setattr(rm, "git_tag_for_commit", lambda _commit: None)
    monkeypatch.setattr(rm, "git_dirty", lambda: (False, []))
    monkeypatch.setattr(rm, "git_remote_url", lambda: rm.EXPECTED_REMOTE)
    monkeypatch.setattr(rm, "_run", lambda *_a: "test-fixture")
    monkeypatch.setattr(rm, "dependency_locks", lambda **_kw: {})
    monkeypatch.setattr(rm, "live_build_inputs", lambda: {"src/beamo_wipe/": "b" * 64})
    monkeypatch.setenv("BUILD_ID", "local")
    monkeypatch.delenv("PROJECT_ID", raising=False)
    (tmp_path / "pyproject.toml").write_text(f'[project]\nversion="{__version__}"\n')
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / f"beamo-wipe-{__version__}-amd64.iso").write_bytes(b"harmless fixture, not a bootable ISO")
    manifest = rm.generate_manifest(strict=False)
    path = rm.write_manifest(manifest, dist / rm.MANIFEST_NAME_TEMPLATE.format(version=__version__))
    return tmp_path, path, manifest


def test_generated_unsigned_and_build_only_guidance(generated):
    _root, path, manifest = generated
    for data in (manifest, rm.generate_manifest(strict=True, build_only=True)):
        info = data["verification"]
        assert "not configured" not in info["signing"]
        assert "Generation alone does not sign" in info["signing"]
        assert "signing is skipped" in info["signing"]
        assert "unauthenticated" in info["signing"]
        assert "runtime safety" in info["signing"]
        assert "no signature is embedded" in info["signing"]
        assert info["signature_file"] == path.name + ".sig"
        assert info["signature_algorithm"] == "Ed25519"
        assert "Obtain" in info["verification_order"][0]
        assert "Authenticate" in info["verification_order"][1]
        assert "Verify the detached signature" in info["verification_order"][2]
        assert "Only after signature verification" in info["verification_order"][3]
        assert "After verifying the detached signature" in info["checksum_instructions"]
        assert "signed" not in data and "signature" not in data
    assert not Path(str(path) + ".sig").exists()
    # Generated build evidence cannot masquerade as qualified release evidence.
    with pytest.raises(RuntimeError):
        rm.verify_manifest(path)


@pytest.fixture
def signed_fixture(generated, monkeypatch):
    pytest.importorskip("cryptography")
    root, path, manifest = generated
    private, public = rs.generate_keypair()  # Kept in memory; never written/logged.
    registry_data = {"schema": rs.KEYS_SCHEMA, "keys": {
        rs.key_id(public): {
            "fingerprint": rs.fingerprint(public),
            "public_key": base64.b64encode(public).decode("ascii"), "status": "active",
        }
    }}
    registry_path = root / "packaging/release-keys/keys.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(json.dumps(registry_data))
    spec = importlib.util.spec_from_file_location(
        "metadata_test_publisher", Path(__file__).resolve().parents[1] / "scripts/publish_release_gcs.py"
    )
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    monkeypatch.setattr(publisher, "ROOT", root)
    monkeypatch.setattr(publisher, "_read_signing_key", lambda: private)
    # Test the real sidecar writer only; publish/upload paths are never called.
    before = path.read_bytes()
    signature_path, digest = publisher._sign_release_manifest(path.parent, __version__)
    assert path.read_bytes() == before
    assert hashlib.sha256(signature_path.read_bytes()).hexdigest() == digest
    return root, path, manifest, signature_path, registry_path


def verify_generated_command(root, manifest):
    command = shlex.split(manifest["verification"]["signature_command"])
    assert command[:4] == ["PYTHONPATH=src", "python3", "-m", "beamo_wipe.release_signing"]
    args = command[4:]
    for option in ("--manifest", "--signature", "--registry"):
        i = args.index(option) + 1
        args[i] = str(root / args[i])
    return rs.main(args)


def test_generated_signature_command_verifies_exact_publisher_bytes(signed_fixture):
    root, _path, manifest, _signature_path, _registry_path = signed_fixture
    assert verify_generated_command(root, manifest) == 0


@pytest.mark.parametrize("mutation", ["missing", "invalid", "stale", "tampered", "revoked"])
def test_generated_metadata_never_substitutes_for_signature_verification(signed_fixture, mutation):
    root, path, manifest, signature_path, registry_path = signed_fixture
    signature = json.loads(signature_path.read_text())
    if mutation == "missing":
        signature_path.unlink()
    elif mutation == "invalid":
        blob = bytearray(base64.b64decode(signature["signature"]))
        blob[0] ^= 1
        signature["signature"] = base64.b64encode(blob).decode("ascii")
        signature_path.write_text(json.dumps(signature))
    elif mutation == "stale":
        data = json.loads(path.read_text())
        data["source"]["commit"] = "c" * 40
        path.write_text(json.dumps(data))
    elif mutation == "tampered":
        path.write_bytes(path.read_bytes() + b" ")  # Harmless JSON whitespace.
    else:
        registry = json.loads(registry_path.read_text())
        registry["keys"][signature["key_id"]]["status"] = "revoked"
        registry_path.write_text(json.dumps(registry))
    with pytest.raises(RuntimeError):
        verify_generated_command(root, manifest)


def test_unsigned_generated_command_refuses_missing_sidecar(generated):
    root, _path, manifest = generated
    with pytest.raises(RuntimeError, match="signature sidecar"):
        verify_generated_command(root, manifest)


def test_signing_skipped_publication_leaves_manifest_unauthenticated(generated, monkeypatch):
    _root, path, _manifest = generated
    spec = importlib.util.spec_from_file_location(
        "metadata_skipped_publisher", Path(__file__).resolve().parents[1] / "scripts/publish_release_gcs.py"
    )
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    monkeypatch.setenv("PUBLISH_RELEASE", "false")
    monkeypatch.setattr(publisher, "_read_signing_key", lambda: pytest.fail("must not read a key"))
    before = path.read_bytes()
    assert publisher.publish() is None
    assert path.read_bytes() == before
    assert not Path(str(path) + ".sig").exists()


@pytest.mark.parametrize("name,version", [("../m.json", "1.0.0"), ("m.json", "1.0.0; echo x")])
def test_signature_guidance_refuses_nonliteral_command_inputs(name, version):
    with pytest.raises(ValueError):
        rs.detached_verification_metadata(name, version)
