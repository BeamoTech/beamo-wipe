# Design record: installing Linux after a verified erase (Notion Ref 194)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 194 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: state 9, L7, L11,
> N4, D3, D8, D11), the Ref 185–193 design records and the repository at
> main `1d727981`. The full Notion row text was not available; §3 lists the
> requirements this record assumes. Statements about each distribution's own
> installer automation must be confirmed per distribution and version before
> building (§5).
>
> **Gating.** Ref 184 Phase 4 (N1, N3, N4, N5, D1–D4, D7, D8, D11). Nothing
> here is built until Jack decides Ref 184.
>
> **Numbering.** "Ref 194" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. After an erase that nwipe verified, Beamo Wipe can put a fresh copy of a
   supported Linux on the same disk, using the distribution's **own, signed
   installer**, downloaded and checked earlier (Ref 188).
2. Beamo copies that installer onto the erased disk, checks the copy byte by
   byte, and asks the owner to restart without the Beamo USB. The
   distribution's installer then sets up the computer and stops at its
   first-run screen, so the next owner creates their own account.
3. Beamo never changes firmware settings, never turns off Secure Boot and
   never installs onto the Beamo USB or any disk other than the one just
   erased.
4. Five choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today |
|---|---|
| Install of any OS | None; Beamo Wipe only erases |
| Writes to a disk | Only nwipe, only to the authorized target (`nwipe_runner.py`) |
| Firmware or EFI variables | Never written; Secure Boot state read only for a QEMU marker (`beamo-wipe-kiosk`) |
| Verified payloads | Proposed in Ref 188 (signed catalog, pinned SHA-256/512) |

## 3. Requirements assumed (confirm against the Notion row)

- R1 Install only after a **verified** erase of the same disk in the same journey (L11, D11).
- R2 The installed system comes from the vendor's own signed media, verified against the signed catalog, and keeps the vendor's Secure Boot chain (L12, L13).
- R3 The new owner meets the system's own first-run setup (D8); no account or password is created by Beamo (N4).
- R4 No firmware variable is written; no Secure Boot or TPM change.
- R5 An interrupted install never continues by itself (L8); a retry needs rediscovery and a fresh **Install now** (D11).

## 4. Approaches considered

| Approach | How | For | Against |
|---|---|---|---|
| **A. Stage the vendor installer on the erased disk** (recommended) | Write the verified vendor ISO (hybrid images boot from a disk in UEFI and BIOS) to the start of the target, read it back and hash it, then add a small answer-file partition the installer reads; the owner restarts without the Beamo USB | Vendor's own signed boot chain and installer; no redistribution; no firmware writes; the installer replaces the staging copy | Two restarts; depends on each vendor's unattended or OEM mode; installer UI may still ask a question |
| B. Beamo-built "golden" disk images per distribution | Release-side build of a ready system image, written and grown | One restart, fastest | Modified redistributions raise trademark and licence questions; Beamo must maintain and patch images |
| C. Hand over to the vendor kernel with `kexec` | Boot the vendor installer directly from the Beamo session | No extra restart | With Secure Boot, kernel lockdown restricts `kexec`; fragile across vendors |

## 5. Approach A in detail

1. **Preconditions** (state 8 passed): erase outcome `verified` for this disk; rediscovery matches the disk identity (L7); payload hash re-checked from the OS cache (Ref 188); Computer check suitability still holds (Ref 189).
2. **Owner decision:** a review screen "Install <name version> on <disk>" with **Install now** (a separate decision from **Erase now**, D11).
3. **Write:** stream the verified ISO bytes to the start of the target with `O_DIRECT`/fsync, then read the written range back and compare its SHA-256 with the catalog value. Mismatch → stop, report, offer to retry once.
4. **Answer file (N4):** generated in memory from fixed templates with strictly escaped values (language, keyboard, time zone from the session; no user, no password, no Wi-Fi secret unless D7 allows it), written to a small labelled partition after the ISO range. Mechanism per distribution, **to be confirmed per version**:
   - Ubuntu and derivatives: `autoinstall` with a NoCloud `CIDATA` volume; recent Ubuntu asks the person to confirm the automated install, which is acceptable as a second human step.
   - Fedora: Kickstart from a labelled volume; needs the boot entry to name it.
   - Debian: preseeding; needs the boot entry to name it.
   Where the vendor boot entry must change, the change is limited to its menu configuration and must keep the signed boot files unchanged.
5. **Hand-off:** "Remove the Beamo USB and restart. The <name> installer will finish and stop at its welcome screen." No firmware variable is written; disk boot uses the image's own removable-media path.
6. **After:** booting the Beamo USB again detects the installed system (contents line) and records "install finished" in the journal (Ref 193) and report (Ref 200). Beamo cannot verify the vendor installer's own success beyond that.

## 6. Safety rules this design needs (proposed)

1. Install writes only to the disk erased and verified in this journey, after rediscovery (L7, L11, D11).
2. Only catalog-verified vendor bytes are written; the written range is read back and hashed before hand-off.
3. No firmware, EFI variable, Secure Boot or TPM change; no bypass (L12).
4. Answer files hold no secrets and no user account (N4, D8).
5. Restart never continues an install by itself (L8).

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Install refused without a verified erase of the same disk, after an identity change, or with a stale payload hash | Unit |
| Writer: short write, read-back mismatch, disk removed mid-write → stop with "install not finished" | Unit (regular files as disks) |
| Answer-file templates: escaping of every field, no secrets, size bounds | Unit |
| Each supported distribution installs unattended from a staged virtual disk, UEFI with Secure Boot on and off, and BIOS | QEMU (Ref 203) |
| Real PCs | Physical (Ref 208), Jack's authorization |

## 8. What changes where (when approved)

| Area | Change |
|---|---|
| New `installer_stage.py` | Writer, read-back verifier, answer-file builder |
| `wizard.py` | States 8–10 and **Install now** |
| Catalog (Ref 188) | Per-entry `install_method` and answer-file template ID |
| `docs/claims.md` | Only after verified installs (Ref 207) |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D194-1 | Install approach | A staged vendor installer / B golden images / C kexec | A |
| D194-2 | Supported distributions in v1 | From the catalog (Ref 188 D188-6) | Two long-support desktop distributions with documented unattended or OEM install, confirmed in QEMU first |
| D194-3 | Disk encryption in the new system | Vendor default / always offer / never | Vendor default; the first-run setup offers what the vendor offers |
| D194-4 | Language, keyboard and time zone carried from the Beamo session | Yes / no | Yes; no other personal data |
| D194-5 | If the vendor installer fails after hand-off | Guidance only / Beamo re-stages once | Guidance, plus re-staging after a fresh **Install now** |

## 10. Not done here

No code, image, partition or test was created, and nothing was spent. The
Notion row's full text should be checked against §3.
