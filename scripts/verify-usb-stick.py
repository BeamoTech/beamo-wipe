#!/usr/bin/env python3
"""Read back a written Beamo Wipe USB stick against its verified image; never write media.

Expected bytes come from the regular .img already verified by
scripts/verify-usb-download.py (--image), or from that image's authenticated
size and SHA-256 given explicitly. This tool does not authenticate them.
TARGET is the whole written stick: a Linux block device, preferably its
/dev/disk/by-id/usb-... link, or a regular file for rehearsal only. Exactly
the first expected-size bytes are hashed. Capacity beyond the image is not
compared. PASS proves those image bytes only, not boot, firmware, hardware,
Secure Boot or erase acceptance.

Read-only by construction: TARGET, --image and every inspected sysfs/proc file
are opened O_RDONLY; there is no write, ioctl, cache flush or partition rescan.
Only the optional new --receipt is created (O_EXCL, mode 0600, never replaced).

Symlink policy: TARGET may be a deliberate link (for example by-id). It is
resolved once and printed, the resolved node is opened with O_NOFOLLOW, and the
link is resolved again and must still name the same node; it is checked again
after reading. --image and --receipt never follow a final symlink.

On Linux a block TARGET must be a whole disk. It is refused when it, one of its
partitions or a holder (device-mapper, RAID, LVM) is mounted, holds the running
root filesystem, or is held at all. It is opened O_EXCL, so the kernel also
refuses it while in use and refuses new mounts until the read finishes.

Exit status: 0 PASS; 1 FAIL (different bytes, short target, read error, or the
target changed during readback; a receipt is still written, and a FAIL whose
receipt cannot be written still exits 1); 2 usage error or refusal before any
comparison, or a PASS whose receipt could not be written (no qualifying result).
"""

import argparse
import errno
import functools
import hashlib
import json
import os
import re
import stat
import sys
import time

SCHEMA = "beamo-wipe-usb-readback/1"
TOOL = "scripts/verify-usb-stick.py"
CHUNK = 4 * 1024 * 1024
SCOPE = (
    "Proves only that the first expected_bytes of the target equaled the expected image "
    "bytes when read. Bytes beyond the image were not compared. It is not boot, firmware, "
    "hardware, Secure Boot or erase acceptance, and it does not authenticate the image "
    "publisher; verify the image with scripts/verify-usb-download.py first."
)
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
HEX64_RE = re.compile(r"[0-9a-f]{64}")
SIZE_RE = re.compile(r"[1-9][0-9]{0,18}")
DEVNUM_RE = re.compile(r"([0-9]{1,10}):([0-9]{1,10})\n?")
KERNEL_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._!+-]{0,63}")
MAX_BYTES = 2**63 - 1
MAX_RELATED = 256
READ_FLAGS = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
              | getattr(os, "O_NONBLOCK", 0))
GZIP_MAGIC = b"\x1f\x8b"


class Refusal(RuntimeError):
    """Stop before any comparison result exists (exit 2, no receipt)."""


class Host:
    """Read-only observation boundary; tests pass fake sysfs, mountinfo and stat results."""

    def __init__(self, *, sysfs="/sys", mountinfo="/proc/self/mountinfo", linux=None,
                 lstat=None, fstat=None, read=None, realpath=None):
        self.sysfs = sysfs
        self.mountinfo = mountinfo
        self.linux = sys.platform.startswith("linux") if linux is None else linux
        self.lstat = lstat or os.lstat
        self.fstat = fstat or os.fstat
        self.read = read or os.read
        self.realpath = realpath or functools.partial(os.path.realpath, strict=True)


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def describe(exc):
    if getattr(exc, "errno", None):
        name = errno.errorcode.get(exc.errno, "unknown")
        return f"errno {exc.errno} ({name}): {exc.strerror or exc}"
    return str(exc)


def identifier(text):
    if not ID_RE.fullmatch(text):
        raise argparse.ArgumentTypeError(
            "use 1-64 ASCII letters, digits, '.', '_' or '-', starting with a letter or digit")
    return text


def byte_count(text):
    if not SIZE_RE.fullmatch(text) or int(text) > MAX_BYTES:
        raise argparse.ArgumentTypeError("must be a positive decimal byte count")
    return int(text)


