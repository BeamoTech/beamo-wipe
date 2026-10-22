"""Owned recovery publication, using only ordinary temporary files/fake disks.

These hooks model same-owner replacement in a private directory. They prove
bounded checks at publication boundaries, not an atomic filesystem compare/swap.
"""

import errno
import json
import os
from types import SimpleNamespace

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError
from beamo_wipe.session_recovery import NAME, SessionStore
from test_session_recovery import BOOT, BUILD, armed


@pytest.fixture(params=["preference", "journal"])
def publication(request, tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    directory = tmp_path / "private"
    if request.param == "preference":
        directory.mkdir(mode=0o700)
        store = ReportIntentStore(directory)
        store.save(False)
        prefix, name = ".report-intent-", store.NAME
        def operation():
            return store.save(True)
    else:
        store = SessionStore(directory, boot=BOOT, build=BUILD).open()
        prefix, name = ".recovery-", NAME
        def operation():
            return armed(store)
    destination = directory / name
    case = SimpleNamespace(
        kind=request.param, directory=directory, store=store,
        prefix=prefix, destination=destination, operation=operation,
        old=destination.read_bytes(),
    )
    try:
        yield case
    finally:
        if request.param == "journal":
            store.close()


def assert_saved(case):
    if case.kind == "preference":
        assert case.store.load() is True
    else:
        assert not case.store.invalid
        assert case.store.record["phase"] == "armed"
        assert json.loads(case.destination.read_bytes())["payload"]["phase"] == "armed"


def replace_entry(case, path, mutation):
    """Return the foreign entry, retaining the owned inode as an ordinary file."""
    if mutation in {"opposite", "same-size"}:
        content = case.old if mutation == "opposite" else path.read_bytes().replace(
            b"wanted" if case.kind == "preference" else b"armed",
            b"WANTED" if case.kind == "preference" else b"armXd", 1,
        )
        path.write_bytes(content)
        return None
    path.rename(case.directory / "retired-owned-temporary")
    if mutation == "remove":
        return None
    if mutation == "symlink":
        target = case.directory / "symlink-target"
        target.write_bytes(case.old)
        target.chmod(0o600)
        path.symlink_to(target)
    elif mutation == "hardlink":
        target = case.directory / "hardlink-target"
        target.write_bytes(case.old)
        target.chmod(0o600)
        os.link(target, path)
    elif mutation == "fifo":
        os.mkfifo(path, 0o600)
    elif mutation == "directory":
        path.mkdir(mode=0o700)
    else:
        path.write_bytes(case.old)
        path.chmod(0o600)
    return path.lstat()


def assert_same_entry(path, expected):
    actual = path.lstat()
    assert (actual.st_dev, actual.st_ino, actual.st_mode) == (
        expected.st_dev, expected.st_ino, expected.st_mode,
    )


@pytest.mark.parametrize("mutation", [
    "replace", "remove", "symlink", "hardlink", "fifo", "directory",
    "opposite", "same-size",
])
def test_changed_temporary_is_refused_before_publication(publication, monkeypatch, mutation):
    case = publication
    real_sync = os.fsync
    changed = []

    def sync(fd):
        real_sync(fd)
        for path in case.directory.glob(case.prefix + "*"):
            if not changed and os.fstat(fd).st_ino == path.stat().st_ino:
                changed.append((path, replace_entry(case, path, mutation)))

    monkeypatch.setattr(os, "fsync", sync)
    with pytest.raises((OSError, SafetyError)):
        case.operation()
    assert len(changed) == 1
    assert case.destination.read_bytes() == case.old
    path, foreign = changed[0]
    if foreign is not None:
        assert_same_entry(path, foreign)


@pytest.mark.parametrize("mutation", ["replace", "opposite", "same-size"])
def test_changed_published_entry_is_not_reported_saved(publication, monkeypatch, mutation):
    case = publication
    real_replace = os.replace
    changed = []

    def replace(source, destination, **kwargs):
        real_replace(source, destination, **kwargs)
        changed.append(replace_entry(case, case.destination, mutation))

    monkeypatch.setattr(os, "replace", replace)
    with pytest.raises((OSError, SafetyError)):
        case.operation()
    assert len(changed) == 1
    if case.kind == "journal":
        assert case.store.invalid
        with pytest.raises(SafetyError):
            case.store.save({})


@pytest.mark.parametrize("boundary", ["write", "fsync"])
def test_failed_save_preserves_foreign_temporary(publication, monkeypatch, boundary):
    case = publication
    real_write, real_sync, real_open = os.write, os.fsync, os.open
    opened, changed = [], []

    def track_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if str(path).startswith(case.prefix):
            opened.append(fd)
        return fd

    def fail(fd, *args):
        if fd in opened and not changed:
            path = next(case.directory.glob(case.prefix + "*"))
            changed.append((path, replace_entry(case, path, "replace")))
            raise OSError(errno.EIO, "fake publication storage failure")
        return real_write(fd, *args) if boundary == "write" else real_sync(fd)

    monkeypatch.setattr(os, "open", track_open)
    monkeypatch.setattr(os, boundary, fail)
    with pytest.raises(OSError, match="fake publication storage failure"):
        case.operation()
    assert len(changed) == len(opened) == 1
    assert_same_entry(*changed[0])
    assert case.destination.read_bytes() == case.old
    with pytest.raises(OSError) as error:
        os.fstat(opened[0])
    assert error.value.errno == errno.EBADF


@pytest.mark.parametrize("boundary", ["write", "fsync", "replace"])
def test_ordinary_precommit_storage_failure_allows_retry(publication, monkeypatch, boundary):
    case = publication
    real = getattr(os, boundary)
    failed = []

    def fail_once(*args, **kwargs):
        if not failed:
            failed.append(True)
            raise OSError(errno.EIO, "fake recoverable storage failure")
        return real(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, boundary, fail_once)
        with pytest.raises(OSError, match="fake recoverable storage failure"):
            case.operation()
    assert case.destination.read_bytes() == case.old
    assert not list(case.directory.glob(case.prefix + "*"))
    case.operation()
    assert_saved(case)


@pytest.mark.parametrize("short_io", ["normal", "write", "read"])
def test_exact_publication_survives_short_io(publication, monkeypatch, short_io):
    case = publication
    if short_io == "write":
        real_write = os.write
        monkeypatch.setattr(os, "write", lambda fd, data: real_write(fd, data[:2]))
    elif short_io == "read":
        real_read, real_pread = os.read, os.pread
        monkeypatch.setattr(os, "read", lambda fd, size: real_read(fd, min(size, 2)))
        monkeypatch.setattr(
            os, "pread", lambda fd, size, offset: real_pread(fd, min(size, 2), offset),
        )
    case.operation()
    assert_saved(case)
    assert not list(case.directory.glob(case.prefix + "*"))


@pytest.mark.parametrize("swap", [False, True], ids=["normal", "swapped-temporary"])
def test_real_wizard_restart_discloses_failed_intent_save(tmp_path, monkeypatch, swap):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    forbidden_calls = []

    def forbidden(*_args, **_kwargs):
        forbidden_calls.append(True)
        raise AssertionError("Native device/process/power callback forbidden")

    for boundary in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.app._shutdown",
    ):
        monkeypatch.setattr(boundary, forbidden)
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(False)
    wizard = make_demo_wizard()
    wizard.enable_report_intent_recovery(store)
    wizard.screen = Screen.REPORT_HELP
    real_sync = os.fsync
    swapped = []

    def sync(fd):
        real_sync(fd)
        for path in directory.glob(".report-intent-*"):
            if swap and not swapped and os.fstat(fd).st_ino == path.stat().st_ino:
                swapped.append(path.name)
                path.rename(directory / "retired-owned-temporary")
                path.write_bytes(b"not-wanted\n")
                path.chmod(0o600)

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", sync)
        wizard.set_report_wanted(True)
    restarted = make_demo_wizard()
    restarted.enable_report_intent_recovery(ReportIntentStore(directory))
    restarted.shutdown()
    assert not forbidden_calls
    assert wizard.report_recovery_warning or restarted.report_wanted
    if swap:
        assert swapped and wizard.report_recovery_warning
    else:
        assert not wizard.report_recovery_warning
        assert restarted.screen == Screen.SHUTDOWN_CONFIRM
        assert not restarted.wants_shutdown
