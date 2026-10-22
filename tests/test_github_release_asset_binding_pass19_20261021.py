"""PASS19 regressions for authenticated GitHub release-asset verification."""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from beamo_wipe.release_signing import (
    fingerprint,
    generate_keypair,
    key_id,
    sign_manifest_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "verify_github_release_assets_pass19",
        ROOT / "scripts" / "verify_github_release_assets.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(path: Path) -> dict[str, object]:
    blob = path.read_bytes()
    return {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


def remote_for(path: Path, *, size: object | None = None) -> dict[str, object]:
    item = record(path)
    return {
        "draft": True,
        "assets": [
            {
                "name": path.name,
                "size": item["bytes"] if size is None else size,
                "digest": "sha256:" + str(item["sha256"]),
            }
        ],
    }


def test_verified_requires_every_asset_to_be_in_authenticated_inventory(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    assert not checker.verified(remote_for(asset), [asset], {})


def test_verified_rejects_symlink_asset_leaf(tmp_path):
    checker = load_checker()
    target = tmp_path / "target.iso"
    target.write_bytes(b"qualified release bytes")
    asset = tmp_path / "release.iso"
    asset.symlink_to(target)

    assert not checker.verified(remote_for(asset), [asset], {asset.name: record(asset)})


def test_verified_rejects_symlinked_asset_parent(tmp_path):
    checker = load_checker()
    real = tmp_path / "real"
    real.mkdir()
    (real / "release.iso").write_bytes(b"qualified release bytes")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    asset = alias / "release.iso"

    assert not checker.verified(remote_for(asset), [asset], {asset.name: record(asset)})


def test_verified_rejects_same_byte_path_replacement_after_hash(tmp_path, monkeypatch):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")
    release = remote_for(asset)
    signed = {asset.name: record(asset)}

    real_sha256 = hashlib.sha256
    replaced = False

    class ReplacingHash:
        def __init__(self, *args, **kwargs):
            self.inner = real_sha256(*args, **kwargs)

        def update(self, blob):
            return self.inner.update(blob)

        def hexdigest(self):
            nonlocal replaced
            if not replaced:
                replacement = asset.with_suffix(".replacement")
                replacement.write_bytes(asset.read_bytes())
                os.replace(replacement, asset)
                replaced = True
            return self.inner.hexdigest()

    monkeypatch.setattr(hashlib, "sha256", ReplacingHash)
    assert not checker.verified(release, [asset], signed)
    assert replaced


def test_verified_rejects_boolean_remote_size(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"x")

    assert not checker.verified(
        remote_for(asset, size=True), [asset], {asset.name: record(asset)}
    )


def test_verified_rejects_boolean_authenticated_size(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"x")
    signed = {asset.name: {"sha256": record(asset)["sha256"], "bytes": True}}

    assert not checker.verified(remote_for(asset), [asset], signed)


def test_verified_returns_false_for_malformed_asset_record(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")
    release = {"draft": True, "assets": [None]}

    assert not checker.verified(release, [asset], {asset.name: record(asset)})


def test_verified_accepts_bound_regular_assets(tmp_path):
    checker = load_checker()
    first = tmp_path / "release.iso"
    second = tmp_path / "release.img.gz"
    first.write_bytes(b"qualified ISO")
    second.write_bytes(b"qualified compressed image")
    paths = [first, second]
    release = {
        "draft": True,
        "assets": [remote_for(path)["assets"][0] for path in paths],
    }
    signed = {path.name: record(path) for path in paths}

    assert checker.verified(release, paths, signed)


def test_verified_allows_only_explicit_inventory_bootstrap_assets(tmp_path):
    checker = load_checker()
    inventory = tmp_path / "release-downloads.json"
    signature = tmp_path / "release-downloads.json.sig"
    inventory.write_bytes(b"signed inventory bytes")
    signature.write_bytes(b"detached signature bytes")
    paths = [inventory, signature]
    release = {
        "draft": True,
        "assets": [remote_for(path)["assets"][0] for path in paths],
    }

    assert checker.verified(
        release,
        paths,
        {},
        bootstrap_names=frozenset(path.name for path in paths),
    )
    assert not checker.verified(
        release,
        paths,
        {},
        bootstrap_names=frozenset({inventory.name}),
    )
    unrelated = tmp_path / "unrelated.bin"
    unrelated.write_bytes(b"other bytes")
    assert not checker.verified(
        remote_for(unrelated),
        [unrelated],
        {},
        bootstrap_names=frozenset({unrelated.name}),
    )


def test_main_verifies_real_signature_and_exact_uploaded_bytes(
    tmp_path, monkeypatch, capsys
):
    checker = load_checker()
    root = tmp_path / "source"
    stage = tmp_path / "stage"
    (root / "packaging/release-keys").mkdir(parents=True)
    stage.mkdir()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    private, public = generate_keypair()
    registry = {
        "schema": "beamo-wipe-release-keys/1",
        "keys": {
            key_id(public): {
                "public_key": base64.b64encode(public).decode("ascii"),
                "fingerprint": fingerprint(public),
                "status": "active",
            }
        },
    }
    (root / "packaging/release-keys/keys.json").write_text(json.dumps(registry))
    inventory_path = stage / "release-downloads.json"
    signature_path = stage / "release-downloads.json.sig"
    inventory_bytes = json.dumps(
        {
            "schema": "beamo-wipe-release-downloads/1",
            "files": {asset.name: record(asset)},
        }
    ).encode()
    inventory_path.write_bytes(inventory_bytes)
    signature_path.write_text(json.dumps(sign_manifest_bytes(inventory_bytes, private)))
    paths = [asset, inventory_path, signature_path]
    release_path = stage / "github-release.json"
    release_path.write_text(
        json.dumps(
            {
                "id": 123,
                "draft": True,
                "prerelease": False,
                "tag_name": "v0.2.13",
                "name": "Beamo Wipe 0.2.13",
                "body": "qualified notes\n",
                "assets": [remote_for(path)["assets"][0] for path in paths],
            }
        )
    )
    monkeypatch.setattr(checker, "ROOT", root)
    monkeypatch.setattr(
        checker,
        "_committed_release_notes",
        lambda _version, _commit: "qualified notes\n",
    )
    monkeypatch.setenv("BEAMO_WIPE_VERSION", "0.2.13")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)

    argv = ["verify_github_release_assets.py", str(release_path), *map(str, paths)]
    assert checker.main(argv) == 0
    assert capsys.readouterr().out == "123\n"
    shadow_inventory = tmp_path / inventory_path.name
    shadow_inventory.write_bytes(inventory_bytes)
    assert checker.main([*argv[:3], str(shadow_inventory), *argv[4:]]) == 2
    release = json.loads(release_path.read_text())
    release["assets"][0]["digest"] = "sha256:" + "0" * 64
    release_path.write_text(json.dumps(release))
    assert checker.main(argv) == 2
