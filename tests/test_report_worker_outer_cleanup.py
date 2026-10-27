"""The report worker retires only its owned descriptors on every exit path."""

from __future__ import annotations

import io
import os
import sys
import traceback
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostics, support_export as export


@pytest.fixture
def worker_state(tmp_path, monkeypatch, request):
    real_open, real_close, real_fstat = os.open, os.close, os.fstat
    paths = {stage: tmp_path / (stage + ".fixture") for stage in ("parent", "volume")}
    for path in paths.values():
        path.write_bytes(b"inert owned file")
    sentinel = real_open(tmp_path / "parent.fixture", os.O_RDONLY)
    opened, identities, closed, diagnostics_seen = {}, {}, [], []
    state = SimpleNamespace(
        open_failure=None, close_failures={}, primary=None, diagnostics_seen=diagnostics_seen,
        opened=opened, closed=closed, sentinel=sentinel, receipt=object(),
    )
    volume = SimpleNamespace(
        path="/dev/fake-report-volume", rdev=102,
        parent=SimpleNamespace(path="/dev/fake-report-parent", rdev=101),
    )

    def retire_fixture_handles():
        # A failed red test may strand its descriptors. Close only an fd still
        # referring to the exact regular-file inode opened by this fixture.
        for fd, identity in identities.items():
            try:
                current = real_fstat(fd)
            except OSError:
                continue
            if (current.st_dev, current.st_ino) == identity:
                real_close(fd)

    sentinel_stat = real_fstat(sentinel)
    identities[sentinel] = (sentinel_stat.st_dev, sentinel_stat.st_ino)
    request.addfinalizer(retire_fixture_handles)

    def owned_open(path, _flags):
        if path == volume.parent.path:
            stage = "parent"
        elif path == volume.path:
            stage = "volume"
        else:
            pytest.fail("unexpected worker open boundary")
        if state.open_failure == stage:
            raise OSError("fixture open refused")
        fd = real_open(paths[stage], os.O_RDONLY)
        opened[stage] = fd
        st = real_fstat(fd)
        identities[fd] = (st.st_dev, st.st_ino)
        return fd

    def owned_fstat(fd):
        if fd == opened.get("parent"):
            return SimpleNamespace(st_rdev=volume.parent.rdev)
        if fd == opened.get("volume"):
            return SimpleNamespace(st_rdev=volume.rdev)
        return real_fstat(fd)

    def owned_close(fd):
        assert fd != sentinel
        assert fd in opened.values()
        closed.append(fd)
        real_close(fd)
        for stage, error in state.close_failures.items():
            if fd == opened.get(stage):
                raise error

    def persist(*_args):
        if state.primary is not None:
            raise state.primary
        return state.receipt

    def forbidden_command(*_args, **_kwargs):
        pytest.fail("a cleanup fixture cannot execute a command")

    monkeypatch.setattr(export, "sys", SimpleNamespace(stdin=SimpleNamespace(buffer=io.BytesIO(b"fixture"))))
    monkeypatch.setattr(export, "_decode_worker_request", lambda _raw: (None, volume, [], (), b"", "unavailable", False))
    monkeypatch.setattr(export, "_emit_export_marker", lambda *_args: None)
    monkeypatch.setattr(export, "run_lsblk", lambda: {})
    monkeypatch.setattr(export, "select_export_volume", lambda *_args: volume)
    monkeypatch.setattr(export, "_same_volume", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(export, "_protected_rdevs", lambda *_args: ())
    monkeypatch.setattr(export, "_volume_with_rdev", lambda *_args: volume)
    monkeypatch.setattr(export, "_assert_partition_parent", lambda *_args: None)
    monkeypatch.setattr(export, "_persist_and_verify_report", persist)
    monkeypatch.setattr(export, "_run_command", forbidden_command)
    monkeypatch.setattr(export, "os", SimpleNamespace(
        O_RDONLY=os.O_RDONLY, O_NONBLOCK=os.O_NONBLOCK, O_NOFOLLOW=os.O_NOFOLLOW,
        open=owned_open, fstat=owned_fstat, close=owned_close,
    ))
    monkeypatch.setattr(diagnostics, "log_diag", lambda *args: diagnostics_seen.append(args))

    def assert_retired():
        assert len(closed) == len(set(closed)), "each owned fd is closed once"
        assert set(closed) == set(opened.values())
        for fd in opened.values():
            with pytest.raises(OSError):
                real_fstat(fd)
        assert real_fstat(sentinel).st_ino == sentinel_stat.st_ino

    state.assert_retired = assert_retired
    return state


def test_normal_worker_preserves_receipt_and_unrelated_descriptor(worker_state):
    assert export._worker() is worker_state.receipt
    worker_state.assert_retired()
    assert not worker_state.diagnostics_seen


@pytest.mark.parametrize("primary_fails", [False, True])
@pytest.mark.parametrize("stage", ["volume", "parent"])
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("caller_handling_error", [False, True])
def test_worker_close_failure_preserves_primary_and_retires_both(
    worker_state, primary_fails, stage, error_type, caller_handling_error
):
    primary = ValueError("private primary report refusal")
    cleanup = error_type("private cleanup detail")
    worker_state.primary = primary if primary_fails else None
    worker_state.close_failures[stage] = cleanup

    def invoke():
        if caller_handling_error:
            try:
                raise LookupError("unrelated caller error")
            except LookupError:
                return export._worker()
        return export._worker()

    with pytest.raises(BaseException) as caught:
        invoke()
    assert caught.value is (primary if primary_fails else cleanup)
    if primary_fails:
        assert "persist" in [frame.name for frame in traceback.extract_tb(caught.tb)]
    worker_state.assert_retired()
    events = worker_state.diagnostics_seen
    assert events and events[0][:2] == ("report_export", "cleanup_failed")
    assert stage + "_close:" + error_type.__name__ in events[0][2]
    assert "private" not in events[0][2]


@pytest.mark.parametrize("stage", ["parent", "volume"])
def test_worker_open_failure_closes_only_started_descriptors(worker_state, stage):
    worker_state.open_failure = stage
    with pytest.raises(OSError, match="fixture open refused"):
        export._worker()
    worker_state.assert_retired()
    assert set(worker_state.opened) == ({"parent"} if stage == "volume" else set())
    assert not worker_state.diagnostics_seen


def test_worker_primary_interrupt_survives_all_cleanup_failures(worker_state):
    primary = KeyboardInterrupt("primary interrupted export")
    worker_state.primary = primary
    worker_state.close_failures = {
        "volume": OSError("first cleanup failed"),
        "parent": KeyboardInterrupt("second cleanup interrupted"),
    }
    with pytest.raises(KeyboardInterrupt) as caught:
        export._worker()
    assert caught.value is primary
    worker_state.assert_retired()
    detail = worker_state.diagnostics_seen[0][2]
    assert "volume_close:OSError" in detail and "parent_close:KeyboardInterrupt" in detail


@pytest.mark.parametrize("primary_fails", [False, True])
@pytest.mark.parametrize("diagnostic_error_type", [RuntimeError, KeyboardInterrupt])
def test_worker_optional_diagnostic_cannot_replace_failure(
    worker_state, monkeypatch, primary_fails, diagnostic_error_type
):
    primary, cleanup = ValueError("original refusal"), OSError("volume close failed")
    worker_state.primary = primary if primary_fails else None
    worker_state.close_failures["volume"] = cleanup

    def fail_diagnostic(*_args):
        raise diagnostic_error_type("optional diagnostic failed")

    monkeypatch.setattr(diagnostics, "log_diag", fail_diagnostic)
    with pytest.raises(BaseException) as caught:
        export._worker()
    assert caught.value is (primary if primary_fails else cleanup)
    worker_state.assert_retired()


def test_worker_request_failure_opens_no_descriptors(worker_state, monkeypatch):
    primary = ValueError("malformed request")

    def fail_decode(_raw):
        raise primary

    monkeypatch.setattr(export, "_decode_worker_request", fail_decode)
    with pytest.raises(ValueError) as caught:
        export._worker()
    assert caught.value is primary
    assert not worker_state.opened
    worker_state.assert_retired()


def test_worker_interrupt_after_parent_acquisition_retires_owned_handle(worker_state):
    primary = KeyboardInterrupt("fixture interruption after parent acquisition")
    previous_trace = sys.gettrace()
    fired = False

    def interrupt_after_parent(frame, event, _argument):
        nonlocal fired
        if (
            not fired
            and frame.f_code is export._worker.__code__
            and event == "line"
            and "parent" in worker_state.opened
            and "volume" not in worker_state.opened
        ):
            fired = True
            raise primary
        return interrupt_after_parent

    try:
        sys.settrace(interrupt_after_parent)
        with pytest.raises(KeyboardInterrupt) as caught:
            export._worker()
    finally:
        sys.settrace(previous_trace)

    assert fired and caught.value is primary
    assert set(worker_state.opened) == {"parent"}
    worker_state.assert_retired()
    assert not worker_state.diagnostics_seen
