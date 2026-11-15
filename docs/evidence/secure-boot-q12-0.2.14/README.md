# Secure Boot component receipt for published v0.2.14

Status: the components of the published 0.2.14 bytes have been inspected.
Physical qualification is **NOT TESTED**.

- Inspected 2026-11-15 17:31Z-17:45Z by Claude (Opus 5.5). It ran on a
  Windows development host using Python with `cryptography` 50.0.1. No WSL,
  Linux, QEMU, firmware or device was used, and nothing was written to any
  device.
- The bytes were read straight from the GitHub release assets: ISO byte
  ranges, then one full streamed pass of the ISO, and one streamed pass of
  the USB gzip.
- [Q12](../../secure-boot-acceptance.md#inspected-image-identity--q12) remains
  the 0.2.12 identity until the owner chooses which image physical cases
  use. This receipt is the inspection that the acceptance document requires
  before a newer image can be used.

## Exact identities

| Input | Identity / result |
| --- | --- |
| Release | [v0.2.14](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.14), published 2026-11-12 18:05:27Z by release run 43259400038; tag `v0.2.14` peels to `aecf84569b27591821295c1a4de256544c5bcbe1` |
| ISO | `beamo-wipe-0.2.14-amd64.iso`, 846200832 bytes, SHA-256 `b38514399a410090e1fc4e17a16b82036f690970ec994f6f57a7159af82c2564`. This equals the published `SHA256SUMS`, and every ranged extent equals the streamed bytes |
| Compressed USB | `beamo-wipe-0.2.14-amd64.img.gz`, 956902680 bytes, SHA-256 `5ccad10c2a77a812f16020d6a322197403d40c1fdc4ecc428913373b938c0911`, equal to the published `.sha256` |
| Decompressed USB | 2147483648 bytes, SHA-256 `10ce123e1cf1384c91110c9bf6d46956e3bca3cebd15c227fc03cc200c597d02`, equal to the published `.img.sha256`. MBR; one active FAT32 partition (type 0x0c) at sector 2048 |
| ISO EFI image | El Torito EFI entry and `boot/grub/efi.img`: 5308416 bytes, SHA-256 `0a763df6a9ea85c06ac906d5a53318007f36e20ae470df37f094f611adb6593a`, FAT12. It is also the isohybrid ESP partition (MBR type 0xEF at 512-byte sector 748) |
| UEFI GRUB menu | `boot/grub/grub.cfg` SHA-256 `efb5878b97ff7bf226bb696b2b5b830e944b69cad78e08e6c43bb9790ec1b8c5`. All three entries (guide, speech, troubleshoot) boot `/live/vmlinuz-6.12.115+deb12-amd64` |

Not re-verified here: the publisher Ed25519 signatures on the manifest and the
download inventory (key `93caaf7ca93eff4d`). The checksums above come from
the published release assets.

## The inspected chain

The removable-media x64 files are byte-identical in three places: the ISO's
`EFI/boot`, the El Torito EFI filesystem and the USB's FAT32 `EFI/boot`.

| Component | SHA-256 | Authenticode SHA-256 | Signatures (all verified) |
| --- | --- | --- | --- |
| `EFI/boot/bootx64.efi` (Debian shim 16.1) | `0fc347af103ec1dfac6e3f184c0a5241a2ce756a0932b359c404d39c45423806` | `80a66d53a945d2286fcadd780fae1c225aa732079cd67b5225dc78aaab4e2ff8` | 1. **Microsoft Windows UEFI Driver Publisher**, issued by **Microsoft Corporation UEFI CA 2011**. 2. **Microsoft UEFI CA 2023 signer**, issued by **Microsoft UEFI CA 2023** |
| `EFI/boot/grubx64.efi` (GRUB 2.06-13+deb12u2) | `f0cf6c345219815d6cd51e42736074e0fe466dfe57b86d6469afeddb16fec1eb` | `dca841985136f0533ecd18b589ddf75503660b499c2dcd77b7c7efa7bc5d6a02` | **Debian Secure Boot Signer 2022 - grub2**, issued by **Debian Secure Boot CA** |
| `live/vmlinuz-6.12.115+deb12-amd64` | `02f73dc8e02097bc04daa86a651141f6e0fc75c5504af17854c7637944b2be12` | `419aa641b541a3cdf4eed3514dbdc087e8aca32f4b7506bcb6d942c21ea0f773` | **Debian Secure Boot Signer 2022 - linux**, issued by **Debian Secure Boot CA** |

For each of the four signatures, all three of these checks passed:

- **Image digest:** the Authenticode digest recomputed from the PE equals the
  signed digest.
- **Message digest:** the signed `messageDigest` attribute equals the digest
  of the `SpcIndirectDataContent`.
- **Signature:** the RSA signature over the signed attributes verifies with
  the embedded signer certificate.

Each signer certificate was also verified as directly issued by its anchor:

- **Microsoft:** the Microsoft Corporation UEFI CA 2011 and Microsoft UEFI CA
  2023 certificates, fetched from Microsoft PKI on 2026-11-15:
  - 2011: SHA-256 `48e99b991f57fc52f76149599bff0a58c47154229b9f8d603ac40d3500248507`,
    the same value as the 0.2.12 receipt;
  - 2023: SHA-256 `f6124e34125bee3fe6d79a574eaa7b91c0e7bd9d929c1a321178efd611dad901`.
- **Debian:** the Debian Secure Boot CA embedded in this shim's
  `.vendor_cert` (DER SHA-256
  `079646974bce09b1f04da67bd722d1fb0947ae4c4010bccdbba52d5b23cbf1a2`, valid
  2016-08-16 to 2046-08-09).

The shim's vendor denylist is 8664 bytes, SHA-256
`45e89b4a5f8283cd8ae7c66bda8346697120c84880537aadb49a665c7d7eec0f`. The
Debian CA and this denylist are the same as in 0.2.12.

SBAT, as read from the PE sections:

- **Shim:** `shim,4`, `shim.debian,1`.
- **Shim's embedded policies (`.sbatlevel`):**
  - automatic `sbat,1,2025021800` with `shim,4` and `grub,5`;
  - latest `sbat,1,2025051000` with `shim,4`, `grub,5` and `grub.proxmox,2`.
- **GRUB:** `grub,5`, `grub.debian,5`, `grub.debian12,1`.
- **Kernel:** it has no `.sbat` section, which is normal for a Debian kernel;
  shim checks the kernel through GRUB's Debian signature.

## What changed from 0.2.12, and a correction

- **Kernel:** Linux `6.12.115+deb12-amd64` replaces `6.1.0-53-amd64`. It has
  the same Debian signer.
- **Unchanged:** shim, GRUB, the SBAT entries and the embedded Debian CA are
  byte-identical to the 0.2.12 receipt (same SHA-256 and Authenticode digests).
- **Correction to the 0.2.12 receipt.** These same shim bytes carry **two**
  `WIN_CERTIFICATE` entries:
  - 9792 bytes, signed under UEFI CA 2011;
  - 9576 bytes, signed under UEFI CA 2023.

  The 0.2.12 inspection listed only "Signature Index: 0". So its statement
  "this shim is not signed by the Microsoft UEFI CA 2023" is wrong for these
  bytes; a firmware that trusts only the 2023 CA can authorize this shim.
  This is an inference from the signatures; it was not observed on firmware.
  The 0.2.12 evidence files are left unchanged as historical records.
- **Certificate dates.** The 2011-chain signer certificate's validity
  (2026-03-12 to 2026-06-26) and the Microsoft Corporation UEFI CA 2011's
  validity (to 2026-06-27) have both passed. The 2023 signer is valid to
  2026-07-23. UEFI image verification normally does not enforce certificate
  expiry, but this receipt does not establish any particular firmware's
  behaviour.

## Scope and what stays unknown

- No firmware `db`, `dbx`, MOK list, `SbatLevel`/`SbatLevelRT` or shim
  runtime policy was inspected. Whether a given PC accepts this chain is still
  decided by the cases in
  [secure-boot-acceptance.md](../../secure-boot-acceptance.md). Unknown is
  never Pass.
- No timestamp or CRL checks were done. No firmware state was changed.
- These are outside the PE signature chain and were only listed, not
  authenticated by Secure Boot:
  - the initrd and `grub.cfg`;
  - the squashfs;
  - the unsigned `bootia32.efi`.

  Installed helper copies under `/usr/lib` (inside the squashfs) were not
  inventoried this time.
- Physical qualification for SB-ACCEPT, SB-NO-ANCHOR, SB-DBX, SB-SHIM and the
  other cases is **NOT TESTED**.

## Files

- [components.json](components.json): machine-readable receipt.
- `raw/`: the full inspector outputs and the UEFI `grub.cfg`:
  - `q12-iso-0.2.14.json`;
  - `q12-usb-0.2.14.json`;
  - `q12-chain-0.2.14.json`.
- `tools/`: the exact inspector code. `pe_sig.py` covers PE, Authenticode and
  SBAT, `fat.py` reads FAT12/16/32, and the remaining scripts are drivers.

  To reproduce:
  1. `python -I tools/iso_q12.py <iso-url> <sha256> out.json`.
  2. `EXTRA_WINDOW_MB=900:1100 python -I tools/usb_q12.py <img.gz-url> <gz-sha256> <img-sha256> out.json`.
  3. With the Microsoft CA certificates beside the extracted files,
     `python -I tools/chain_check.py` and `tools/make_components.py`.

  The committed `chain_check.py` has two cosmetic lint fixes and was
  re-run; it reproduces `raw/q12-chain-0.2.14.json` byte-for-byte.
