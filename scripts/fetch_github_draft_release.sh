#!/usr/bin/env bash
# Fetch a draft by its numeric ID; GitHub's release-by-tag API can return 404.
set -euo pipefail
[[ $# -eq 2 ]] || exit 2
repo="$1"
tag="$2"
release_id="$(gh release view "$tag" --repo "$repo" \
  --json databaseId --jq .databaseId)"
[[ "$release_id" =~ ^[1-9][0-9]*$ ]] || {
  echo "Release $tag has no valid GitHub draft ID." >&2
  exit 2
}
gh api "repos/$repo/releases/$release_id"