def sha256_hex(text):
    if not HEX64_RE.fullmatch(text):
        raise argparse.ArgumentTypeError("must be 64 lowercase hexadecimal characters")
    return text


def checked_path(text, what):
    if not text or any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise Refusal(f"{what} path is empty or contains control characters")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Refusal(f"{what} path is not valid UTF-8") from exc
    return text


def read_small(path, limit=1024 * 1024):
    """Read one small sysfs/proc/tool file through a read-only descriptor."""
    fd = os.open(path, READ_FLAGS)
    try:
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                return b"".join(chunks)
            total += len(chunk)
            if total > limit:
                raise Refusal(f"{path} is unexpectedly large")
            chunks.append(chunk)
    finally:
        os.close(fd)


def _identity(st):
    return (stat.S_IFMT(st.st_mode), st.st_dev, st.st_ino, getattr(st, "st_rdev", 0))


def _kind(mode):
    for test, label in ((stat.S_ISBLK, "block"), (stat.S_ISREG, "regular"),
                        (stat.S_ISCHR, "a character device"), (stat.S_ISDIR, "a directory"),
                        (stat.S_ISFIFO, "a FIFO"), (stat.S_ISSOCK, "a socket"),
                        (stat.S_ISLNK, "a symbolic link")):
        if test(mode):
            return label
    return "an unsupported file type"


# --- Linux in-use checks (sysfs holders/partitions + mountinfo major:minor) ---

def _devnum(text, what):
    match = DEVNUM_RE.fullmatch(text)
    if not match:
        raise Refusal(f"cannot parse the device number of {what}; mount state unknown")
    return int(match[1]), int(match[2])


def _sys_dev(directory):
    return _devnum(read_small(os.path.join(directory, "dev"), 64).decode("ascii", "replace"),
                   directory)


def _sys_node(sysfs, devnum):
    link = os.path.join(sysfs, "dev", "block", "%d:%d" % devnum)
    directory = os.path.realpath(link, strict=True)
    name = os.path.basename(directory)
    if not KERNEL_NAME_RE.fullmatch(name) or _sys_dev(directory) != devnum:
        raise Refusal("sysfs entry for %d:%d is inconsistent; mount state unknown" % devnum)
    return name, directory


def _related(sysfs, name, directory, devnum):
    """Map the disk, its partitions and (recursively) their holders to device numbers."""
    related = {name: (devnum, "disk")}
    aliases = {}
    pending = [(name, directory)]
    for entry in sorted(os.listdir(directory)):
        sub = os.path.join(directory, entry)
        if KERNEL_NAME_RE.fullmatch(entry) and os.path.isfile(os.path.join(sub, "partition")):
            related[entry] = (_sys_dev(sub), "partition")
            pending.append((entry, sub))
    while pending:
        owner, path = pending.pop()
        for holder in sorted(os.listdir(os.path.join(path, "holders"))):
            if holder in related:
                continue
            if not KERNEL_NAME_RE.fullmatch(holder) or len(related) >= MAX_RELATED:
                raise Refusal(f"cannot inspect holders of {owner}; mount state unknown")
            held = os.path.realpath(os.path.join(sysfs, "class", "block", holder), strict=True)
            related[holder] = (_sys_dev(held), f"holder of {owner}")
            mapper = os.path.join(held, "dm", "name")
            if os.path.isfile(mapper):
                aliases["/dev/mapper/" + read_small(mapper, 256).decode("utf-8", "replace")
                        .strip()] = holder
            pending.append((holder, held))
    return related, aliases


def _unescape(field):
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), field)


def parse_mountinfo(data):
    """Return (major:minor, mount point, source) for every /proc/self/mountinfo line."""
    mounts = []
    for line in data.decode("utf-8", "surrogateescape").splitlines():
        fields = line.split(" ")
        try:
            separator = fields.index("-", 6)
            mounts.append((_devnum(fields[2], "a mount"), _unescape(fields[4]),
                           _unescape(fields[separator + 2])))
        except (ValueError, IndexError, Refusal) as exc:
            raise Refusal("cannot parse the mount table; mount state unknown") from exc
    if not mounts:
        raise Refusal("the mount table is empty; mount state unknown")
    return mounts


