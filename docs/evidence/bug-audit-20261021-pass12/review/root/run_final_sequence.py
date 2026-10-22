"""Run the PASS12 final checks serially in one unprivileged dev container."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as E

os.umask(0o022)
r = Path(__file__).parent
w = r.parent
repo = Path("/workspace/beamo-wipe")
freeze = json.loads((r / "final-freeze.json").read_text())
source_hashes = json.loads((r / "final-source-sha256.json").read_text())
assert "BEAMO_DESKTOP_NATIVE_INVENTORY_TEST" not in os.environ


def frozen():
    assert len(source_hashes) == freeze["source_files"] == 825
    assert all(
        hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest
        for name, digest in source_hashes.items()
    )


def group(name, *command, cwd=repo):
    subprocess.run(
        ["python3", str(r / "run_group.py"), name, *command],
        cwd=cwd,
        check=True,
    )


def green(name, count):
    cases = list(E.parse(r / (name + ".xml")).iter("testcase"))
    assert len(cases) == len({(c.get("classname"), c.get("name")) for c in cases}) == count
    assert all(c.find(kind) is None for c in cases for kind in ("failure", "error", "skipped"))


x11 = [
    "env", "BEAMO_ISOLATED_X11_TEST=1", "BEAMO_WIPE_DRY_RUN=1",
    "dbus-run-session", "--", "xvfb-run", "-a", "-n", "1251", "-s",
    "-screen 0 1600x1000x24 -dpi 72",
]
pytest = [
    "python3", "-m", "pytest", "-W", "error", "-p", "no:cacheprovider",
    "-o", "addopts=", "-o", "pythonpath=src tests", "-q",
]

frozen()
group(
    "final-new-regressions", *x11, *pytest, *freeze["new_case_breakdown"],
    "--junitxml=" + str(r / "final-new-regressions.xml"),
)
green("final-new-regressions", freeze["new_python_cases"])
group(
    "final-preference-independent", *pytest,
    str(r / "test_preference_snapshot_probe.py"),
    "--junitxml=" + str(r / "final-preference-independent.xml"),
)
green("final-preference-independent", 8)
group("final-doctor-independent", "python3", str(r / "doctor_independent_probe.py"))
group("final-doctor-reviewer", "python3", str(w / "boot" / "doctor_probe.py"))

group(
    "final-model-discovery", "env", "PYTHONPATH=" + str(repo / "src") + ":" + str(repo / "tests"),
    "python3", "-W", "error", str(r / "model-replays" / "probe_identity_freshness.py"),
    "--output", str(r / "model-replays" / "identity-freshness.json"),
)
for name in ("launch_reuse_matrix.py", "terminal_handoff_model.py", "journal_admission_model.py"):
    group(
        "final-model-" + name.removesuffix(".py"), "env",
        "PYTHONPATH=" + str(repo / "src") + ":" + str(repo / "tests"),
        "python3", "-W", "error", str(r / "model-replays" / name),
    )

for phase in ("lint", "preview", "negative"):
    group("final-" + phase, "env", "BEAMO_GATE_CHILD=1", "bash", "scripts/ci-hosted.sh", phase)
for operation in ("test", "desktop"):
    group("doctor-" + operation, "python3", "dev.py", "doctor", "--for", operation)

group(
    "final-go-new", "go", "test", "-count=1", "-race",
    "-run=" + freeze["new_go_test_pattern"], "-json", "./...", cwd=repo / "desktop",
)
group(
    "final-go-root-native-probe", "go", "test", "-count=1", "-race",
    "-overlay", str(r / "native-json-independent-overlay.json"),
    "-run=^TestPass12IndependentNativeJSONBoundary$", "-json", "./...", cwd=repo / "desktop",
)
group(
    "final-go-reviewer-parser-probe", "go", "test", "-count=1", "-race",
    "-overlay", str(w / "boot" / "native-probe-overlay.json"),
    "-run=^TestPass12NativeParseProbe$", "-json", "./...", cwd=repo / "desktop",
)
group(
    "final-go-reviewer-readiness-probe", "go", "test", "-count=1", "-race",
    "-overlay", str(w / "boot" / "native-readiness-overlay.json"),
    "-run=^TestPass12ContradictoryJSONAuthorizesPlan$", "-json", "./...", cwd=repo / "desktop",
)
group(
    "final-go-epoch-model", "go", "test", "-count=1", "-race",
    "-overlay", str(r / "model-replays" / "request-epoch-overlay.json"),
    "-run=^TestPass12RequestEpochModel$", "-json", "./...", cwd=repo / "desktop",
)
group("final-go-race", "go", "test", "-count=1", "-race", "-json", "./...", cwd=repo / "desktop")
group("final-go-vet", "go", "vet", "./...", cwd=repo / "desktop")
group(
    "final-go-fuzz", "go", "test", "-run=^$", "-fuzz=FuzzBootOption",
    "-fuzztime=350000x", "-parallel=2", cwd=repo / "desktop",
)
group(
    "final-windows-test-build", "env", "GOOS=windows", "GOARCH=amd64", "go", "test",
    "-c", "-o", str(r / "desktop-windows.test.exe"), cwd=repo / "desktop",
)

frozen()
group("final-desktop-build", "python3", "scripts/build_desktop.py")
group("actual-preview-inspect", *x11, "python3", str(r / "inspect_live_preview.py"))
group("artifact-inspection", "python3", str(r / "review_artifacts.py"))
group("system-browser-tests", "python3", str(r / "system_browser_check.py"))
green("system-browser-tests", 9)

frozen()
group(
    "final-tests", "env", "BEAMO_GATE_CHILD=1",
    "BEAMO_GATE_JUNIT=" + str(r / "final-tests.xml"),
    "bash", "scripts/ci-hosted.sh", "tests",
)
frozen()
print("All PASS12 final serial phases exited 0", flush=True)
