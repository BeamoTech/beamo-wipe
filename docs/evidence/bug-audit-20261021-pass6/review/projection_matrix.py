"""Fresh deterministic full-log/projection comparison; ordinary files only."""

import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
from unittest.mock import patch

from beamo_wipe import nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId


SEED = 0x2026102106
rng = random.Random(SEED)
stamp = "[2026/10/21 12:00:00] info: "
target = "/dev/nvme0n100"
column = "vme0n100"
headers = (
    m.NWIPE_DRIVE_STATUS_HEADER,
    m.NWIPE_ERROR_SUMMARY_HEADER,
    "******************************* Erasure Summary ********************************",
)
records = [
    "ordinary notice", "", "-" * 80, "*" * 80,
    stamp + target + ", ATA, Ordinary model",
    stamp + "No hidden sectors on " + target,
    stamp + "*** HIDDEN SECTORS DETECTED ! *** on " + target,
    stamp + "HIDDEN SECTORS INDETERMINATE! on " + target,
    stamp + "hdparm command not found",
    stamp + "SG_IO bad/missing sense data " + target,
    stamp + target + " is reported as IN USE",
    stamp + "Unable to open device '" + target + "'.",
    stamp + target + ": No sane device geometry",
    stamp + "Nwipe was aborted by the user",
    stamp + target + ": >>> FAILURE! <<<: code 1",
    stamp + "Verification mismatch on '" + target + "'",
    "observed /dev/x-vme0n100",  # colliding 8-character status column
    "observed /dev/sdb",  # ordinary foreign control
    " " + column + " | Erased | 120MB/s | 00:01:00 | FAKE/DISK",
    "! " + column + " |-FAILED-| 120MB/s | 00:01:00 | FAKE/DISK",
    " " + column + " | 0 | 0 | 0",
    "! " + column + " | 1 | 0 | 0",
    " " + column + " | 18446744073709551616 | 0 | 0",
    " " + column + " | 100 | 100 | 100.00%",
    "! " + column + " | 50 | 100 | 50.00%",
    " " + column + " | invalid | 100 | 50.00%",
    "Error Summary", "info: Error Summary",
    "Erasure Summary", "info: " + "*" * 80,
] + list(headers)
for phase in ("writing", "verifying", "syncing", "retrying", "unknown"):
    for count in (1, 3, 4):
        for percent in ("003.17", "099.99", "100.00"):
            records.append(
                stamp + target + f": {percent}%, round 1 of 1, pass {count} of {count}, "
                f"eta 00:00:01, [{phase}]"
            )


def forbidden(*args, **kwargs):
    raise AssertionError("projection matrix attempted an external action")


native_realpath = os.path.realpath


def fake_realpath(path, *args, **kwargs):
    if os.fsdecode(path).startswith("/dev/"):
        return os.fspath(path)
    return native_realpath(path, *args, **kwargs)


mismatches = []
comparisons = 0
with tempfile.TemporaryDirectory(prefix="beamo-pass6-projection-") as scratch:
    logfile = Path(scratch) / "fake.log"
    with (
        patch.object(m.subprocess, "Popen", forbidden),
        patch.object(m.subprocess, "run", forbidden),
        patch.object(m, "_try_log_diag", lambda *_args: None),
        patch.object(os.path, "realpath", fake_realpath),
    ):
        for case in range(1500):
            chosen = rng.choices(records, k=rng.randrange(1, 17))
            # Native engine logs always retain a real timestamped startup
            # record. A wholly bare legacy log with no relevant record has
            # equivalent unavailable checks but differing missing provenance;
            # that exploratory history is retained in *_legacy_origin.*.
            text = stamp + "Program options are set as follows\n" + "\n".join(chosen) + "\n"
            logfile.write_text(text, encoding="utf-8")
            projected = m.NwipeRunner()._scan_completion_log(
                str(logfile), target, m._log_signature(logfile.stat())
            )
            if projected is None:
                mismatches.append({"case": case, "kind": "unexpected-none", "text": text})
                continue
            for method in MethodId:
                for code in (0, 1, -15, 143):
                    expected = m.completion_for_method(code, text, target, method)
                    actual = m.completion_for_method(code, projected, target, method)
                    comparisons += 1
                    if actual != expected:
                        mismatches.append({
                            "case": case, "kind": "completion", "method": method.value,
                            "code": code, "expected": expected, "actual": actual,
                            "text": text, "projection": projected,
                        })
            expected_checks = check_payloads(text, target)
            actual_checks = check_payloads(projected, target)
            comparisons += 1
            if actual_checks != expected_checks:
                mismatches.append({
                    "case": case, "kind": "engine-checks", "text": text,
                    "projection": projected, "expected": expected_checks,
                    "actual": actual_checks,
                })

result = {
    "seed": SEED, "sequences": 1500, "comparisons": comparisons,
    "mismatch_count": len(mismatches), "mismatches": mismatches[:10],
    "runner_sha256": hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
}
Path(__file__).with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items() if key != "mismatches"}))
raise SystemExit(bool(mismatches))
