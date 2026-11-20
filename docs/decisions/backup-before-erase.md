# Design record: optional backup before the erase (Notion Ref 198)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 198 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: Erase everything mode
> "optional backup first", the proposed **N2**, L4, L12, L14), the Ref
> 185–197 design records and the repository at main `1d727981`. The full
> Notion row text was not available; §3 lists the requirements this record
> assumes.
>
> **Gating.** Needs the proposed **N2** ("the backup destination is protected
> like the boot USB for the whole session"). Ref 184 Phase 3. Nothing here is
> built until Jack decides Ref 184.
>
> **Numbering.** "Ref 198" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. Before erasing, the owner can copy personal files from the disk to a
   separate USB drive or external disk they bring.
2. Beamo only **reads** the disk being backed up. It writes only to the
   backup drive, and that drive can never be erased in the same session.
3. Encrypted disks (BitLocker, LUKS) are not opened; Beamo says so and
   suggests backing up from the old system first.
4. The erase cannot start until the backup has finished and been checked, or
   the owner has chosen to skip it.
5. Five choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today | Where |
|---|---|---|
| Reading files from a disk | Never; contents shown only from lsblk metadata, nothing mounted | `discover.py`, `docs/screens.md` (#147) |
| Writing to a second USB | Report USB only: exactly one new removable USB with one FAT32 or exFAT volume, same across two scans; boot disk and target pinned as protected devices; private mount namespace; read-only remount and byte-for-byte verification; then unmount | `support_export.py` |
| Encrypted volumes | BitLocker/LUKS shown as such; no unlocking (L12) | `discover.py`, AGENTS.md |

The backup reuses the report-USB discipline for the destination and adds a
read-only source side.

## 3. Requirements assumed (confirm against the Notion row)

- R1 Optional, offered before Plan's disk choice is final; skipping is one clear button.
- R2 Source opened **read-only**; nothing on the source changes (no journal replay, no access-time writes).
- R3 Destination protected for the whole session (N2): never listed as a target, never selectable, rediscovery checks it is still the same device.
- R4 No password, BitLocker or SAM work (L12); encrypted volumes are skipped with an explanation.
- R5 The backup is verified by reading it back before the erase is offered.
- R6 No file names or personal data go into Beamo's report or support codes.

## 4. Flow

| Step | What happens |
|---|---|
| B1 | "Back up files first?" with **Skip** as an equal choice |
| B2 | Owner plugs in the backup drive; Beamo identifies exactly one new device (report-USB rules, extended to exFAT/NTFS-capable external disks per D198-2) |
| B3 | Beamo lists what it can read on the chosen disk: user folders it recognises (Windows `Users\<name>\Documents`, `Desktop`, `Pictures`, `Music`, `Videos`, `Downloads`; Linux `/home/<name>`), with sizes; encrypted or unreadable volumes listed with the reason |
| B4 | Free-space check on the backup drive; if it does not fit, the owner deselects folders |
| B5 | Copy in a private mount namespace: source mounted `ro` with no journal replay where the driver supports it (`ntfs3 ro`, `ext4 ro,noload`), destination as the report USB; files written to a new folder `Beamo-backup-<date>` |
| B6 | Read-back: every copied file re-hashed from the destination and compared; a manifest (`MANIFEST.sha256`) written last |
| B7 | Unmount both; destination stays protected until the session ends |

## 5. Safety rules this design needs

1. **N2** as proposed: the destination is a protected device for the whole session.
2. The source is never written: read-only mounts only, no `fsck` repair, no journal replay; any driver that cannot guarantee read-only is not used (that volume is skipped).
3. Boot identity uncertain (L4) → no backup destination is accepted.
4. Encrypted volumes are never unlocked (L12).
5. The erase is offered only after B6 succeeds or the owner explicitly skips; a failed backup never starts an erase by itself.
6. Names of files and folders never leave the backup drive: not in logs, reports, QR codes or support codes (R6).

## 6. Limits stated to the owner

- Only files are copied; applications, licences and settings are not.
- Files in places Beamo does not recognise may be missed; the owner can add whole folders per D198-3.
- A backup is only as good as the drive it is on; Beamo checks the copy once, now.

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Destination never in `selectable_disks` after B2; a changed destination identity stops the backup | Unit (fake discovery) |
| Source mounted with read-only options only; refusal when a read-only mount is not possible | Unit (fake mount runner) |
| Read-back mismatch, full destination, removed destination → no erase offered, clear message | Unit (regular files) |
| No file names in logs, reports, QR or support codes | Unit |
| Windows NTFS and Linux ext4 virtual disks backed up to a virtual USB | QEMU (Ref 203) |
| Real drives | Physical (Ref 208), Jack's authorization |

## 8. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D198-1 | Offer backup | (a) in Erase everything and Erase and install; (b) not in v1 | (a) |
| D198-2 | Destination file systems | (a) FAT32 and exFAT only (as the report USB); (b) also NTFS external disks | (b) for large backups, with NTFS written by the in-kernel `ntfs3` driver |
| D198-3 | What to copy | (a) recognised user folders only; (b) also owner-chosen folders | (b), with recognised folders preselected |
| D198-4 | Encrypt the backup | (a) no; (b) optional passphrase | (a) in v1, stated clearly; (b) later after review |
| D198-5 | Backup failure | (a) stop and ask; (b) continue to erase with a warning | (a): the erase needs an explicit "Erase without a backup" choice |

## 9. Not done here

No code, mount or test was created, and nothing was spent. The Notion row's
full text should be checked against §3.
