"""Disk model continuation lines cannot arm telemetry before engine readiness."""

import signal

import pytest

from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner, nwipe_accepts_sigusr1


PHRASES = [
    "Using direct I/O", "Using cached I/O", "do not show GUI interface",
    "Program options are set as follows",
]


@pytest.mark.parametrize("prefix", ["", "info:"])
@pytest.mark.parametrize("phrase", PHRASES)
def test_model_continuation_cannot_arm_or_signal_engine(monkeypatch, prefix, phrase):
    model = "\n" + prefix + phrase
    assert len(model.encode("ascii")) <= 40
    text = f"[2026/10/16 12:00:00] info: /dev/sda, ATA, {model}, serial FAKE\n"
    # A period/space after the readiness phrase is accepted by the old parser;
    # the real suffix from the enclosing device-info record must not arm it.
    signals = []

    class Process:
        def poll(self):
            return None

        def send_signal(self, value):
            signals.append(value)

    runner = NwipeRunner()
    runner._proc = Process()
    monkeypatch.setattr(runner, "_read_log_tail", lambda *_args: text)
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sdb", "fake-log")
    assert runner.poll(request) is None
    assert signal.SIGUSR1 not in signals
    assert not runner._sigusr1_armed
    assert not nwipe_accepts_sigusr1(text)


@pytest.mark.parametrize("phrase", PHRASES)
def test_pinned_timestamped_readiness_still_signals(monkeypatch, phrase):
    text = f"[2026/10/16 12:00:00] info: {phrase}\n"
    signals = []

    class Process:
        def poll(self):
            return None

        def send_signal(self, value):
            signals.append(value)

    runner = NwipeRunner()
    runner._proc = Process()
    monkeypatch.setattr(runner, "_read_log_tail", lambda *_args: text)
    request = WipeRequest("/dev/sda", MethodId.EVERYDAY, "/dev/sdb", "fake-log")
    assert runner.poll(request) is None
    assert nwipe_accepts_sigusr1(text)
    assert runner._sigusr1_armed
    assert signals == [signal.SIGUSR1]
