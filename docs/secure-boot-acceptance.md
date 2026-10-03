# Physical Secure Boot acceptance

This is the current operator procedure. [Claims](claims.md) still limit the
product to x64 PCs that start from this USB. A Debian-signed boot path is not
a promise of acceptance by every firmware. Beamo's Ed25519 release key
authenticates downloads; it is not an EFI signing key and needs no firmware
enrollment. No physical configuration has been accepted by this task.

## Inspected image identity — Q12

Every case below names **Q12**, the published, qualified 0.2.12 bytes inspected
in [the component receipt](evidence/secure-boot-119/README.md). Record the actual
flashed image in [BUILD-IDENTITY](evidence/physical-acceptance-111/BUILD-IDENTITY.md)
before a case. A different image requires its own signature inspection and
receipt; neither a version string nor a source-only build transfers this one.
Q12 identifies test inputs, not authorization to overwrite a USB or disk.
Before a physical boot, complete the [post-flash readback](evidence/physical-acceptance-111/README.md#post-flash-readback)
and record its receipt. A source-file hash or successful write alone does not
bind the stick to Q12; a mismatch or unavailable readback is SB-INSPECTION.

| Input | Identity |
| --- | --- |
| Source | `e986419379f512f8088f5982ee02a51dc91a9dae`, tag `v0.2.12`, clean |
| Build | `625971a4-afef-5398-9bec-d96455192ab3`, Blacksmith |
| ISO | `beamo-wipe-0.2.12-amd64.iso`, 564133888 bytes, SHA-256 `73554d35aecafac7fc6dffe41d1f1efdb658b43c39da85a2f0bebfe8f1beb598` |
| Compressed USB download | `beamo-wipe-0.2.12-amd64.img.gz`, 601441384 bytes, SHA-256 `a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972` |
| Decompressed USB | `beamo-wipe-0.2.12-amd64.img`, 2147483648 bytes, SHA-256 `1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b` |
| Signed manifest | SHA-256 `0bb56538500330086f507538e94ec68846ff5ab39ddf491dbeaf467a50cfd5b8`, publisher key `93caaf7ca93eff4d` |

## What the bytes establish

The ISO's removable-media EFI directory, its El Torito EFI filesystem, and
the USB's FAT32 EFI files are byte-identical. Their x64 path is:

1. Firmware loads `EFI/boot/bootx64.efi`: Debian shim 16.1, signed by
   **Microsoft Windows UEFI Driver Publisher**, issued by **Microsoft
   Corporation UEFI CA 2011**. There is one inspected signature; this shim
   is not signed by the Microsoft UEFI CA 2023.
2. Shim's embedded **Debian Secure Boot CA** verifies `grubx64.efi`, the
   signed Debian CD/removable-media GRUB (`gcdx64.efi.signed`), signed by
   **Debian Secure Boot Signer 2022 - grub2**. Shim's vendor denylist, firmware
   `dbx`, MOK denylist, and active SBAT policy can still reject a component.
3. GRUB's ordinary, speech, and troubleshooting entries all select
   `/live/vmlinuz-6.1.0-53-amd64`, signed by **Debian Secure Boot Signer
   2022 - linux**, also issued by the Debian CA.

Firmware `db` authorization must cover the actual shim signature or an
accepted image hash; an entry in PK or KEK alone is not image authorization.
Microsoft's Windows signing CAs are distinct from the third-party UEFI CA.
A 2023-only trust store does not authenticate this 2011-only shim unless it
has another applicable authorization. This is an inference from the inspected
signatures, consistent with [Microsoft's Linux transition guidance](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/linux-distribution-guidance-handling-2023keys).

Shim has `shim,4` / `shim.debian,1` SBAT entries. GRUB has `grub,5`,
`grub.debian,5`, and `grub.debian12,1`. Evaluate every matching entry against
the active policy, including retained firmware variables; these numbers are
not a universal non-revocation guarantee. See [shim's SBAT specification](https://github.com/rhboot/shim/blob/main/SBAT.md).

Shim can persist its built-in SBAT policy during an ordinary boot
([shim 16.1 implementation](https://github.com/rhboot/shim/blob/16.1/sbat.c)).
Capture read-only policy evidence **before and after** each attempt; a later
attempt may have a different state. Do not reset or roll back that policy to
repeat a case. Q12 embeds automatic `2025021800` and latest `2025051000`
payloads with `shim,4` / `grub,5`; latest also names `grub.proxmox,2`.
The active policy must still be inspected, including any higher retained floor.

The separate initrd, GRUB configuration, and squashfs are **outside the PE
signature chain**. The signed release manifest authenticates the downloaded
image's bytes, but Secure Boot does not thereby authenticate every live file
or prove erasure. Unsigned `bootia32.efi` also ships; its presence does not
establish IA32 Secure Boot support. BIOS/CSM paths do not exercise UEFI Secure
Boot. Installed signed and unsigned helper/GRUB copies that are not selected
by this path are inventoried in the receipt, not treated as booted components.

## Read-only prerequisites and evidence

Use a dedicated spare x64 PC and authorized spare USB, with valuable disks
disconnected. Boot testing stops at the guide; it does not need an erase.
Follow [the physical safety procedure](evidence/physical-acceptance-111/README.md).
Use an already configured machine for each trust state. **Do not enroll or
remove keys, change revocations or SBAT policy, disable validation or Secure
Boot, or alter a firmware clock to obtain a result.** This procedure authorizes
none of those changes. If a state is unavailable, leave its row NOT TESTED.

For every case capture:

- Tester, UTC date, PC model, CPU **and firmware** architecture, firmware version,
  port, USB identity, image hashes, source/build identity, and component receipt.
- Read-only firmware evidence for `SecureBoot=1` and `SetupMode=0` in enforcing
  cases; record AuditMode/DeployedMode if exposed and any OEM policy restriction.
  A setup-screen toggle alone is not proof of enforcement.
- Actual `db / dbx` contents or authorized read-only export before and after
  the attempt, hashes of those
  exports, certificate fingerprints and relevant revocation matches. Record
  firmware update versions and dates as context, not as a replacement for the
  databases. Unknown contents must be declared unknown.
- Shim validation state (`MokSBStateRT`, if present), MOK trust/deny entries,
  embedded vendor denylist identity, and active `SbatLevelRT`/SBAT revocations.
  Validation disabled, audit mode, or an unreadable policy cannot qualify the
  enforcing acceptance case. An absent optional variable must be explained
  using that component's defaults; do not silently read it as zero.
- Boot entry/path selected, exact refusal text and stage, or guide/welcome
  screen plus post-boot enforcement evidence. A missing USB entry alone is
  not proof of cryptographic rejection; it may be a port or enumeration issue.

On a lab system that already permits read-only inspection, established tools
include `mokutil --sb-state`, `mokutil --db`, `mokutil --dbx`,
`mokutil --list-enrolled`, `mokutil --list-blacklisted`, and
`mokutil --list-sbat-revocations`; availability varies by version. Preserve
their output or error and use the manufacturer's read-only evidence for
unavailable fields. Never substitute a write/enrollment/reset command.
Capture refusal-state databases from an already authorized OS or firmware
viewer without changing trust. If no such inspection is possible, use UNKNOWN.

## Cases and truthful expected outcomes

All physical cases below are **NOT TESTED**. Prerequisites include the identity
and evidence above. Match a case before judging the observation; do not
choose a rejection case retrospectively merely because a machine failed.

| Case | Prerequisites / exact image | Observable result | Expected outcome | Additional evidence to capture |
| --- | --- | --- | --- | --- |
| SB-ACCEPT | Q12; x64 UEFI enforcing; `db` authorizes this shim (normally the inspected UEFI CA 2011); complete inspected policy permits shim, GRUB and kernel; shim validation active | The actual removable-media x64 path reaches the guide, Secure Boot remains enabled, nothing is erased | **ACCEPT** inferred from signatures and observed in the recorded OVMF configuration; physical Pass requires named-machine evidence | Applicable `db` certificate/hash, all denylist/SBAT comparisons, selected entry, welcome screen, post-boot enforcement readings |
| SB-NO-ANCHOR | Q12; x64 UEFI enforcing; complete `db` inspection proves no applicable shim signer or image-hash authorization (e.g. Windows-only or 2023-only with no other authorization) | Explicit firmware authentication failure before the guide | **REJECT** inferred; a missing menu entry without a diagnostic leaves the cause UNKNOWN | Complete `db` evidence and certificate comparison, exact authentication diagnostic, failure stage |
| SB-DBX | Q12; x64 UEFI enforcing; inspected `dbx` explicitly denies the shim or applicable signing certificate even if `db` trusts it | Firmware refuses the component; guide never starts | **REJECT** inferred; refusal is policy enforcement, not erase success or an erase failure | Match entry type and value to the correct Authenticode image digest or certificate/TBS digest, not just a full-file SHA-256 or a CA name; photo of refusal |
| SB-SHIM | Q12; firmware permits shim; validation active; inspected shim/vendor/MOK denylist or active SBAT policy rejects this shim, GRUB or kernel | Shim/GRUB reports validation or SBAT failure; guide never starts | **REJECT** inferred at the rejecting stage; seeing GRUB alone does not mean successful boot | Actual denylist match or SBAT entry/floor comparison and exact failing stage/message |
| SB-UNKNOWN | Q12; firmware `db`, revocations, enforcement, shim policy, or entry path cannot be established | Record either startup or refusal exactly as observed | **UNKNOWN**; neither result is a qualifying Pass for SB-ACCEPT or a proven policy refusal | Missing field and inspection error; available photos/logs; retain the observed boot separately from the unproven trust claim |
| SB-INSPECTION | Q12 intended, but download identity, signature verification, component extraction, or flashed-media binding fails | Stop qualification before boot; preserve the inspection failure | **INSPECTION FAILED**; Result BLOCKED (or Fail for the failed artifact check), never physical Pass | Failed command/exit code, expected vs measured identity; do not use those bytes as the qualified image |
| SB-ARCH | Q12; IA32-only UEFI, ARM/Apple Silicon, Chromebook, or another platform outside claims | No boot attempt is required by this matrix; record architecture/support boundary | **UNSUPPORTED**; Result Excluded with reason, never accepted by implication from an EFI filename | CPU and firmware architecture, platform, applicable claims boundary |

Unknown is never Pass. A Pass in a proven rejection case means that the
specified policy was enforced on that machine, not that it supports starting
Beamo Wipe. Unexpected acceptance under a proven deny policy is a Fail and
must be investigated without starting an erase. Other startup failures remain
boot failures; they cannot be reported as an erase outcome.

Legacy BIOS, CSM, and **already** non-enforcing UEFI cases can record ordinary
boot observations in [the firmware sheet](evidence/physical-acceptance-111/results/firmware.md).
They are not Secure Boot acceptance evidence and are not a suggested fallback
that changes a machine's security configuration.

## Coverage and refresh

Artifact/signature inspection and the retained enforced OVMF USB boot are
Tier 2 evidence for Q12 only. Physical trust, revocation, port, and firmware
states remain NOT TESTED. The [component receipt](evidence/secure-boot-119/README.md)
records the executed commands and their limits. Repeat artifact inspection for
each proposed image and repeat a physical case when its image, firmware,
trust database, or revocation policy changes. Preserve older receipts and
published release assets as historical records.
