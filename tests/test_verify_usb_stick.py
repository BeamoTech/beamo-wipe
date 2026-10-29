"""USB stick readback against KB-sized regular-file fixtures; never a real device or /sys.

Block devices are simulated by injected stat results plus a fake sysfs tree and
fake mountinfo under tmp_path. An autouse guard fails any test that would open
a /dev, /sys or /proc path on this host.
"""

import builtins
import collections
import errno
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify-usb-stick.py"
IMAGE = bytes(range(256)) * 12  # 3 KiB fixture image
SHA = hashlib.sha256(IMAGE).hexdigest()
CHUNK = 1024
ACCMODE = getattr(os, "O_ACCMODE", os.O_RDONLY | os.O_WRONLY | os.O_RDWR)
WRITE_FLAGS = os.O_CREAT | os.O_TRUNC | os.O_APPEND
UTC_RE = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
HOST_PATHS = ("/dev", "/sys", "/proc")
ROOT_LINE = "22 1 8:1 / / rw,relatime shared:1 - ext4 /dev/sda1 rw,errors=remount-ro"
DEV_LINE = "25 22 0:5 / /dev rw,nosuid shared:2 - devtmpfs udev rw,size=4096k"
RECEIPT_FIELDS = {
    "schema", "tool", "tool_sha256", "result", "reason", "lot", "unit", "started_at",
    "finished_at", "target_given", "target_resolved", "target_type", "target_device",
    "target_total_bytes", "expected_source", "expected_image", "expected_bytes",
    "expected_sha256", "observed_sha256", "bytes_compared", "bytes_beyond_image_not_compared",
    "scope",
}
pytestmark = pytest.mark.skipif(os.name != "posix", reason="USB readback supports POSIX only")
Open = collections.namedtuple("Open", "path flags fd")


@pytest.fixture(autouse=True)
def opens(monkeypatch):
    """Record every os.open and refuse host device/sysfs/proc paths outright."""
    real_open = os.open
    calls = []

    def recording_open(path, flags, *args, **kwargs):
        text = os.fsdecode(path)
        if any(text == prefix or text.startswith(prefix + "/") for prefix in HOST_PATHS):
            raise AssertionError(f"test reached a host path: {text}")
        fd = real_open(path, flags, *args, **kwargs)
        calls.append(Open(text, flags, fd))
        return fd

    monkeypatch.setattr(os, "open", recording_open)
    return calls


@pytest.fixture
def tool(monkeypatch):
    spec = importlib.util.spec_from_file_location("usb_stick", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "CHUNK", CHUNK)  # several reads per tiny fixture
    return module


def run(tool, *argv, host=None):
    try:
        return tool.main([str(arg) for arg in argv], host=host)
    except SystemExit as exc:
        return exc.code


def stick(tmp_path, data, name="stick.bin"):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def expected(size=len(IMAGE), sha=SHA):
    return ["--expected-size", str(size), "--expected-sha256", sha]


