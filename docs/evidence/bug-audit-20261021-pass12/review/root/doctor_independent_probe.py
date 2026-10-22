"""Independent bounded malformed-output probe for the public doctor path."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

repo = Path("/workspace/beamo-wipe")
spec = importlib.util.spec_from_file_location("pass12_doctor", repo / "dev.py")
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)

payloads = {
    "normal": json.dumps({"version": [3, 13, 5], "modules": {"venv": True, "pip": True}}),
    "malformed": "{",
    "deep-object": '{"version":[3,13,5],"modules":' + '{"a":' * 20000 + '0' + '}' * 20000 + '}',
    "deep-array": '{"version":' + '[' * 20000 + '0' + ']' * 20000 + ',"modules":{}}',
}
rows = []
for name, payload in payloads.items():
    output = io.StringIO()
    with (
        patch.object(dev, "live_environment", return_value=False),
        patch.object(dev, "doctor_probe", return_value=(payload, None)),
        patch.object(dev.shutil, "which", return_value="/owned/fake/git"),
        contextlib.redirect_stdout(output),
    ):
        try:
            status = dev.doctor("local")
            report = json.loads(output.getvalue())
            expected = 0 if name == "normal" else 2
            passed = status == expected and report["status"] == ("ok" if expected == 0 else "blocked")
            rows.append({"name": name, "status": status, "structured": True, "pass": passed})
        except BaseException as exc:
            rows.append({"name": name, "exception": type(exc).__name__, "structured": False, "pass": False})

print(json.dumps({"results": rows}, indent=2))
raise SystemExit(0 if all(row["pass"] for row in rows) else 1)
