#!/usr/bin/env bash
# Native Linux tests plus Windows compilation on the isolated hosted runner.
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
TOOL_ROOT="$(mktemp -d /tmp/beamo-wipe-go.XXXXXX)"
trap 'rm -rf -- "$TOOL_ROOT"' EXIT
apt-get update -qq
apt-get install -y -qq --no-install-recommends ca-certificates python3 git gcc libc6-dev util-linux
bash "$ROOT/scripts/fetch-ci-go.sh" "$TOOL_ROOT"
export BEAMO_GO_BIN="$TOOL_ROOT/go/bin/go" GOCACHE="$TOOL_ROOT/cache" GOTOOLCHAIN=local
export BEAMO_DESKTOP_NATIVE_INVENTORY_TEST=1
cd "$ROOT/desktop"
"$BEAMO_GO_BIN" test -race ./...
"$BEAMO_GO_BIN" vet ./...
# Cross-compilation checks platform-specific test code without claiming native
# Windows execution. Run this test executable on a separate Windows worker.
GOOS=windows GOARCH=amd64 "$BEAMO_GO_BIN" test -c -o "$TOOL_ROOT/desktop-windows.test.exe"
# A duration can expire while Go's coordinator is stopping workers and report
# its own context deadline as a failure. Count completed fuzz executions so
# worker scheduling changes do not turn a healthy run red. This exceeds the
# 346,790 executions observed in the failed 15-second hosted run.
"$BEAMO_GO_BIN" test -run='^$' -fuzz=FuzzBootOption -fuzztime=350000x -parallel=2
"$ROOT/scripts/build-desktop.sh"
