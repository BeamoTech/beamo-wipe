"""Report fingerprints use the same bounded hardware text as discovery."""

import copy

import pytest

from beamo_wipe.discover import node_to_disk
from beamo_wipe.safety import SafetyError
from beamo_wipe.support_export import baseline_fingerprints, select_export_volume
from test_usb_report_workflow import _payload


@pytest.mark.parametrize("index", [0, 1, 2], ids=["boot", "target", "report"])
@pytest.mark.parametrize("field", ["model", "serial", "wwn"])
@pytest.mark.parametrize("padding", [" ", "   ", "\u00a0"])
def test_unchanged_padded_hardware_can_export(index, field, padding):
    payload, _ = _payload()
    node = payload["blockdevices"][index]
    node[field] = padding + node[field] + padding
    disks = tuple(
        node_to_disk(item, is_boot=i == 0)
        for i, item in enumerate(payload["blockdevices"][:2])
    )
    original = copy.deepcopy(payload)
    volume = select_export_volume(payload, baseline_fingerprints(disks))
    assert volume.path == "/dev/sdc1"
    assert volume.parent.serial == "REPORT-1"
    assert payload == original


@pytest.mark.parametrize("field", ["model", "serial", "wwn"])
def test_maximum_hardware_length_with_padding_can_export(field):
    payload, _ = _payload()
    payload["blockdevices"][1][field] = " " + "T" * 128 + " "
    disks = tuple(
        node_to_disk(item, is_boot=i == 0)
        for i, item in enumerate(payload["blockdevices"][:2])
    )
    assert select_export_volume(payload, baseline_fingerprints(disks)).path == "/dev/sdc1"


@pytest.mark.parametrize("field", ["model", "serial", "wwn"])
@pytest.mark.parametrize("bad", ["bad\n", "bad\t", "bad\x00", "bad\u2028", "x" * 129, 123, []])
def test_malformed_hardware_still_refused(field, bad):
    payload, disks = _payload()
    payload["blockdevices"][2][field] = bad
    with pytest.raises(SafetyError):
        select_export_volume(payload, baseline_fingerprints(disks))


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize("field", ["model", "serial", "wwn"])
def test_padding_cannot_hide_protected_hardware_change(index, field):
    payload, disks = _payload()
    payload["blockdevices"][index][field] = " changed "
    with pytest.raises(SafetyError):
        select_export_volume(payload, baseline_fingerprints(disks))


@pytest.mark.parametrize("field", ["path", "type", "tran"])
def test_nonhardware_text_retains_exact_edges(field):
    payload, disks = _payload()
    payload["blockdevices"][2][field] += " "
    with pytest.raises(SafetyError):
        select_export_volume(payload, baseline_fingerprints(disks))


@pytest.mark.parametrize("field", ["path", "pkname", "fstype", "fsver", "uuid"])
def test_volume_text_retains_exact_edges(field):
    payload, disks = _payload()
    payload["blockdevices"][2]["children"][0][field] += " "
    with pytest.raises(SafetyError):
        select_export_volume(payload, baseline_fingerprints(disks))
