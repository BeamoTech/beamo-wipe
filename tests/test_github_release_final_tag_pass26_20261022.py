"""PASS26 regressions for the final GitHub release tag binding."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def publisher_script() -> str:
    return (ROOT / "scripts" / "publish-release-blacksmith.sh").read_text(
        encoding="utf-8"
    )


def final_lookup_block(script: str) -> str:
    start = script.index('if ! final_tag_sha="$(')
    end = script.index("\n    fi", start) + len("\n    fi")
    return script[start:end]


def final_mismatch_block(script: str) -> str:
    start = script.index('[[ "$final_tag_sha" == "$GITHUB_SHA" ]]')
    end = script.index("\n    }", start) + len("\n    }")
    return script[start:end]


def test_latest_release_response_remains_fully_authenticated_control():
    script = publisher_script()
    start = script.index('if ! latest_release_id="$(')
    end = script.index('[[ "$latest_release_id" == "$verified_release_id" ]]', start)
    block = script[start:end]

    assert 'gh api "repos/$GITHUB_REPOSITORY/releases/latest"' in block
    assert "BEAMO_GITHUB_RELEASE_DRAFT=false" in block
    assert "scripts/verify_github_release_assets.py" in block


def test_publisher_rechecks_tag_after_latest_release_identity():
    script = publisher_script()
    latest_identity = '[[ "$latest_release_id" == "$verified_release_id" ]]'
    final_lookup = 'if ! final_tag_sha="$('

    assert script.index(latest_identity) < script.index(final_lookup)


def test_final_tag_lookup_uses_exact_release_tag():
    block = final_lookup_block(publisher_script())

    assert (
        'gh api \\\n        "repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha'
    ) in block


def test_final_tag_lookup_failure_restores_verified_draft():
    block = final_lookup_block(publisher_script())

    assert (
        "Remote tag $tag could not be rechecked after latest release verification."
        in block
    )
    assert "restore_verified_draft || true" in block
    assert "exit 2" in block


def test_final_tag_mismatch_restores_verified_draft():
    block = final_mismatch_block(publisher_script())

    assert "Remote tag $tag moved while the latest release was verified" in block
    assert "restore_verified_draft || true" in block
    assert "exit 2" in block


def test_success_is_reported_only_after_final_tag_binding():
    script = publisher_script()
    final_binding = '[[ "$final_tag_sha" == "$GITHUB_SHA" ]]'
    success = 'echo "Published verified signed release $tag from $GITHUB_SHA'

    assert script.index(final_binding) < script.index(success)
