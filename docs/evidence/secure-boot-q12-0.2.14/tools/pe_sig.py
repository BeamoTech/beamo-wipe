"""Read-only PE / Authenticode / SBAT inspection with only `cryptography`.

Functions take bytes and return plain dicts; nothing touches firmware, disks
or the network.
"""
import hashlib
import struct

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

OIDS = {
    "2.16.840.1.101.3.4.2.1": "sha256",
    "2.16.840.1.101.3.4.2.2": "sha384",
    "2.16.840.1.101.3.4.2.3": "sha512",
    "1.3.14.3.2.26": "sha1",
}
OID_MESSAGE_DIGEST = "1.2.840.113549.1.9.4"
OID_NESTED_SIGNATURE = "1.3.6.1.4.1.311.2.4.1"
OID_SPC_INDIRECT = "1.3.6.1.4.1.311.2.1.4"
HASHES = {"sha256": hashes.SHA256, "sha384": hashes.SHA384,
          "sha512": hashes.SHA512, "sha1": hashes.SHA1}


# ---------------------------------------------------------------- DER walk
def tlv(b, i):
    """Return (tag, header_start, value_start, value_end) at offset i."""
    start = i
    tag = b[i]
    i += 1
    length = b[i]
    i += 1
    if length & 0x80:
        n = length & 0x7F
        length = int.from_bytes(b[i:i + n], "big")
        i += n
    return tag, start, i, i + length


def children(b, value_start, value_end):
    out = []
    i = value_start
    while i < value_end:
        t = tlv(b, i)
        out.append(t)
        i = t[3]
    return out


