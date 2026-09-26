# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise CI orchestration using fake Docker; never start a container."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("failed_gate", ["", "lint", "tests", "desktop-launchers", "negative", "preview"])
def test_parallel_sources_waits_for_every_gate_and_propagates_failure(tmp_path, failed_gate):
    tools = tmp_path / "bin"
    tools.mkdir()
    uname = tools / "uname"
    uname.write_text("#!/bin/sh\necho 'Linux x86_64'\n")
    uname.chmod(0o755)
    docker = tools / "docker"
    docker.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys, time
root = pathlib.Path(os.environ['FAKE_OUTPUT'])
gate = sys.argv[-1]
(root / (gate + '.json')).write_text(json.dumps(sys.argv[1:]))
deadline = time.monotonic() + 10
while len(list(root.glob('*.json'))) != 5:
    if time.monotonic() > deadline:
        raise SystemExit('source gates did not start in parallel')
    time.sleep(.01)
(root / (gate + '.done')).touch()
raise SystemExit(7 if gate == os.environ['FAILED_GATE'] else 0)
''')
    docker.chmod(0o755)
    output = tmp_path / "output"
    output.mkdir()
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci-blacksmith.sh"), "sources"],
        env=dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                 GITHUB_ACTIONS="true", RUNNER_ENVIRONMENT="self-hosted",
                 GITHUB_RUN_ID="123", GITHUB_RUN_ATTEMPT="2", GITHUB_REPOSITORY="fixture/repo",
                 FAKE_OUTPUT=str(output), FAILED_GATE=failed_gate),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == int(bool(failed_gate)), result.stderr
    assert len(list(output.glob("*.done"))) == 5
    for path in output.glob("*.json"):
        args = json.loads(path.read_text())
        assert "--privileged" not in args
        assert "/var/run/docker.sock:/var/run/docker.sock" not in args
        assert "SKIP_QEMU=false" in args
        assert "ALLOW_DIRTY=0" in args
        assert f"{ROOT}:{ROOT}" in args


def test_blacksmith_refuses_developer_machine():
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci-blacksmith.sh"), "sources"],
        env=dict(os.environ, GITHUB_ACTIONS="false"), capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "isolated Blacksmith" in result.stderr


@pytest.mark.parametrize("orca_failed", [False, True])
def test_receipt_includes_separate_orca_execution(tmp_path, orca_failed):
    from beamo_wipe.ci_evidence import run_gate

    command = '''
import os, pathlib
main = pathlib.Path(os.environ['BEAMO_GATE_JUNIT'])
orca = pathlib.Path(str(main) + '.orca.xml')
orca.write_text('<testsuite tests="1" failures="%d"><testcase name="orca">%s</testcase></testsuite>')
if not %r:
    main.write_text('<testsuite tests="1"><testcase name="main"/></testsuite>')
raise SystemExit(%d)
''' % (int(orca_failed), '<failure message="fixture"/>' if orca_failed else '', orca_failed, int(orca_failed))
    receipt = run_gate("tests", [sys.executable, "-c", command], root=ROOT,
                       evidence_dir=tmp_path, build_id="local")
    assert receipt["status"] == ("fail" if orca_failed else "pass")
    assert receipt["measured"]["passed"] == (0 if orca_failed else 2)
    assert receipt["measured"]["failed"] == int(orca_failed)


def test_blacksmith_receipt_binds_run_and_attempt(tmp_path, monkeypatch):
    from beamo_wipe.ci_evidence import run_gate

    for key, value in dict(BEAMO_CI_RUNNER="blacksmith", GITHUB_RUN_ID="123",
                           GITHUB_RUN_ATTEMPT="2", GITHUB_REPOSITORY="fixture/repo").items():
        monkeypatch.setenv(key, value)
    receipt = run_gate("preview", [sys.executable, "-c", "pass"], root=ROOT,
                       evidence_dir=tmp_path, build_id="local")
    assert receipt["environment"]["runner"] == "blacksmith"
    assert receipt["environment"]["github_run_id"] == "123"
    assert receipt["environment"]["github_run_attempt"] == "2"


def test_pipeline_rejects_broken_safe_test_then_accepts_repaired_test(tmp_path):
    from beamo_wipe.ci_evidence import run_gate

    suite = tmp_path / "test_safe_fixture.py"
    for name, assertion, expected in (("broken", "1 == 2", "fail"),
                                      ("restored", "1 == 1", "pass")):
        suite.write_text(f"def test_safe_fixture():\n    assert {assertion}\n")
        evidence = tmp_path / name
        receipt = run_gate(
            # Same-size edits within one filesystem timestamp tick must not
            # reuse the failing mutant's assertion-rewrite bytecode.
            "tests", [sys.executable, "-B", "-m", "pytest", str(suite),
                      "--junitxml=" + str(evidence / "tests.xml")],
            root=ROOT, evidence_dir=evidence, build_id="local",
        )
        assert receipt["status"] == expected
        assert receipt["measured"]["failed"] == int(name == "broken")


def test_stale_orca_report_cannot_be_counted_as_fresh(tmp_path):
    from beamo_wipe.ci_evidence import run_gate

    (tmp_path / "tests.xml.orca.xml").write_text("stale")
    with pytest.raises(RuntimeError, match="stale evidence"):
        run_gate("tests", [sys.executable, "-c", "pass"], root=ROOT,
                 evidence_dir=tmp_path, build_id="local")