def receipt_of(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fake_stat(mode, *, dev=5, ino=7, rdev=0, size=0):
    return types.SimpleNamespace(st_mode=mode, st_dev=dev, st_ino=ino, st_rdev=rdev,
                                 st_size=size, st_mtime_ns=0)


def make_sysfs(root, *, holder=False):
    """Fake sysfs: stick sdb (8:16) with sdb1/sdb2; workstation disk sda (8:0) with sda1."""
    (root / "class/block").mkdir(parents=True)
    (root / "dev/block").mkdir(parents=True)

    def node(path, devnum, partition=False):
        path.mkdir(parents=True)
        (path / "dev").write_text(devnum + "\n")
        (path / "holders").mkdir()
        if partition:
            (path / "partition").write_text("1\n")
        (root / "class/block" / path.name).symlink_to(path)
        (root / "dev/block" / devnum).symlink_to(path)
        return path

    sdb = node(root / "devices/usb1/block/sdb", "8:16")
    node(sdb / "sdb1", "8:17", partition=True)
    sdb2 = node(sdb / "sdb2", "8:18", partition=True)
    sda = node(root / "devices/pci0/block/sda", "8:0")
    node(sda / "sda1", "8:1", partition=True)
    if holder:
        mapped = node(root / "devices/virtual/block/dm-0", "253:0")
        (mapped / "dm").mkdir()
        (mapped / "dm/name").write_text("beamo-crypt\n")
        (sdb2 / "holders/dm-0").symlink_to(mapped)
    return root


def mountinfo(tmp_path, *lines):
    path = tmp_path / "mountinfo"
    path.write_text("\n".join((ROOT_LINE, DEV_LINE) + lines) + "\n")
    return path


def block_host(tool, tmp_path, target, *lines, holder=False, linux=True, read=None):
    """Present a regular fixture file as whole block device 8:16 with fake sysfs/mountinfo."""
    info = mountinfo(tmp_path, *lines)
    fake = fake_stat(stat.S_IFBLK | 0o660, ino=os.stat(target).st_ino, rdev=os.makedev(8, 16))
    host = tool.Host(sysfs=str(make_sysfs(tmp_path / "sys", holder=holder)), mountinfo=str(info),
                     linux=linux, lstat=lambda path: fake, fstat=lambda fd: fake, read=read)
    return host, info


# --- comparison results ---

def test_exact_size_target_passes_against_image(tool, tmp_path, capsys):
    image = stick(tmp_path, IMAGE, "golden.img")
    target = stick(tmp_path, IMAGE)
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, "--image", image, "--receipt", receipt,
               "--lot", "L-2026.10", "--unit", "U_0007") == 0
    out = capsys.readouterr().out
    assert f"EXPECTED: {len(IMAGE)} bytes, SHA256 {SHA} (from --image {image}" in out
    assert "regular file" in out and "rehearsal only" in out
    assert "RESULT: PASS" in out and "(lot L-2026.10, unit U_0007)" in out
    assert "not boot, firmware, hardware" in out
    data = receipt_of(receipt)
    assert data["result"] == "PASS" and data["observed_sha256"] == SHA == data["expected_sha256"]
    assert data["expected_source"] == "image" and data["expected_image"] == str(image)
    assert data["bytes_compared"] == len(IMAGE) == data["expected_bytes"]
    assert data["bytes_beyond_image_not_compared"] == 0
    assert (data["lot"], data["unit"]) == ("L-2026.10", "U_0007")


def test_larger_target_passes_and_extra_bytes_are_not_compared(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE + os.urandom(1500))
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt) == 0
    out = capsys.readouterr().out
    assert "NOT COMPARED: 1500 bytes after the image" in out and "RESULT: PASS" in out
    data = receipt_of(receipt)
    assert data["target_total_bytes"] == len(IMAGE) + 1500
    assert data["bytes_compared"] == len(IMAGE)
    assert data["bytes_beyond_image_not_compared"] == 1500
    assert data["expected_source"] == "explicit" and data["expected_image"] is None


@pytest.mark.parametrize("offset", [0, len(IMAGE) // 2, len(IMAGE) - 1])
def test_single_byte_difference_fails(tool, tmp_path, capsys, offset):
    damaged = bytearray(IMAGE)
    damaged[offset] ^= 0x01
    target = stick(tmp_path, bytes(damaged) + b"\0" * 16)
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt) == 1
    captured = capsys.readouterr()
    assert "RESULT: FAIL" in captured.out and "PASS" not in captured.out
    assert "STOP: USB stick readback FAIL" in captured.err
    data = receipt_of(receipt)
    assert data["result"] == "FAIL" and "differs from the expected image" in data["reason"]
    assert data["observed_sha256"] == hashlib.sha256(bytes(damaged)).hexdigest() != SHA
    assert data["bytes_compared"] == len(IMAGE)


@pytest.mark.parametrize("data", [IMAGE[:-1], b""], ids=["short", "empty"])
def test_short_or_empty_target_fails(tool, tmp_path, capsys, data):
    target = stick(tmp_path, data)
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt) == 1
    assert "RESULT: FAIL" in capsys.readouterr().out
    result = receipt_of(receipt)
    assert result["result"] == "FAIL"
    assert result["reason"] == f"target holds only {len(data)} bytes; the image needs {len(IMAGE)}"
    assert result["observed_sha256"] is None and result["bytes_compared"] == 0
    assert result["bytes_beyond_image_not_compared"] is None


