#!/usr/bin/env bash
set -euo pipefail
r=/workspace/beamo-tools/audit-pass6-20261021/root
for phase in lint preview negative; do
 python3 "$r/run_group.py" "final-$phase" /workspace/beamo-tools/beamo-dev env BEAMO_GATE_CHILD=1 bash scripts/ci-hosted.sh "$phase"
done
