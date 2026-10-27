# SPDX-License-Identifier: GPL-3.0-or-later
"""Invalid evidence blocks erasure, not an explicitly accepted safe poweroff.

All disks, process probes and power actions are fake. Journal and lock fixtures
reuse the actual recovery module on owned temporary regular files.
"""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os

import pytest

from beamo_wipe import app
from beamo_wipe.models import Screen, WipeResult
from beamo_wipe.nwipe_runner import NwipeRunner
from beamo_wipe.safety import SafetyError
from beamo_wipe.session_recovery import NAME, _bytes
from test_session_recovery import recover, session as session_fixture

session = session_fixture
JOURNALS = ["corrupt", "foreign", "missing", "valid"]


@pytest.fixture
def shutdown_session(session, monkeypatch):
    powered = []
    monkeypatch.setattr(app, "_shutdown", lambda: powered.append(True) or True)

    def build(journal):
        first = session()
        path = first.directory / NAME
        if journal == "corrupt":
            path.write_bytes(b"{")
        elif journal == "foreign":
            envelope = json.loads(path.read_bytes())
            envelope["payload"]["build"] = "b" * 64
            envelope["sha256"] = hashlib.sha256(_bytes(envelope["payload"])).hexdigest()
            path.write_bytes(_bytes(envelope))
        elif journal == "missing":
            path.unlink()
            old_log = first.directory / "nwipe-old.log"
            old_log.write_text("Unconfirmed old run\n")
            old_log.chmod(0o600)
        first.close()
        store = session()
        assert store.invalid is (journal != "valid")
        wizard = recover(store)
        # Exercise the live process recheck, with the existing session fixture's
        # fake probe. This runner is never started and owns no real process.
        wizard.runner = NwipeRunner()
        wizard.dry_run = False
        wizard.report_wanted = True
        monkeypatch.setattr(
            wizard.runner, "start", lambda *_args: pytest.fail("must not start an erase")
        )
        assert store.is_quiescent()
        return wizard, store, powered

    return build


def _accept_discard(wizard):
    wizard.shutdown()
    assert wizard.screen == Screen.SHUTDOWN_CONFIRM
    assert not wizard.wants_shutdown
    wizard.confirm_shutdown_without_saving(wizard.shutdown_generation - 1)
    assert not wizard.wants_shutdown
    wizard.confirm_shutdown_without_saving(wizard.shutdown_generation)
    assert wizard.wants_shutdown


@pytest.mark.parametrize("journal", JOURNALS)
def test_quiescent_journal_poweroff_requires_explicit_discard(shutdown_session, journal):
    wizard, store, powered = shutdown_session(journal)
    before = {p.name: p.read_bytes() for p in store.directory.iterdir()
              if p.name == NAME or p.name.startswith("nwipe")}
    assert wizard._new_session_store_blocked() is store.invalid
    wizard.shutdown()
    assert wizard.screen == Screen.SHUTDOWN_CONFIRM and not wizard.wants_shutdown
    assert not app._shutdown_if_still_safe(wizard)
    assert powered == []
    # The ordinary shutdown request cannot stand in for accepting report loss.
    wizard.shutdown()
    wizard.confirm_shutdown_without_saving(wizard.shutdown_generation - 1)
    assert not wizard.wants_shutdown
    wizard.confirm_shutdown_without_saving(wizard.shutdown_generation)
    assert wizard.wants_shutdown
    assert app._shutdown_if_still_safe(wizard)
    assert powered == [True]
    assert wizard._new_session_store_blocked() is store.invalid
    assert before == {p.name: p.read_bytes() for p in store.directory.iterdir()
                      if p.name == NAME or p.name.startswith("nwipe")}
    assert wizard._wipe_request is None and not wizard.wants_new_session


@contextmanager
def _busy_after_discard(wizard, store, monkeypatch, busy):
    held_fd = None
    try:
        if busy == "held_lock":
            store._release_quiescent()
            held_fd = os.open(store.directory / "wipe.lock", os.O_RDWR)
            fcntl.flock(held_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif busy in {"interface_replaced", "wipe_replaced"}:
            path = store.directory / ("interface.lock" if busy == "interface_replaced" else "wipe.lock")
            path.rename(path.with_suffix(".old"))
            path.write_bytes(b"")
            path.chmod(0o600)
        elif busy == "closed_store":
            store.close()
        elif busy in {"lock_io_error", "lock_safety_error"}:
            def uncertain_lock():
                raise (OSError if busy == "lock_io_error" else SafetyError)("fake lock failure")
            monkeypatch.setattr(store, "is_quiescent", uncertain_lock)
        elif busy in {"pinned_running", "pinned_unknown", "pinned_error"}:
            def probe(**_kwargs):
                if busy == "pinned_error":
                    raise OSError("fake process table failure")
                return True if busy == "pinned_running" else None
            monkeypatch.setattr("beamo_wipe.nwipe_runner.pinned_nwipe_already_running", probe)
        elif busy in {"runner_handle", "runner_lock"}:
            monkeypatch.setattr(wizard.runner, "_proc" if busy == "runner_handle" else "_lock_fd", object())
        else:
            monkeypatch.setattr(wizard, busy, True)
        yield
    finally:
        if held_fd is not None:
            os.close(held_fd)


@pytest.mark.parametrize("journal", ["corrupt", "valid"])
@pytest.mark.parametrize("busy", [
    "held_lock", "interface_replaced", "wipe_replaced", "closed_store",
    "lock_io_error", "lock_safety_error", "pinned_running", "pinned_unknown", "pinned_error",
    "runner_handle", "runner_lock", "_finishing", "_evidence_saving", "_report_exporting",
    "_diagnostic_busy", "wants_new_session",
])
def test_poweroff_rechecks_ownership_and_busy_state(
    shutdown_session, monkeypatch, journal, busy,
):
    wizard, store, powered = shutdown_session(journal)
    _accept_discard(wizard)
    with _busy_after_discard(wizard, store, monkeypatch, busy):
        assert not app._shutdown_if_still_safe(wizard)
    assert powered == []


@pytest.mark.parametrize("journal", JOURNALS[:-1])
def test_invalid_journal_still_refuses_another_erase(shutdown_session, journal):
    wizard, store, powered = shutdown_session(journal)
    # Supply an idle terminal presentation so only the invalid-store guard
    # prevents this otherwise eligible new-session transition.
    wizard.screen = Screen.DONE
    wizard.wipe_result = WipeResult(False, None, "Unconfirmed previous result", "")
    assert wizard.result_view.code != "stop_unconfirmed"
    assert wizard._new_session_store_blocked()
    assert not wizard.can_erase_another
    wizard.erase_another_disk()
    assert not wizard.wants_new_session and wizard.screen == Screen.DONE
    with pytest.raises(SafetyError):
        store.begin_new_session()
    assert store.invalid and powered == []
