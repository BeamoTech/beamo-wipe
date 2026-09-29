# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real mixed-module tests in isolated, controlled interpreters."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODES = [
    "tests/test_compat_story.py::test_what_screen_keeps_title_and_shows_this_usb_line",
    "tests/test_separate_footer_actions.py::test_assist_nav_names_do_not_rewrite_result_heading",
]
CONTROL = "tests/test_compat_story.py::test_source_helper_is_honest_checkout_stub"

# Only the child interpreter sees the simulated dependency. No sys.modules or
# import hooks escape into the main suite, regardless of test order/platform.
CHILD = r'''
import builtins, importlib.util, os, sys, types
from importlib.machinery import ModuleSpec
mode = sys.argv[1]
real_find = importlib.util.find_spec
real_import = builtins.__import__
def find(name, *a, **kw):
    if name == "gi":
        return None if mode == "missing" else ModuleSpec("gi", loader=None)
    return real_find(name, *a, **kw)
def controlled_import(name, *a, **kw):
    if name == "gi":
        if mode == "missing":
            raise ModuleNotFoundError("No module named 'gi'", name="gi")
        if mode == "nested-missing":
            raise ModuleNotFoundError("broken gi native dependency", name="gi._gi")
        if mode == "syntax":
            raise SyntaxError("broken gi syntax")
        if mode == "import-error":
            raise ImportError("broken gi ABI")
    return real_import(name, *a, **kw)
importlib.util.find_spec = find
builtins.__import__ = controlled_import
if mode in {"version", "initialization", "assertion"}:
    gi = types.ModuleType("gi")
    def require_version(*a):
        if mode == "version":
            raise ValueError("required GTK version unavailable")
    gi.require_version = require_version
    repo = types.ModuleType("gi.repository")
    repo.Atk = types.SimpleNamespace(Role=types.SimpleNamespace(HEADING=1))
    repo.Gtk = types.SimpleNamespace(Label=type("Label", (), {}))
    sys.modules["gi"] = gi
    sys.modules["gi.repository"] = repo
    # Reach the actual assertions with deliberately incorrect UI substitutes.
    # These are not evidence of rendered GTK execution.
    ui = types.ModuleType("beamo_wipe.ui.accessible_wizard")
    class App:
        def __init__(self, wizard):
            if mode == "initialization":
                raise RuntimeError("GTK initialization failed")
            self.window = types.SimpleNamespace(get_focus=lambda: object(), resize=lambda *a: None)
        def close(self): pass
    ui.AccessibleWizard = App
    sys.modules[ui.__name__] = ui
    helpers = types.ModuleType("test_accessible_runtime")
    sys.path.insert(0, "src")
    from beamo_wipe.demo import make_demo_wizard
    helpers.make_demo_wizard = make_demo_wizard
    helpers.drain = lambda: None
    helpers.text = lambda app: ""
    helpers.widgets = lambda window: []
    sys.modules[helpers.__name__] = helpers
import pytest
raise SystemExit(pytest.main(sys.argv[2:]))
'''


@pytest.mark.parametrize("mode", [
    "missing", "missing-reversed", "nested-missing", "syntax", "import-error", "version", "initialization", "assertion",
])
def test_dependency_boundary_preserves_non_dependency_failures(tmp_path, mode):
    report = tmp_path / "results.xml"
    nodes = list(reversed(NODES)) if mode == "missing-reversed" else NODES
    mode = "missing" if mode == "missing-reversed" else mode
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", CHILD, mode, "-p", "no:cacheprovider", "-o", "addopts=",
         "-q", *nodes, CONTROL, f"--junitxml={report}"],
        cwd=ROOT, env=dict(os.environ, BEAMO_WIPE_DRY_RUN="1", PYTEST_ADDOPTS="",
                           PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"),
        capture_output=True, text=True, timeout=30,
    )
    cases = list(ET.parse(report).getroot().iter("testcase"))
    assert len(cases) == 3, result.stdout + result.stderr
    by_name = {case.get("name"): case for case in cases}
    assert len(by_name[CONTROL.split("::")[1]]) == 0  # unrelated test passed
    for node in NODES:
        case = by_name[node.split("::")[1]]
        if mode == "missing":
            assert case.find("failure") is None
            assert "GTK bindings are validated on the hosted Linux image" in case.find("skipped").get("message")
        else:
            assert case.find("skipped") is None
            assert case.find("failure") is not None, result.stdout + result.stderr
            if mode == "assertion":
                assert "AssertionError" in case.find("failure").text
    assert result.returncode == (0 if mode == "missing" else 1), result.stdout + result.stderr


@pytest.fixture
def guard():
    spec = importlib.util.spec_from_file_location("gtk_results", ROOT / "scripts/check-gtk-test-results.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("outcome", ["pass", "skipped", "failure", "error", "missing", "duplicate"])
def test_hosted_guard_requires_both_actual_passes(tmp_path, guard, outcome):
    suite = ET.Element("testsuite")
    for module, name in guard.REQUIRED:
        case = ET.SubElement(suite, "testcase", classname="tests." + module, name=name)
    if outcome == "missing":
        suite.remove(case)
    elif outcome == "duplicate":
        ET.SubElement(suite, "testcase", case.attrib)
    elif outcome != "pass":
        ET.SubElement(case, outcome)
    report = tmp_path / "results.xml"
    ET.ElementTree(suite).write(report)
    if outcome == "pass":
        guard.check(report)
    else:
        with pytest.raises(RuntimeError, match="Mandatory GTK test"):
            guard.check(report)


def test_qualification_wires_dependency_and_result_guards():
    hosted = (ROOT / "scripts/ci-hosted.sh").read_text()
    body = hosted.split("run_pytest() (", 1)[1].split("\n)\n", 1)[0]
    assert body.index('gi.require_version("Gtk", "3.0")') < body.index("python3 -m pytest")
    assert 'gi.require_version("Atk", "1.0")' in body
    assert body.index('wait "$suite_pid"') < body.index("scripts/check-gtk-test-results.py")
    assert 'scripts/check-gtk-test-results.py "${BEAMO_GATE_JUNIT:-$ROOT/dist/evidence/tests.xml}" || failed=1' in body
    for workflow in ("ci.yml", "release.yml"):
        assert "bash scripts/ci-blacksmith.sh sources" in (ROOT / ".github/workflows" / workflow).read_text()
    assert "for gate in lint tests preview desktop-launchers negative" in (ROOT / "scripts/ci-blacksmith.sh").read_text()