def oid_text(b, vs, ve):
    raw = b[vs:ve]
    first = raw[0]
    parts = [first // 40, first % 40]
    value = 0
    for byte in raw[1:]:
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(value)
            value = 0
    return ".".join(map(str, parts))


# ------------------------------------------------------------------ PE
def pe_layout(data):
    off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[off:off + 4] != b"PE\0\0":
        raise ValueError("not a PE image")
    machine, nsec = struct.unpack_from("<HH", data, off + 4)
    opt_size = struct.unpack_from("<H", data, off + 20)[0]
    opt = off + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (96 if magic == 0x10B else 112)
    size_of_headers = struct.unpack_from("<I", data, opt + 60)[0]
    cert_dir = dd + 4 * 8
    cert_off, cert_size = struct.unpack_from("<II", data, cert_dir)
    sym_ptr, nsyms = struct.unpack_from("<II", data, off + 12)
    strtab = sym_ptr + 18 * nsyms if sym_ptr else None
    sections = []
    table = opt + opt_size
    for k in range(nsec):
        e = table + 40 * k
        name = data[e:e + 8].rstrip(b"\0").decode("ascii", "replace")
        if name.startswith("/") and name[1:].isdigit() and strtab:
            # Long section names live in the COFF string table ("/4" etc.).
            at = strtab + int(name[1:])
            name = data[at:data.index(b"\0", at)].decode("ascii", "replace")
        vsize, vaddr, raw_size, raw_off = struct.unpack_from("<IIII", data, e + 8)
        sections.append({"name": name, "vsize": vsize, "raw_size": raw_size, "raw_off": raw_off})
    return {"machine": f"0x{machine:04x}", "checksum_off": opt + 64, "cert_dir": cert_dir,
            "cert_off": cert_off, "cert_size": cert_size, "headers": size_of_headers,
            "sections": sections}


def authenticode_digests(data, layout, alg):
    """Two common Authenticode digest constructions; one must match."""
    co, cd, ct, cs = layout["checksum_off"], layout["cert_dir"], layout["cert_off"], layout["cert_size"]
    end = ct if ct else len(data)
    flat = hashlib.new(alg)
    flat.update(data[:co])
    flat.update(data[co + 4:cd])
    flat.update(data[cd + 8:end])
    if ct and ct + cs < len(data):
        flat.update(data[ct + cs:])
    spec = hashlib.new(alg)
    h = layout["headers"]
    spec.update(data[:co])
    spec.update(data[co + 4:cd])
    spec.update(data[cd + 8:h])
    done = h
    for s in sorted((s for s in layout["sections"] if s["raw_size"]), key=lambda s: s["raw_off"]):
        spec.update(data[s["raw_off"]:s["raw_off"] + s["raw_size"]])
        done = max(done, s["raw_off"] + s["raw_size"])
    if end > done:
        spec.update(data[done:end])
    return {"flat": flat.hexdigest(), "spec": spec.hexdigest()}


def section(data, layout, name):
    for s in layout["sections"]:
        if s["name"] == name:
            return data[s["raw_off"]:s["raw_off"] + min(s["vsize"] or s["raw_size"], s["raw_size"])]
    return None


def sbat_lines(raw):
    if raw is None:
        return None
    text = raw.rstrip(b"\0").decode("ascii", "replace")
    return [line for line in text.splitlines() if line.strip()]


def sbatlevel(raw):
    """shim's .sbatlevel: NUL-terminated policy strings (automatic, latest)."""
    if raw is None:
        return None
    out = []
    for chunk in raw.split(b"\0"):
        text = chunk.decode("ascii", "replace")
        start = text.find("sbat,1,")
        if start >= 0:
            out.append([line for line in text[start:].splitlines() if line.strip()])
    return out


def vendor_cert(raw):
    """shim's .vendor_cert: authorized DER cert and vendor denylist bytes."""
    if raw is None:
        return None
    a_size, d_size, a_off, d_off = struct.unpack_from("<IIII", raw, 0)
    der = raw[a_off:a_off + a_size]
    dbx = raw[d_off:d_off + d_size]
    info = {"authorized_der_sha256": hashlib.sha256(der).hexdigest(),
            "vendor_dbx_sha256": hashlib.sha256(dbx).hexdigest(),
            "vendor_dbx_size": d_size}
    try:
        cert = x509.load_der_x509_certificate(der)
        info["authorized_subject"] = cert.subject.rfc4514_string()
        info["authorized_issuer"] = cert.issuer.rfc4514_string()
        info["_cert"] = cert
    except ValueError as exc:
        info["authorized_parse_error"] = str(exc)
    return info


# ------------------------------------------------------- Authenticode PKCS7
def _name_serial(b, sid):
    parts = children(b, sid[2], sid[3])
    return b[parts[0][1]:parts[0][3]], int.from_bytes(b[parts[1][2]:parts[1][3]], "big", signed=True)


def parse_signed_data(b, ci_start=0):
    """Parse one Authenticode ContentInfo; return signature dicts (incl. nested)."""
    ci = tlv(b, ci_start)
    ci_parts = children(b, ci[2], ci[3])
    sd_wrap = ci_parts[1]
    sd = tlv(b, sd_wrap[2])
    parts = children(b, sd[2], sd[3])
    content_info = parts[2]
    cparts = children(b, content_info[2], content_info[3])
    if oid_text(b, cparts[0][2], cparts[0][3]) != OID_SPC_INDIRECT:
        raise ValueError("content is not SpcIndirectDataContent")
    spc = tlv(b, cparts[1][2])
    spc_value = b[spc[2]:spc[3]]
    spc_parts = children(b, spc[2], spc[3])
    digest_info = children(b, spc_parts[1][2], spc_parts[1][3])
    alg_seq = children(b, digest_info[0][2], digest_info[0][3])
    signed_alg = OIDS.get(oid_text(b, alg_seq[0][2], alg_seq[0][3]), "unknown")
    signed_digest = b[digest_info[1][2]:digest_info[1][3]].hex()
    certs = []
    signer_infos = None
    for p in parts[3:]:
        if p[0] == 0xA0:
            for c in children(b, p[2], p[3]):
                certs.append(x509.load_der_x509_certificate(b[c[1]:c[3]]))
        elif p[0] == 0x31:
            signer_infos = p
    results = []
    for si in children(b, signer_infos[2], signer_infos[3]):
        sparts = children(b, si[2], si[3])
        issuer_der, serial = _name_serial(b, sparts[1])
        dalg = children(b, sparts[2][2], sparts[2][3])
        digest_alg = OIDS.get(oid_text(b, dalg[0][2], dalg[0][3]), "unknown")
        idx = 3
        auth = None
        if sparts[idx][0] == 0xA0:
            auth = sparts[idx]
            idx += 1
        idx += 1  # digestEncryptionAlgorithm
        enc = b[sparts[idx][2]:sparts[idx][3]]
        unauth = sparts[idx + 1] if len(sparts) > idx + 1 and sparts[idx + 1][0] == 0xA1 else None
        signer = next((c for c in certs if c.serial_number == serial
                       and c.issuer.public_bytes() == issuer_der), None)
        message_digest_ok = None
        signature_ok = None
        if auth is not None:
            for attr in children(b, auth[2], auth[3]):
                ap = children(b, attr[2], attr[3])
                if oid_text(b, ap[0][2], ap[0][3]) == OID_MESSAGE_DIGEST:
                    val = children(b, ap[1][2], ap[1][3])[0]
                    md = b[val[2]:val[3]]
                    message_digest_ok = md == hashlib.new(digest_alg, spc_value).digest()
            if signer is not None and isinstance(signer.public_key(), rsa.RSAPublicKey):
                signed_attrs = b"\x31" + b[auth[1] + 1:auth[3]]
                try:
                    signer.public_key().verify(enc, signed_attrs, padding.PKCS1v15(),
                                               HASHES[digest_alg]())
                    signature_ok = True
                except Exception:  # noqa: BLE001 - recorded as a failed verification
                    signature_ok = False
        chain = []
        current = signer
        seen = set()
        while current is not None and current.fingerprint(hashes.SHA256()) not in seen:
            seen.add(current.fingerprint(hashes.SHA256()))
            parent = next((c for c in certs if c.subject == current.issuer and c is not current), None)
            link = {"subject": current.subject.rfc4514_string(),
                    "issuer": current.issuer.rfc4514_string(),
                    "serial": hex(current.serial_number),
                    "not_before": current.not_valid_before_utc.isoformat(),
                    "not_after": current.not_valid_after_utc.isoformat(),
                    "der_sha256": current.fingerprint(hashes.SHA256()).hex()}
            if parent is not None:
                try:
                    current.verify_directly_issued_by(parent)
                    link["issued_by_next_verified"] = True
                except Exception:  # noqa: BLE001
                    link["issued_by_next_verified"] = False
            chain.append(link)
            current = parent
        results.append({"signed_digest_alg": signed_alg, "signed_digest": signed_digest,
                        "message_digest_ok": message_digest_ok, "signature_ok": signature_ok,
                        "signer_found": signer is not None, "chain": chain,
                        "_top": chain[-1]["issuer"] if chain else None,
                        "_signer_cert": signer, "_certs": certs})
        if unauth is not None:
            for attr in children(b, unauth[2], unauth[3]):
                ap = children(b, attr[2], attr[3])
                if oid_text(b, ap[0][2], ap[0][3]) == OID_NESTED_SIGNATURE:
                    for nested in children(b, ap[1][2], ap[1][3]):
                        for r in parse_signed_data(b, nested[1]):
                            r["nested"] = True
                            results.append(r)
    return results


def inspect_pe(data):
    layout = pe_layout(data)
    sigs = []
    off, end = layout["cert_off"], layout["cert_off"] + layout["cert_size"]
    while off and off + 8 <= end:
        length, revision, ctype = struct.unpack_from("<IHH", data, off)
        if length < 8:
            break
        blob = data[off + 8:off + length]
        if ctype == 0x0002:
            sigs.extend(parse_signed_data(blob))
        off += (length + 7) & ~7
    digests = {}
    for s in sigs:
        alg = s["signed_digest_alg"]
        if alg not in digests:
            digests[alg] = authenticode_digests(data, layout, alg)
        d = digests[alg]
        s["pe_digest_match"] = ("flat" if s["signed_digest"] == d["flat"] else
                                "spec" if s["signed_digest"] == d["spec"] else "NO")
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "machine": layout["machine"], "layout": layout, "signatures": sigs,
            "authenticode_sha256": digests.get("sha256", authenticode_digests(data, layout, "sha256")),
            "sbat": sbat_lines(section(data, layout, ".sbat")),
            "sbatlevel": sbatlevel(section(data, layout, ".sbatlevel")),
            "vendor_cert": vendor_cert(section(data, layout, ".vendor_cert"))}
