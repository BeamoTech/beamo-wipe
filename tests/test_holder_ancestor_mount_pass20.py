"""Fake-only root-run proof: an opened mount inherits multiparent uncertainty."""
import pytest
from test_discovery_observation_fallback_pass16 import _disk, fake_machine  # noqa: F401


def _payload(kind, placement, mounted=True):
    boot = _disk("sdz", tran="usb", mountpoints=["/run/live/medium"])
    backing, other = _disk("sda"), _disk("sdc")
    holder = dict(name="holder77", path="/dev/holder77", type=kind, size=128_000_000_000,
                  pkname="sda", ro=False, mountpoints=[])
    opened = dict(name="opened77", path="/dev/opened77", type="crypt", size=128_000_000_000,
                  pkname="holder77", ro=False, mountpoints=["/data"] if mounted else [])
    rows = [boot, backing, other]
    if placement == "flat":
        rows.extend((holder, opened))
    else:
        backing["children"] = [holder]
        holder["children"] = [opened]
    return dict(blockdevices=rows)


@pytest.mark.parametrize("kind", ("dm", "mpath", "md", "raid1", "lvm"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
def test_opened_mount_preserves_ancestor_member_uncertainty(fake_machine, kind, placement, route):  # noqa: F811
    result = fake_machine(_payload(kind, placement), route)
    assert result.error
    assert not result.boot_identified
    assert result.selectable == ()


@pytest.mark.parametrize("kind", ("dm", "mpath", "md", "raid1", "lvm"))
@pytest.mark.parametrize("placement", ("flat", "nested"))
@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
def test_blank_unmounted_holder_chain_keeps_existing_behavior(fake_machine, kind, placement, route):  # noqa: F811
    result = fake_machine(_payload(kind, placement, mounted=False), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sda", "/dev/sdc"}


@pytest.mark.parametrize("placement", ("flat", "nested"))
@pytest.mark.parametrize("route", ("injected", "production-metadata-stub"))
def test_nested_single_parent_crypt_keeps_unrelated_disk(fake_machine, placement, route):  # noqa: F811
    result = fake_machine(_payload("crypt", placement), route)
    assert result.boot_identified
    assert not result.error
    assert {disk.path for disk in result.selectable} == {"/dev/sdc"}
