"""PASS25 regressions for the public GitHub latest-release binding."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def publisher_script() -> str:
    return (ROOT / "scripts" / "publish-release-blacksmith.sh").read_text(
        encoding="utf-8"
    )


def latest_verification_block(script: str) -> str:
    start = script.index('if ! latest_release_id="$(')
    end = script.index('[[ "$latest_release_id" == "$verified_release_id" ]]', start)
    return script[start:end]


def test_publisher_fetches_public_latest_release_after_promotion():
    script = publisher_script()
    endpoint = '"repos/$GITHUB_REPOSITORY/releases/latest"'
    tag_lookup = '"repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha'
    promotion = script.index("-F draft=false -f make_latest=true")
    latest = script.index(endpoint)
    post_promotion_tag = script.index(tag_lookup, promotion)

    assert endpoint in script
    assert promotion < post_promotion_tag < latest


def test_publisher_authenticates_complete_latest_release_response():
    block = latest_verification_block(publisher_script())

    assert 'gh api "repos/$GITHUB_REPOSITORY/releases/latest"' in block
    assert "BEAMO_GITHUB_RELEASE_DRAFT=false" in block
    assert "scripts/verify_github_release_assets.py" in block
    assert '- "${assets[@]}"' in block
    assert "--jq" not in block


def test_publisher_requires_latest_endpoint_to_return_verified_release_id():
    script = publisher_script()

    assert '[[ "$latest_release_id" == "$verified_release_id" ]]' in script
    assert "GitHub latest release does not identify the verified release." in script


def test_latest_response_failure_restores_exact_verified_draft():
    script = publisher_script()
    start = script.index('if ! latest_release_id="$(')
    end = script.index("\n    fi", start) + len("\n    fi")
    failure_path = script[start:end]

    assert "GitHub latest release response failed exact verification." in failure_path
    assert "restore_verified_draft || true" in failure_path
    assert "exit 2" in failure_path


def test_latest_identity_mismatch_restores_exact_verified_draft():
    script = publisher_script()
    start = script.index('[[ "$latest_release_id" == "$verified_release_id" ]]')
    end = script.index("}", start) + len("}")
    mismatch_path = script[start:end]

    assert (
        "GitHub latest release does not identify the verified release." in mismatch_path
    )
    assert "restore_verified_draft || true" in mismatch_path
    assert "exit 2" in mismatch_path


def test_success_is_reported_only_after_latest_release_is_authenticated():
    script = publisher_script()
    identity_check = '[[ "$latest_release_id" == "$verified_release_id" ]]'
    success = 'echo "Published verified signed release $tag from $GITHUB_SHA'

    assert script.index(identity_check) < script.index(success)