def check_block_idle(host, devnum):
    """Refuse a partition, or a disk that is mounted, held, or carries the running root."""
    try:
        name, directory = _sys_node(host.sysfs, devnum)
        if os.path.lexists(os.path.join(directory, "partition")):
            raise Refusal(f"{name} is a partition; give the whole USB device, not a partition")
        related, aliases = _related(host.sysfs, name, directory, devnum)
        mounts = parse_mountinfo(read_small(host.mountinfo, 8 * 1024 * 1024))
    except OSError as exc:
        raise Refusal(f"cannot inspect block device {devnum[0]}:{devnum[1]} in sysfs or the "
                      f"mount table ({describe(exc)}); mount state unknown") from exc
    by_number = {number: member for member, (number, _role) in related.items()}
    by_source = {"/dev/" + member: member for member in related}
    by_source.update(aliases)

    def owner(number, source):
        return by_number.get(number) or by_source.get(source)

    for number, point, source in mounts:
        member = owner(number, source)
        if point == "/" and member:
            raise Refusal(f"{name} holds this workstation's running root filesystem "
                          f"(via {member}); refusing")
    for number, point, source in mounts:
        member = owner(number, source)
        if member:
            raise Refusal(f"{member} on {name} is mounted at {point!r}; unmount it (do not "
                          "format or write it) before readback")
    for member, (_number, role) in related.items():
        if role.startswith("holder"):
            raise Refusal(f"{name} is in use: {member} is the {role} (device-mapper, RAID or "
                          "LVM); release it before readback")
    return name


# --- Expected image and target ---

