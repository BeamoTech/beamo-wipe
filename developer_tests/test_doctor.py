"""Deterministic doctor checks: no credentials, network, GUI or device access."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def doctor(monkeypatch):
    spec = importlib.util.spec_from_file_location("doctor_dev", ROOT / "dev.py")
    dev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev)
    monkeypatch.setattr(dev.sys, "platform", "linux")
    monkeypatch.setattr(dev, "live_environment", lambda: False)
    monkeypatch.setattr(dev, "python", lambda: "fixture-python")
    tools = {"git": "/fixture/git", "go": "/fixture/go"}
    requested = []
    calls = []
    missing = set()

    def which(name):
        requested.append(name)
        return tools.get(name)

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert kwargs["timeout"] == 5
        assert kwargs["capture_output"] is True
        assert kwargs["cwd"] == dev.ROOT
        if argv[0] == "fixture-python":
            # Match dev.py test's module search (including user site packages).
            # Isolated mode would incorrectly report installed pytest missing.
            assert argv[1] == "-c"
            assert kwargs["env"]["BEAMO_WIPE_DRY_RUN"] == "1"
            value = {
                "version": [3, 11, 2],
                "modules": {n: n not in missing for n in argv[3:]},
            }
            return subprocess.CompletedProcess(argv, 0, json.dumps(value), "")
        assert argv == ["/fixture/go", "version"]
        assert kwargs["env"]["GOTOOLCHAIN"] == "local"
        return subprocess.CompletedProcess(
            argv, 0, "go version go1.26.8 linux/amd64\n", ""
        )

    monkeypatch.setattr(dev.shutil, "which", which)
    monkeypatch.setattr(dev.subprocess, "run", run)
    return dev, tools, requested, calls, missing


@pytest.mark.parametrize(
    "operation",
    [
        "local",
        "test",
        "test-native",
        "preview",
        "preview-web",
        "desktop",
        "qualification",
    ],
)
def test_present_prerequisites_never_authenticate_or_dispatch(
    doctor, capsys, operation
):
    dev, _, requested, calls, _ = doctor
    assert dev.main(["doctor", "--for", operation]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "ok" and result["operation"] == operation
    assert "Blacksmith" in " ".join(result["notes"])
    assert len(calls) <= 2
    assert not {"gcloud", "docker", "aws"}.intersection(requested)
    assert all(cmd[0] in ("fixture-python", "/fixture/go") for cmd, _ in calls)


def test_default_local_needs_no_go_tk_or_cloud(doctor, capsys):
    dev, tools, requested, calls, missing = doctor
    tools.pop("go")
    missing.update(("tkinter", "pytest"))
    assert dev.main(["doctor"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["modules"] == {"venv": True, "pip": True}
    assert requested == ["git"]
    assert len(calls) == 1


@pytest.mark.parametrize(
    "operation,module",
    [
        ("local", "venv"),
        ("local", "pip"),
        ("test", "pytest"),
        ("test-native", "pytest"),
    ],
)
def test_missing_selected_module_is_actionable(doctor, capsys, operation, module):
    dev, _, _, _, missing = doctor
    missing.add(module)
    assert dev.doctor(operation) == 2
    data = json.loads(capsys.readouterr().out)
    assert module in " ".join(data["problems"])
    assert "setup" in " ".join(data["problems"])


def test_legacy_only_tools_cannot_satisfy_git_prerequisite(doctor, capsys):
    dev, tools, requested, _, _ = doctor
    tools.clear()
    tools["gcloud"] = "/fixture/gcloud"
    assert dev.doctor() == 2
    assert "Git" in " ".join(json.loads(capsys.readouterr().out)["problems"])
    assert "gcloud" not in requested


def test_qualification_does_not_probe_credentials_or_broken_venv(doctor, capsys):
    dev, tools, requested, calls, _ = doctor
    tools["gcloud"] = "/fixture/gcloud"
    assert dev.doctor("qualification") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["gh"] is None
    assert "web UI" in " ".join(data["notes"])
    assert requested == ["git", "gh"] and not calls


@pytest.mark.parametrize("operation", ["preview", "preview-web"])
def test_preview_keeps_tk_fallback_optional(doctor, capsys, operation):
    dev, _, _, _, missing = doctor
    missing.add("tkinter")
    assert dev.doctor(operation) == 0
    data = json.loads(capsys.readouterr().out)
    if operation == "preview-web":
        assert not data["modules"]
    else:
        assert data["modules"]["tkinter"] is False
        assert "console" in " ".join(data["notes"])


@pytest.mark.parametrize("installed", [False, True])
@pytest.mark.parametrize("operation", ["test", "preview", "preview-web"])
def test_windows_requires_actual_wsl_preflight(
    doctor, monkeypatch, capsys, installed, operation
):
    dev, tools, _, calls, _ = doctor
    monkeypatch.setattr(dev.sys, "platform", "win32")
    if installed:
        tools["wsl.exe"] = "/fixture/wsl.exe"
    assert dev.doctor(operation) == 2
    assert "WSL2" in " ".join(json.loads(capsys.readouterr().out)["problems"])
    assert not calls


def test_windows_native_tools_do_not_require_wsl(doctor, monkeypatch):
    dev, _, requested, _, _ = doctor
    monkeypatch.setattr(dev.sys, "platform", "win32")
    assert dev.doctor("test-native") == 0
    assert "wsl.exe" not in requested


def test_live_system_refuses_without_probes(doctor, monkeypatch):
    dev, _, _, calls, _ = doctor
    monkeypatch.setattr(dev, "live_environment", lambda: True)
    assert dev.doctor() == 2
    assert not calls


@pytest.mark.parametrize(
    "failure", ["timeout", "oserror", "stderr", "json", "old-python"]
)
def test_probe_failure_is_bounded_and_does_not_echo_diagnostics(
    doctor, monkeypatch, capsys, failure
):
    dev, _, _, _, _ = doctor

    def run(argv, **kwargs):
        assert kwargs["timeout"] == 5
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 5, output="private-diagnostic")
        if failure == "oserror":
            raise OSError("private-diagnostic")
        if failure == "stderr":
            return subprocess.CompletedProcess(
                argv, 1, "private-diagnostic", "private-diagnostic"
            )
        value = (
            json.dumps({"version": [3, 9, 0], "modules": {"venv": True, "pip": True}})
            if failure == "old-python"
            else "private-diagnostic"
        )
        return subprocess.CompletedProcess(argv, 0, value, "")

    monkeypatch.setattr(dev.subprocess, "run", run)
    assert dev.doctor() == 2
    output = capsys.readouterr()
    assert "private-diagnostic" not in output.out + output.err
    assert json.loads(output.out)["status"] == "blocked"


def test_desktop_missing_go_is_actionable(doctor, capsys):
    dev, tools, _, _, _ = doctor
    tools.pop("go")
    assert dev.doctor("desktop") == 2
    assert "Go 1.26.8" in " ".join(json.loads(capsys.readouterr().out)["problems"])


def test_desktop_wrong_version_and_missing_pin_fail_closed(
    doctor, monkeypatch, capsys, tmp_path
):
    dev, _, _, _, _ = doctor
    original = dev.doctor_probe
    monkeypatch.setattr(
        dev,
        "doctor_probe",
        lambda argv, **kw: ("go version go1.1.0 linux/amd64\n", None)
        if argv[-1] == "version"
        else original(argv, **kw),
    )
    assert dev.doctor("desktop") == 2
    assert "pinned Go" in " ".join(json.loads(capsys.readouterr().out)["problems"])
    monkeypatch.setattr(dev, "ROOT", tmp_path)
    assert dev.doctor("desktop") == 2
    assert "go.mod" in " ".join(json.loads(capsys.readouterr().out)["problems"])


@pytest.mark.skipif(not Path("/bin/bash").is_file(), reason="legacy POSIX scripts")
def test_legacy_help_exits_before_any_cloud_command(tmp_path):
    # An empty PATH is sufficient for these bash built-in-only help routes.
    for name in ("ci-cloud.sh", "install-cloud-triggers.sh"):
        result = subprocess.run(
            ["/bin/bash", str(ROOT / "scripts" / name), "--help"],
            env={"PATH": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        assert "Legacy Cloud Build" in result.stdout
        assert "authorization" in result.stdout
