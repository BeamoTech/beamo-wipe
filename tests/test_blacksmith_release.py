"""Focused release packaging checks; no real key, cloud object or ISO needed."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from beamo_wipe.release_signing import (
    fingerprint, generate_keypair, key_id, load_key_registry,
    sign_manifest_bytes, verify_with_registry,
)

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def test_blacksmith_workload_token_refresh_is_validated(monkeypatch):
    publisher = load_script("publish_release_gcs")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/gha-creds.json")
    monkeypatch.setenv("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", "/tmp/gha-creds.json")

    class Result:
        stdout = "x" * 32 + "\n"

    called = []

    def run(argv, **kw):
        called.append((argv, kw))
        return Result()

    monkeypatch.setattr(publisher.subprocess, "run", run)
    assert publisher._metadata_token() == "x" * 32
    assert called[0][0] == ["gcloud", "auth", "print-access-token"]
    Result.stdout = "bad token with spaces"
    with pytest.raises(publisher.PublishError, match="invalid token"):
        publisher._metadata_token()
    monkeypatch.setenv("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", "/tmp/other.json")
    with pytest.raises(publisher.PublishError, match="not selected"):
        publisher._metadata_token()


def test_public_release_asset_digest_check_rejects_missing_and_altered(tmp_path):
    checker = load_script("verify_github_release_assets")
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b"first")
    b.write_bytes(b"second")
    release = {"draft": True, "assets": [
        {"name": p.name, "size": p.stat().st_size, "digest": "sha256:" + sha(p.read_bytes())}
        for p in (a, b)
    ]}
    assert checker.verified(release, [a, b])
    assert not checker.verified(release, [a, b], {"a": {"sha256": "0" * 64, "bytes": 5}})
    b.write_bytes(b"changed")
    assert not checker.verified(release, [a, b])
    b.write_bytes(b"second")
    assert not checker.verified({**release, "draft": False}, [a, b])
    assert not checker.verified({**release, "assets": release["assets"][:1]}, [a, b])


@pytest.mark.parametrize("release_id,expected_code", [("397823407", 0), ("null", 2), ("0", 2), ("42/extra", 2)])
def test_draft_release_lookup_uses_numeric_id(tmp_path, monkeypatch, release_id, expected_code):
    fake_gh = tmp_path / "gh"
    fake_gh.write_text("""#!/usr/bin/env python3
import json, os, sys
with open(os.environ['FAKE_GH_CALLS'], 'a') as calls:
    calls.write(json.dumps(sys.argv[1:]) + '\\n')
if sys.argv[1:3] == ['release', 'view']:
    print(os.environ['FAKE_GH_RELEASE_ID'])
elif sys.argv[1] == 'api':
    print('{"draft": true}')
else:
    sys.exit(3)