def test_end_of_target_during_read_fails(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)
    calls = []

    def read(fd, count):
        calls.append(count)
        if len(calls) > 2:
            raise AssertionError("target read again after end of file")
        return os.read(fd, count) if len(calls) == 1 else b""

    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt, host=tool.Host(read=read)) == 1
    assert calls == [CHUNK, CHUNK]
    assert "RESULT: FAIL" in capsys.readouterr().out
    data = receipt_of(receipt)
    assert data["reason"] == f"target ended after {CHUNK} of {len(IMAGE)} bytes"
    assert data["observed_sha256"] is None and data["bytes_compared"] == CHUNK


def test_io_error_mid_read_fails_with_errno_never_pass(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)
    calls = []

    def read(fd, count):
        calls.append(count)
        if len(calls) == 2:
            raise OSError(errno.EIO, "Input/output error")
        return os.read(fd, count)

    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt, host=tool.Host(read=read)) == 1
    captured = capsys.readouterr()
    assert "PASS" not in captured.out and "errno 5 (EIO)" in captured.err
    data = receipt_of(receipt)
    assert data["result"] == "FAIL"
    assert data["reason"].startswith(f"read error after {CHUNK} bytes: errno 5 (EIO)")
    assert data["observed_sha256"] is None and data["bytes_compared"] == CHUNK


# --- node types and symlink policy ---

@pytest.mark.parametrize("kind", ["character device", "socket", "directory", "FIFO"])
def test_non_block_special_nodes_are_refused_without_opening(tool, tmp_path, capsys, opens, kind):
    target = tmp_path / "node"
    host = None
    if kind == "directory":
        target.mkdir()
    elif kind == "FIFO":
        os.mkfifo(target)
    else:  # Simulated by stat only; no real device or socket is created or opened.
        target.write_bytes(IMAGE)
        mode = stat.S_IFCHR if kind == "character device" else stat.S_IFSOCK
        host = tool.Host(lstat=lambda path: fake_stat(mode | 0o666, rdev=os.makedev(1, 3)))
    assert run(tool, target, *expected(), host=host) == 2
    captured = capsys.readouterr()
    assert f"TARGET is a {kind}; only a whole block device" in captured.err
    assert "RESULT:" not in captured.out
    assert not [call for call in opens if call.path == os.path.realpath(target)]


def test_deliberate_symlink_is_resolved_printed_and_recorded(tool, tmp_path, capsys, opens):
    real = stick(tmp_path, IMAGE + b"tail")
    link = tmp_path / "usb-Fixture_Stick_0001-0:0"
    link.symlink_to(real)
    resolved = os.path.realpath(real)
    receipt = tmp_path / "receipt.json"
    assert run(tool, link, *expected(), "--receipt", receipt) == 0
    assert f"TARGET: {link} -> {resolved} (" in capsys.readouterr().out
    data = receipt_of(receipt)
    assert (data["target_given"], data["target_resolved"]) == (str(link), resolved)
    target_opens = [call.flags for call in opens if call.path == resolved]
    assert len(target_opens) == 1 and target_opens[0] & os.O_NOFOLLOW
    assert not [call for call in opens if call.path == str(link)]


def test_dangling_symlink_is_refused(tool, tmp_path, capsys):
    link = tmp_path / "usb-gone"
    link.symlink_to(tmp_path / "missing")
    assert run(tool, link, *expected()) == 2
    assert "cannot resolve TARGET" in capsys.readouterr().err


def test_resolution_change_between_check_and_open_is_refused(tool, tmp_path, capsys):
    first = stick(tmp_path, IMAGE, "first.bin")
    second = stick(tmp_path, IMAGE, "second.bin")
    answers = iter([str(first), str(second)])
    host = tool.Host(realpath=lambda path: next(answers))
    assert run(tool, tmp_path / "usb-link", *expected(), host=host) == 2
    assert "changed between resolution and open" in capsys.readouterr().err


def test_different_node_at_open_is_refused(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)

    def fstat(fd):
        real = os.fstat(fd)
        return fake_stat(real.st_mode, dev=real.st_dev, ino=real.st_ino + 1, size=real.st_size)

    assert run(tool, target, *expected(), host=tool.Host(fstat=fstat)) == 2
    assert "changed between resolution and open" in capsys.readouterr().err


