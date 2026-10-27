"""Owned report-worker cleanup cannot hide an export refusal or leak handles."""

from __future__ import annotations

import os
import subprocess
import sys
import traceback

import pytest

from beamo_wipe import diagnostics
from beamo_wipe.safety import SafetyError
from test_usb_report_workflow import _fake_export_state


def _worker_fixture(tmp_path, monkeypatch, request):
    export, volume, evidence, backing_fd = _fake_export_state(tmp_path, monkeypatch)
    opened = {}
    closed = []
    diagnostic_events = []
    real_open, real_close = os.open, os.close

    def retire_owned_handles():
        # Red regressions must not strand their own fixture descriptors.
        for fd in (*opened.values(), backing_fd):
            if fd in closed:
                continue
            try:
                real_close(fd)
            except OSError:
                pass

    request.addfinalizer(retire_owned_handles)

    def track_open(path, *args, **kwargs):
        fd = real_open(path, *args, **kwargs)
        if path == export.MOUNT_ROOT:
            opened["root"] = fd
        elif path == ".lock":
            opened["lock"] = fd
        return fd

    def track_close(fd):
        closed.append(fd)
        return real_close(fd)

    monkeypatch.setattr(export.os, "open", track_open)
    monkeypatch.setattr(export.os, "close", track_close)
    monkeypatch.setattr(
        diagnostics, "log_diag", lambda *args, **kwargs: diagnostic_events.append(args)
    )
    monkeypatch.setattr(
        export, "_run_command", lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0)
    )
    monkeypatch.setattr(export, "_ordinary_unmount", lambda *_args: True)
    monkeypatch.setattr(
        export, "write_report_bundle", lambda *_args, **_kwargs: ("report-" + "a" * 24, {})
    )
    monkeypatch.setattr(export, "verify_report_bundle", lambda *_args: None)

    def run():
        return export._persist_and_verify_report(
            volume, evidence, b"", "unavailable", backing_fd
        )

    def assert_closed():
        assert {opened["lock"], opened["root"]}.issubset(closed)
        for fd in opened.values():
            with pytest.raises(OSError):
                os.fstat(fd)

    return export, run, opened, closed, diagnostic_events, assert_closed, backing_fd


@pytest.mark.parametrize("cleanup_failure", ["timeout", "inspection", "refused", "interrupt"])
def test_primary_failure_survives_unmount_cleanup_failure(
    tmp_path, monkeypatch, request, cleanup_failure
):
    export, run, _opened, _closed, events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    primary = ValueError("original mount verification failure")

    def fail_primary(*_args, **_kwargs):
        raise primary

    def fail_cleanup(*_args):
        if cleanup_failure == "timeout":
            raise subprocess.TimeoutExpired(["fixture-umount"], 15)
        if cleanup_failure == "inspection":
            raise OSError("fixture mount inspection unavailable")
        if cleanup_failure == "interrupt":
            raise KeyboardInterrupt("fixture cleanup interrupted")
        return False

    monkeypatch.setattr(export, "_verify_mount", fail_primary)
    monkeypatch.setattr(export, "_ordinary_unmount", fail_cleanup)
    try:
        with pytest.raises(BaseException) as caught:
            run()
        assert caught.value is primary
        assert "fail_primary" in [frame.name for frame in traceback.extract_tb(caught.tb)]
        assert_closed()
        assert events and events[0][:2] == ("report_export", "cleanup_failed")
        assert "unmount" in events[0][2]
    finally:
        os.close(backing_fd)


@pytest.mark.parametrize("primary_fails", [False, True])
@pytest.mark.parametrize("caller_handling_error", [False, True])
@pytest.mark.parametrize("close_error_type", [OSError, KeyboardInterrupt])
def test_first_close_failure_cannot_skip_root_close_or_return_success(
    tmp_path, monkeypatch, request, primary_fails, caller_handling_error, close_error_type
):
    export, run, opened, closed, events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    original_close = export.os.close
    primary = ValueError("original mount verification failure")
    close_error = close_error_type("fixture lock close failed")

    def first_close_fails(fd):
        original_close(fd)
        if fd == opened.get("lock"):
            raise close_error

    def fail_primary(*_args, **_kwargs):
        raise primary

    monkeypatch.setattr(export.os, "close", first_close_fails)
    if primary_fails:
        monkeypatch.setattr(export, "_verify_mount", fail_primary)

    def invoke():
        if caller_handling_error:
            try:
                raise LookupError("unrelated caller error")
            except LookupError:
                return run()
        return run()

    try:
        with pytest.raises(BaseException) as caught:
            invoke()
        assert caught.value is (primary if primary_fails else close_error)
        assert_closed()
        assert closed.count(opened["lock"]) == 1
        assert events and events[0][:2] == ("report_export", "cleanup_failed")
        assert "lock_close" in events[0][2]
    finally:
        os.close(backing_fd)


