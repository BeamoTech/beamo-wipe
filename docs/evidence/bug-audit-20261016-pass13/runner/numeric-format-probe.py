"""Record parser numeric-format permissiveness; this is not a bug verdict."""

import json
from pathlib import Path

from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import completion_for_method


baseline = (
    "/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, "
    "eta 00:00:00, [verifying]\n"
)
cases = {
    "ascii_final": baseline,
    "arabic_round": baseline.replace("round 1 of 1", "round ١ of ١"),
    "arabic_pass": baseline.replace("pass 1 of 1", "pass ١ of ١"),
    "arabic_eta": baseline.replace("00:00:00", "٠٠:٠٠:٠٠"),
    "arabic_percent": baseline.replace("100.00%", "١٠٠.٠٠%"),
    "no_record_delimiter": baseline[:-1],
    "wrong_pass_total": baseline.replace("pass 1 of 1", "pass 3 of 3"),
    "partial_phase": baseline.replace("[verifying]", "[verifying"),
    "round_numeric_suffix": baseline.replace("round 1 of 1", "round 1 of 1e3"),
    "pass_numeric_suffix": baseline.replace("pass 1 of 1", "pass 1 of 1e3"),
}
results = {
    name: dict(zip(("ok", "summary", "reason"), completion_for_method(
        0, text, "/dev/sda", MethodId.EVERYDAY
    )))
    for name, text in cases.items()
}
assert results["ascii_final"]["ok"]
assert all(not results[name]["ok"] for name in (
    "arabic_percent", "no_record_delimiter", "wrong_pass_total", "partial_phase",
    "round_numeric_suffix", "pass_numeric_suffix",
))
output = {
    "probe_only": True,
    "product_bug_proved": False,
    "disposition": (
        "Counter/ETA Unicode digit acceptance is recorded without a product fix: "
        "the pinned C logger emits ASCII counters; no supported path was shown "
        "to produce these records or bypass existing completion provenance."
    ),
    "results": results,
}
Path("/tmp/pass13-runner/numeric-format-probe.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output))