""")
    fake_gh.chmod(0o755)
    calls = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_CALLS", str(calls))
    monkeypatch.setenv("FAKE_GH_RELEASE_ID", release_id)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/fetch_github_draft_release.sh"),
         "BeamoTech/beamo-wipe", "v0.2.11"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == expected_code
    invoked = [json.loads(line) for line in calls.read_text().splitlines()]
    assert invoked[0] == ["release", "view", "v0.2.11", "--repo", "BeamoTech/beamo-wipe",
                          "--json", "databaseId", "--jq", ".databaseId"]
    if expected_code == 0:
        assert invoked[1] == ["api", f"repos/BeamoTech/beamo-wipe/releases/{release_id}"]
        assert len(invoked) == 2
        assert json.loads(result.stdout) == {"draft": True}
    else:
        assert len(invoked) == 1
        assert "no valid GitHub draft ID" in result.stderr


def test_release_download_inventory_is_signed_and_binds_compressed_usb(tmp_path, monkeypatch):
    assembler = load_script("prepare_release_assets")
    private, public_key = generate_keypair()
    registry_data = {"schema": "beamo-wipe-release-keys/1", "keys": {
        key_id(public_key): {
            "public_key": __import__("base64").b64encode(public_key).decode(),
            "fingerprint": fingerprint(public_key), "status": "active",
        }
    }}
    root = tmp_path / "source"
    dist = root / "dist"
    stage = tmp_path / "stage"
    (root / "packaging/release-keys").mkdir(parents=True)
    dist.mkdir()
    stage.mkdir()
    (root / "packaging/release-keys/keys.json").write_text(json.dumps(registry_data))
    monkeypatch.setattr(assembler, "ROOT", root)
    monkeypatch.setattr(assembler, "_read_signing_key", lambda: private)
    version, build_id, commit = "0.2.11", "a" * 8 + "-aaaa-aaaa-aaaa-" + "a" * 12, "b" * 40
    stem = f"beamo-wipe-{version}-amd64"
    iso, raw = b"test ISO", b"USB image contents"
    (dist / f"{stem}.iso").write_bytes(iso)
    (dist / f"{stem}.img").write_bytes(raw)
    manifest = {"beamo_wipe_version": version, "source": {"commit": commit},
                "build": {"release_build_id": build_id},
                "artifact": {"iso_sha256": sha(iso)}, "test_evidence": {"gates": {}}}
    manifest_bytes = json.dumps(manifest).encode()
    (dist / f"{stem}.manifest.json").write_bytes(manifest_bytes)
    (dist / f"{stem}.manifest.json.sig").write_text(json.dumps(sign_manifest_bytes(manifest_bytes, private)))
    monkeypatch.setattr(assembler, "verify_manifest", lambda _path: manifest_bytes)
    (dist / f"{stem}.img.json").write_text(json.dumps({"sha256": sha(raw), "iso_sha256": sha(iso)}))
    for name in (f"{stem}.iso.sha256", f"{stem}.img.sha256",
                 f"{stem}.manifest.json.sha256", "SHA256SUMS"):
        (dist / name).write_text("test\n")
    (stage / f"{stem}.img.gz").write_bytes(gzip.compress(raw, mtime=0))
    compressed = stage / f"{stem}.img.gz"
    (stage / f"{stem}.img.gz.sha256").write_text(f"{sha(compressed.read_bytes())}  {compressed.name}\n")
    (stage / "verification-evidence.tar.gz").write_bytes(b"evidence")
    (stage / "RELEASE_COMPLETE.txt").write_text(
        "\n".join(["release_complete=true", f"build_id={build_id}",
                   f"version={version}", f"source_commit={commit}",
                   f"{sha(iso)}  {stem}.iso", f"{sha(raw)}  {stem}.img",
                   f"{sha(manifest_bytes)}  {stem}.manifest.json",
                   f"{sha((dist / f'{stem}.manifest.json.sig').read_bytes())}  {stem}.manifest.json.sig"]) + "\n"
    )
    assembler.prepare(stage, version, build_id, commit)
    inventory_bytes = (stage / "release-downloads.json").read_bytes()
    signed = json.loads((stage / "release-downloads.json.sig").read_text())
    verify_with_registry(inventory_bytes, signed, load_key_registry(registry_data))
    files = json.loads(inventory_bytes)["files"]
    assert files[f"{stem}.img"]["sha256"] == sha(raw)
    assert files[f"{stem}.img.gz"]["sha256"] == sha(compressed.read_bytes())


@pytest.mark.parametrize("alter_transfer", [False, True])
def test_release_transfer_binds_publisher_to_qualified_bytes(tmp_path, monkeypatch, alter_transfer):
    transfer = load_script("release_transfer")
    root = tmp_path / "source"
    dist = root / "dist"
    evidence = root / "qemu-evidence"
    dist.mkdir(parents=True)
    evidence.mkdir()
    version, build_id, commit = "0.2.11", "a" * 8 + "-aaaa-aaaa-aaaa-" + "a" * 12, "b" * 40
    stem = f"beamo-wipe-{version}-amd64"
    iso, image = dist / f"{stem}.iso", dist / f"{stem}.img"
    iso.write_bytes(b"iso bytes")
    image.write_bytes(b"raw USB bytes")
    sidecar = dist / f"{stem}.img.sha256"
    sidecar.write_text(f"{sha(image.read_bytes())}  {image.name}\n")
    log = evidence / "bios.log"
    log.write_bytes(b"qualified evidence")
    monkeypatch.setattr(transfer, "ROOT", root)
    monkeypatch.setattr(transfer, "identity", lambda: (version, commit, build_id))
    monkeypatch.setattr(transfer, "release_inputs", lambda _version: [iso, image, sidecar, log])
    staged = transfer.pack()
    monkeypatch.setenv("TRANSFER_MANIFEST_SHA256", sha((staged / "transfer-manifest.json").read_bytes()))
    shutil.rmtree(dist)
    shutil.rmtree(evidence)
    if alter_transfer:
        (staged / "dist" / f"{stem}.img.gz").write_bytes(b"tampered")
        with pytest.raises(RuntimeError, match="checksum mismatch"):
            transfer.restore()
    else:
        transfer.restore()
        assert image.read_bytes() == b"raw USB bytes"
        assert iso.read_bytes() == b"iso bytes"
        assert log.read_bytes() == b"qualified evidence"
