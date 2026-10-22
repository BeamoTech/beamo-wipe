"""Runtime preflight uses fake proc markers and never launches real helpers."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("setup",),
    ("setup", "--native"),
    ("test",),
    ("test", "--native"),
    ("preview",),
    ("preview", "--web"),
    ("preview", "--console"),
    ("desktop-build",),
    ("desktop-test",),
)


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("dev_runtime", ROOT / "dev.py")
    dev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev)
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr(dev.sys, "platform", "linux")
    monkeypatch.setattr(dev, "ROOT", tmp_path / "checkout")
    monkeypatch.setattr(dev, "python", lambda: "fixture-python")
    monkeypatch.setattr(dev.shutil, "which", lambda name: None)
    marker = tmp_path / "cmdline"
    marker.write_bytes(b"quiet splash")
    state = {"read_error": None, "mounted": False, "mount_error": None}
    calls = []
    read_text = Path.read_text

    def read(path, *args, **kwargs):
        assert path == Path("/proc/cmdline"), "Unexpected runtime file read"
        calls.append("read-marker")
        if state["read_error"] is not None:
            raise state["read_error"]
        # Decode real regular-file bytes with a deterministic Linux fixture codec.
        return read_text(marker, encoding="utf-8")

    def mounted(path):
        assert path == Path("/run/live/medium"), "Unexpected mount check"
        calls.append("mount-check")
        if state["mount_error"] is not None:
            raise state["mount_error"]
        return state["mounted"]

    def no_spawn(*args, **kwargs):
        pytest.fail("A runtime preflight launched a helper before refusing")

    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(Path, "is_mount", mounted)
    monkeypatch.setattr(dev, "run", no_spawn)
    for name in ("run", "Popen", "check_call", "check_output", "call"):
        monkeypatch.setattr(dev.subprocess, name, no_spawn)
    return dev, marker, state, calls


@pytest.mark.parametrize(
    "payload,error,mounted,mount_error,expected",
    [
        (b"quiet splash", None, False, None, False),
        ("quiet label=caf\u00e9".encode(), None, False, None, False),
        (b"boot=live quiet", None, False, None, True),
        ("boot=live label=caf\u00e9".encode(), None, False, None, True),
        (b"", PermissionError("fixture denied"), False, None, True),
        (b"", OSError("fixture read failure"), False, None, True),
        (b"boot=live label=\xff", None, False, None, True),
        (b"quiet label=\xff", None, False, None, True),
        (b"quiet", None, True, None, True),
        (b"quiet", None, False, OSError("fixture mount failure"), True),
    ],
    ids=(
        "normal",
        "unicode-normal",
        "live",
        "unicode-live",
        "permission-denied",
        "read-failure",
        "undecodable-live",
        "undecodable-normal",
        "mounted-live",
        "mount-failure",
    ),
)
def test_runtime_markers_return_a_conservative_boolean(
    runtime, payload, error, mounted, mount_error, expected
):
    dev, marker, state, calls = runtime
    marker.write_bytes(payload)
    state.update(read_error=error, mounted=mounted, mount_error=mount_error)
    assert dev.live_environment() is expected
    assert calls[0] == "read-marker"


@pytest.mark.parametrize("command", COMMANDS, ids=lambda argv: "-".join(argv))
def test_undecodable_runtime_refuses_before_command_helpers(runtime, command, capsys):
    dev, marker, _, calls = runtime
    marker.write_bytes(b"boot=live label=\xff")
    assert dev.main(command) == 2
    assert "Use a separate development machine" in capsys.readouterr().err
    assert calls == ["read-marker"]


@pytest.mark.parametrize(
    "operation",
    (
        "local",
        "test",
        "test-native",
        "preview",
        "preview-web",
        "desktop",
        "qualification",
    ),
)
def test_undecodable_runtime_doctor_reports_blocked_without_probes(
    runtime, operation, capsys
):
    dev, marker, _, calls = runtime
    marker.write_bytes(b"boot=live label=\xff")
    assert dev.main(["doctor", "--for", operation]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["live_environment"] is True
    assert report["status"] == "blocked"
    assert "separate development machine" in " ".join(report["problems"])
    assert calls == ["read-marker"]


@pytest.mark.parametrize("command", COMMANDS, ids=lambda argv: "-".join(argv))
def test_readable_unicode_runtime_allows_fake_command_dispatch(
    runtime, command, monkeypatch
):
    dev, marker, _, calls = runtime
    marker.write_bytes("quiet label=caf\u00e9".encode())
    helpers = []

    def run(argv, **kwargs):
        helpers.append(argv)
        return 0

    monkeypatch.setattr(dev, "run", run)
    assert dev.main(command) == 0
    assert calls == ["read-marker", "mount-check"]
    assert helpers
    if command[0] == "setup":
        assert helpers[0][1:3] == ["-m", "venv"]
        assert helpers[-1][1:4] == ["-m", "pip", "install"]
    elif command[0] == "test":
        assert helpers[0][1:3] == ["-m", "pytest"]
    elif command[0] == "preview":
        assert helpers[0][0] == "sh"
        assert helpers[0][2:] == list(command[1:])
    elif command[0] == "desktop-build":
        assert Path(helpers[0][1]).name == "build_desktop.py"
    else:
        assert [argv[1:] for argv in helpers] == [["test", "./..."], ["vet", "./..."]]


@pytest.mark.parametrize("host", ("linux", "win32", "darwin"))
def test_explicit_live_marker_needs_no_runtime_reads(runtime, monkeypatch, host):
    dev, _, _, calls = runtime
    monkeypatch.setenv("BEAMO_WIPE_LIVE", "1")
    monkeypatch.setattr(dev.sys, "platform", host)
    assert dev.live_environment() is True
    assert calls == []


@pytest.mark.parametrize("host", ("win32", "darwin"))
def test_other_hosts_need_no_linux_runtime_reads(runtime, monkeypatch, host):
    dev, _, _, calls = runtime
    monkeypatch.setattr(dev.sys, "platform", host)
    assert dev.live_environment() is False
    assert calls == []