def test_target_replaced_during_readback_fails(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)

    def read(fd, count):
        if target.exists() and not (tmp_path / "unplugged.bin").exists():
            target.rename(tmp_path / "unplugged.bin")  # same bytes, different node
            target.write_bytes(IMAGE)
        return os.read(fd, count)

    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt, host=tool.Host(read=read)) == 1
    assert "PASS" not in capsys.readouterr().out
    data = receipt_of(receipt)
    assert data["result"] == "FAIL" and data["observed_sha256"] is None
    assert data["reason"].startswith("target state changed during readback: TARGET no longer")


def test_relative_target_is_refused(tool, tmp_path, monkeypatch, capsys):
    stick(tmp_path, IMAGE)
    monkeypatch.chdir(tmp_path)
    assert run(tool, "stick.bin", *expected()) == 2
    assert "TARGET must be an absolute path" in capsys.readouterr().err


@pytest.mark.parametrize("problem", ["symlink", "gzip", "empty", "directory", "same-file"])
def test_image_input_refusals(tool, tmp_path, capsys, problem):
    target = stick(tmp_path, IMAGE)
    image = tmp_path / "golden.img"
    if problem == "symlink":
        image.symlink_to(stick(tmp_path, IMAGE, "real.img"))
    elif problem == "gzip":
        image.write_bytes(gzip.compress(IMAGE, mtime=0))
    elif problem == "empty":
        image.write_bytes(b"")
    elif problem == "directory":
        image.mkdir()
    else:
        image = target
    assert run(tool, target, "--image", image) == 2
    captured = capsys.readouterr()
    assert "STOP: USB stick readback refused" in captured.err and "RESULT:" not in captured.out


# --- argument validation ---

@pytest.mark.parametrize("extra", [
    ["--image", "IMG", "--expected-size", "3072"],
    ["--image", "IMG", "--expected-sha256", SHA],
    ["--image", "IMG", "--expected-size", "3072", "--expected-sha256", SHA],
    ["--expected-size", "3072"],
    ["--expected-sha256", SHA],
    [],
])
def test_image_and_explicit_expectations_are_mutually_exclusive(tool, tmp_path, opens, extra):
    image = stick(tmp_path, IMAGE, "golden.img")
    target = stick(tmp_path, IMAGE)
    assert run(tool, target, *[str(image) if arg == "IMG" else arg for arg in extra]) == 2
    assert opens == []


@pytest.mark.parametrize("size,sha", [
    ("0", SHA), ("-1", SHA), ("+3072", SHA), ("03072", SHA), ("3e3", SHA), ("3072.0", SHA),
    ("99999999999999999999", SHA), ("3072", SHA.upper()), ("3072", SHA[:-1]),
    ("3072", SHA + "0"), ("3072", "g" * 64), ("3072", " " + SHA[1:]),
])
def test_invalid_explicit_expectations_are_refused(tool, tmp_path, opens, size, sha):
    target = stick(tmp_path, IMAGE)
    assert run(tool, target, f"--expected-size={size}", f"--expected-sha256={sha}") == 2
    assert opens == []


@pytest.mark.parametrize("option", ["--lot", "--unit"])
@pytest.mark.parametrize("value", [
    "", "a b", "a/b", "a\\b", "..", ".hidden", "-x", "lot\n1", "lot\t1", "lot\x7f", "lot\x00",
    "é", "a" * 65, "a:b", "a*b",
])
def test_invalid_lot_and_unit_are_refused(tool, tmp_path, opens, option, value):
    target = stick(tmp_path, IMAGE)
    assert run(tool, target, *expected(), f"{option}={value}") == 2
    assert opens == []


@pytest.mark.parametrize("value", ["control\x01path", "line\nbreak"])
def test_control_characters_in_paths_are_refused(tool, tmp_path, capsys, value):
    assert run(tool, str(tmp_path / value), *expected()) == 2
    assert "control characters" in capsys.readouterr().err


# --- receipts ---

