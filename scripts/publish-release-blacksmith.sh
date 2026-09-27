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
if draft_state="$(gh release view "$tag" --repo "$GITHUB_REPOSITORY" \
  --json isDraft --jq .isDraft 2>/dev/null)"; then
  [[ "$draft_state" == true ]] || {
    echo "Release $tag is already public; refusing to replace its assets." >&2
    exit 2
  }
else
  gh release create "$tag" --repo "$GITHUB_REPOSITORY" --verify-tag --draft \
    --title "Beamo Wipe $BEAMO_WIPE_VERSION" \
    --notes-file "docs/release-${BEAMO_WIPE_VERSION}.md"
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
# A failed attempt may have left a partial draft. Replace only draft assets;
# the complete server digest check below still gates public promotion.
gh release upload "$tag" --repo "$GITHUB_REPOSITORY" --clobber "${assets[@]}"

# GitHub supplies the SHA-256 of each stored asset. Refuse public promotion
# until every server digest equals the exact local bytes we uploaded.
# A draft can be read by release ID even when the release-by-tag API returns
# 404, so resolve its ID with the authenticated release CLI first.
release_id="$(gh release view "$tag" --repo "$GITHUB_REPOSITORY" \
  --json databaseId --jq .databaseId)"
[[ "$release_id" =~ ^[1-9][0-9]*$ ]] || {
  echo "Release $tag has no valid GitHub draft ID." >&2
  exit 2
}
for ((attempt = 1; attempt <= 6; attempt++)); do
  gh api "repos/$GITHUB_REPOSITORY/releases/$release_id" > "$stage/github-release.json"
  if "$RUNNER_TEMP/beamo-release-venv/bin/python" scripts/verify_github_release_assets.py \
    "$stage/github-release.json" "${assets[@]}"; then
    gh release edit "$tag" --repo "$GITHUB_REPOSITORY" --draft=false --latest
    echo "Published verified signed release $tag from $GITHUB_SHA (build $BUILD_ID)"
    exit 0
  fi
  sleep 10
done
echo 'GitHub asset digest verification failed; release remains a draft.' >&2
exit 2
