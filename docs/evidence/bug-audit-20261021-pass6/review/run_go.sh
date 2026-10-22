#!/usr/bin/env bash
set -euo pipefail
r=/workspace/beamo-tools/audit-pass6-20261021/root
python3 "$r/run_group.py" final-go-race /workspace/beamo-tools/beamo-dev bash -c 'cd desktop; go test -count=1 -race -json ./...'
python3 "$r/run_group.py" final-go-vet /workspace/beamo-tools/beamo-dev bash -c 'cd desktop; go vet ./...'
python3 "$r/run_group.py" final-go-fuzz /workspace/beamo-tools/beamo-dev bash -c 'cd desktop; go test -run="^$" -fuzz=FuzzBootOption -fuzztime=350000x -parallel=2'
python3 "$r/run_group.py" identity-null-independent-after /workspace/beamo-tools/beamo-dev bash -c 'cd desktop; go test -count=1 -race -json -overlay=/workspace/beamo-tools/audit-pass6-20261021/root/identity-null-overlay.json -run=TestRootBuildIdentityDirtyType .'
python3 "$r/run_group.py" final-windows-test-build /workspace/beamo-tools/beamo-dev bash -c 'cd desktop; GOOS=windows GOARCH=amd64 go test -c -o /workspace/beamo-tools/audit-pass6-20261021/root/desktop-windows.test.exe'
python3 "$r/run_group.py" final-desktop-build /workspace/beamo-tools/beamo-dev python3 scripts/build_desktop.py
