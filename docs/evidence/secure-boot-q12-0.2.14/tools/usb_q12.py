"""Q12 inspection of the published USB image (.img.gz), streamed once.

Usage: python -I usb_q12.py <img.gz-url> <expected-gz-sha256> <expected-img-sha256> <out.json>

Streams the gzip download through SHA-256 and decompresses it in memory,
hashing the decompressed image too. Keeps only the first CAPTURE bytes of the
decompressed image (partition table, FAT and early data region), then reads
EFI/boot/*.efi from the EFI-capable FAT partition held in that window. Writes
only <out.json>; nothing is written to a disk or device.
"""
import hashlib
import json
import os
import struct
import sys
import urllib.request
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fat  # noqa: E402
import pe_sig  # noqa: E402

URL, GZ_EXPECT, IMG_EXPECT, OUT = sys.argv[1:5]
CAPTURE = 192 * 1024 * 1024
# Optional extra window "START_MB:END_MB" (absolute image offsets).
EXTRA = [int(x) * 1024 * 1024 for x in os.environ.get("EXTRA_WINDOW_MB", "0:0").split(":")]
extra = bytearray()
gz_h, img_h = hashlib.sha256(), hashlib.sha256()
captured = bytearray()
img_size = gz_size = 0
d = zlib.decompressobj(16 + zlib.MAX_WBITS)
req = urllib.request.Request(URL, headers={"User-Agent": "q12-inspector/1.0"})
with urllib.request.urlopen(req, timeout=300) as r:
    while True:
        chunk = r.read(8 * 1024 * 1024)
        if not chunk:
            break
        gz_size += len(chunk)
        gz_h.update(chunk)
        out = d.decompress(chunk)
        img_h.update(out)
        img_size += len(out)
        if len(captured) < CAPTURE:
            captured += out[:CAPTURE - len(captured)]
        lo, hi = max(EXTRA[0], img_size - len(out)), min(EXTRA[1], img_size)
        if lo < hi:
            extra += out[lo - (img_size - len(out)):hi - (img_size - len(out))]
    tail = d.flush()
    img_h.update(tail)
    img_size += len(tail)

report = {"url": URL, "gz_size": gz_size, "gz_sha256": gz_h.hexdigest(),
          "gz_sha256_matches_published": gz_h.hexdigest() == GZ_EXPECT.lower(),
          "img_size": img_size, "img_sha256": img_h.hexdigest(),
          "img_sha256_matches_published": img_h.hexdigest() == IMG_EXPECT.lower(),
          "captured_bytes": len(captured), "extra_window": [EXTRA[0], EXTRA[0] + len(extra)]}
mbr = bytes(captured[:512])
parts = []
for k in range(4):
    e = 446 + 16 * k
    if mbr[e + 4]:
        parts.append({"index": k + 1, "type": f"0x{mbr[e + 4]:02x}", "boot": mbr[e] == 0x80,
                      "start_lba512": struct.unpack_from("<I", mbr, e + 8)[0],
                      "sectors512": struct.unpack_from("<I", mbr, e + 12)[0]})
report["mbr_partitions"] = parts
report["gpt"] = bytes(captured[512:520]) == b"EFI PART"
report["components"] = {}
for p in parts:
    base = p["start_lba512"] * 512

    def read(off, n, base=base):
        lo, hi = base + off, base + off + n
        if hi <= len(captured):
            return bytes(captured[lo:hi])
        if EXTRA[0] <= lo and hi <= EXTRA[0] + len(extra):
            return bytes(extra[lo - EXTRA[0]:hi - EXTRA[0]])
        raise KeyError(f"bytes {lo}-{hi} beyond captured windows")

    try:
        vol = fat.Fat(None, read)
    except (KeyError, struct.error, ZeroDivisionError) as exc:
        p["fat_error"] = repr(exc)
        continue
    p["fat"] = vol.info
    try:
        p["efi_boot_listing"] = vol.listdir("EFI/boot")
        for path in ["EFI/boot/bootx64.efi", "EFI/boot/grubx64.efi"]:
            data = vol.read(path)
            report["components"][f"p{p['index']}:{path}"] = pe_sig.inspect_pe(data) if data else None
        live = vol.listdir("live") or []
        p["live_listing"] = [n for n in live if n.startswith(("vmlinuz", "initrd"))]
        for name in p["live_listing"]:
            if name.startswith("vmlinuz"):
                data = vol.read("live/" + name)
                report["components"][f"p{p['index']}:live/{name}"] = pe_sig.inspect_pe(data)
    except KeyError as exc:
        p["read_error"] = str(exc)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if not k.startswith("_") and k != "layout"}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


with open(OUT, "w", encoding="utf-8") as f:
    json.dump(clean(report), f, indent=2)
print("wrote", OUT, report["gz_sha256_matches_published"], report["img_sha256_matches_published"])
