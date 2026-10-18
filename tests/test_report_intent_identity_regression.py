"""Preference recovery rejects changed files/directories instead of losing intent."""

import os

import pytest

from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError


def test_load_does_not_return_an_obsolete_false_preference(tmp_path, monkeypatch):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(False)
    real_read = os.read
    swapped = False

    def replace_after_read(fd, count):
        nonlocal swapped
        data = real_read(fd, count)
        if not swapped:
            swapped = True
            store.save(True)
        return data

    monkeypatch.setattr(os, "read", replace_after_read)
    with pytest.raises(SafetyError):
        store.load()
    monkeypatch.setattr(os, "read", real_read)
    assert store.load() is True


@pytest.mark.parametrize("operation", ["load", "save"])
def test_preference_operation_cannot_succeed_in_retired_directory(tmp_path, monkeypatch, operation):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(True)
    real_open = os.open
    swapped = False

    def replace_after_open(path, *args, **kwargs):
        nonlocal swapped
        fd = real_open(path, *args, **kwargs)
        if not swapped and path == directory:
            swapped = True
            directory.rename(tmp_path / "retired")
            directory.mkdir(mode=0o700)
            replacement = ReportIntentStore(directory)
            replacement.save(True)
        return fd

    monkeypatch.setattr(os, "open", replace_after_open)
    with pytest.raises(SafetyError):
        if operation == "load":
            store.load()
        else:
            store.save(False)
    monkeypatch.setattr(os, "open", real_open)
    assert store.load() is True
