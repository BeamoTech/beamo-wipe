"""Fake-only source trace: normalize table context consistently at any log size."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner

ROOT = Path("/tmp/pass11-runner")
PREFIX = "[2026/10/16 12:00:00] info: "
STATUS = (
    "********************************* Drive Status *********************************\n"
    "      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n"
)
HEADER = "******************************* Erasure Summary ********************************\n"
CLOSE = "********************************************************************************\n"
NONE = PREFIX + "No hidden sectors on /dev/sda\n"
PADDING = "unrelated log detail\n" * 60000


class Exited:
    def poll(self):
        return 0


rows = []
for name, evidence in {
    "plain-shortfall": NONE + HEADER + " sda | 1 | 2 | 50.00%\n" + CLOSE,
    "prefixed-shortfall": NONE + HEADER + PREFIX + "! sda | 1 | 2 | 50.00%\n" + CLOSE,
    "prefixed-malformed": NONE + HEADER + PREFIX + "! sda | invalid | 2 | 50.00%\n" + CLOSE,
    "prefixed-complete": NONE + HEADER + PREFIX + "! sda | 2 | 2 | 100.00%\n" + CLOSE,
    "prefixed-close": NONE + HEADER + " sda | 2 | 2 | 100.00%\n" + PREFIX + CLOSE + " sda | 1 | 2 | 50.00%\n",
}.items():
    for large in (False, True):
        logfile = ROOT / (name + ("-large" if large else "-small") + ".log")
        content = evidence + (PADDING if large else "") + STATUS
        logfile.write_text(content)
        before = hashlib.sha256(logfile.read_bytes()).hexdigest()
        runner = NwipeRunner()
        runner._proc = Exited()
        request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sr0", str(logfile))
        result = runner.poll(request)
        direct = {c["id"]: c["status"] for c in check_payloads(content, "/dev/sda")}
        projected = {c["id"]: c["status"] for c in check_payloads(runner._assessment_log_text, "/dev/sda")}
        assert before == hashlib.sha256(logfile.read_bytes()).hexdigest()
        rows.append({"name": name, "large": large, "bytes": logfile.stat().st_size,
                     "direct": direct, "assessment": projected, "result": result.reason,
                     "assessment_text": runner._assessment_log_text if large else "same-as-input"})
print(json.dumps(rows, indent=2))
