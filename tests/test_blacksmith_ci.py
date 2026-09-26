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


@pytest.mark.parametrize("probe_code", [0, 1])
def test_kvm_preflight_checks_privileged_api_not_runner_permissions(tmp_path, probe_code):
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "uname").write_text("#!/bin/sh\necho 'Linux x86_64'\n")
    (tools / "grep").write_text("#!/bin/sh\nexit 0\n")
    # No KVM device exists on this fixture host. sudo represents the isolated
    # worker's privileged view, where the device exists but its API may fail.
    (tools / "sudo").write_text(f"#!{sys.executable}\n" + '''
import os, pathlib, sys
if sys.argv[1:] in (['test', '-c', '/dev/kvm'], ['test', '-c', '/dev/loop-control']):
    raise SystemExit(0)
assert sys.argv[1:] == ['python3', '-']
with pathlib.Path(os.environ['PROBE_OUTPUT']).open('a') as output:
    output.write(sys.stdin.read())
raise SystemExit(int(os.environ['PROBE_CODE']))
''')
    for tool in tools.iterdir():
        tool.chmod(0o755)
    probe = tmp_path / "probe.py"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/check-ci-kvm.sh")],
        env=dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                 GITHUB_ACTIONS="true", PROBE_OUTPUT=str(probe), PROBE_CODE=str(probe_code)),
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == probe_code, result.stderr
    assert probe.is_file(), "must exercise the privileged API even if runner cannot read KVM"
    compile(probe.read_text(), str(probe), "exec")


@pytest.mark.parametrize("failure", ["", "attach", "ownership"])
def test_loop_pool_prepares_concurrent_nodes_and_cleans_only_owned_files(tmp_path, failure):
    tools = tmp_path / "bin"
    tools.mkdir()
    state = tmp_path / "loops.json"
    state.write_text(json.dumps({"loops": {}, "peak": 0, "files": []}))
    command = tools / "losetup"
    command.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys
path = pathlib.Path(os.environ['LOOP_STATE'])
state = json.loads(path.read_text())
args = sys.argv[1:]
failure = os.environ['LOOP_FAILURE']
if args[:3] == ['--find', '--show', '--read-only']:
    if failure == 'attach' and len(state['loops']) == 3:
        raise SystemExit(1)
    source = pathlib.Path(args[3])
    assert source.is_file() and source.stat().st_size == 1024 * 1024
    device = '/dev/loop' + str(len(state['loops']))
    state['loops'][device] = str(source)
    state['files'].append(str(source))
    state['peak'] = max(state['peak'], len(state['loops']))
    print(device)
elif args[:5] == ['--list', '--noheadings', '--raw', '--output', 'BACK-FILE']:
    print('another-owner' if failure == 'ownership' and args[5] == '/dev/loop0'
          else state['loops'][args[5]])
elif args[0] == '--detach':
    assert not (failure == 'ownership' and args[1] == '/dev/loop0')
    del state['loops'][args[1]]
else:
    raise AssertionError(args)
path.write_text(json.dumps(state))
''')
    command.chmod(0o755)
    shell = (ROOT / "scripts/check-ci-kvm.sh").read_text()
    code = shell.split("sudo python3 - <<'PY'\n")[2].split("\nPY", 1)[0]
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                 TMPDIR=str(tmp_path), LOOP_STATE=str(state), LOOP_FAILURE=failure),
        capture_output=True, text=True, timeout=15,
    )
    recorded = json.loads(state.read_text())
    assert (result.returncode == 0) == (failure == ""), result.stderr
    assert recorded['peak'] == (3 if failure == 'attach' else 8)
    if failure == 'ownership':
        assert list(recorded['loops']) == ['/dev/loop0']
        assert all(Path(path).is_file() for path in recorded['files'])
    else:
        assert recorded['loops'] == {}
        assert not any(Path(path).exists() for path in recorded['files'])


@pytest.mark.parametrize("runner", ["blacksmith", "local"])
@pytest.mark.parametrize("label", ["bios", "secureboot-usb"])
def test_blacksmith_guest_cannot_silently_fall_back_to_emulation(runner, label):
    shell = (ROOT / "scripts/qemu-verify.sh").read_text()
    function = 'qemu_machine() {' + shell.split('qemu_machine() {', 1)[1].split('\n}', 1)[0] + '\n}'
    result = subprocess.run(
        ['bash', '-c', function + '\nqemu_machine "$1"', 'fixture', label],
        env=dict(os.environ, BEAMO_CI_RUNNER=runner),
        capture_output=True, text=True, check=True,
    )
    acceleration = 'kvm' if runner == 'blacksmith' else 'kvm:tcg'
    expected = f'q35,accel={acceleration},smm=on' if label == 'secureboot-usb' else f'pc,accel={acceleration}'
    assert result.stdout.strip() == expected


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
