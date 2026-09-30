# SPDX-License-Identifier: GPL-3.0-or-later
"""Harmless synchronized children; never run nwipe or inspect host disks."""

from contextlib import contextmanager
import os
import selectors
import signal
import subprocess
import sys
import time

import pytest

from negative_gate_child import owned_gate_child

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX negative-gate lifecycle")
SLEEPER = "import time; print('ready', flush=True); time.sleep(30)"
STUBBORN = "import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); " + SLEEPER


def ready(proc):
    with selectors.DefaultSelector() as selector:
        selector.register(proc.stdout, selectors.EVENT_READ)
        assert selector.select(timeout=3), "child did not signal readiness"
        assert os.read(proc.stdout.fileno(), 1024).strip() == b"ready"


def reaped(proc):
    assert proc.returncode is not None
    assert proc.stdout.closed
    assert proc.stdin is None and proc.stderr is None
    with pytest.raises(ChildProcessError):
        os.waitpid(proc.pid, os.WNOHANG)


@pytest.mark.parametrize("failure", [AssertionError("assertion"), RuntimeError("unexpected"),
                                    KeyboardInterrupt(), SystemExit(3)])
def test_body_failures_preserve_exception_reap_child_and_leave_sentinel(failure):
    with owned_gate_child([sys.executable, "-c", SLEEPER]) as sentinel:
        ready(sentinel)
        started = time.monotonic()
        with pytest.raises(type(failure)) as caught:
            with owned_gate_child([sys.executable, "-c", SLEEPER]) as proc:
                ready(proc)
                assert os.getpgid(proc.pid) == proc.pid != os.getpgid(sentinel.pid)
                raise failure
        assert caught.value is failure
        reaped(proc)
        assert time.monotonic() - started < 5
        assert sentinel.poll() is None
    reaped(sentinel)


def test_timeout_escalates_only_stubborn_owned_child():
    with owned_gate_child([sys.executable, "-c", SLEEPER]) as sentinel:
        ready(sentinel)
        started = time.monotonic()
        with pytest.raises(subprocess.TimeoutExpired):
            with owned_gate_child([sys.executable, "-c", STUBBORN]) as proc:
                ready(proc)  # SIGTERM is ignored before readiness is announced.
                proc.communicate(timeout=0.05)
        assert proc.returncode == -signal.SIGKILL
        reaped(proc)
        assert time.monotonic() - started < 5
        assert sentinel.poll() is None


@pytest.mark.parametrize("exit_code", [0, 7])
def test_early_exit_and_success_close_pipes(exit_code):
    with owned_gate_child([sys.executable, "-c", f"print('done'); raise SystemExit({exit_code})"]) as proc:
        output, _ = proc.communicate(timeout=3)
        assert output == "done\n" and proc.returncode == exit_code
    reaped(proc)


def test_launch_failure_does_not_enter_body_or_signal_sentinel(tmp_path):
    with owned_gate_child([sys.executable, "-c", SLEEPER]) as sentinel:
        ready(sentinel)
        with pytest.raises(FileNotFoundError):
            with owned_gate_child([str(tmp_path / "nonexistent-child")]):
                pytest.fail("failed launch entered body")
        assert sentinel.poll() is None


@pytest.mark.parametrize("new_session", [True, False])
def test_startup_exception_after_child_acquired_still_reaps(monkeypatch, new_session):
    original_init = subprocess.Popen.__init__
    failure = OSError("parent-side startup failed after fork")
    processes = []
    def broken_init(self, *args, **kwargs):
        kwargs["start_new_session"] = new_session
        original_init(self, *args, **kwargs)
        processes.append(self)
        ready(self)
        raise failure
    monkeypatch.setattr(subprocess.Popen, "__init__", broken_init)
    with pytest.raises(OSError) as caught:
        with owned_gate_child([sys.executable, "-c", SLEEPER]):
            pytest.fail("partially failed launch entered body")
    assert caught.value is failure
    reaped(processes[0])
    # The no-session simulation must signal only the owned PID, never our group.
    assert os.getpgrp() != processes[0].pid


def test_repeated_runs_reap_and_close_every_pipe():
    for _ in range(8):
        with owned_gate_child([sys.executable, "-c", "print('ok')"]) as proc:
            assert proc.communicate(timeout=3)[0] == "ok\n"
        reaped(proc)


def test_output_larger_than_pipe_capacity_is_drained():
    with owned_gate_child([sys.executable, "-c", "import sys; sys.stdout.write('x' * 1048576)"]) as proc:
        assert len(proc.communicate(timeout=3)[0]) == 1048576
    reaped(proc)


