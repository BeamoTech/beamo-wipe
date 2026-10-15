"""Empty unrelated readers never become targets or invalidate the journal."""

import pytest
import test_session_recovery as recovery_tests

from beamo_wipe.discover import parse_lsblk_json
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import selectable_disks
from test_usb_report_workflow import _payload, _root

session = recovery_tests.session


def _baseline(store, *, zero_path="/dev/sdd", size=0):
    payload, _ = _payload()
    payload["blockdevices"] = payload["blockdevices"][:2]
    if zero_path in {"/dev/sdb", "/dev/nvme0n1"}:
        for node in payload["blockdevices"]:
            if node["path"] == zero_path:
                node["size"] = size
    else:
        payload["blockdevices"].append(_root(
            zero_path, size=size, tran="usb", model="Empty reader", serial="READER",
            rm=1, hotplug=1,
        ))
    discovery = parse_lsblk_json(payload, boot_path="/dev/sdb")
    request = WipeRequest(
        "/dev/nvme0n1", MethodId.QUICK_ZERO, "/dev/sdb",
        str(store.directory / "nwipe-test.log"),
    )
    return discovery, request


def test_unrelated_zero_capacity_survives_armed_restart_without_eligibility(session):
    first = session()
    discovery, request = _baseline(first)
    assert [disk.path for disk in selectable_disks(discovery)] == [request.device]
    first.arm(discovery, request)
    first.close()

    second = session()
    assert not second.invalid
    _, recovered, target = second.context()
    assert target.path == request.device
    reader = next(disk for disk in recovered.disks if disk.path == "/dev/sdd")
    assert reader.size_bytes == 0
    assert reader not in selectable_disks(recovered)
    wizard = recovery_tests.recover(second)
    assert wizard.result_view.code == "indeterminate"
    assert wizard.selectable == ()


def test_unrelated_zero_capacity_preserves_terminal_recovery(session):
    first = session()
    discovery, request = _baseline(first)
    first.arm(discovery, request)
    path = recovery_tests.finish(first, discovery, request)
    first.close()

    second = session()
    assert not second.invalid
    recovered_path, evidence = second.terminal()
    assert recovered_path == path
    assert evidence["device"]["path"] == request.device
    assert recovery_tests.recover(second).done_ok


@pytest.mark.parametrize("path", ["/dev/sdb", "/dev/nvme0n1"])
def test_zero_capacity_target_or_boot_is_still_refused(session, path):
    store = session()
    discovery, request = _baseline(store, zero_path=path)
    with pytest.raises(ValueError, match="disk size"):
        store.arm(discovery, request)
    assert store.record["phase"] == "preflight"


def test_negative_unrelated_capacity_is_still_refused(session):
    store = session()
    discovery, request = _baseline(store, size=-1)
    with pytest.raises(ValueError, match="disk size"):
        store.arm(discovery, request)
    assert store.record["phase"] == "preflight"
