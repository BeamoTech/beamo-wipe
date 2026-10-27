# SPDX-License-Identifier: GPL-3.0-or-later
"""exFAT report USBs are accepted beside FAT32 with every safety check intact.

Fake lsblk payloads, regular files and recorded command argv only. No block
device, loop device or real mount is opened. Linux's in-kernel exfat driver
(fs/exfat, 6.1 and 6.12) accepts the same fmask/dmask options as vfat, and
libblkid reports exFAT as TYPE=exfat with VERSION "<major>.<minor>" ("1.0").
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import os
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from beamo_wipe import lang
from beamo_wipe import support_export as E
from beamo_wipe.safety import SafetyError
from beamo_wipe.support_code import code_for_export_detail
from test_usb_report_workflow import (
    _discovery,
    _fake_export_state,
    _partition,
    _payload,
    _root,
    _terminal_evidence,
    _worker_success_stdout,
)

EXFAT = {"fstype": "exfat", "fsver": "1.0", "uuid": "1A2B-3C4D"}
PERMISSIONS = "fmask=0177,dmask=0077"


@pytest.fixture(autouse=True)
def _no_markers(monkeypatch):
    monkeypatch.setattr(E, "_emit_export_marker", lambda *_args: None)
    yield
    lang.set_language("en")


def _exfat_payload(*extra):
    payload, disks = _payload(*extra)
    payload["blockdevices"][2]["children"] = [_partition(**EXFAT)]
    return payload, E.baseline_fingerprints(disks)


def _refusal(payload, baseline) -> str:
    with pytest.raises(SafetyError) as caught:
        E.select_export_volume(payload, baseline)
    return str(caught.value)


def test_every_supported_type_has_exactly_one_accepted_version():
    assert E.SUPPORTED_FILESYSTEMS == frozenset({"vfat", "exfat"})
    assert dict(E._REQUIRED_FSVER) == {"vfat": "FAT32", "exfat": "1.0"}
    assert set(E._REQUIRED_FSVER) == E.SUPPORTED_FILESYSTEMS
    with pytest.raises(TypeError):
        E._REQUIRED_FSVER["ntfs"] = "3.1"  # type: ignore[index]


def test_exfat_partition_is_selected_with_its_full_identity():
    payload, baseline = _exfat_payload()
    volume = E.select_export_volume(payload, baseline)
    assert (volume.path, volume.parent.path) == ("/dev/sdc1", "/dev/sdc")
    assert (volume.fstype, volume.fsver, volume.uuid) == ("exfat", "1.0", "1A2B-3C4D")
    assert (volume.parent.serial, volume.parent.wwn) == ("REPORT-1", "report-wwn")
    assert volume.size_bytes == 31_000_000


def test_unpartitioned_exfat_stick_is_selected_as_its_whole_disk():
    payload, disks = _payload()
    payload["blockdevices"][2].update(children=[], **EXFAT)
    volume = E.select_export_volume(payload, E.baseline_fingerprints(disks))
    assert volume.path == volume.parent.path == "/dev/sdc"
    assert (volume.fstype, volume.fsver) == ("exfat", "1.0")


def test_fat32_selection_is_unchanged():
    payload, disks = _payload()
    volume = E.select_export_volume(payload, E.baseline_fingerprints(disks))
    assert (volume.path, volume.fstype, volume.fsver, volume.uuid) == (
        "/dev/sdc1", "vfat", "FAT32", "ABCD-1234",
    )


@pytest.mark.parametrize(
    ("fstype", "fsver", "expected"),
    [
        ("ntfs", None, "USB_FAT32_ONLY"),
        ("ntfs", "3.1", "USB_FAT32_ONLY"),
        ("ntfs3", None, "USB_FAT32_ONLY"),
        ("ext4", "1.0", "USB_FAT32_ONLY"),
        ("btrfs", None, "USB_FAT32_ONLY"),
        ("hfsplus", None, "USB_FAT32_ONLY"),
        ("udf", "2.01", "USB_FAT32_ONLY"),
        ("iso9660", "Joliet Extension", "USB_FAT32_ONLY"),
        ("msdos", "FAT16", "USB_FAT32_ONLY"),
        ("EXFAT", "1.0", "USB_FAT32_ONLY"),
        ("VFAT", "FAT32", "USB_FAT32_ONLY"),
        ("vfat", "FAT12", "USB_FAT32_NOT_12_16"),
        ("vfat", "FAT16", "USB_FAT32_NOT_12_16"),
        # A version is valid only for its own filesystem type.
        ("vfat", "1.0", "USB_FAT32_NOT_12_16"),
        ("exfat", "FAT32", "USB_FAT32_ONLY"),
        # exFAT revision 1.00 is the only published one; others are refused.
        ("exfat", "2.0", "USB_FAT32_ONLY"),
        ("exfat", "1.1", "USB_FAT32_ONLY"),
        ("exfat", "1.00", "USB_FAT32_ONLY"),
        ("exfat", "0.0", "USB_FAT32_ONLY"),
        ("exfat", None, "USB_META_INCOMPLETE"),
        ("exfat", "", "USB_META_MALFORMED"),
        (None, "1.0", "USB_META_INCOMPLETE"),
    ],
)
def test_only_fat32_and_exfat_1_0_volumes_are_accepted(fstype, fsver, expected):
    payload, disks = _payload()
    payload["blockdevices"][2]["children"][0].update(fstype=fstype, fsver=fsver)
    assert _refusal(payload, E.baseline_fingerprints(disks)) == getattr(E, expected)


def _second_usb(path="/dev/sdd", **partition):
    return _root(
        path, size=64_000_000, tran="usb", model="Second", serial="REPORT-2",
        wwn="second-wwn", rm=1, hotplug=1,
        children=[_partition(path + "1", pkname=path.removeprefix("/dev/"), **partition)],
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda p: p["blockdevices"].pop(), lambda: E.USB_NOT_SINGLE.format(detail=E.USB_NONE_FOUND)),
        (lambda p: p["blockdevices"].append(_second_usb(**EXFAT)),
         lambda: E.USB_NOT_SINGLE.format(detail=E.USB_MANY_FOUND)),
        (lambda p: p["blockdevices"].append(_second_usb()),
         lambda: E.USB_NOT_SINGLE.format(detail=E.USB_MANY_FOUND)),
        (lambda p: p["blockdevices"][2].update(tran="sata"),
         lambda: E.USB_NOT_SINGLE.format(detail=E.USB_NONE_FOUND)),
        (lambda p: p["blockdevices"][2].update(rm=0), lambda: E.NEW_NOT_REMOVABLE),
        (lambda p: p["blockdevices"][2].update(hotplug=0), lambda: E.NEW_NOT_REMOVABLE),
        (lambda p: p["blockdevices"][2].update(rm=None), lambda: E.USB_META_INCOMPLETE),
        (lambda p: p["blockdevices"][2].update(ro=1), lambda: E.USB_MUST_BE_WRITABLE),
        (lambda p: p["blockdevices"][2]["children"].__setitem__(0, _partition(mounted=True, **EXFAT)),
         lambda: E.USB_MUST_BE_WRITABLE),
        (lambda p: p["blockdevices"][2]["children"][0].update(ro=1), lambda: E.USB_VOLUME_WRITABLE),
        (lambda p: p["blockdevices"][2]["children"].append(_partition("/dev/sdc2", **EXFAT)),
         lambda: E.USB_NEED_ONE_VOLUME),
        (lambda p: p["blockdevices"][2]["children"].clear(), lambda: E.USB_NEED_ONE_VOLUME),
        (lambda p: p["blockdevices"][2].update(**EXFAT), lambda: E.USB_LAYOUT_AMBIGUOUS),
        (lambda p: p["blockdevices"][2]["children"][0].update(pkname="sdb"),
         lambda: E.USB_PARTITION_ORPHAN),
        (lambda p: p["blockdevices"][2]["children"][0].update(path="/dev/sdb1"),
         lambda: E.USB_PARTITION_ORPHAN),
        (lambda p: p["blockdevices"][2]["children"][0].update(type="lvm"),
         lambda: E.USB_LAYOUT_UNSUPPORTED),
        (lambda p: p["blockdevices"][2]["children"][0].update(size=4096), lambda: E.USB_VOLUME_SMALL),
        (lambda p: p["blockdevices"][2]["children"][0].update(size=64_000_000),
         lambda: E.USB_LAYOUT_MALFORMED),
        (lambda p: p["blockdevices"][2]["children"][0].update(uuid=None), lambda: E.USB_META_INCOMPLETE),
        (lambda p: p["blockdevices"][0].update(serial="changed"), lambda: E.BASELINE_KEEP_CONNECTED),
        (lambda p: p["blockdevices"][1].update(wwn="other-wwn"), lambda: E.BASELINE_KEEP_CONNECTED),
        (lambda p: p["blockdevices"][2].update(wwn="boot-wwn"), lambda: E.PROTECTED_IDENTITY_UNVERIFIED),
        (lambda p: p["blockdevices"][2].update(serial="BOOT-1", wwn=""),
         lambda: E.PROTECTED_IDENTITY_UNVERIFIED),
    ],
)
def test_exfat_keeps_every_device_identity_and_layout_refusal(mutation, expected):
    payload, baseline = _exfat_payload()
    mutation(payload)
    assert _refusal(payload, baseline) == expected()


def test_exfat_volume_on_the_boot_usb_or_target_is_never_a_report_volume():
    payload, baseline = _exfat_payload()
    stick = payload["blockdevices"].pop()
    boot, target = payload["blockdevices"]
    boot["children"] = [_partition("/dev/sdb1", pkname="sdb", **EXFAT)]
    target["children"] = [_partition("/dev/nvme0n1p1", pkname="nvme0n1", **EXFAT)]
    assert _refusal(payload, baseline) == E.USB_NOT_SINGLE.format(detail=E.USB_NONE_FOUND)
    payload["blockdevices"].append(stick)
    assert E.select_export_volume(payload, baseline).path == "/dev/sdc1"


def test_a_reformatted_stick_between_scans_is_a_different_volume():
    fat_payload, disks = _payload()
    exfat_payload, _baseline = _exfat_payload()
    exfat_payload["blockdevices"][2]["children"][0]["uuid"] = "ABCD-1234"
    baseline = E.baseline_fingerprints(disks)
    fat = E.select_export_volume(fat_payload, baseline)
    exfat = E.select_export_volume(exfat_payload, baseline)
    assert (fat.path, fat.uuid, fat.parent) == (exfat.path, exfat.uuid, exfat.parent)
    assert not E._same_volume(fat, exfat, include_rdev=False)
    assert E._same_volume(exfat, exfat, include_rdev=False)


def _recorded_commands(tmp_path, monkeypatch, fstype, fsver):
    export, fat_volume, evidence, fd = _fake_export_state(tmp_path, monkeypatch)
    volume = dataclasses.replace(fat_volume, fstype=fstype, fsver=fsver)
    commands = []

    def run_command(argv, **kwargs):
        commands.append((list(argv), tuple(kwargs.get("pass_fds", ()))))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(export, "_run_command", run_command)
    monkeypatch.setattr(export, "_ordinary_unmount", lambda *_args: True)
    try:
        receipt = export._persist_and_verify_report(
            volume, evidence, b"", "unavailable", fd
        )
    finally:
        os.close(fd)
    assert receipt.ok is True and receipt.safe_to_remove is True
    assert len(commands) == 3
    mountpoint = commands[0][0][-1]
    assert re.fullmatch(
        re.escape(str(tmp_path / "run")) + r"/mount-[0-9a-f]{24}", mountpoint
    )
    return commands, fd, mountpoint


def test_fat32_mount_argv_is_byte_for_byte_unchanged(tmp_path, monkeypatch):
    commands, fd, mountpoint = _recorded_commands(tmp_path, monkeypatch, "vfat", "FAT32")
    source = f"/proc/self/fd/{fd}"
    assert commands == [
        (["/usr/bin/mount", "-t", "vfat", "-o",
          "rw,nodev,nosuid,noexec,nosymfollow,fmask=0177,dmask=0077",
          source, mountpoint], (fd,)),
        (["/usr/bin/sync", "-f", mountpoint], ()),
        (["/usr/bin/mount", "-t", "vfat", "-o",
          "ro,nodev,nosuid,noexec,nosymfollow,fmask=0177,dmask=0077",
          source, mountpoint], (fd,)),
    ]


def test_exfat_mount_uses_the_exfat_type_and_identical_options(tmp_path, monkeypatch):
    commands, fd, mountpoint = _recorded_commands(tmp_path, monkeypatch, "exfat", "1.0")
    source = f"/proc/self/fd/{fd}"
    for mode, (argv, pass_fds) in zip(("rw", "ro"), (commands[0], commands[2])):
        assert argv == [
            E.MOUNT_BIN, "-t", "exfat", "-o",
            f"{mode},nodev,nosuid,noexec,nosymfollow,{PERMISSIONS}",
            source, mountpoint,
        ]
        assert pass_fds == (fd,)
        assert "--force" not in argv and "-f" not in argv and "-i" not in argv
    assert commands[1] == ([E.SYNC_BIN, "-f", mountpoint], ())


def test_mount_type_comes_from_the_freshly_selected_volume_only():
    source = Path("src/beamo_wipe/support_export.py").read_text(encoding="utf-8")
    mounts = re.findall(r"\[MOUNT_BIN, [^\]]*\]", source)
    assert mounts == [
        '[MOUNT_BIN, "-t", volume.fstype, "-o", rw_options, stable_source, str(mountpoint)]',
        '[MOUNT_BIN, "-t", volume.fstype, "-o", ro_options, stable_source, str(mountpoint)]',
    ]
    assert 'permission_options = "fmask=0177,dmask=0077"' in source


def _mountinfo_case(tmp_path, monkeypatch, *, mounted_type, volume_type, options):
    mountpoint = tmp_path / "mount"
    mountpoint.mkdir()
    source = "/dev/sdz1"
    rdev = os.makedev(8, 241)
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        f"20 1 8:241 / {mountpoint} {options} - {mounted_type} {source} rw\n"
    )
    volume = E.ExportVolume(
        E.DeviceFingerprint("/dev/sdz", 10_000_000, "USB", "", ""),
        source, 9_000_000, volume_type, E._REQUIRED_FSVER[volume_type], "1A2B-3C4D", rdev,
    )
    real_stat = E.os.stat

    def stat_for_mount(path, *args, **kwargs):
        if str(path) == source:
            return SimpleNamespace(st_rdev=rdev)
        if str(path) == str(mountpoint):
            return SimpleNamespace(st_dev=rdev)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(E, "MOUNTINFO_PATH", str(mountinfo))
    monkeypatch.setattr(E.os, "stat", stat_for_mount)
    return mountpoint, volume


@pytest.mark.parametrize("read_only", [False, True])
def test_exfat_mount_record_is_verified_like_fat32(tmp_path, monkeypatch, read_only):
    mode = "ro" if read_only else "rw"
    mountpoint, volume = _mountinfo_case(
        tmp_path, monkeypatch, mounted_type="exfat", volume_type="exfat",
        options=f"{mode},nodev,nosuid,noexec,nosymfollow",
    )
    assert E._mounted_exact(mountpoint, volume)
    E._verify_mount(mountpoint, volume, read_only=read_only)


@pytest.mark.parametrize(
    ("mounted_type", "volume_type"),
    # A FUSE mount helper reports fuseblk, never the selected kernel type.
    [("fuseblk", "exfat"), ("vfat", "exfat"), ("exfat", "vfat"), ("ntfs3", "exfat")],
)
def test_a_mount_of_another_type_fails_closed(tmp_path, monkeypatch, mounted_type, volume_type):
    mountpoint, volume = _mountinfo_case(
        tmp_path, monkeypatch, mounted_type=mounted_type, volume_type=volume_type,
        options="rw,nodev,nosuid,noexec,nosymfollow",
    )
    assert not E._mounted_exact(mountpoint, volume)
    with pytest.raises(SafetyError) as caught:
        E._verify_mount(mountpoint, volume, read_only=False)
    assert str(caught.value) == E.MOUNT_IDENTITY_MISMATCH


def test_exfat_mount_missing_a_vfs_safety_flag_fails_closed(tmp_path, monkeypatch):
    mountpoint, volume = _mountinfo_case(
        tmp_path, monkeypatch, mounted_type="exfat", volume_type="exfat",
        options="rw,nodev,nosuid,noexec",
    )
    with pytest.raises(SafetyError) as caught:
        E._verify_mount(mountpoint, volume, read_only=False)
    assert str(caught.value) == E.MOUNT_MISSING_OPTIONS


def test_controller_sends_the_selected_exfat_volume_to_the_private_worker(
    tmp_path, monkeypatch
):
    evidence_path = _terminal_evidence(tmp_path)
    payload, disks = _payload()
    payload["blockdevices"][2]["children"] = [_partition(**EXFAT)]
    rdevs = {"/dev/sdb": 201, "/dev/nvme0n1": 202, "/dev/sdc": 301, "/dev/sdc1": 302}
    monkeypatch.setattr(E, "_block_rdev", lambda path: rdevs[path])
    requests = []

    def fake_run(command, **kwargs):
        request = json.loads(kwargs["input"])
        requests.append(request)
        return subprocess.CompletedProcess(
            command, 0, stdout=_worker_success_stdout(request), stderr=""
        )

    receipt = E.export_to_new_usb(
        evidence_path=evidence_path,
        discovery=_discovery(disks),
        target_path="/dev/nvme0n1",
        scan=lambda: payload,
        run=fake_run,
    )
    assert receipt.ok and receipt.safe_to_remove
    assert len(requests) == 1
    volume = requests[0]["volume"]
    assert (volume["path"], volume["fstype"], volume["fsver"], volume["uuid"]) == (
        "/dev/sdc1", "exfat", "1.0", "1A2B-3C4D",
    )
    assert (volume["rdev"], volume["parent"]["rdev"]) == (302, 301)
    assert 301 not in requests[0]["protected_rdevs"]
    assert {201, 202} <= set(requests[0]["protected_rdevs"])


def _worker_request(volume, baseline) -> bytes:
    data = b'{"schema_version": 1}\n'
    evidence = E.VerifiedEvidence(data, hashlib.sha256(data).hexdigest(), "failed", "", "", 0)
    wire = E._request_dict(evidence, volume, baseline, [], b"", "unavailable")
    return json.dumps(wire).encode()


@pytest.mark.parametrize(
    ("requested", "fresh_partition", "expected"),
    [
        # The stick changed type after the controller selected it.
        ({"fstype": "exfat", "fsver": "1.0"}, {}, "USB_CHANGED_BEFORE_MOUNT"),
        ({}, EXFAT, "USB_CHANGED_BEFORE_MOUNT"),
        # A request can never choose a filesystem type the fresh scan rejects.
        ({"fstype": "ntfs", "fsver": "3.1"}, EXFAT, "USB_CHANGED_BEFORE_MOUNT"),
        ({"fstype": "exfat", "fsver": "1.0"}, dict(EXFAT, fsver="2.0"), "USB_FAT32_ONLY"),
        ({"fstype": "exfat", "fsver": "1.0"}, {"fstype": "ntfs", "fsver": None}, "USB_FAT32_ONLY"),
    ],
)
def test_worker_reselects_before_opening_or_mounting(monkeypatch, requested, fresh_partition, expected):
    payload, disks = _payload()
    baseline = list(E.baseline_fingerprints(disks))
    volume = dataclasses.replace(
        E.select_export_volume(payload, baseline), rdev=302, **requested
    )
    payload["blockdevices"][2]["children"][0].update(fresh_partition)
    reached = []

    def forbidden(*_args, **_kwargs):
        reached.append(True)
        raise AssertionError("device identity, open or mount reached")

    for name in ("_block_rdev", "_run_command", "_persist_and_verify_report", "_assert_partition_parent"):
        monkeypatch.setattr(E, name, forbidden)
    monkeypatch.setattr(E.os, "open", forbidden)
    monkeypatch.setattr(E, "run_lsblk", lambda: payload)
    monkeypatch.setattr(
        E.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(_worker_request(volume, baseline)))
    )
    with pytest.raises(SafetyError) as caught:
        E._worker()
    assert str(caught.value) == getattr(E, expected)
    assert not reached


@pytest.mark.parametrize("code", ["en", "fr", "de", "es"])
def test_exfat_refusals_keep_stable_support_codes_markers_and_next_steps(code):
    lang.set_language(code)
    payload, disks = _payload()
    payload["blockdevices"][2]["children"][0].update(fstype="exfat", fsver="2.0")
    detail = _refusal(payload, E.baseline_fingerprints(disks))
    assert detail == E.USB_FAT32_ONLY
    assert "FAT32" in detail and "exFAT" in detail
    assert code_for_export_detail(detail) == "BW-X-FAT"
    assert E._marker_for(detail) == "BEAMO_WIPE_EXPORT_FAIL_MOUNTED"
    assert E.next_step_for(detail) == E.NEXT_DIFFERENT_STICK
    assert "exFAT" in E.NEXT_DIFFERENT_STICK
    assert code_for_export_detail(E.USB_FAT32_NOT_12_16) == "BW-X-FATN"
    assert E._marker_for(E.USB_FAT32_NOT_12_16) == "BEAMO_WIPE_EXPORT_FAIL_FAT32"
    assert code_for_export_detail(E.USB_NEED_ONE_VOLUME) == "BW-X-VSNG"
    none = E.USB_NOT_SINGLE.format(detail=E.USB_NONE_FOUND)
    assert code_for_export_detail(none) == "BW-X-NUSB" and "exFAT" in none


def test_every_report_media_string_names_both_formats_in_every_language():
    named = []
    for module, names in lang.surface().items():
        for name, english in names.items():
            texts = english if isinstance(english, tuple) else (english,)
            if not any("FAT32" in text for text in texts):
                continue
            named.append((module, name))
            for code in ("en", "fr", "de", "es"):
                value = english if code == "en" else lang.translated(code, module, name)
                joined = " ".join(value) if isinstance(value, tuple) else value
                assert "FAT32" in joined and "exFAT" in joined, (code, module, name)
                assert "exFAT, NTFS" not in joined, (code, module, name)
    assert len(named) >= 13
    assert {("copy", "REPORT_HELP_NEED"), ("support_export", "USB_FAT32_ONLY"),
            ("wizard", "DIAG_BASELINE_READY"), ("diagnostic_report", "PREPARE")} <= set(named)


def test_help_names_the_refused_formats_without_exfat():
    from beamo_wipe import copy as C

    assert "FAT32 or exFAT" in C.REPORT_HELP_NEED
    assert "NTFS, FAT12 and FAT16 are not supported." in C.REPORT_HELP_NEED
    assert "FAT32 or exFAT" in C.REPORT_MEDIA_WHAT and "one volume" in C.REPORT_MEDIA_WHAT


@pytest.mark.parametrize("name", ["index.html", "fr.html", "de.html", "es.html"])
def test_helper_pages_name_both_report_formats(name):
    text = (Path("helper") / name).read_text(encoding="utf-8")
    card = text.split('id="after-erasing"', 1)[0]
    assert "FAT32" in card and "exFAT" in card
    assert all("exFAT" in line for line in text.splitlines() if "FAT32" in line)


def test_owner_docs_no_longer_say_exfat_is_refused():
    claims = Path("docs/claims.md").read_text(encoding="utf-8")
    assert "formatted FAT32 or exFAT" in claims
    assert "exFAT and NTFS sticks are refused" not in claims
    for doc in ("docs/ADVANCED.md", "docs/startup-diagnostics.md"):
        text = Path(doc).read_text(encoding="utf-8")
        assert "FAT32 or exFAT" in text and "exFAT, NTFS" not in text, doc


def test_live_image_uses_only_the_signed_in_kernel_exfat_module():
    lines = Path("packaging/live/config/package-lists/beamo.list.chroot").read_text(
        encoding="utf-8"
    ).splitlines()
    packages = {line.strip() for line in lines if line.strip() and not line.startswith("#")}
    assert "linux-image-amd64" in packages
    # A FUSE mount.exfat helper would make `mount -t exfat` a fuseblk mount.
    assert not packages & {"exfat-fuse", "exfat-utils", "fuse", "fuse3"}
    assert "--apt-recommends false" in Path("packaging/live/inside-docker.sh").read_text(
        encoding="utf-8"
    )
    qemu = Path("scripts/qemu-verify.sh").read_text(encoding="utf-8")
    for module, label in (("vfat", "FAT32"), ("exfat", "exFAT")):
        assert (
            f"find \"$SQUASH_MOUNT/lib/modules\" -type f -name '{module}.ko*' -print -quit"
            f" | grep -q . || {{\n  echo \"{label} kernel module missing from ISO\" >&2\n  exit 2\n}}"
        ) in qemu