def image_identity(path):
    """Hash the --image regular file; its size and SHA-256 are the expected values."""
    try:
        fd = os.open(path, READ_FLAGS)
    except OSError as exc:
        raise Refusal(f"cannot open --image read-only without following links: "
                      f"{describe(exc)}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise Refusal("--image must be a non-empty regular file")
        digest, count = hashlib.sha256(), 0
        while True:
            chunk = os.read(fd, CHUNK)
            if not chunk:
                break
            if count == 0 and chunk.startswith(GZIP_MAGIC):
                raise Refusal("--image is gzip-compressed; use the decompressed .img verified "
                              "by scripts/verify-usb-download.py")
            count += len(chunk)
            if count > before.st_size:
                raise Refusal("--image grew while being hashed")
            digest.update(chunk)
        after = os.fstat(fd)
        if (count != before.st_size or _identity(after) != _identity(before)
                or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns):
            raise Refusal("--image changed while being hashed")
    finally:
        os.close(fd)
    return count, digest.hexdigest(), (before.st_dev, before.st_ino)


def open_target(host, given, image_id):
    if not os.path.isabs(given):
        raise Refusal("TARGET must be an absolute path, for example /dev/disk/by-id/usb-...")
    try:
        resolved = host.realpath(given)
        before = host.lstat(resolved)
    except OSError as exc:
        raise Refusal(f"cannot resolve TARGET: {describe(exc)}") from exc
    kind = _kind(before.st_mode)
    if kind not in ("block", "regular"):
        raise Refusal(f"TARGET is {kind}; only a whole block device (or a regular file for "
                      "rehearsal) is accepted")
    devnum = None
    flags = READ_FLAGS
    if kind == "block":
        if not host.linux:
            raise Refusal("block-device readback is supported on Linux only, where mount and "
                          "root-disk checks are available")
        devnum = (os.major(before.st_rdev), os.minor(before.st_rdev))
        check_block_idle(host, devnum)
        flags |= os.O_EXCL  # Linux: exclusive read-only claim, never creation.
    try:
        fd = os.open(resolved, flags)
    except OSError as exc:
        if exc.errno == errno.EBUSY:
            raise Refusal("TARGET is in use by the kernel (mounted, swap, RAID/LVM or "
                          "device-mapper); release it before readback") from exc
        raise Refusal(f"cannot open TARGET read-only: {describe(exc)}") from exc
    try:
        opened = host.fstat(fd)
        again = host.realpath(given)
        named = host.lstat(again)
        if again != resolved or not _identity(before) == _identity(opened) == _identity(named):
            raise Refusal("TARGET changed between resolution and open; re-identify the stick "
                          "and run again")
        if kind == "regular" and (opened.st_dev, opened.st_ino) == image_id:
            raise Refusal("TARGET is the --image file itself")
        if kind == "block":
            total = os.lseek(fd, 0, os.SEEK_END)
            os.lseek(fd, 0, os.SEEK_SET)
        else:
            total = opened.st_size
    except BaseException as exc:
        os.close(fd)
        if isinstance(exc, OSError):
            raise Refusal(f"cannot inspect opened TARGET: {describe(exc)}") from exc
        raise
    return fd, resolved, kind, devnum, _identity(opened), total


def compare(host, fd, total, expected_bytes, expected_sha256):
    """Return (result, reason, observed_sha256, bytes_compared)."""
    if total < expected_bytes:
        return ("FAIL", f"target holds only {total} bytes; the image needs {expected_bytes}",
                None, 0)
    digest, count, chunk = hashlib.sha256(), 0, CHUNK
    while count < expected_bytes:
        want = min(chunk, expected_bytes - count)
        try:
            data = host.read(fd, want)
        except OSError as exc:
            return "FAIL", f"read error after {count} bytes: {describe(exc)}", None, count
        if not data:
            return "FAIL", f"target ended after {count} of {expected_bytes} bytes", None, count
        if len(data) > want:
            return "FAIL", "target returned more bytes than requested", None, count
        digest.update(data)
        count += len(data)
    observed = digest.hexdigest()
    if observed != expected_sha256:
        return ("FAIL", f"SHA-256 of the first {expected_bytes} bytes differs from the "
                "expected image", observed, count)
    return "PASS", f"the first {expected_bytes} bytes match the expected SHA-256", observed, count


def recheck(host, given, resolved, identity, devnum):
    """Describe a state change during readback, or return None."""
    try:
        if host.realpath(given) != resolved or _identity(host.lstat(resolved)) != identity:
            return "TARGET no longer names the device that was read (unplugged, replaced or relinked)"
        if devnum is not None:
            check_block_idle(host, devnum)
    except Refusal as exc:
        return str(exc)
    except OSError as exc:
        return f"TARGET could not be re-identified after reading: {describe(exc)}"
    return None


def write_receipt(path, receipt):
    payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_CLOEXEC", 0))
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "short receipt write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    directory = os.open(os.path.dirname(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                        | getattr(os, "O_CLOEXEC", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def tool_sha256():
    try:
        return hashlib.sha256(read_small(os.path.realpath(__file__))).hexdigest()
    except (OSError, Refusal):
        return None


def run(args, host):
    started = utc_now()
    checked_path(args.target, "TARGET")
    if os.name != "posix":
        raise Refusal("supported on Linux (block devices) and POSIX regular-file rehearsal only")
    receipt_path = None
    if args.receipt is not None:
        receipt_path = os.path.abspath(checked_path(args.receipt, "--receipt"))
        if os.path.lexists(receipt_path):
            raise Refusal(f"receipt already exists; refusing to overwrite {receipt_path}")
        if not os.path.isdir(os.path.dirname(receipt_path)):
            raise Refusal("the --receipt directory does not exist")
    if args.image is not None:
        image = os.path.abspath(checked_path(args.image, "--image"))
        expected_bytes, expected_sha256, image_id = image_identity(image)
        origin = f"from --image {image}; verify it first with scripts/verify-usb-download.py"
    else:
        image, image_id = None, None
        expected_bytes, expected_sha256 = args.expected_size, args.expected_sha256
        origin = "given explicitly; take both from the authenticated release inventory"
    print(f"EXPECTED: {expected_bytes} bytes, SHA256 {expected_sha256} ({origin})")

    fd, resolved, kind, devnum, identity, total = open_target(host, args.target, image_id)
    try:
        if kind == "block":
            detail = "block device %d:%d, %d bytes" % (devnum[0], devnum[1], total)
        else:
            detail = f"regular file, {total} bytes; rehearsal only, not a physical stick"
        print(f"TARGET: {args.target} -> {resolved} ({detail})")
        print(f"READING: the first {expected_bytes} bytes read-only; nothing is written")
        result, reason, observed, compared = compare(host, fd, total, expected_bytes,
                                                     expected_sha256)
        problem = recheck(host, args.target, resolved, identity, devnum)
    finally:
        os.close(fd)
    if problem:
        reason = (f"target state changed during readback: {problem}" if result == "PASS"
                  else f"{reason}; also {problem}")
        result, observed = "FAIL", None
    beyond = total - expected_bytes if total >= expected_bytes else None
    receipt = {
        "schema": SCHEMA,
        "tool": TOOL,
        "tool_sha256": tool_sha256(),
        "result": result,
        "reason": reason,
        "lot": args.lot,
        "unit": args.unit,
        "started_at": started,
        "finished_at": utc_now(),
        "target_given": args.target,
        "target_resolved": resolved,
        "target_type": kind,
        "target_device": None if devnum is None else "%d:%d" % devnum,
        "target_total_bytes": total,
        "expected_source": "image" if image else "explicit",
        "expected_image": image,
        "expected_bytes": expected_bytes,
        "expected_sha256": expected_sha256,
        "observed_sha256": observed,
        "bytes_compared": compared,
        "bytes_beyond_image_not_compared": beyond,
        "scope": SCOPE,
    }
    if observed:
        print(f"OBSERVED: SHA256 {observed} of the first {compared} bytes")
    else:
        print(f"OBSERVED: no complete hash; {compared} of {expected_bytes} bytes were read")
    if beyond is not None:
        print(f"NOT COMPARED: {beyond} bytes after the image; capacity beyond the image is "
              "not part of this check")
    labels = ", ".join(f"{key} {value}" for key, value in (("lot", args.lot), ("unit", args.unit))
                       if value)
    print(f"RESULT: {result} - {reason}" + (f" ({labels})" if labels else ""))
    print("SCOPE: image bytes only; not boot, firmware, hardware, Secure Boot or erase acceptance")
    if receipt_path is not None:
        try:
            write_receipt(receipt_path, receipt)
        except OSError as exc:
            print(f"STOP: the {result} receipt was not written ({describe(exc)}); nothing "
                  f"qualifies this unit until a new run writes one: {receipt_path}",
                  file=sys.stderr)
            if result != "PASS":
                # A real mismatch or read error stays a FAIL: a later passing
                # rerun must not hide it. Keep this output as the record.
                print(f"STOP: USB stick readback FAIL: {reason}; keep this output and hold "
                      "the lot", file=sys.stderr)
                return 1
            return 2
        print(f"RECEIPT: {receipt_path}")
    if result == "PASS":
        return 0
    print(f"STOP: USB stick readback FAIL: {reason}", file=sys.stderr)
    return 1


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", metavar="TARGET",
                        help="whole written stick, e.g. /dev/disk/by-id/usb-...; a regular "
                             "file only for rehearsal")
    parser.add_argument("--image", help="regular .img already verified by "
                                        "scripts/verify-usb-download.py")
    parser.add_argument("--expected-size", type=byte_count, metavar="BYTES")
    parser.add_argument("--expected-sha256", type=sha256_hex, metavar="HEX")
    parser.add_argument("--lot", type=identifier, help="lot ID recorded in the receipt")
    parser.add_argument("--unit", type=identifier, help="unit ID recorded in the receipt")
    parser.add_argument("--receipt", help="new JSON receipt path (never overwritten; mode 0600)")
    return parser


def main(argv=None, host=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    explicit = args.expected_size is not None or args.expected_sha256 is not None
    if args.image is not None and explicit:
        parser.error("use either --image or --expected-size with --expected-sha256, not both")
    if args.image is None and (args.expected_size is None or args.expected_sha256 is None):
        parser.error("give --image, or both --expected-size and --expected-sha256")
    try:
        return run(args, host or Host())
    except (Refusal, OSError, ValueError) as exc:
        detail = describe(exc) if isinstance(exc, OSError) else str(exc)
        print(f"STOP: USB stick readback refused: {detail}", file=sys.stderr)
    except KeyboardInterrupt:
        print("STOP: interrupted; no result and no receipt", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
