"""The Orca gate retires its owned children across startup and cleanup errors."""

import subprocess
from types import SimpleNamespace

import pytest

pytest.importorskip("gi")
import test_accessible_runtime as runtime  # noqa: E402


@pytest.mark.parametrize(
    "stage",
    ["reader-start", "reader-terminate", "reader-wait", "normal", "reader-timeout", "audio-exited"],
)
def test_orca_gate_always_attempts_audio_cleanup(monkeypatch, tmp_path, stage):
    calls = []
    body_error = RuntimeError("owned fake UI interruption")
    child_error = OSError("owned fake reader failure")
    monkeypatch.setenv("BEAMO_TEST_ORCA_CHILD", "1")
    monkeypatch.delenv("BEAMO_HOSTED_ORCA_SEPARATE", raising=False)
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/owned/fake-bus")
    monkeypatch.setattr("shutil.which", lambda _name: "/owned/fake-orca")

    class Child:
        def __init__(self, name):
            self.name = name
            self.waits = 0

        def poll(self):
            calls.append((self.name, "poll"))
            return 0 if self.name == "audio" and stage == "audio-exited" else None

        def terminate(self):
            calls.append((self.name, "terminate"))
            if self.name == "reader" and stage == "reader-terminate":
                raise child_error

        def kill(self):
            calls.append((self.name, "kill"))

        def wait(self, timeout):
            calls.append((self.name, "wait", timeout))
            self.waits += 1
            if self.name == "reader" and stage == "reader-wait":
                raise child_error
            if self.name == "reader" and stage == "reader-timeout" and self.waits == 1:
                raise subprocess.TimeoutExpired("owned-fake-reader", timeout)
            return 0

    audio, reader = Child("audio"), Child("reader")

    def popen(argv, **kwargs):
        assert kwargs == {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if argv[0] == "pulseaudio":
            calls.append(("audio", "start"))
            return audio
        assert argv[:2] == [runtime.sys.executable, "-c"]
        calls.append(("reader", "start"))
        if stage == "reader-start":
            raise child_error
        return reader

    def fail_ui_step():
        raise body_error

    monkeypatch.setattr(runtime.subprocess, "Popen", popen)
    monkeypatch.setattr(runtime, "drain", fail_ui_step)
    request = SimpleNamespace(getfixturevalue=lambda name: object())
    expected = child_error if stage in {"reader-start", "reader-terminate", "reader-wait"} else body_error
    with pytest.raises(type(expected)) as caught:
        runtime.test_orca_announces_every_result(tmp_path, request)
    assert caught.value is expected
    assert calls[:2] == [("audio", "start"), ("reader", "start")]
    if stage != "audio-exited":
        assert calls[-2:] == [("audio", "terminate"), ("audio", "wait", 5)]
    else:
        assert ("audio", "terminate") not in calls
    if stage == "reader-start":
        assert ("reader", "terminate") not in calls
    elif stage == "reader-timeout":
        assert [call for call in calls if call[0] == "reader"] == [
            ("reader", "start"),
            ("reader", "terminate"),
            ("reader", "wait", 10),
            ("reader", "kill"),
            ("reader", "wait", 5),
        ]
