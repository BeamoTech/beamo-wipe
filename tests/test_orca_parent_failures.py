"""Orca parent diagnostics and cleanup use inert children, never a real display."""

import subprocess
from types import SimpleNamespace

import pytest

pytest.importorskip("gi")
import test_accessible_runtime as runtime  # noqa: E402


def parent(monkeypatch, tmp_path, run, *, stop_error=None):
    calls = []
    child = object()
    directory = tmp_path / "runtime"
    monkeypatch.delenv("BEAMO_TEST_ORCA_CHILD", raising=False)
    monkeypatch.delenv("BEAMO_HOSTED_ORCA_SEPARATE", raising=False)

    def start():
        calls.append("start-display")
        return child, ":fake"

    def stop(observed):
        assert observed is child
        calls.append("stop-display")
        if stop_error is not None:
            raise stop_error

    def child_env(display, path):
        assert display == ":fake" and path == directory
        return {"BEAMO_TEST_ORCA_CHILD": "1"}

    def execute(argv, **kwargs):
        calls.append("run")
        assert argv == [
            "dbus-run-session", "--", runtime.sys.executable, "-m", "pytest",
            "-p", "no:cacheprovider",
            f"{runtime.__file__}::test_orca_announces_every_result",
        ]
        assert kwargs == {
            "env": {"BEAMO_TEST_ORCA_CHILD": "1"},
            "capture_output": True,
            "text": True,
            "timeout": 300,
        }
        return run(argv)

    def no_ui(_name):
        pytest.fail("The parent must not construct a GTK window")

    monkeypatch.setattr(runtime, "_start_private_xvfb", start)
    monkeypatch.setattr(runtime, "_stop_private_xvfb", stop)
    monkeypatch.setattr(runtime, "_orca_runtime_dir", lambda: SimpleNamespace(
        name=str(directory), cleanup=lambda: calls.append("cleanup-runtime"),
    ))
    monkeypatch.setattr(runtime, "_orca_child_env", child_env)
    monkeypatch.setattr(runtime.subprocess, "run", execute)
    return calls, SimpleNamespace(getfixturevalue=no_ui)


@pytest.mark.parametrize(
    "stdout,stderr,expected",
    [
        (b"stdout before timeout\n", b"stderr before timeout\n", "stdout before timeout\nstderr before timeout\n"),
        (b"stdout only", None, "stdout only"),
        (None, b"stderr only", "stderr only"),
        (None, None, ""),
        ("text stdout\n", "text stderr", "text stdout\ntext stderr"),
        (b"mixed stdout\n", "mixed stderr", "mixed stdout\nmixed stderr"),
        (b"x" * 5000 + b"invalid \xff\n", b"final stderr", "x" * 3978 + "invalid \ufffd\nfinal stderr"),
    ],
    ids=["bytes", "stdout-only", "stderr-only", "empty", "text", "mixed", "invalid-utf8-tail"],
)
def test_parent_timeout_preserves_bounded_diagnostic_and_cleanup(
    monkeypatch, tmp_path, stdout, stderr, expected,
):
    def timeout(argv):
        raise subprocess.TimeoutExpired(argv, 300, output=stdout, stderr=stderr)

    calls, request = parent(monkeypatch, tmp_path, timeout)
    with pytest.raises(pytest.fail.Exception, match="Orca child exceeded 300s") as caught:
        runtime.test_orca_announces_every_result(tmp_path, request)
    assert str(caught.value) == "Orca child exceeded 300s on private Xvfb/XDG_RUNTIME_DIR: " + expected
    assert len(str(caught.value)) <= 4100
    assert calls == ["start-display", "run", "stop-display", "cleanup-runtime"]


def test_display_cleanup_failure_still_retires_runtime(monkeypatch, tmp_path):
    error = OSError("owned fake display cleanup failed")
    calls, request = parent(
        monkeypatch, tmp_path,
        lambda _argv: SimpleNamespace(returncode=0, stdout="", stderr=""),
        stop_error=error,
    )
    with pytest.raises(OSError) as caught:
        runtime.test_orca_announces_every_result(tmp_path, request)
    assert caught.value is error
    assert calls == ["start-display", "run", "stop-display", "cleanup-runtime"]


@pytest.mark.parametrize("returncode", [0, 1])
def test_parent_retains_child_pass_or_failure(monkeypatch, tmp_path, returncode):
    calls, request = parent(monkeypatch, tmp_path, lambda _argv: SimpleNamespace(
        returncode=returncode, stdout="child stdout", stderr="child stderr",
    ))
    if returncode:
        with pytest.raises(AssertionError, match="child stdoutchild stderr"):
            runtime.test_orca_announces_every_result(tmp_path, request)
    else:
        runtime.test_orca_announces_every_result(tmp_path, request)
    assert calls == ["start-display", "run", "stop-display", "cleanup-runtime"]
