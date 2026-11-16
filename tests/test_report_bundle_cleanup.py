"""Bundle helpers preserve refusal identity and retire only acquired handles."""

import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostics, support_export as export


@pytest.fixture
def bundle_state(monkeypatch):
    state = SimpleNamespace(opened=[], closed=[], primary=None, close_errors={}, events=[])

    def open_directory(*_args, **_kwargs):
        fd = 10 + len(state.opened)
        state.opened.append(fd)
        return fd

    def close_directory(fd):
        assert fd in state.opened
        assert fd not in state.closed
        state.closed.append(fd)
        if fd in state.close_errors:
            raise state.close_errors[fd]

    def io_boundary(*_args, **_kwargs):
        if state.primary is not None:
            raise state.primary
        return b"data"

    monkeypatch.setattr(export, "os", SimpleNamespace(
        O_RDONLY=os.O_RDONLY, O_DIRECTORY=os.O_DIRECTORY, O_NOFOLLOW=os.O_NOFOLLOW,
        open=open_directory, close=close_directory, mkdir=lambda *_a, **_k: None,
        fsync=lambda *_a: None, listdir=lambda *_a: ["DATA", "COMPLETE"],
    ))
    monkeypatch.setattr(export, "_bundle_files", lambda *_a, **_k: {"DATA": b"data", "COMPLETE": b"data"})
    monkeypatch.setattr(export, "_write_exclusive", io_boundary)
    monkeypatch.setattr(export, "_read_at", io_boundary)
    monkeypatch.setattr(diagnostics, "log_diag", lambda *args: state.events.append(args))
    return state


def invoke(helper):
    if helper == "write":
        return export.write_report_bundle(Path("/inert/mount"), b"", b"", "unavailable", session_name="report-" + "a" * 24)
    return export.verify_report_bundle(Path("/inert/mount"), "report-" + "a" * 24, {"DATA": b"data", "COMPLETE": b"data"})


@pytest.mark.parametrize("helper", ["write", "verify"])
@pytest.mark.parametrize("primary_fails", [False, True])
@pytest.mark.parametrize("close_fd", [10, 11, 12])
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
def test_bundle_cleanup_preserves_primary_and_closes_every_directory(
    bundle_state, helper, primary_fails, close_fd, error_type
):
    primary = export.SafetyError("private original I/O refusal")
    close_error = error_type("private cleanup detail")
    bundle_state.primary = primary if primary_fails else None
    bundle_state.close_errors[close_fd] = close_error
    with pytest.raises(BaseException) as caught:
        invoke(helper)
    assert caught.value is (primary if primary_fails else close_error)
    assert bundle_state.closed == [12, 11, 10]
    assert bundle_state.events and bundle_state.events[0][:2] == ("report_export", "cleanup_failed")
    assert "private" not in bundle_state.events[0][2]


@pytest.mark.parametrize("helper", ["write", "verify"])
def test_bundle_normal_control_has_no_cleanup_diagnostic(bundle_state, helper):
    invoke(helper)
    assert bundle_state.opened == [10, 11, 12]
    assert bundle_state.closed == [12, 11, 10]
    assert not bundle_state.events


@pytest.mark.parametrize("helper", ["write", "verify"])
def test_bundle_interrupted_acquisition_retires_mount_directory(bundle_state, helper):
    function = export.write_report_bundle if helper == "write" else export.verify_report_bundle
    primary = KeyboardInterrupt("fixture interruption after mount-directory open")
    previous = sys.gettrace()
    fired = False

    def interrupt(frame, event, _arg):
        nonlocal fired
        if not fired and frame.f_code is function.__code__ and event == "line" and bundle_state.opened:
            fired = True
            raise primary
        return interrupt

    try:
        sys.settrace(interrupt)
        with pytest.raises(KeyboardInterrupt) as caught:
            invoke(helper)
    finally:
        sys.settrace(previous)
    assert fired and caught.value is primary
    assert bundle_state.opened == bundle_state.closed == [10]
    assert not bundle_state.events


@pytest.mark.parametrize("helper", ["write", "verify"])
def test_bundle_multiple_cleanup_failures_preserve_first(bundle_state, helper):
    first = OSError("first close error")
    bundle_state.close_errors = {12: first, 11: KeyboardInterrupt("second close error")}
    with pytest.raises(BaseException) as caught:
        invoke(helper)
    assert caught.value is first
    assert bundle_state.closed == [12, 11, 10]


def test_mount_open_file_exists_error_is_not_treated_as_existing_reports(bundle_state, monkeypatch):
    primary = FileExistsError("mount open refused")

    def refuse_open(*_args, **_kwargs):
        raise primary

    monkeypatch.setattr(export.os, "open", refuse_open)
    with pytest.raises(FileExistsError) as caught:
        invoke("write")
    assert caught.value is primary
    assert bundle_state.opened == bundle_state.closed == []


def test_existing_reports_directory_is_reused(bundle_state, monkeypatch):
    def existing_reports(name, *_args, **_kwargs):
        if name == export.REPORTS_DIR:
            raise FileExistsError("existing reports directory")

    monkeypatch.setattr(export.os, "mkdir", existing_reports)
    invoke("write")
    assert bundle_state.opened == [10, 11, 12]
    assert bundle_state.closed == [12, 11, 10]
