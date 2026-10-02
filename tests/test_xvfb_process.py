"""Deterministic private-display ownership and readiness regressions."""

from pathlib import Path
import subprocess

import pytest

import xvfb_process as xvfb


class FakeProcess:
    def __init__(self, *, exited=False, ignore_term=False):
        self.returncode = 0 if exited else None
        self.ignore_term = ignore_term
        self.terminated = 0
        self.killed = 0
        self.waits = []

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated += 1
        if not self.ignore_term:
            self.returncode = 0

    def kill(self):
        self.killed += 1
        self.returncode = -9

    def wait(self, *, timeout):
        self.waits.append(timeout)
        if self.returncode is None:
            raise subprocess.TimeoutExpired("owned fake Xvfb", timeout)
        return self.returncode


@pytest.fixture
def harness(monkeypatch):
    class Harness:
        now = 0.0

        def __init__(self):
            self.children = []
            self.launches = []
            self.probes = []
            self.factory = FakeProcess

        def sleep(self, seconds):
            self.now += seconds

        def popen(self, argv, **kwargs):
            proc = self.factory()
            self.children.append(proc)
            self.launches.append((argv, kwargs))
            return proc

        def run(self, argv, **kwargs):
            self.probes.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0)

    state = Harness()
    monkeypatch.setattr(xvfb.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(xvfb.Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(xvfb.os.path, "exists", lambda path: False)
    monkeypatch.setattr(xvfb.time, "monotonic", lambda: state.now)
    monkeypatch.setattr(xvfb.time, "sleep", state.sleep)
    monkeypatch.setattr(xvfb.subprocess, "Popen", state.popen)
    monkeypatch.setattr(xvfb.subprocess, "run", state.run)
    return state


def test_client_connection_is_ready_without_filesystem_socket(harness):
    proc, display = xvfb.start_private_xvfb()
    assert display == ":110"
    assert proc is harness.children[0]
    assert proc.poll() is None
    assert harness.probes == [
        (["xdpyinfo", "-display", ":110"],
         {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "timeout": 1})
    ]
    argv, options = harness.launches[0]
    assert argv == ["Xvfb", ":110", "-screen", "0", "1600x1000x24", "-dpi", "72",
                    "-nolisten", "tcp", "-ac"]
    assert options == {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    xvfb.stop_private_xvfb(proc)
    assert proc.terminated == 1 and proc.killed == 0 and proc.waits == [5]


@pytest.mark.parametrize("missing", ["Xvfb", "xdpyinfo"])
def test_missing_tool_is_an_actionable_failure(harness, monkeypatch, missing):
    monkeypatch.setattr(xvfb.shutil, "which", lambda command: None if command == missing else command)
    with pytest.raises(AssertionError, match=f"require {missing}.*xvfb and x11-utils"):
        xvfb.start_private_xvfb()
    assert not harness.children


@pytest.mark.parametrize("occupied", ["/tmp/.X110-lock", "/tmp/.X11-unix/X110"])
def test_occupied_display_is_not_started_or_stopped(harness, monkeypatch, occupied):
    sentinel = FakeProcess()
    monkeypatch.setattr(xvfb.os.path, "exists", lambda path: path == occupied)
    proc, display = xvfb.start_private_xvfb()
    assert display == ":111"
    xvfb.stop_private_xvfb(proc)
    assert sentinel.poll() is None and sentinel.terminated == sentinel.killed == 0
    assert sentinel.waits == []


def test_all_displays_occupied_fails_without_launch(harness, monkeypatch):
    monkeypatch.setattr(xvfb.os.path, "exists", lambda path: True)
    with pytest.raises(RuntimeError, match="could not start"):
        xvfb.start_private_xvfb()
    assert not harness.children and not harness.probes


@pytest.mark.parametrize("failure", ["timeout", "rejected"])
def test_unready_probes_have_bounded_attempts_and_reap_each_child(harness, monkeypatch, failure):
    def unready(argv, **kwargs):
        harness.probes.append((argv, kwargs))
        if failure == "timeout":
            harness.now += kwargs["timeout"]
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        return subprocess.CompletedProcess(argv, 1)

    monkeypatch.setattr(xvfb.subprocess, "run", unready)
    with pytest.raises(RuntimeError, match="could not start"):
        xvfb.start_private_xvfb()
    assert len(harness.children) == 31
    assert all(proc.terminated == 1 and proc.waits == [5] for proc in harness.children)
    assert 155 <= harness.now < 157
    assert all(0 < kwargs["timeout"] <= 1 for _, kwargs in harness.probes)


def test_early_exits_are_reaped_without_probe(harness):
    harness.factory = lambda: FakeProcess(exited=True)
    with pytest.raises(RuntimeError, match="could not start"):
        xvfb.start_private_xvfb()
    assert len(harness.children) == 31
    assert all(proc.waits == [5] and proc.terminated == proc.killed == 0
               for proc in harness.children)
    assert not harness.probes


def test_server_exit_during_successful_probe_is_not_ready(harness, monkeypatch):
    def probe(argv, **kwargs):
        harness.probes.append((argv, kwargs))
        if len(harness.children) == 1:
            harness.children[0].returncode = 1
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(xvfb.subprocess, "run", probe)
    proc, display = xvfb.start_private_xvfb()
    assert display == ":111"
    assert harness.children[0].waits == [5]
    xvfb.stop_private_xvfb(proc)


@pytest.mark.parametrize("error", [RuntimeError("probe failed"), KeyboardInterrupt()])
def test_probe_exception_or_interruption_reaps_owned_child(harness, monkeypatch, error):
    def broken_probe(*args, **kwargs):
        raise error

    monkeypatch.setattr(xvfb.subprocess, "run", broken_probe)
    with pytest.raises(type(error)) as caught:
        xvfb.start_private_xvfb()
    assert caught.value is error
    assert len(harness.children) == 1
    assert harness.children[0].terminated == 1
    assert harness.children[0].waits == [5]


def test_cleanup_error_preserves_original_exception(harness, monkeypatch, caplog):
    error = RuntimeError("original probe failure")

    def broken_probe(*args, **kwargs):
        raise error

    def broken_cleanup(proc):
        raise OSError("controlled cleanup error")

    monkeypatch.setattr(xvfb.subprocess, "run", broken_probe)
    monkeypatch.setattr(xvfb, "stop_private_xvfb", broken_cleanup)
    with pytest.raises(RuntimeError) as caught:
        xvfb.start_private_xvfb()
    assert caught.value is error
    diagnostics = " ".join(getattr(error, "__notes__", [])) + caplog.text
    assert "controlled cleanup error" in diagnostics


def test_launch_failure_has_no_owned_child_to_stop(harness, monkeypatch):
    def failed_launch(*args, **kwargs):
        raise OSError("controlled launch failure")

    monkeypatch.setattr(xvfb.subprocess, "Popen", failed_launch)
    with pytest.raises(OSError, match="controlled launch failure"):
        xvfb.start_private_xvfb()
    assert not harness.children and not harness.probes


def test_stubborn_child_is_killed_and_reaped(harness):
    proc = FakeProcess(ignore_term=True)
    xvfb.stop_private_xvfb(proc)
    assert proc.terminated == proc.killed == 1
    assert proc.waits == [5, 5] and proc.poll() == -9


def test_repeated_start_and_stop_leave_every_owned_child_reaped(harness):
    for _ in range(5):
        proc, _display = xvfb.start_private_xvfb()
        xvfb.stop_private_xvfb(proc)
    assert len(harness.children) == 5
    assert all(proc.poll() == 0 and proc.waits == [5] for proc in harness.children)


def test_readiness_tool_is_declared_for_all_linux_setup_paths():
    root = Path(__file__).resolve().parents[1]
    assert "xvfb x11-utils" in (root / "scripts/ci-hosted.sh").read_text(encoding="utf-8")
    assert "xvfb x11-utils" in (root / "docs/development.md").read_text(encoding="utf-8")
    installer = (root / ".cursor/install.sh").read_text(encoding="utf-8")
    required_packages = installer.split("REQUIRED_PKGS=(", 1)[1].split("\n)", 1)[0]
    assert "x11-utils" in required_packages.split()
