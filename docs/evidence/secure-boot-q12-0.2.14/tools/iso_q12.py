"""Q12 inspection of a published ISO, read over HTTP range requests.

Usage: py -3 -I iso_q12.py <iso-url> <expected-sha256> <out.json>

Reads the ISO9660 tree (Rock Ridge names), the El Torito EFI image and the
isohybrid partition table; extracts shim, GRUB and every live/vmlinuz-*;
then streams the whole ISO once through SHA-256 and checks that every ranged
extent equals the streamed bytes. Writes nothing but <out.json>.
"""
import hashlib
import json
import struct
import sys
import urllib.request

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import fat  # noqa: E402
import pe_sig  # noqa: E402

URL, EXPECT, OUT = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
UA = {"User-Agent": "q12-inspector/1.0"}
EXTENTS = {}


def get(start, length, label=None):
    req = urllib.request.Request(URL, headers={**UA, "Range": f"bytes={start}-{start + length - 1}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.status != 206:
            raise SystemExit(f"server did not honour Range (status {r.status})")
        data = r.read()
    if len(data) != length:
        raise SystemExit(f"short range read {len(data)} != {length}")
    if label:
        EXTENTS[label] = (start, data)
    return data


def rr_name(rec, nl):
    su = rec[33 + nl + ((nl + 1) % 2):]
    i = 0
    while i + 4 <= len(su):
        sig, ln = su[i:i + 2], su[i + 2]
        if ln < 4:
            break
        if sig == b"NM":
            return su[i + 5:i + ln].decode("utf-8", "replace")
        i += ln
    return None


pvd = get(16 * 2048, 2048)
assert pvd[0] == 1 and pvd[1:6] == b"CD001", "no primary volume descriptor"
BLOCK = struct.unpack_from("<H", pvd, 128)[0]
volume_id = pvd[40:72].decode().strip()


def listdir(lba, length):
    d = get(lba * BLOCK, length)
    out = {}
    off = 0
    while off < len(d):
        ln = d[off]
        if ln == 0:
            off = (off // BLOCK + 1) * BLOCK
            continue
        rec = d[off:off + ln]
        nl = rec[32]
        raw = rec[33:33 + nl]
        if raw not in (b"\x00", b"\x01"):
            name = rr_name(rec, nl) or raw.decode("latin-1").split(";")[0]
            out[name] = {"lba": struct.unpack_from("<I", rec, 2)[0],
                         "size": struct.unpack_from("<I", rec, 10)[0],
                         "dir": bool(rec[25] & 2)}
        off += ln
    return out


root_rec = pvd[156:190]
root = listdir(struct.unpack_from("<I", root_rec, 2)[0], struct.unpack_from("<I", root_rec, 10)[0])


def lookup(path):
    entries, node = root, None
    for part in path.split("/"):
        match = next((k for k in entries if k.lower() == part.lower()), None)
        if match is None:
            return None, None
        node = entries[match]
        if node["dir"]:
            entries = listdir(node["lba"], node["size"])
    return node, entries


def read_file(path):
    node, _ = lookup(path)
    if node is None:
        return None
    return get(node["lba"] * BLOCK, node["size"], label="iso:" + path)


report = {"url": URL, "volume_id": volume_id, "block": BLOCK, "components": {}}
# ISO9660 tree
efi_boot_node, efi_boot_entries = lookup("EFI/boot")
report["iso_efi_boot_listing"] = sorted(efi_boot_entries) if efi_boot_entries else None
live_node, live_entries = lookup("live")
kernels = sorted(k for k in (live_entries or {}) if k.startswith("vmlinuz"))
report["iso_live_kernels"] = kernels
iso_files = {}
for path in ["EFI/boot/bootx64.efi", "EFI/boot/grubx64.efi"] + [f"live/{k}" for k in kernels]:
    data = read_file(path)
    iso_files[path] = data
    if data:
        import os
        dump = os.path.join(os.path.dirname(OUT), "extracted", path.replace("/", "_"))
        os.makedirs(os.path.dirname(dump), exist_ok=True)
        with open(dump, "wb") as f:
            f.write(data)
    report["components"]["iso:" + path] = pe_sig.inspect_pe(data) if data else None
for extra in ["boot/grub/grub.cfg", "boot/grub/efi.img"]:
    node, _ = lookup(extra)
    report.setdefault("iso_other", {})[extra] = node

# El Torito
eltorito = None
sector = 17
while True:
    vd = get(sector * 2048, 2048)
    if vd[0] == 255:
        break
    if vd[0] == 0 and vd[7:30].rstrip(b"\0") == b"EL TORITO SPECIFICATION":
        cat_lba = struct.unpack_from("<I", vd, 71)[0]
        cat = get(cat_lba * 2048, 2048)
        entries = []
        i = 32
        platform = cat[1]
        entries.append({"kind": "initial", "platform": platform,
                        "sectors": struct.unpack_from("<H", cat, 32 + 6)[0],
                        "rba": struct.unpack_from("<I", cat, 32 + 8)[0]})
        i = 64
        while i + 32 <= len(cat) and cat[i] in (0x90, 0x91):
            platform, count = cat[i + 1], struct.unpack_from("<H", cat, i + 2)[0]
            for k in range(count):
                e = i + 32 * (k + 1)
                entries.append({"kind": "section", "platform": platform,
                                "sectors": struct.unpack_from("<H", cat, e + 6)[0],
                                "rba": struct.unpack_from("<I", cat, e + 8)[0]})
            last = cat[i] == 0x91
            i += 32 * (count + 1)
            if last:
                break
        eltorito = {"catalog_lba": cat_lba, "entries": entries}
        break
    sector += 1
report["eltorito"] = eltorito

# isohybrid partition table (MBR, GPT)
mbr = get(0, 512 * 34)
parts = []
for k in range(4):
    e = 446 + 16 * k
    ptype = mbr[e + 4]
    if ptype:
        parts.append({"scheme": "mbr", "index": k + 1, "type": f"0x{ptype:02x}",
                      "start_lba512": struct.unpack_from("<I", mbr, e + 8)[0],
                      "sectors512": struct.unpack_from("<I", mbr, e + 12)[0]})
if mbr[512:520] == b"EFI PART":
    ents_lba, n_ents, ent_size = struct.unpack_from("<QII", mbr, 512 + 72)
    for k in range(n_ents):
        e = ents_lba * 512 + k * ent_size
        if e + ent_size > len(mbr):
            break
        tguid = mbr[e:e + 16]
        if tguid == b"\0" * 16:
            continue
        first, last = struct.unpack_from("<QQ", mbr, e + 32)
        parts.append({"scheme": "gpt", "index": k + 1, "type_guid": tguid.hex(),
                      "start_lba512": first, "sectors512": last - first + 1})
report["partitions"] = parts

# EFI FAT image: El Torito EFI section, else the ESP partition
efi_img = None
efi_entry = next((e for e in (eltorito or {}).get("entries", []) if e["platform"] == 0xEF), None)
if efi_entry:
    img_node, _ = lookup("boot/grub/efi.img")
    size = efi_entry["sectors"] * 512
    if img_node and img_node["lba"] == efi_entry["rba"]:
        size = img_node["size"]
    efi_img = get(efi_entry["rba"] * 2048, size, label="eltorito-efi")
    report["eltorito_efi_bytes"] = len(efi_img)
    report["eltorito_efi_sha256"] = hashlib.sha256(efi_img).hexdigest()
    esp = next((p for p in parts if p.get("type") == "0xef" or p.get("type_guid") ==
                "28732ac11ff8d211ba4b00a0c93ec93b"), None)
    report["esp_is_eltorito_image"] = bool(esp and esp["start_lba512"] * 512 == efi_entry["rba"] * 2048)
if efi_img:
    vol = fat.Fat(efi_img)
    report["eltorito_fat"] = vol.info
    report["eltorito_efi_boot_listing"] = vol.listdir("EFI/boot")
    for path in ["EFI/boot/bootx64.efi", "EFI/boot/grubx64.efi"]:
        data = vol.read(path)
        report["components"]["eltorito:" + path] = pe_sig.inspect_pe(data) if data else None
        report.setdefault("eltorito_matches_iso_tree", {})[path] = (
            data is not None and data == iso_files.get(path))

# Bind every ranged extent to the published bytes.
h, pos = hashlib.sha256(), 0
checks = {label: bytearray() for label in EXTENTS}
req = urllib.request.Request(URL, headers=UA)
with urllib.request.urlopen(req, timeout=300) as r:
    while True:
        chunk = r.read(8 * 1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        for label, (start, data) in EXTENTS.items():
            lo, hi = max(start, pos), min(start + len(data), pos + len(chunk))
            if lo < hi:
                checks[label] += chunk[lo - pos:hi - pos]
        pos += len(chunk)
report["iso_size"] = pos
report["iso_sha256"] = h.hexdigest()
report["iso_sha256_matches_published"] = h.hexdigest() == EXPECT
report["ranged_extents_match_stream"] = {label: bytes(checks[label]) == EXTENTS[label][1]
                                         for label in EXTENTS}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if not k.startswith("_") and k != "layout"}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


with open(OUT, "w", encoding="utf-8") as f:
    json.dump(clean(report), f, indent=2)
print("wrote", OUT, "iso_sha256_matches_published", report["iso_sha256_matches_published"])
