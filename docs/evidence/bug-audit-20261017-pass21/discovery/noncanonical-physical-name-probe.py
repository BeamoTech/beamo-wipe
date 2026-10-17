"""UNRUN follow-up: lexical PATH aliases must not mint an unbound disk NAME.

Root owns runtime. Uses fake lexical normalization, not host /dev symlinks.
All native acquisition/file guards from fake_machine remain active.
"""

import os
import posixpath

import pytest

from beamo_wipe.models import CONTENTS_WINDOWS
from beamo_wipe.safety import disk_identity
from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - imported guarded fake-machine pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
NAMES = ("sda", "./sda", "x/../sda", "sda/", "/sda")


@pytest.fixture
def lexical_fake_machine(fake_machine, monkeypatch):  # noqa: F811
    previous = os.path.realpath

    def fake_lexical_realpath(path, *args, **kwargs):
        text = os.fspath(path)
        if text.startswith("/dev/"):
            # os.path.realpath collapses these lexical segments on a real
            # machine. Reproduce that pure string behavior without any lstat.
            return posixpath.normpath(text)
        return previous(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", fake_lexical_realpath)
    return fake_machine


def _target(scan, route, name, *, uuid="fake-before"):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    target = _disk("sda")
    target["name"] = name
    part = {
        "name": "sda1", "path": "/dev/sda1", "type": "part",
        "pkname": "sda", "size": 120_000_000_000, "fstype": "ntfs",
        "uuid": uuid, "partlabel": "Windows Recovery", "ro": False,
        "mountpoints": [],
    }
    try:
        result = scan({"blockdevices": [boot, target, part]}, route)
    except ValueError:
        assert route == "direct"
        return None
    candidates = [disk for disk in result.selectable if disk.path == "/dev/sda"]
    assert len(candidates) <= 1
    if candidates:
        assert result.boot_identified and not result.error
        assert result.boot is not None and result.boot.path == "/dev/sdz"
        assert "/dev/sdz" not in {disk.path for disk in result.selectable}
        return candidates[0]
    return None


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("name", NAMES)
def test_lexically_equivalent_noncanonical_name_cannot_drop_flat_evidence(
    lexical_fake_machine, route, name,
):
    target = _target(lexical_fake_machine, route, name)
    if target is not None:
        assert target.contents == CONTENTS_WINDOWS
        assert target.layout_id


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("name", NAMES)
def test_lexically_equivalent_noncanonical_name_cannot_merge_changed_layout(
    lexical_fake_machine, route, name,
):
    before = _target(lexical_fake_machine, route, name)
    after = _target(lexical_fake_machine, route, name, uuid="fake-after")
    assert before is None or after is None or disk_identity(before) != disk_identity(after)
