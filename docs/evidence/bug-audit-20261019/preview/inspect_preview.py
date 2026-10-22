"""Capture the actual ./preview on an owned private 72-DPI display."""
from pathlib import Path
import json
import os
import subprocess
import time

from PIL import ImageGrab


root = Path(__file__).resolve().parent
assert os.environ.get("BEAMO_ISOLATED_X11_TEST") == "1"
assert os.environ.get("DISPLAY") not in {":1", ":99", ":100", ":200"}
with (root / "tk-preview.log").open("w") as log:
    child = subprocess.Popen(["./preview"], stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(12):
            if child.poll() is not None:
                raise RuntimeError("preview exited before inspection")
            time.sleep(0.5)
        ImageGrab.grab().save(root / "tk-preview-72dpi.png")
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
    (root / "tk-preview-capture.json").write_text(json.dumps({
        "command": ["./preview"],
        "display": os.environ["DISPLAY"],
        "dpi": 72,
        "fake_disks_only": True,
        "capture": "tk-preview-72dpi.png",
        "teardown": "SIGTERM to owned preview child after capture",
        "normal_close_acceptance": False,
        "returncode": child.returncode,
    }, indent=2) + "\n")