def test_failed_mount_checks_cleanup_before_closing_handles(tmp_path, monkeypatch, request):
    export, run, _opened, _closed, events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    monkeypatch.setattr(
        export, "_run_command", lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1)
    )
    monkeypatch.setattr(export, "_mounted_exact", lambda *_args: False)
    inspected = []

    def no_mount_to_remove(mountpoint, volume):
        inspected.append(mountpoint)
        assert not export._mounted_exact(mountpoint, volume)
        assert export._mount_record(mountpoint) is None
        return True

    monkeypatch.setattr(export, "_ordinary_unmount", no_mount_to_remove)
    try:
        with pytest.raises(SafetyError, match="mounted safely"):
            run()
        assert_closed()
        assert len(inspected) == 1
        assert not events
    finally:
        os.close(backing_fd)


def test_normal_export_closes_handles_and_preserves_success(tmp_path, monkeypatch, request):
    _export, run, _opened, _closed, events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    try:
        receipt = run()
        assert receipt.ok is True and receipt.safe_to_remove is True
        assert_closed()
        assert not events
    finally:
        os.close(backing_fd)


@pytest.mark.parametrize("mount_number", [1, 2], ids=["read-write", "read-only"])
@pytest.mark.parametrize("interruption", ["command", "after-command"])
def test_interrupted_mount_acquisition_attempts_identity_checked_cleanup(
    tmp_path, monkeypatch, request, mount_number, interruption
):
    export, run, _opened, _closed, events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    primary = KeyboardInterrupt("fixture interruption after fake mount")
    mounts = 0
    active = False
    unmounted = []
    fired = False

    def fake_command(command, **_kwargs):
        nonlocal mounts, active, fired
        if command[0] == export.MOUNT_BIN:
            mounts += 1
            active = True
            if mounts == mount_number and interruption == "command":
                fired = True
                raise primary
        return subprocess.CompletedProcess(command, 0)

    def fake_unmount(*_args):
        nonlocal active
        unmounted.append(mounts)
        active = False
        return True

    def interrupt_after_command(frame, event, _argument):
        nonlocal fired
        if (
            not fired
            and interruption == "after-command"
            and frame.f_code is export._persist_and_verify_report.__code__
            and event == "line"
            and mounts == mount_number
            and active
        ):
            fired = True
            raise primary
        return interrupt_after_command

    monkeypatch.setattr(export, "_run_command", fake_command)
    monkeypatch.setattr(export, "_ordinary_unmount", fake_unmount)
    previous_trace = sys.gettrace()
    try:
        sys.settrace(interrupt_after_command)
        with pytest.raises(BaseException) as caught:
            run()
        assert fired and caught.value is primary
        assert unmounted == list(range(1, mount_number + 1))
        assert not active
        assert_closed()
        assert not events
    finally:
        sys.settrace(previous_trace)
        os.close(backing_fd)


@pytest.mark.parametrize("primary_fails", [False, True])
@pytest.mark.parametrize("diagnostic_error_type", [RuntimeError, KeyboardInterrupt])
def test_optional_diagnostic_failure_cannot_replace_export_error(
    tmp_path, monkeypatch, request, primary_fails, diagnostic_error_type
):
    export, run, opened, _closed, _events, assert_closed, backing_fd = _worker_fixture(
        tmp_path, monkeypatch, request
    )
    primary = ValueError("original mount verification failure")
    close_error = OSError("fixture lock close failed")
    original_close = export.os.close

    def fail_primary(*_args, **_kwargs):
        raise primary

    def fail_unmount(*_args):
        raise OSError("fixture unmount failed")

    def fail_close(fd):
        original_close(fd)
        if fd == opened.get("lock"):
            raise close_error

    def fail_diagnostic(*_args, **_kwargs):
        raise diagnostic_error_type("optional diagnostic failed")

    monkeypatch.setattr(diagnostics, "log_diag", fail_diagnostic)
    if primary_fails:
        monkeypatch.setattr(export, "_verify_mount", fail_primary)
        monkeypatch.setattr(export, "_ordinary_unmount", fail_unmount)
    else:
        monkeypatch.setattr(export.os, "close", fail_close)
    try:
        # Capture an unexpected KeyboardInterrupt as a failed identity assertion,
        # rather than letting a deliberately injected fixture abort pytest.
        with pytest.raises(BaseException) as caught:
            run()
        assert caught.value is (primary if primary_fails else close_error)
        assert_closed()
    finally:
        os.close(backing_fd)
