"""Report intent reads bind the final name to the complete private snapshot."""

import os

import pytest

from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError


@pytest.mark.parametrize("wanted", [False, True])
@pytest.mark.parametrize("mutation", ["normal", "mode", "link", "rewrite"])
def test_load_checks_final_named_snapshot(tmp_path, monkeypatch, wanted, mutation):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    store = ReportIntentStore(directory)
    store.save(wanted)
    path = directory / store.NAME
    original_stat = os.stat
    before = original_stat(path)
    changed = False

    def mutate_before_final_named_stat(name, *args, **kwargs):
        nonlocal changed
        if name == store.NAME and kwargs.get("dir_fd") is not None and not changed:
            changed = True
            if mutation == "mode":
                path.chmod(0o644)
            elif mutation == "link":
                os.link(path, directory / "another-name")
            elif mutation == "rewrite":
                original = path.read_bytes()
                path.write_bytes(original.replace(b"wanted", b"vanted"))
                # Force a distinct same-size snapshot even on a coarse clock.
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        return original_stat(name, *args, **kwargs)

    monkeypatch.setattr(os, "stat", mutate_before_final_named_stat)
    if mutation == "normal":
        assert store.load() is wanted
    else:
        with pytest.raises(SafetyError, match="Unsafe report preference file"):
            store.load()
    assert changed
    after = original_stat(path)
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert before.st_size == after.st_size
    if mutation == "mode":
        assert after.st_mode & 0o777 == 0o644
    elif mutation == "link":
        assert after.st_nlink == 2
    elif mutation == "rewrite":
        assert after.st_mtime_ns != before.st_mtime_ns
        assert b"vanted" in path.read_bytes()