def test_receipt_is_new_private_json_with_required_fields(tool, tmp_path):
    target = stick(tmp_path, IMAGE + b"tail")
    receipt = tmp_path / "lot-A1-unit-7.json"
    previous = os.umask(0)
    try:
        assert run(tool, target, *expected(), "--lot", "A1", "--unit", "7",
                   "--receipt", receipt) == 0
    finally:
        os.umask(previous)
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    raw = receipt.read_bytes()
    assert raw.endswith(b"}\n")
    data = json.loads(raw)
    assert set(data) == RECEIPT_FIELDS
    assert data["schema"] == "beamo-wipe-usb-readback/1"
    assert data["tool"] == "scripts/verify-usb-stick.py"
    assert data["tool_sha256"] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
    assert data["result"] == "PASS" and data["reason"].startswith(f"the first {len(IMAGE)} bytes")
    assert (data["lot"], data["unit"]) == ("A1", "7")
    assert re.fullmatch(UTC_RE, data["started_at"]) and re.fullmatch(UTC_RE, data["finished_at"])
    assert data["started_at"] <= data["finished_at"]
    assert data["target_given"] == str(target) and data["target_type"] == "regular"
    assert data["target_resolved"] == os.path.realpath(target)
    assert data["target_device"] is None and data["target_total_bytes"] == len(IMAGE) + 4
    assert (data["expected_bytes"], data["expected_sha256"]) == (len(IMAGE), SHA)
    assert (data["observed_sha256"], data["bytes_compared"]) == (SHA, len(IMAGE))
    assert data["bytes_beyond_image_not_compared"] == 4
    assert "not boot, firmware, hardware, Secure Boot or erase acceptance" in data["scope"]
    assert "does not authenticate the image publisher" in data["scope"]


@pytest.mark.parametrize("existing", ["file", "symlink", "dangling-symlink"])
def test_receipt_never_overwrites_and_refuses_before_reading(tool, tmp_path, capsys, existing):
    target = stick(tmp_path, IMAGE)
    receipt = tmp_path / "receipt.json"
    other = tmp_path / "other.json"
    if existing == "file":
        receipt.write_text("keep")
    elif existing == "symlink":
        other.write_text("keep")
        receipt.symlink_to(other)
    else:
        receipt.symlink_to(other)
    reads = []
    host = tool.Host(read=lambda fd, count: reads.append(count) or os.read(fd, count))
    assert run(tool, target, *expected(), "--receipt", receipt, host=host) == 2
    assert "receipt already exists" in capsys.readouterr().err
    assert reads == []
    if existing == "dangling-symlink":
        assert receipt.is_symlink() and not other.exists()
    else:
        assert receipt.read_text() == "keep"


def test_receipt_created_during_readback_is_not_replaced(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)
    receipt = tmp_path / "receipt.json"

    def read(fd, count):
        if not receipt.exists():
            receipt.write_text("someone else")
        return os.read(fd, count)

    assert run(tool, target, *expected(), "--receipt", receipt, host=tool.Host(read=read)) == 2
    captured = capsys.readouterr()
    assert receipt.read_text() == "someone else"
    assert "receipt was not written" in captured.err and "RECEIPT:" not in captured.out


def test_fail_stays_exit_1_when_its_receipt_cannot_be_written(tool, tmp_path, capsys):
    # A real mismatch must not turn into "error, rerun": a passing rerun
    # would then hide it. Manufacturing holds the lot on exit 1.
    target = stick(tmp_path, IMAGE[:-1] + b"\x00")
    receipt = tmp_path / "receipt.json"

    def read(fd, count):
        if not receipt.exists():
            receipt.write_text("someone else")
        return os.read(fd, count)

    assert run(tool, target, *expected(), "--receipt", receipt, host=tool.Host(read=read)) == 1
    captured = capsys.readouterr()
    assert receipt.read_text() == "someone else"
    assert "RESULT: FAIL" in captured.out and "RECEIPT:" not in captured.out
    assert "receipt was not written" in captured.err and "readback FAIL" in captured.err


