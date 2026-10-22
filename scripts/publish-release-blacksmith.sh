#!/usr/bin/env bash
# Invoked only by the protected manual release job after all Blacksmith gates.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == true && "${GITHUB_EVENT_NAME:-}" == workflow_dispatch ]] || exit 2
[[ "${GITHUB_REPOSITORY:-}" == BeamoTech/beamo-wipe && "${GITHUB_REF:-}" == refs/heads/main ]] || exit 2
[[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" && -n "${GH_TOKEN:-}" ]] || exit 2
[[ "${BEAMO_WIPE_VERSION:-}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2

export BUILD_ID
BUILD_ID="$(python3 - <<'PY'
import os, uuid
identity = '/'.join(os.environ[k] for k in ('GITHUB_REPOSITORY', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'))
print(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/' + identity))
PY
)"
stage="$(mktemp -d "$RUNNER_TEMP/beamo-release.XXXXXX")"
key_file="$(mktemp "$RUNNER_TEMP/beamo-signing-key.XXXXXX")"
trap 'rm -f -- "$key_file"' EXIT
umask 077
gcloud secrets versions access latest \
  --project=beamo-wipe --secret=beamo-wipe-release-signing-ed25519-v1 \
  --out-file="$key_file" --quiet
chmod 600 "$key_file"
export BEAMO_WIPE_SIGNING_KEY_FILE="$key_file" PUBLISH_RELEASE=true

"$RUNNER_TEMP/beamo-release-venv/bin/python" scripts/publish_release_gcs.py
gcloud storage cp \
  "gs://beamo-wipe_cloudbuild/releases/$BUILD_ID/RELEASE_COMPLETE.txt" \
  "$stage/RELEASE_COMPLETE.txt" --quiet

iso="dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.iso"
cp -- "release-transfer/dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz" \
  "$stage/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz"
(cd "$stage" && sha256sum "beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz" \
  > "beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz.sha256")
tar --exclude=qemu-evidence/PATH -czf "$stage/verification-evidence.tar.gz" \
  dist/evidence qemu-evidence

PYTHONPATH=src "$RUNNER_TEMP/beamo-release-venv/bin/python" \
  scripts/prepare_release_assets.py "$stage"

tag="v$BEAMO_WIPE_VERSION"
title="Beamo Wipe $BEAMO_WIPE_VERSION"
notes_file="docs/release-${BEAMO_WIPE_VERSION}.md"
if draft_state="$(gh release view "$tag" --repo "$GITHUB_REPOSITORY" \
  --json isDraft --jq .isDraft 2>/dev/null)"; then
  [[ "$draft_state" == true ]] || {
    echo "Release $tag is already public; refusing to replace its assets." >&2
    exit 2
  }
  gh release edit "$tag" --repo "$GITHUB_REPOSITORY" --draft=true --prerelease=false \
    --title "$title" --notes-file "$notes_file"
else
  gh release create "$tag" --repo "$GITHUB_REPOSITORY" --verify-tag --draft \
    --prerelease=false \
    --title "$title" --notes-file "$notes_file"
fi

assets=(
  "$iso" "$iso.sha256"
  "dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.sha256"
  "dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.json"
  "dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.manifest.json"
  "dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.manifest.json.sha256"
  "dist/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.manifest.json.sig"
  dist/SHA256SUMS packaging/release-keys/keys.json
  "$stage/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz"
  "$stage/beamo-wipe-${BEAMO_WIPE_VERSION}-amd64.img.gz.sha256"
  "$stage/verification-evidence.tar.gz" "$stage/BUILD-RECEIPT.json"
  "$stage/release-downloads.json" "$stage/release-downloads.json.sig"
  "$stage/RELEASE_COMPLETE.txt"
)

restore_verified_draft() {
  local restored_release_id
  if restored_release_id="$(
    gh api --method PATCH \
      "repos/$GITHUB_REPOSITORY/releases/$verified_release_id" \
      -F draft=true | \
      BEAMO_GITHUB_RELEASE_DRAFT=true \
        "$RUNNER_TEMP/beamo-release-venv/bin/python" \
          scripts/verify_github_release_assets.py - "${assets[@]}"
  )" && [[ "$restored_release_id" == "$verified_release_id" ]]; then
    return 0
  fi
  echo "Failed to restore the verified GitHub release draft $verified_release_id." >&2
  return 1
}

# A failed attempt may have left a partial draft. Replace only draft assets;
# the complete server digest check below still gates public promotion.
gh release upload "$tag" --repo "$GITHUB_REPOSITORY" --clobber "${assets[@]}"

# GitHub supplies the SHA-256 of each stored asset. Refuse public promotion
# until every server digest equals the exact local bytes we uploaded.
for ((attempt = 1; attempt <= 6; attempt++)); do
  if verified_release_id="$(
    scripts/fetch_github_draft_release.sh "$GITHUB_REPOSITORY" "$tag" | \
      "$RUNNER_TEMP/beamo-release-venv/bin/python" scripts/verify_github_release_assets.py \
        - "${assets[@]}"
  )"; then
    [[ "$verified_release_id" =~ ^[1-9][0-9]*$ ]] || {
      echo "Verified GitHub release ID is invalid." >&2
      exit 2
    }
    remote_tag_sha="$(gh api \
      "repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha)"
    [[ "$remote_tag_sha" == "$GITHUB_SHA" ]] || {
      echo "Remote tag $tag no longer identifies qualified source $GITHUB_SHA." >&2
      exit 2
    }
    if ! promoted_release_id="$(
      gh api --method PATCH \
        "repos/$GITHUB_REPOSITORY/releases/$verified_release_id" \
        -F draft=false -f make_latest=true | \
        BEAMO_GITHUB_RELEASE_DRAFT=false \
          "$RUNNER_TEMP/beamo-release-venv/bin/python" \
            scripts/verify_github_release_assets.py - "${assets[@]}"
    )"; then
      echo "GitHub publication response failed exact verification." >&2
      restore_verified_draft || true
      exit 2
    fi
    [[ "$promoted_release_id" == "$verified_release_id" ]] || {
      echo "GitHub promoted an unexpected release record." >&2
      restore_verified_draft || true
      exit 2
    }
    if ! published_tag_sha="$(gh api \
      "repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha)"; then
      echo "Remote tag $tag could not be rechecked after publication." >&2
      restore_verified_draft || true
      exit 2
    fi
    [[ "$published_tag_sha" == "$GITHUB_SHA" ]] || {
      echo "Remote tag $tag moved during publication; restoring the draft." >&2
      restore_verified_draft || true
      exit 2
    }
    if ! latest_release_id="$(
      gh api "repos/$GITHUB_REPOSITORY/releases/latest" | \
        BEAMO_GITHUB_RELEASE_DRAFT=false \
          "$RUNNER_TEMP/beamo-release-venv/bin/python" \
            scripts/verify_github_release_assets.py - "${assets[@]}"
    )"; then
      echo "GitHub latest release response failed exact verification." >&2
      restore_verified_draft || true
      exit 2
    fi
    [[ "$latest_release_id" == "$verified_release_id" ]] || {
      echo "GitHub latest release does not identify the verified release." >&2
      restore_verified_draft || true
      exit 2
    }
    if ! final_tag_sha="$(gh api \
        "repos/$GITHUB_REPOSITORY/commits/$tag" --jq .sha)"; then
      echo "Remote tag $tag could not be rechecked after latest release verification." >&2
      restore_verified_draft || true
      exit 2
    fi
    [[ "$final_tag_sha" == "$GITHUB_SHA" ]] || {
      echo "Remote tag $tag moved while the latest release was verified; restoring the draft." >&2
      restore_verified_draft || true
      exit 2
    }
    echo "Published verified signed release $tag from $GITHUB_SHA (build $BUILD_ID)"
    exit 0
  fi
  sleep 10
done
echo 'GitHub asset digest verification failed; release remains a draft.' >&2
exit 2
