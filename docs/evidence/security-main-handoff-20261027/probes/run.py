"""Portable source/model replay; all device, process and power boundaries are fake."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.absolute()
    # Refuse reuse: prior failures and receipts must remain intact.
    output.mkdir(mode=0o700)
    source_paths = [
        "src/beamo_wipe/models.py",
        "src/beamo_wipe/methods.py",
        "src/beamo_wipe/nwipe_runner.py",
        "src/beamo_wipe/wizard.py",
        "src/beamo_wipe/app.py",
        "tests/test_security_terminal_progress.py",
        "tests/test_security_startup_power_guard.py",
    ]

    def hashes():
        return {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in source_paths
        }

    before = hashes()
    harness = Path(__file__).resolve().parent
    env = dict(
        os.environ,
        BEAMO_SECURITY_ROOT=str(root),
        BEAMO_SECURITY_OUTPUT=str(output),
        PYTHONDONTWRITEBYTECODE="1",
    )
    command = [sys.executable, "-I", "-B", str(harness / "final-regression-replay.py")]
    with (output / "replay.log").open("xb") as log:
        try:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
            code = result.returncode
            failure = None
        except subprocess.TimeoutExpired:
            code, failure = None, "timeout; not a passing exit"
    after = hashes()
    record = {
        "scope": "Exact source/test AST with fake OS, descriptor, process and power boundaries; not actual Linux module, VM, image or physical acceptance",
        "command": command,
        "exit": code,
        "failure": failure,
        "source": before,
        "source_unchanged": before == after,
        "harness": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(harness.glob("*.py"))},
    }
    (output / "source-bindings.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print((output / "replay.log").read_text(encoding="utf-8"))
    print(json.dumps({"exit": code, "source_unchanged": before == after, "output": str(output)}))
    return 0 if code == 0 and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
