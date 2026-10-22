#!/usr/bin/env bash
set -euo pipefail
r=/workspace/beamo-tools/audit-pass6-20261021/root
w=/workspace/beamo-tools/audit-pass6-20261021
python3 "$r/run_group.py" final-ui-exact-original /workspace/beamo-tools/beamo-dev env BEAMO_WIPE_DRY_RUN=1 dbus-run-session -- xvfb-run -a -n 764 -s '-screen 0 1600x1000x24 -dpi 72' python3 -m pytest -p no:cacheprovider -c "$r/pytest-ui-original.ini" -q "$r/ui-final-tests-original" --junitxml="$r/final-ui-exact-original.xml" && exit 2 || code=$?
test "$code" = 1
python3 "$r/run_group.py" final-original-probes /workspace/beamo-tools/beamo-dev dbus-run-session -- xvfb-run -a -n 762 -s '-screen 0 1600x1000x24 -dpi 72' python3 -m pytest -W error -p no:cacheprovider -o addopts= -o pythonpath=src -q "$w/discovery/test_hidden_descendant_mount_probe.py" "$w/ui/test_tk_poll_interruption_candidate.py" "$w/ui/test_tk_stop_render_failure_candidate.py" "$w/ui/test_curses_write_failure_candidate.py" "$w/runner/test_cancel_inner_poll_probe.py" --junitxml="$r/final-original-probes.xml"
python3 "$r/run_group.py" actual-preview-inspect /workspace/beamo-tools/beamo-dev env BEAMO_ISOLATED_X11_TEST=1 dbus-run-session -- xvfb-run -a -n 763 -s '-screen 0 1600x1000x24 -dpi 72' python3 "$r/inspect_live_preview.py"
python3 "$r/run_group.py" system-browser-tests /workspace/beamo-tools/beamo-dev python3 "$r/system_browser_check.py"
python3 "$r/run_group.py" final-tests /workspace/beamo-tools/beamo-dev env BEAMO_GATE_CHILD=1 BEAMO_GATE_JUNIT="$r/final-tests.xml" bash scripts/ci-hosted.sh tests
