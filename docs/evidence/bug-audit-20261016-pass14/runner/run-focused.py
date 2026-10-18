"""Serialized fake-only runner/progress/recovery regression selection."""

import json
import os
from pathlib import Path
import subprocess
import time


root = Path("/root/dev/Beamo Wipe")
out = Path("/tmp/pass14-runner")
names = (
    "test_runner_", "test_nwipe_", "test_engine_check", "test_engine_numeric",
    "test_progress_", "test_session_recovery",
)
extra = {
    "test_cancel_after_exit_regression.py",
    "test_ambiguous_popen_interrupt_pass5_regression.py",
    "test_recovery_directory_identity_regression.py",
    "test_recovery_lock_identity_regression.py",
    "test_recovery_zero_capacity_baseline_regression.py",
    "test_recovery_unicode_line_break_pass29.py",
    "test_pass6_session_open_cleanup.py",
    "test_pass10_recovery_evidence_swap.py",
    "test_pass11_recovery_evidence_metadata.py",
    "test_new_session_pinned_engine_regression.py",
    "test_preflight_restart_regression.py",
}
files = sorted(
    str(path.relative_to(root))
    for path in (root / "tests").glob("test_*.py")
    if path.name.startswith(names) or path.name in extra
)
(out / "focused-selection.txt").write_text("\n".join(files) + "\n")
env = dict(os.environ)
env["BEAMO_WIPE_DRY_RUN"] = "1"
env.pop("BEAMO_WIPE_LIVE", None)
env.pop("BEAMO_DESKTOP_NATIVE_INVENTORY_TEST", None)
started = time.monotonic()
with (out / "focused.txt").open("wb") as log:
    code = subprocess.call(
        ["/tmp/beamo-wipe-audit-python/bin/python", "-m", "pytest", "-q", *files,
         "--junitxml=" + str(out / "focused.xml")],
        cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
record = {"exit_code": code, "modules": len(files), "elapsed_seconds": time.monotonic() - started}
(out / "focused-status.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
raise SystemExit(code)
