# Design record: installing Windows 11 after a verified erase (Notion Ref 195)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 195 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: D1, D2, L11, L12, N4,
> D8, D11), the Ref 185–194 design records and the repository at main
> `1d727981`. The full Notion row text was not available; §3 lists the
> requirements this record assumes. Statements about Windows Setup behaviour
> are marked **to confirm** and must be checked against Microsoft's current
> documentation and in QEMU before building.
>
> **Gating.** Everything here depends on **D1** (how Windows media is
> obtained; recommendation: downloaded from Microsoft at run time and
> checked against a hash in the signed catalog, never redistributed) and
> **D2** (Windows 10 not offered). Ref 184 Phase 4. Nothing is built until
> Jack decides Ref 184.
>
> **Numbering.** "Ref 195" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. After a verified erase, Beamo Wipe can prepare the disk so that
   **Microsoft's own Windows Setup** installs Windows 11 on it.
2. Beamo never ships Windows itself and never uses or sells a product key.
   Many PCs activate automatically from a licence stored in their firmware;
   otherwise the new owner enters their own key in Windows.
3. Windows 11's own requirements (TPM 2.0, Secure Boot capable UEFI, enough
   memory and disk) are checked first (Ref 189) and never bypassed.
4. The new owner meets Windows' own first-run setup (D8).
5. Five choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today |
|---|---|
| Windows media, keys, activation | None; L12 forbids keys and requirement bypasses |
| Windows found on a disk | Display-only contents line (#147) |
| BitLocker | Display-only detection; guidance to find the recovery key before firmware changes (`docs/claims.md`) |
| Disk writes | nwipe only, authorized target only |

## 3. Requirements assumed (confirm against the Notion row)

- R1 Only Windows 11 (D2), only on computers that meet Microsoft's requirements (Ref 189, D189-1); no bypass of TPM, Secure Boot or CPU checks (L12).
- R2 Windows media comes only from Microsoft and matches a hash in the signed catalog (D1, Ref 188). Beamo never redistributes it.
- R3 No product key is supplied, stored or generated (L12).
- R4 Install only after a verified erase of the same disk and a separate **Install now** (L11, D11).
- R5 No firmware variable writes; Microsoft's signed boot files are used unchanged, so Secure Boot keeps working.
- R6 Answer files hold no secrets and create no user (N4, D8).

## 4. Getting the media (D1)

- (a) **Download from Microsoft at run time.** The catalog entry names Microsoft's download source and the expected SHA-256 of the ISO for each language/edition offered; the downloader (Ref 188) fetches and verifies it. The exact download mechanism must follow Microsoft's terms and current site behaviour (**to confirm**; it may need the owner to accept Microsoft's terms on screen).
- (b) **Owner-supplied ISO** on a second USB, verified against the same catalog hashes; anything else is refused.
- Hash publication: Beamo publishes hashes only for ISOs it has itself verified from Microsoft (release-side, like the Linux entries).

## 5. Staging Windows Setup on the erased disk

1. **Preconditions** as Ref 194 §5.1: verified erase of this disk, rediscovery match, payload hash re-check, Computer check still passes.
2. **Layout written to the target** (GPT): a FAT32 staging partition at the **end** of the disk holding the ISO's files, with `sources/install.wim` split into `install.swm` parts to fit FAT32 (Microsoft documents split images for FAT32 media; **to confirm** for current Setup). The rest of the disk is left unallocated for Windows.
3. **Boot:** Microsoft's own signed `efi/boot/bootx64.efi` on that partition, unchanged. No EFI variable is written; the removable-media path is used.
4. **Answer file (N4):** an `autounattend.xml` generated in memory from a fixed template: language, keyboard and time zone from the session; disk configuration that installs into the unallocated space **only on this disk** and never touches the staging partition; no product key, no account, OOBE left to the owner (D8). Whether Setup finds an answer file on a fixed disk's partition, or only on removable media, is **to confirm**; if only removable, the answer file goes on the Beamo USB's state area (Ref 185) and the owner keeps the stick in for Setup (D195-3).
5. **Read-back:** every staged file is re-hashed against the ISO's file list before hand-off.
6. **Hand-off:** "Restart. Windows Setup will install Windows and stop at its welcome screen." After Windows' first start, a generated `SetupComplete.cmd` (no secrets) deletes the staging partition and extends the Windows partition (D195-4).

## 6. Safety rules this design needs (proposed)

1. Windows is installed only on the disk erased and verified in this journey (L11, D11); the answer file names that disk by a property Setup can check (**to confirm**: disk size and bus), and the template refuses any other disk.
2. No bypass of Windows 11 requirements, no registry tweaks to skip checks, no keys (L12).
3. Media and staged files are verified against the signed catalog and read back (L13).
4. No firmware or EFI variable writes; Microsoft's signed boot files unchanged.
5. Interrupted staging or Setup never continues by itself (L8); the report says "install not finished".

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Install refused without TPM 2.0, UEFI, Secure Boot capability, memory or disk size per Ref 189 | Unit |
| Answer-file template: escaping, no key, no account, only the target disk, OOBE left on | Unit (XML schema and content checks) |
| Staging writer: split image sizes under FAT32 limits, read-back mismatch stops, disk change stops | Unit (regular files) |
| Full Setup from a staged virtual disk with a virtual TPM (`swtpm`) and Secure Boot on | QEMU (Ref 203), using a Microsoft evaluation ISO only if its licence allows automated testing (**to confirm**) |
| Real PCs, activation from firmware licence | Physical (Ref 208), Jack's authorization |

## 8. Legal and claims notes

- Beamo does not redistribute Windows and does not provide licences; listing text must say the owner needs a valid Windows licence (many PCs have one in firmware). Any such claim is added to `docs/claims.md` only after review (Ref 207).
- Microsoft trademarks are used only to name the product being installed.

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D195-1 | Windows media (Ref 184 D1) | (a) download from Microsoft; (b) owner-supplied ISO; (c) not offered | (a) with (b) as fallback |
| D195-2 | Editions and languages | Home and Pro, all Microsoft languages / a short list | Home and Pro in the five Beamo UI languages first |
| D195-3 | Where the answer file lives | (a) on the staged disk; (b) on the Beamo USB state area with the stick kept in | (a) if Setup supports it, else (b) |
| D195-4 | Remove the staging partition after install | (a) yes, by `SetupComplete.cmd`; (b) leave it | (a) |
| D195-5 | If Windows Setup fails | Guidance only / re-stage after a fresh **Install now** | Re-stage after a fresh **Install now**, plus guidance |

## 10. Not done here

No code, media, key, partition or test was created, and nothing was spent.
The Notion row's full text should be checked against §3.