def test_output_collection_error_still_reaps_and_records_cleanup_error(monkeypatch):
    failure = OSError("output collection failed")
    with pytest.raises(OSError) as caught:
        with owned_gate_child([sys.executable, "-c", SLEEPER]) as proc:
            ready(proc)
            def broken_collection(*_args, **_kwargs):
                raise failure
            monkeypatch.setattr(proc, "communicate", broken_collection)
            proc.communicate(timeout=0.1)
    assert caught.value is failure
    assert "cleanup failed" in str(caught.value.__cause__)
    assert "output collection failed" in str(caught.value.__cause__)
    reaped(proc)


def test_cleanup_failure_is_not_success_without_an_original_error(monkeypatch):
    with pytest.raises(RuntimeError, match="cleanup failed"):
        with owned_gate_child([sys.executable, "-c", SLEEPER]) as proc:
            ready(proc)
            def broken_collection(*_args, **_kwargs):
                raise OSError("collection unavailable")
            monkeypatch.setattr(proc, "communicate", broken_collection)
    reaped(proc)


def test_descendant_inherits_owned_group_and_is_reaped_by_its_parent(tmp_path):
    receipt = tmp_path / "descendant-reaped"
    child_code = '''
import os, pathlib, select, signal, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; print("child", flush=True); time.sleep(30)'], stdout=subprocess.PIPE)
assert select.select([child.stdout], [], [], 2)[0]
assert os.read(child.stdout.fileno(), 1024) == b'child\\n'
assert os.getpgid(child.pid) == os.getpgrp()
def stop(*_args):
    code = child.wait(timeout=.8)
    child.stdout.close()
    pathlib.Path(sys.argv[1]).write_text(str(code))
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
print('ready', flush=True)
time.sleep(30)
'''
    with owned_gate_child([sys.executable, "-c", child_code, str(receipt)]) as proc:
        ready(proc)
    reaped(proc)
    assert receipt.read_text() == str(-signal.SIGTERM)
    assert proc.returncode == 0  # Parent's graceful handler reaped its child.


def test_negative_test_timeout_now_reaps_owned_child(tmp_path, monkeypatch):
    import test_boot_pipeline_pass5_negative as gate

    processes = []
    @contextmanager
    def slow_gate(_argv, *, cwd, env):
        code = ("import os,pathlib,time; "
                "pathlib.Path(os.environ['BEAMO_NEGATIVE_PROBE_MARKER']).touch(); time.sleep(30)")
        with owned_gate_child([sys.executable, "-c", code], cwd=cwd, env=env) as proc:
            processes.append(proc)
            real_communicate = proc.communicate
            def timeout_once(*args, **kwargs):
                proc.communicate = real_communicate
                kwargs['timeout'] = .05
                return real_communicate(*args, **kwargs)
            proc.communicate = timeout_once
            yield proc
    monkeypatch.setattr(gate, "owned_gate_child", slow_gate)
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        gate.test_negative_gate_mutates_only_private_source(tmp_path)
    reaped(processes[0])
    assert time.monotonic() - started < 5


def test_shared_source_violation_still_fails_and_reaps(tmp_path, monkeypatch):
    import test_boot_pipeline_pass5_negative as gate

    processes = []
    @contextmanager
    def corrupt_fake_checkout(_argv, *, cwd, env):
        code = ("import os,pathlib; "
                "p=pathlib.Path('src/beamo_wipe/safety.py'); p.write_bytes(p.read_bytes()+b'\\n# forbidden shared mutation\\n'); "
                "pathlib.Path(os.environ['BEAMO_NEGATIVE_PROBE_MARKER']).touch()")
        with owned_gate_child([sys.executable, "-c", code], cwd=cwd, env=env) as proc:
            processes.append(proc)
            yield proc
    monkeypatch.setattr(gate, "owned_gate_child", corrupt_fake_checkout)
    with pytest.raises(AssertionError, match="changed its checkout's safety.py"):
        gate.test_negative_gate_mutates_only_private_source(tmp_path)
    reaped(processes[0])


def test_removed_boot_guard_still_causes_expected_negative_failure(monkeypatch):
    import test_boot_exclusion_fails_closed as safety_test

    monkeypatch.setattr(safety_test, "assert_boot_excluded", lambda _discovery: None)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        safety_test.test_boot_guard_rejects_false_identity_with_otherwise_selectable_target()
