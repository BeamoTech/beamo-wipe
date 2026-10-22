"""Supplemental unchanged assertions using the installed development browser.

This does not qualify the missing Playwright-pinned runtime.
"""
from pathlib import Path
import json
import subprocess

import pytest
from playwright.sync_api import BrowserType


original_launch = BrowserType.launch


def system_launch(self, *args, **kwargs):
    kwargs["executable_path"] = "/usr/bin/chromium"
    return original_launch(self, *args, **kwargs)


BrowserType.launch = system_launch
root = Path(__file__).resolve().parent
version = subprocess.check_output(["/usr/bin/chromium", "--version"], text=True).strip()
print("Supplemental browser:", version, flush=True)
(root / "system-browser-runtime.json").write_text(json.dumps({
    "runtime": version,
    "executable": "/usr/bin/chromium",
    "pinned_playwright_runtime": False,
    "scope": "Unchanged inventory and protected-card assertions; supplemental only",
}, indent=2) + "\n")
raise SystemExit(pytest.main([
    "-o", "addopts=", "-q", "-p", "no:cacheprovider",
    "tests/test_inventory_count.py::test_browser_inventory_count_is_visible",
    "tests/test_protected_boot_gallery.py",
    "--junitxml=" + str(root / "system-browser-tests.xml"),
]))
