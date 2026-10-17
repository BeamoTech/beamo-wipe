# Pinned engine record-origin source verification

2026-10-17, source-only review; no downloaded code was executed. The primary
authorized web-tool reads of official upstream/Debian source. The runtime skill
and networking reference were read; `environment_status` is absent from the live
catalog and `/etc/codex/network-policy.json` is absent. No credentials, proxy
settings, native command or executor networking configuration were accessed.

Exact nwipe commit: `6082bde060091e66365d852a1877f2ee80c67105`, matching
`src/beamo_wipe/__init__.py` and the live build hook. The following observations
are source evidence, not physical-device or installed-binary acceptance.

## nwipe input and log paths

[`context.h`](https://raw.githubusercontent.com/martijnvanbrummelen/nwipe/6082bde060091e66365d852a1877f2ee80c67105/src/context.h)
lines 89–100 defines a 20-byte processed serial, 40-byte UUID buffer and 64-byte
stored DMI fields. The model is a pointer, not a 40-byte nwipe allocation.

[`device.c`](https://raw.githubusercontent.com/martijnvanbrummelen/nwipe/6082bde060091e66365d852a1877f2ee80c67105/src/device.c)
lines 531–536 takes the libparted model and applies prefix/endian adjustments.
Lines 624–640 replace the processed serial with twenty fixed X/question-mark
characters for quiet mode, terminate it, then normalize ASCII/control content.
The normalizer at 838–862 removes non-ASCII and control bytes. Initial device
info at 738–744 uses that processed serial, fixed enum-derived bus text, and the
model. The smartctl transcript logger at 1142–1180 requires verbose mode, which
the shipped argv does not enable. These paths do not expose an arbitrary
unfiltered long serial as a log continuation.

[`logging.c`](https://raw.githubusercontent.com/martijnvanbrummelen/nwipe/6082bde060091e66365d852a1877f2ee80c67105/src/logging.c)
lines 576–601 reads DMI output one line at a time, removes its terminal LF and
logs each with a new timestamp and fixed keyword/body label; quiet mode replaces
identifying values. An internal firmware LF therefore cannot become a bare
continuation of the logged value. Lines 1030–1047 truncate the status-table model
to 17 bytes and use the processed serial. This rejects the proposed long serial
or DMI continuation attack without assuming dmidecode's control filtering.

[`nwipe.c`](https://raw.githubusercontent.com/martijnvanbrummelen/nwipe/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c)
lines 890–894 logs the processed serial. Its progress/success and failure paths
remain distinct from a final Drive Status record. `nwipe.h` was also read;
the relevant string limits are in context.h.

## Exact bookworm libparted paths

[`parted 3.5-3 linux.c`](https://sources.debian.org/src/parted/3.5-3/libparted/arch/linux.c)
is explicitly listed for bookworm. Source lines 914–928 strip whitespace runs
but can preserve an internal LF. IDE copies exactly 40 model bytes and appends
NUL (973–975). SCSI allocates 26 bytes and formats at most eight vendor and
sixteen product bytes, separated by one space (1174–1181). Its longer sysfs
reads cannot bypass that final format limit.

The sysfs helper (1029–1047) uses one `fgets` then strips trailing whitespace.
NVMe (1402–1414) has no independent 40-byte limit here, but LF ends its single
read and is removed. MMC uses the same helper (1372–1398). Xen and Virtio models
are fixed literals (1548–1562). Retained model LFs are bounded by IDE40/SCSI25;
sysfs models cannot retain LF.

Inference: a full timestamp/severity plus target skip/open/geometry marker
cannot be injected as a new native record through these eligible model paths.
No product fix or new regression is justified by this rejected hypothesis.

Direct Debian file/raw/API and GNU/Salsa opens initially returned unavailable
errors. Navigating Debian's package → libparted → arch → linux.c links succeeded;
the raw download link remained unsupported (`text/x-csrc`). The HTML source
contains 3,465 source lines, 115,737 bytes. Source line numbers above are its
displayed C line numbers, not the browser's additional HTML/link line numbers.
The exact HTML was read, not treated as an executed or byte-hashed source receipt.
The dmidecode source fetch failed and is not needed for the fixed-label,
line-oriented nwipe DMI conclusion. No unverified dmidecode sanitization claim
is made.
