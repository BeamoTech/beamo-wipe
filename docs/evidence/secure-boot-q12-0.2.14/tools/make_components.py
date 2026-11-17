"""Build components.json for the 0.2.14 Q12 receipt from the raw inspections."""
import json
import sys

iso = json.load(open("q12-iso-0.2.14.json"))
usb = json.load(open("q12-usb-0.2.14.json"))
chain = json.load(open("q12-chain-0.2.14.json"))

ROLES = {
    "EFI/boot/bootx64.efi": "removable-media entry (shim)",
    "EFI/boot/grubx64.efi": "second stage (GRUB, loaded by shim)",
    "live/vmlinuz-6.12.115+deb12-amd64": "kernel selected by all three UEFI GRUB entries",
}


def sigs(c):
    out = []
    for s in c["signatures"]:
        leaf = s["chain"][0]
        out.append({
            "signer": leaf["subject"],
            "issuer": leaf["issuer"],
            "signer_validity": [leaf["not_before"], leaf["not_after"]],
            "signer_der_sha256": leaf["der_sha256"],
            "embedded_chain": [link["subject"] for link in s["chain"]],
            "pe_digest_matches_signed_digest": s["pe_digest_match"] != "NO",
            "message_digest_matches": s["message_digest_ok"],
            "signature_verifies_with_signer_key": s["signature_ok"],
        })
    return out


usb_part = next(p for p in usb["mbr_partitions"] if p.get("fat"))
components = []
for path, role in ROLES.items():
    c = iso["components"]["iso:" + path]
    el = iso["components"].get("eltorito:" + path)
    u = usb["components"].get(f"p{usb_part['index']}:" + path)
    components.append({
        "path": path, "role": role, "size": c["size"], "sha256": c["sha256"],
        "machine": c["machine"], "authenticode_sha256": c["authenticode_sha256"]["flat"],
        "signatures": sigs(c),
        "leaf_directly_issued_by": [r["leaf_directly_issued_by"] for r in
                                    chain["leaf_issuance"][path.replace("/", "_").replace(
                                        "EFI_boot_", "EFI_boot_")]] if path.replace("/", "_") in chain["leaf_issuance"] else None,
        "sbat": c["sbat"],
        "eltorito_identical": (el or {}).get("sha256") == c["sha256"] if path.startswith("EFI/") else None,
        "usb_identical": (u or {}).get("sha256") == c["sha256"],
    })
receipt = {
    "schema": "beamo-wipe-secure-boot-inspection/2",
    "inspection_date_utc": "2026-11-15",
    "tag": "v0.2.14",
    "tag_commit": "aecf84569b27591821295c1a4de256544c5bcbe1",
    "release_run": 43259400038,
    "iso": {"size": iso["iso_size"], "sha256": iso["iso_sha256"],
            "matches_published_SHA256SUMS": iso["iso_sha256_matches_published"],
            "volume_id": iso["volume_id"]},
    "usb_gzip": {"size": usb["gz_size"], "sha256": usb["gz_sha256"],
                 "matches_published": usb["gz_sha256_matches_published"]},
    "usb": {"size": usb["img_size"], "sha256": usb["img_sha256"],
            "matches_published": usb["img_sha256_matches_published"],
            "partition": {k: usb_part[k] for k in ("index", "type", "boot", "start_lba512", "sectors512")},
            "fat": usb_part["fat"]["fat"]},
    "eltorito_efi_image": {"bytes": iso["eltorito_efi_bytes"], "sha256": iso["eltorito_efi_sha256"],
                           "fat": iso["eltorito_fat"]["fat"],
                           "is_isohybrid_esp_partition": iso["esp_is_eltorito_image"]},
    "ranged_extents_match_streamed_iso": iso["ranged_extents_match_stream"],
    "shim_sbat": [line.split(",")[0] + "," + line.split(",")[1] for line in chain["shim_sbat"][1:]],
    "shim_sbatlevel_automatic": chain["shim_sbatlevel"][0],
    "shim_sbatlevel_latest": chain["shim_sbatlevel"][1],
    "grub_sbat": [line.split(",")[0] + "," + line.split(",")[1]
                  for line in iso["components"]["iso:EFI/boot/grubx64.efi"]["sbat"][1:]],
    "debian_ca_der_sha256": chain["shim_vendor_cert"]["authorized_der_sha256"],
    "vendor_dbx_sha256": chain["shim_vendor_cert"]["vendor_dbx_sha256"],
    "microsoft_uefi_ca_der_sha256": chain["anchor_der_sha256"],
    "components": components,
    "iso_efi_boot_listing": iso["iso_efi_boot_listing"],
    "iso_live_kernels": iso["iso_live_kernels"],
    "grub_cfg_sha256": sys.argv[1],
    "physical_status": "NOT TESTED",
    "signature_scope": ("Authenticode PE digests, signed-attribute message digests and RSA "
                        "signatures verified with each embedded signer key; each signer "
                        "certificate verified as directly issued by the Microsoft UEFI CA "
                        "2011/2023 certificates fetched from Microsoft PKI or by the Debian "
                        "Secure Boot CA embedded in this shim. No firmware db/dbx, MOK or "
                        "active SBAT policy was inspected; no timestamp/CRL checks; no "
                        "firmware state changed."),
}
json.dump(receipt, open("components.json", "w"), indent=2)
print("ok", len(components))
