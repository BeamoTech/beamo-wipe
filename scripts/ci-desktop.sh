#!/usr/bin/env bash
# Native Linux tests and shipped launcher builds on the isolated hosted runner.
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
TOOL_ROOT="$(mktemp -d /tmp/beamo-wipe-go.XXXXXX)"
trap 'rm -rf -- "$TOOL_ROOT"' EXIT
# The hosted wrapper has just refreshed this container's package lists.
# Standalone desktop checks still refresh before installing their dependencies.
if [[ "${BEAMO_DESKTOP_APT_READY:-0}" != 1 ]]; then
  apt-get update -qq
fi
apt-get install -y -qq --no-install-recommends ca-certificates python3 git gcc libc6-dev util-linux
bash "$ROOT/scripts/fetch-ci-go.sh" "$TOOL_ROOT"
export BEAMO_GO_BIN="$TOOL_ROOT/go/bin/go" GOCACHE="$TOOL_ROOT/cache" GOTOOLCHAIN=local
export BEAMO_DESKTOP_NATIVE_INVENTORY_TEST=1
cd "$ROOT/desktop"
"$BEAMO_GO_BIN" test -race ./...
"$BEAMO_GO_BIN" vet ./...
# Blacksmith's native Windows job compiles and runs this same test suite.
# Keep the cross-compile check for standalone and legacy callers.
if [[ "${BEAMO_CI_RUNNER:-}" != blacksmith ]]; then
  GOOS=windows GOARCH=amd64 "$BEAMO_GO_BIN" test -c -o "$TOOL_ROOT/desktop-windows.test.exe"
fi
# A duration can expire while Go's coordinator is stopping workers and report
# its own context deadline as a failure. Count completed fuzz executions so
# worker scheduling changes do not turn a healthy run red. This exceeds the
# 346,790 executions observed in the failed 15-second hosted run.
"$BEAMO_GO_BIN" test -run='^$' -fuzz=FuzzBootOption -fuzztime=350000x -parallel=2
"$ROOT/scripts/build-desktop.sh"