def test_every_open_is_read_only_except_the_new_receipt(tool, tmp_path, monkeypatch, opens):
    import fcntl

    image = stick(tmp_path, IMAGE, "golden.img")
    target = stick(tmp_path, IMAGE + b"more")
    receipt = tmp_path / "receipt.json"
    writes = []
    real_write = os.write

    def recording_write(fd, data):
        writes.append(fd)
        return real_write(fd, data)

    real_builtin_open = builtins.open

    def read_only_builtin_open(file, mode="r", *args, **kwargs):
        assert not set(mode) & set("wax+"), (file, mode)
        return real_builtin_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(os, "write", recording_write)
    monkeypatch.setattr(builtins, "open", read_only_builtin_open)
    monkeypatch.setattr(fcntl, "ioctl", lambda *args, **kwargs: pytest.fail("ioctl called"))
    assert run(tool, target, "--image", image, "--receipt", receipt, "--lot", "A1") == 0

    created = [call for call in opens if call.path == str(receipt)]
    assert len(created) == 1
    flags = created[0].flags
    assert flags & ACCMODE == os.O_WRONLY and flags & os.O_CREAT and flags & os.O_EXCL
    assert flags & os.O_NOFOLLOW and not flags & (os.O_TRUNC | os.O_APPEND)
    others = [call for call in opens if call.path != str(receipt)]
    assert {str(image), os.path.realpath(target)} <= {call.path for call in others}
    for call in others:
        assert call.flags & ACCMODE == os.O_RDONLY, call
        assert not call.flags & (WRITE_FLAGS | os.O_EXCL), call
    for path in (str(image), os.path.realpath(target)):
        assert all(call.flags & os.O_NOFOLLOW for call in others if call.path == path)
    assert writes and set(writes) == {created[0].fd}


# --- Linux block devices: fake sysfs and mountinfo only ---

def test_idle_whole_disk_is_accepted_and_workstation_or_partition_refused(tool, tmp_path):
    host = tool.Host(sysfs=str(make_sysfs(tmp_path / "sys")),
                     mountinfo=str(mountinfo(tmp_path)), linux=True)
    assert tool.check_block_idle(host, (8, 16)) == "sdb"
    with pytest.raises(tool.Refusal, match="sda holds this workstation's running root"):
        tool.check_block_idle(host, (8, 0))
    with pytest.raises(tool.Refusal, match="sdb1 is a partition; give the whole USB device"):
        tool.check_block_idle(host, (8, 17))


@pytest.mark.parametrize("case,lines,message", [
    ("disk", ["40 22 8:16 / /mnt/raw ro - iso9660 /dev/sdb ro"],
     "sdb on sdb is mounted at '/mnt/raw'"),
    ("partition", [r"41 22 8:17 / /media/qa/BEAMO\040WIPE rw,nosuid shared:9 - vfat /dev/sdb1 rw"],
     "sdb1 on sdb is mounted at '/media/qa/BEAMO WIPE'"),
    ("root-partition", ["1 0 8:18 / / rw - ext4 /dev/sdb2 rw"],
     "sdb holds this workstation's running root filesystem (via sdb2)"),
    ("anonymous-device-source", ["43 22 0:78 / /data rw - btrfs /dev/sdb2 rw"],
     "sdb2 on sdb is mounted at '/data'"),
    ("holder-root", ["1 0 253:0 / / rw - ext4 /dev/mapper/beamo-crypt rw"],
     "sdb holds this workstation's running root filesystem (via dm-0)"),
    ("holder-mapper-source", ["42 22 0:77 / /srv rw - btrfs /dev/mapper/beamo-crypt rw"],
     "dm-0 on sdb is mounted at '/srv'"),
    ("holder-unmounted", [], "dm-0 is the holder of sdb2"),
])
def test_in_use_block_device_is_refused(tool, tmp_path, case, lines, message):
    sysfs = make_sysfs(tmp_path / "sys", holder=case.startswith("holder"))
    host = tool.Host(sysfs=str(sysfs), mountinfo=str(mountinfo(tmp_path, *lines)), linux=True)
    with pytest.raises(tool.Refusal, match=re.escape(message)):
        tool.check_block_idle(host, (8, 16))


@pytest.mark.parametrize("damage", ["unknown-device", "missing-holders", "bad-dev",
                                    "malformed-mountinfo", "empty-mountinfo",
                                    "missing-mountinfo"])
