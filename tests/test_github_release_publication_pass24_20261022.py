"""PASS24 regressions for authenticated GitHub publication state."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "verify_github_release_assets_pass24",
        ROOT / "scripts" / "verify_github_release_assets.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(path: Path) -> dict[str, object]:
    blob = path.read_bytes()
    return {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


def release_for(path: Path, *, draft: bool) -> dict[str, object]:
    item = record(path)
    return {
        "id": 123,
        "tag_name": "v0.2.13",
        "name": "Beamo Wipe 0.2.13",
        "body": "qualified release notes\n",
        "draft": draft,
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
    ("remote_draft", "expected_draft", "accepted"),
    [
        (False, False, True),
        (True, False, False),
        (False, True, False),
    ],
)
def test_verifier_authenticates_requested_publication_state(
    tmp_path, remote_draft, expected_draft, accepted
):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    assert (
        checker.verified(
            release_for(asset, draft=remote_draft),
            [asset],
            {asset.name: record(asset)},
            expected_tag="v0.2.13",
            expected_title="Beamo Wipe 0.2.13",
            expected_body="qualified release notes\n",
            expected_draft=expected_draft,
        )
        is accepted
    )


def test_legacy_draft_verification_positive_control(tmp_path):
    checker = load_checker()
    asset = tmp_path / "release.iso"
    asset.write_bytes(b"qualified release bytes")

    assert checker.verified(
        release_for(asset, draft=True),
        [asset],
        {asset.name: record(asset)},
        expected_tag="v0.2.13",
        expected_title="Beamo Wipe 0.2.13",
        expected_body="qualified release notes\n",
    )


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("false", False)])
def test_expected_draft_parser_accepts_only_canonical_values(
    monkeypatch, value, expected
):
    checker = load_checker()
    monkeypatch.setenv("BEAMO_GITHUB_RELEASE_DRAFT", value)

    assert checker._expected_draft() is expected


@pytest.mark.parametrize("value", ["", "TRUE", "0"])
def test_expected_draft_parser_rejects_ambiguous_values(monkeypatch, value):
    checker = load_checker()
    monkeypatch.setenv("BEAMO_GITHUB_RELEASE_DRAFT", value)

    with pytest.raises(RuntimeError, match="expected GitHub release state"):
        checker._expected_draft()


def publisher_script() -> str:
    return (ROOT / "scripts" / "publish-release-blacksmith.sh").read_text(
        encoding="utf-8"
    )


def test_publisher_authenticates_complete_public_patch_response():
    script = publisher_script()

    assert "-F draft=false -f make_latest=true" in script
    assert "BEAMO_GITHUB_RELEASE_DRAFT=false" in script
    assert "scripts/verify_github_release_assets.py" in script
    assert "-F draft=false -f make_latest=true --jq .id" not in script


def test_publisher_rechecks_tag_after_authenticated_publication():
    script = publisher_script()
    tag_lookup = '"repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha'
    publication = '"repos/$GITHUB_REPOSITORY/releases/$verified_release_id"'

    assert script.count(tag_lookup) >= 2
    assert script.index(publication) < script.rindex(tag_lookup)


def test_publisher_restores_and_authenticates_exact_draft_on_failure():
    script = publisher_script()

    assert "restore_verified_draft()" in script
    assert '"repos/$GITHUB_REPOSITORY/releases/$verified_release_id"' in script
    assert "-F draft=true" in script
    assert "BEAMO_GITHUB_RELEASE_DRAFT=true" in script
    assert '[[ "$restored_release_id" == "$verified_release_id" ]]' in script
    assert "Failed to restore the verified GitHub release draft" in script
