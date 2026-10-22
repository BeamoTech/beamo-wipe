"""PASS23 regressions for final GitHub draft promotion."""

from __future__ import annotations

import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "verify_github_release_assets_pass23",
        ROOT / "scripts" / "verify_github_release_assets.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(path: Path) -> dict[str, object]:
    blob = path.read_bytes()
    return {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


def release_for(path: Path) -> dict[str, object]:
    item = record(path)
    return {
        "id": 123,
        "tag_name": "v0.2.13",
        "name": "Beamo Wipe 0.2.13",
        "body": "qualified release notes\n",
        "draft": True,
        "prerelease": False,
        "assets": [
            {
                "name": path.name,
                "size": item["bytes"],
                "digest": "sha256:" + str(item["sha256"]),
            }
        ],
    }


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("id", True),
        ("tag_name", "v0.2.12"),
        ("name", "Altered title"),
        ("body", "altered release notes\n"),
        ("prerelease", True),
    ],
)
def test_asset_verification_binds_release_metadata(tmp_path, field, replacement):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")
    remote = release_for(asset)
    remote[field] = replacement

    assert not checker.verified(
        remote,
        [asset],
        {asset.name: record(asset)},
        expected_tag="v0.2.13",
        expected_title="Beamo Wipe 0.2.13",
        expected_body="qualified release notes\n",
    )


def test_asset_verification_accepts_exact_release_metadata(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    assert checker.verified(
        release_for(asset),
        [asset],
        {asset.name: record(asset)},
        expected_tag="v0.2.13",
        expected_title="Beamo Wipe 0.2.13",
        expected_body="qualified release notes\n",
    )


def test_legacy_asset_digest_verification_positive_control(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    assert checker.verified(release_for(asset), [asset], {asset.name: record(asset)})


def test_remote_release_stdin_rejects_duplicate_fields(monkeypatch):
    checker = load_checker()
    raw = b'{"draft":true,"draft":false}'
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(raw)))

    with pytest.raises(RuntimeError, match="duplicate JSON field"):
        checker._remote_release("-")


def test_remote_release_stdin_is_bounded(monkeypatch):
    checker = load_checker()
    raw = b" " * (checker.MAX_REMOTE_RELEASE_BYTES + 1)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(raw)))

    with pytest.raises(RuntimeError, match="exceeds the safety limit"):
        checker._remote_release("-")


def test_release_notes_come_from_exact_commit(tmp_path, monkeypatch):
    checker = load_checker()
    repo = tmp_path / "repo"
    notes = repo / "docs" / "release-0.2.13.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("qualified committed notes\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", str(notes.relative_to(repo))], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Pass23",
            "-c",
            "user.email=pass23@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    notes.write_text("uncommitted replacement\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", repo)

    assert (
        checker._committed_release_notes("0.2.13", commit)
        == "qualified committed notes\n"
    )


def publisher_script() -> str:
    return (ROOT / "scripts" / "publish-release-blacksmith.sh").read_text(
        encoding="utf-8"
    )


def test_publisher_normalizes_reused_draft_metadata():
    script = publisher_script()

    assert "--draft=true" in script
    assert "--prerelease=false" in script
    assert '--title "$title" --notes-file "$notes_file"' in script


def test_publisher_streams_bounded_remote_record():
    script = publisher_script()

    assert "scripts/verify_github_release_assets.py" in script
    assert '- "${assets[@]}"' in script
    assert "github-release.json" not in script


def test_publisher_rechecks_remote_tag_before_promotion():
    script = publisher_script()

    assert '"repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha' in script
    assert '[[ "$remote_tag_sha" == "$GITHUB_SHA" ]]' in script


def test_publisher_promotes_only_verified_numeric_release_id():
    script = publisher_script()

    assert 'verified_release_id="$(' in script
    assert '[[ "$verified_release_id" =~ ^[1-9][0-9]*$ ]]' in script
    assert '"repos/$GITHUB_REPOSITORY/releases/$verified_release_id"' in script
    assert "-F draft=false -f make_latest=true" in script
    assert '[[ "$promoted_release_id" == "$verified_release_id" ]]' in script
    assert script.index('"repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha') < (
        script.index("-F draft=false -f make_latest=true")
    )
