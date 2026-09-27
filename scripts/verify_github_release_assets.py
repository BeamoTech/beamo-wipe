#!/usr/bin/env python3
"""Check every draft GitHub release asset against the local uploaded bytes."""
import hashlib
import json
from pathlib import Path
import sys


def verified(remote: dict, paths: list[Path], signed_files: dict | None = None) -> bool:
    assets = remote.get("assets")
    if not isinstance(assets, list):
        return False
    expected = {p.name: p for p in paths}
    if len(expected) != len(paths) or not remote.get("draft"):
        return False
    if len(assets) != len(expected) or {a.get("name") for a in assets} != set(expected):
        return False
    for asset in assets:
        path = expected[asset["name"]]
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                h.update(chunk)
        local = h.hexdigest()
        if asset.get("digest") != "sha256:" + local or asset.get("size") != path.stat().st_size:
            return False
        if signed_files is not None and asset["name"] in signed_files:
            record = signed_files[asset["name"]]
            if record != {"sha256": local, "bytes": path.stat().st_size}:
                return False
    return True


if __name__ == "__main__":
    release = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    stage = Path(sys.argv[1]).parent
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    from beamo_wipe.release_signing import load_key_registry, verify_with_registry

    inventory_bytes = (stage / "release-downloads.json").read_bytes()
    signature = json.loads((stage / "release-downloads.json.sig").read_text())
    registry = load_key_registry(json.loads((root / "packaging/release-keys/keys.json").read_text()))
    verify_with_registry(inventory_bytes, signature, registry)
    signed_files = json.loads(inventory_bytes)["files"]
    if not verified(release, [Path(p) for p in sys.argv[2:]], signed_files):
        raise SystemExit(2)
