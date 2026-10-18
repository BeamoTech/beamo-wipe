"""Compare complete fake logs with bounded projections without an engine."""

import hashlib
import itertools
import json
import os
from pathlib import Path
import tempfile

from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import (
    NwipeRunner,
    NWIPE_COMPLETION_LOG_BYTES,
    NWIPE_DRIVE_STATUS_HEADER,
    _log_signature,
    completion_for_method,
    nwipe_status_device_field,
)


STAMP = "[2026/10/16 12:00:00] info: "
ERROR = "******************************** Error Summary *********************************\n"
ERASURE = "******************************* Erasure Summary ********************************\n"
CLOSE = "********************************************************************************\n"
PADDING = ("x" * 65535 + "\n") * 16


class Exited:
    returncode = 0

    def poll(self):
        return self.returncode


def main():
    records = []
    defects = []
    with tempfile.TemporaryDirectory(prefix="pass13-projection-") as directory:
        path = Path(directory) / "fake.log"
        cases = itertools.product(
            ("/dev/sda", "/dev/nvme0n100", "/dev/sdabcdef"),
            ("", "info: ", STAMP),
            (
                "0 | 0 | 0",
                "1 | 0 | 0",
                "0 | 1 | 0",
                "0 | 0 | 1",
                "unknown | 0 | 0",
                f"{2**64} | 0 | 0",
            ),
            ("complete", "shortfall", "malformed", "conflicting"),
        )
        for ordinal, (target, prefix, counts, variant) in enumerate(cases):
            name = nwipe_status_device_field(target).strip()
            erasure_row = {
                "complete": f"! {name} | 2 | 2 | 100.00%\n",
                "shortfall": f"! {name} | 1 | 2 | 50.00%\n",
                "malformed": f"! {name} | invalid | 2 | 50.00%\n",
                "conflicting": (
                    f"! {name} | 2 | 2 | 100.00%\n"
                    + prefix + f"! {name} | 1 | 2 | 50.00%\n"
                ),
            }[variant]
            text = (
                STAMP + f"No hidden sectors on {target}\n"
                + target + ": 25.00%, round 1 of 1, pass 1 of 1, "
                "eta 00:01:00, [writing]\n"
                + ERROR + prefix + f"! {name} | {counts}\n" + prefix + CLOSE
                + ERASURE + prefix + erasure_row + prefix + CLOSE
                + PADDING
                + NWIPE_DRIVE_STATUS_HEADER + "\n"
                + f" {name} | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
            )
            path.write_bytes(text.encode())
            runner = NwipeRunner()
            projected = runner._scan_completion_log(
                str(path), target, _log_signature(path.stat())
            )
            if projected is None:
                raise AssertionError((ordinal, "unexpected incomplete projection"))
            checks = check_payloads(text, target)
            if check_payloads(projected, target) != checks:
                defects.append({"case": ordinal, "kind": "check_projection"})
            outcomes = {}
            for method in MethodId:
                expected = completion_for_method(0, text, target, method)
                actual = completion_for_method(0, projected, target, method)
                if actual != expected:
                    defects.append({"case": ordinal, "kind": "outcome_projection", "method": method.value})
                # Exercise actual terminal polling as well as the scanner.
                runner = NwipeRunner()
                runner._proc = Exited()
                request = WipeRequest(target, method, "/dev/sr0", str(path))
                runner._active_request = request
                result = runner.poll(request)
                if (result.ok, result.summary, result.reason) != expected:
                    defects.append({"case": ordinal, "kind": "terminal_poll", "method": method.value})
                if check_payloads(runner._assessment_log_text, target) != checks:
                    defects.append({"case": ordinal, "kind": "terminal_checks", "method": method.value})
                outcomes[method.value] = {"ok": result.ok, "reason": result.reason}
            if path.read_bytes() != text.encode():
                raise AssertionError("read-only assessment changed a fixture")
            records.append({
                "case": ordinal,
                "target": target,
                "prefix": prefix,
                "counts": counts,
                "variant": variant,
                "bytes": len(text.encode()),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "check_statuses": {item["id"]: item["status"] for item in checks},
                "outcomes": outcomes,
            })
    output = {
        "cases": len(records),
        "methods_per_case": len(MethodId),
        "terminal_polls": len(records) * len(MethodId),
        "log_threshold_bytes": NWIPE_COMPLETION_LOG_BYTES,
        "defects": defects,
        "records": records,
    }
    Path("/tmp/pass13-runner/projection-matrix.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({key: value for key, value in output.items() if key != "records"}))
    if defects:
        raise AssertionError(f"{len(defects)} projection/poll disagreements")


if __name__ == "__main__":
    main()