def test_unknown_mount_state_fails_closed(tool, tmp_path, damage):
    sysfs = make_sysfs(tmp_path / "sys")
    info = mountinfo(tmp_path)
    devnum = (8, 16)
    if damage == "unknown-device":
        devnum = (8, 32)
    elif damage == "missing-holders":
        (sysfs / "devices/usb1/block/sdb/sdb1/holders").rmdir()
    elif damage == "bad-dev":
        (sysfs / "devices/usb1/block/sdb/sdb2/dev").write_text("eight:eighteen\n")
    elif damage == "malformed-mountinfo":
        info.write_text("22 1 8:1 / / rw\n")
    elif damage == "empty-mountinfo":
        info.write_text("")
    else:
        info.unlink()
    host = tool.Host(sysfs=str(sysfs), mountinfo=str(info), linux=True)
    with pytest.raises(tool.Refusal, match="mount state unknown"):
        tool.check_block_idle(host, devnum)


def test_simulated_idle_block_device_uses_exclusive_read_only_open(tool, tmp_path, capsys, opens):
    target = stick(tmp_path, IMAGE + b"\0" * 2048)
    host, _info = block_host(tool, tmp_path, target)
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt, host=host) == 0
    assert "(block device 8:16, %d bytes)" % (len(IMAGE) + 2048) in capsys.readouterr().out
    flags = [call.flags for call in opens if call.path == os.path.realpath(target)]
    assert len(flags) == 1
    assert flags[0] & ACCMODE == os.O_RDONLY and flags[0] & os.O_EXCL
    assert flags[0] & os.O_NOFOLLOW and not flags[0] & WRITE_FLAGS
    data = receipt_of(receipt)
    assert (data["target_type"], data["target_device"]) == ("block", "8:16")
    assert data["target_total_bytes"] == len(IMAGE) + 2048
    assert data["bytes_beyond_image_not_compared"] == 2048


def test_simulated_mounted_block_device_is_refused_before_open(tool, tmp_path, capsys, opens):
    target = stick(tmp_path, IMAGE)
    host, _info = block_host(
        tool, tmp_path, target, r"41 22 8:17 / /media/qa/BEAMO\040WIPE rw - vfat /dev/sdb1 rw")
    assert run(tool, target, *expected(), host=host) == 2
    captured = capsys.readouterr()
    assert "sdb1 on sdb is mounted at '/media/qa/BEAMO WIPE'" in captured.err
    assert "RESULT:" not in captured.out
    assert not [call for call in opens if call.path == os.path.realpath(target)]


def test_simulated_mount_during_readback_fails(tool, tmp_path, capsys):
    target = stick(tmp_path, IMAGE)
    info = tmp_path / "mountinfo"

    def read(fd, count):
        with info.open("a", encoding="utf-8") as table:
            table.write("44 22 8:17 / /media/auto rw - vfat /dev/sdb1 rw\n")
        return os.read(fd, count)

    host, _info = block_host(tool, tmp_path, target, read=read)
    receipt = tmp_path / "receipt.json"
    assert run(tool, target, *expected(), "--receipt", receipt, host=host) == 1
    assert "PASS" not in capsys.readouterr().out
    data = receipt_of(receipt)
    assert data["result"] == "FAIL" and data["observed_sha256"] is None
    assert data["reason"] == ("target state changed during readback: sdb1 on sdb is mounted at "
                              "'/media/auto'; unmount it (do not format or write it) before "
                              "readback")


def test_block_device_is_refused_off_linux(tool, tmp_path, capsys, opens):
    target = stick(tmp_path, IMAGE)
    host, _info = block_host(tool, tmp_path, target, linux=False)
    assert run(tool, target, *expected(), host=host) == 2
    assert "Linux only" in capsys.readouterr().err
    assert not [call for call in opens if call.path == os.path.realpath(target)]


def test_kernel_exclusive_claim_failure_is_refused(tool, tmp_path, monkeypatch, capsys):
    target = stick(tmp_path, IMAGE)
    host, _info = block_host(tool, tmp_path, target)
    resolved = os.path.realpath(target)
    current_open = os.open

    def busy(path, flags, *args, **kwargs):
        if os.fsdecode(path) == resolved:
            raise OSError(errno.EBUSY, "Device or resource busy")
        return current_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", busy)
    assert run(tool, target, *expected(), host=host) == 2
    assert "in use by the kernel" in capsys.readouterr().err
