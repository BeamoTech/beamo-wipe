# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded ownership of the POSIX negative-gate test's shell and descendants."""

from contextlib import contextmanager
import os
import signal
import subprocess
import time

TERM_GRACE = 1.0
KILL_DRAIN = 1.0
REAP_TIMEOUT = 1.0


def _cleanup(proc):
    errors = []

    def signal_group(sig):
        try:
            # start_new_session below gives this child its own group. Never
            # signal by executable name, inherited group, or a stored old PID.
            os.killpg(proc.pid, sig)
            return True
        except ProcessLookupError:
            # A parent-side startup error can happen before setsid in the
            # child. In that case only the acquired child PID is ours.
            if proc.returncode is None:
                try:
                    proc.send_signal(sig)
                    return proc.returncode is None
                except ProcessLookupError:
                    pass
                except BaseException as exc:
                    errors.append(exc)
                    return True
            return False
        except BaseException as exc:
            errors.append(exc)
            return True

    deadline = time.monotonic() + TERM_GRACE
    signal_group(signal.SIGTERM)
    try:
        proc.communicate(timeout=max(0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        pass  # Expected escalation, not a cleanup failure.
    except BaseException as exc:
        errors.append(exc)
    # The shell can exit before a descendant which closed its output pipes.
    # Give that owned group the remainder of the same grace interval.
    while time.monotonic() < deadline and signal_group(0):
        try:
            time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        except BaseException as exc:
            errors.append(exc)
            break
    if signal_group(0):
        signal_group(signal.SIGKILL)
    try:
        proc.communicate(timeout=KILL_DRAIN)
    except BaseException as exc:
        errors.append(exc)
    try:
        # Also reap if output collection itself failed. Never use Popen's
        # context-manager exit: its wait has no timeout.
        proc.wait(timeout=REAP_TIMEOUT)
    except BaseException as exc:
        errors.append(exc)
    finally:
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                try:
                    stream.close()
                except BaseException as exc:
                    errors.append(exc)
    return errors


def _report(errors, original):
    if errors:
        detail = RuntimeError("negative-gate child cleanup failed: " + "; ".join(
            f"{type(exc).__name__}: {exc}" for exc in errors
        ))
        if original is not None:
            # Preserve the original type, instance and traceback; the explicit
            # cause records cleanup failures even on Python 3.10.
            raise original from detail
        raise detail


class _OwnedPopen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except BaseException as exc:
            # Keep access to self if Popen raises after acquiring a child PID,
            # before the context manager's assignment can take ownership.
            if getattr(self, "pid", None) is not None and self.returncode is None:
                _report(_cleanup(self), exc)
            raise


@contextmanager
def owned_gate_child(argv, *, cwd=None, env=None):
    """Own one new session until cleanup; at most 3 s of cleanup waits.

    Supported by the bash gate on Linux/macOS. Descendants must remain in the
    inherited session, as the current shell/wrapper/pytest commands do. Only
    the direct child can be reaped by this parent. Kernel failures to stop or
    reap are reported, never treated as confirmed cleanup.
    """
    if os.name != "posix":
        raise RuntimeError("negative gate requires POSIX process groups")
    proc = None
    original = None
    try:
        proc = _OwnedPopen(
            argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            start_new_session=True,
        )
        yield proc
    except BaseException as exc:
        original = exc
        raise
    finally:
        if proc is not None:
            _report(_cleanup(proc), original)
