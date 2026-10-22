#!/usr/bin/env python3
"""Check every draft GitHub release asset against authenticated local bytes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beamo_wipe.release_manifest import (  # noqa: E402
    _hash_regular_snapshot,
    _require_regular_binding,
)
from beamo_wipe.release_signing import (  # noqa: E402
    _read_bytes_file,
    _read_json_file,
    _unique_json_fields,
    load_key_registry,
    verify_with_registry,
)

SHA256_RE = re.compile(r"[0-9a-f]{64}")
BOOTSTRAP_ASSETS = frozenset({"release-downloads.json", "release-downloads.json.sig"})
MAX_REMOTE_RELEASE_BYTES = 1024 * 1024
MAX_RELEASE_NOTES_BYTES = 1024 * 1024


def _signed_record(value: object) -> tuple[str, int] | None:
    if not isinstance(value, dict) or set(value) != {"sha256", "bytes"}:
        return None
    digest = value.get("sha256")
    size = value.get("bytes")
    if (
        not isinstance(digest, str)
        or not SHA256_RE.fullmatch(digest)
        or type(size) is not int
        or size < 0
    ):
        return None
    return digest, size


def verified(
    remote: object,
    paths: list[Path],
    signed_files: dict | None = None,
    *,
    bootstrap_names: frozenset[str] = frozenset(),
    expected_tag: str | None = None,
    expected_title: str | None = None,
    expected_body: str | None = None,
    expected_draft: bool = True,
) -> bool:
    """Bind draft records, uploaded bytes, and the signed file inventory.

    The signed inventory and its detached signature cannot recursively list
    themselves.  The caller may exempt only those two explicit bootstrap
    names; every other asset must have an exact authenticated record.
    """
    metadata_expectations = (expected_tag, expected_title, expected_body)
    if (
        not isinstance(remote, dict)
        or (
            any(value is not None for value in metadata_expectations)
            and not all(isinstance(value, str) for value in metadata_expectations)
        )
        or type(expected_draft) is not bool
    ):
        return False
    assets = remote.get("assets")
    if not isinstance(assets, list):
        return False
    expected = {p.name: p for p in paths}
    if (
        len(expected) != len(paths)
        or remote.get("draft") is not expected_draft
        or not isinstance(bootstrap_names, frozenset)
        or not all(isinstance(name, str) for name in bootstrap_names)
        or not bootstrap_names.issubset(BOOTSTRAP_ASSETS)
        or not bootstrap_names.issubset(expected)
        or (bootstrap_names and signed_files is None)
        or (signed_files is not None and not isinstance(signed_files, dict))
    ):
        return False
    if expected_tag is not None and (
        type(remote.get("id")) is not int
        or remote["id"] <= 0
        or remote.get("tag_name") != expected_tag
        or remote.get("name") != expected_title
        or remote.get("body") != expected_body
        or remote.get("prerelease") is not False
    ):
        return False
    if len(assets) != len(expected):
        return False
    remote_by_name: dict[str, dict] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            return False
        name = asset.get("name")
        size = asset.get("size")
        digest = asset.get("digest")
        if (
            not isinstance(name, str)
            or name not in expected
            or name in remote_by_name
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
        ):
            return False
        remote_by_name[name] = asset
    if set(remote_by_name) != set(expected):
        return False

    bindings = []
    try:
        for name, path in expected.items():
            local, size, binding = _hash_regular_snapshot(path)
            asset = remote_by_name[name]
            if asset["digest"] != "sha256:" + local or asset["size"] != size:
                return False
            if signed_files is not None and name not in bootstrap_names:
                record = _signed_record(signed_files.get(name))
                if record != (local, size):
                    return False
            bindings.append(binding)
        for binding in bindings:
            _require_regular_binding(binding)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _remote_release(value: str) -> object:
    """Read one bounded, duplicate-free GitHub API response."""
    if value != "-":
        return _read_json_file(Path(value), what="GitHub draft record")
    raw = sys.stdin.buffer.read(MAX_REMOTE_RELEASE_BYTES + 1)
    if len(raw) > MAX_REMOTE_RELEASE_BYTES:
        raise RuntimeError("GitHub draft record exceeds the safety limit")

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_fields,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("GitHub draft record is not JSON") from exc


def _committed_release_notes(version: str, commit: str) -> str:
    """Read release notes from the exact qualified commit, not the worktree."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(
        r"[0-9a-f]{40}", commit
    ):
        raise RuntimeError("invalid qualified release identity")
    relative = f"docs/release-{version}.md"
    object_name = f"{commit}:{relative}"
    try:
        size_result = subprocess.run(
            ["git", "cat-file", "-s", object_name],
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=30,
        )
        size_text = size_result.stdout.strip()
        if not re.fullmatch(rb"[0-9]+", size_text):
            raise RuntimeError("committed release notes size is invalid")
        size = int(size_text)
        if size <= 0 or size > MAX_RELEASE_NOTES_BYTES:
            raise RuntimeError("committed release notes exceed the safety limit")
        notes_result = subprocess.run(
            ["git", "show", object_name],
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("committed release notes cannot be read") from exc
    if len(notes_result.stdout) != size:
        raise RuntimeError("committed release notes changed while being read")
    try:
        return notes_result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("committed release notes are not UTF-8") from exc


def _expected_draft() -> bool:
    """Return the one explicitly requested GitHub release state."""
    value = os.environ.get("BEAMO_GITHUB_RELEASE_DRAFT", "true")
    if value == "true":
        return True
    if value == "false":
        return False
    raise RuntimeError("invalid expected GitHub release state")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        return 2
    release_source = argv[1]
    upload_paths = [Path(p) for p in argv[2:]]
    inventory_paths = [
        path for path in upload_paths if path.name == "release-downloads.json"
    ]
    signature_paths = [
        path for path in upload_paths if path.name == "release-downloads.json.sig"
    ]
    if len(inventory_paths) != 1 or len(signature_paths) != 1:
        return 2
    inventory_path = inventory_paths[0]
    signature_path = signature_paths[0]
    if inventory_path.parent != signature_path.parent:
        return 2
    normalized_uploads = {
        path.name: Path(os.path.abspath(os.fspath(path))) for path in upload_paths
    }
    normalized_bootstrap = {
        path.name: Path(os.path.abspath(os.fspath(path)))
        for path in (inventory_path, signature_path)
    }
    if any(
        normalized_uploads.get(name) != path
        for name, path in normalized_bootstrap.items()
    ):
        return 2
    version = os.environ.get("BEAMO_WIPE_VERSION", "")
    commit = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(
        r"[0-9a-f]{40}", commit
    ):
        return 2
    release = _remote_release(release_source)
    expected_body = _committed_release_notes(version, commit)
    expected_draft = _expected_draft()
    inventory_bytes = _read_bytes_file(
        inventory_path, what="signed release download inventory"
    )
    signature = _read_json_file(signature_path, what="release inventory signature")
    registry = load_key_registry(
        _read_json_file(
            ROOT / "packaging/release-keys/keys.json",
            what="release key registry",
        )
    )
    verify_with_registry(inventory_bytes, signature, registry)
    try:
        inventory = json.loads(
            inventory_bytes.decode("utf-8"), object_pairs_hook=_unique_json_fields
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("signed release download inventory is not JSON") from exc
    if (
        not isinstance(inventory, dict)
        or inventory.get("schema") != "beamo-wipe-release-downloads/1"
        or not isinstance(inventory.get("files"), dict)
    ):
        raise RuntimeError(
            "signed release download inventory has invalid schema or files"
        )
    if not verified(
        release,
        upload_paths,
        inventory["files"],
        bootstrap_names=BOOTSTRAP_ASSETS,
        expected_tag=f"v{version}",
        expected_title=f"Beamo Wipe {version}",
        expected_body=expected_body,
        expected_draft=expected_draft,
    ):
        return 2
    if not isinstance(release, dict) or type(release.get("id")) is not int:
        return 2
    print(release["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
