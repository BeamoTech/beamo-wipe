#!/usr/bin/env bash
# The signed release must be tagged at a successful full main CI source.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == true && "${GITHUB_EVENT_NAME:-}" == workflow_dispatch ]] || exit 2
[[ "${GITHUB_REPOSITORY:-}" == BeamoTech/beamo-wipe && "${GITHUB_REF:-}" == refs/heads/main ]] || exit 2
[[ "${BEAMO_WIPE_VERSION:-}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
[[ -n "${GH_TOKEN:-}" ]] || exit 2
[[ "$(git rev-parse HEAD)" == "${GITHUB_SHA:-}" ]] || exit 2
[[ -z "$(git status --porcelain)" ]] || exit 2
[[ "$(git rev-parse "refs/tags/v${BEAMO_WIPE_VERSION}^{commit}")" == "$GITHUB_SHA" ]] || exit 2
[[ "$(PYTHONPATH=src python3 -c 'import beamo_wipe; print(beamo_wipe.__version__)')" == "$BEAMO_WIPE_VERSION" ]] || exit 2
[[ "$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')" == "$BEAMO_WIPE_VERSION" ]] || exit 2

qualified_runs="$(gh run list --repo "$GITHUB_REPOSITORY" --workflow ci.yml \
  --event push --commit "$GITHUB_SHA" --json headSha,status,conclusion --limit 50)"
python3 - "$GITHUB_SHA" "$qualified_runs" <<'PY'
import json, sys
sha, raw = sys.argv[1:]
runs = json.loads(raw)
if not any(r.get('headSha') == sha and r.get('status') == 'completed'
           and r.get('conclusion') == 'success' for r in runs):
    raise SystemExit('Full main Blacksmith CI has not passed for this exact source')
PY
