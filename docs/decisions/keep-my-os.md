# Design record: Keep my OS mode (Notion Ref 192)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 192 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: the Keep my OS row and
> owner decision D4), the Ref 185–191 design records and the repository at
> main `809cc11e`. The full Notion row text was not available; §3 lists the
> requirements this record assumes.
>
> **Gating.** Ref 184 lists Ref 192 in Phase 4 and makes D4 ("native reset:
> guide only / not offered") Jack's decision. Nothing here is built until he
> decides Ref 184.
>
> **Numbering.** "Ref 192" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. Some owners want to keep their computer's system, for example to hand on
   a laptop with Windows still on it. Keep my OS helps without touching that
   system's disk.
2. It offers three things: step-by-step guidance for the system's **own**
   reset (Windows "Reset this PC"); erasing **other** internal disks only; or
   a read-only check and report with nothing erased.
3. Beamo never runs, checks or certifies the system's own reset, and always
   says so: "We do not verify it, and it is not the same as a verified wipe."
4. Five choices are yours (§9).

## 2. Today (facts from main `809cc11e`)

| Item | Today | Where |
|---|---|---|
| Contents of each disk | One display-only line per disk: Windows (from a Microsoft reserved or Windows recovery partition beside one NTFS/BitLocker partition), other systems, data, unknown; nothing mounted or probed | `discover.py`, `docs/screens.md` (#147) |
| Erasing a disk | Whole disk only, pinned nwipe, full gates | `safety.py`, `nwipe_runner.py` |
| Guidance pages | Boot-menu and BitLocker-key guidance on the helper pages; no reset guidance | `helper/`, `docs/boot-keys.md` |
| Writing to a disk's file system | Never | AGENTS.md safety boundaries |

## 3. Requirements assumed (confirm against the Notion row)

- R1 The disk holding the system to keep is **never** a target in this mode and is never written.
- R2 Native-reset guidance is text only, clearly labelled "not verified by Beamo" (D4).
- R3 Erasing other internal disks uses exactly today's gates (and Ref 191 for several).
- R4 The check-and-report option erases nothing and says so.
- R5 No password, SAM, BitLocker or Secure Boot work (L12); no license keys.

## 4. The three options

| Option | What happens | What Beamo checks | What the result says |
|---|---|---|---|
| (a) Guide to the system's own reset | Screens with the steps for Windows 10/11 "Reset this PC → Remove everything", including the option to clean the drive, and (D192-2) a pointer to reinstall Linux from its own media; the owner restarts into the system and follows them | Nothing about the reset itself | "Beamo did not run or check this reset. It is not a verified wipe." |
| (b) Erase other internal disks | Pick lists every erasable disk **except** the kept system's disk; then today's flow (or Ref 191's set flow) | Everything it checks today | Per-disk results as today; the kept disk is listed as "kept, not erased" |
| (c) Check and report only | Computer check (Ref 189) and the disk list, nothing erased | Read-only facts | "Nothing was erased." |

## 5. Choosing the disk to keep

- The owner picks the disk to keep from today's list, helped by its contents line ("Windows · 237 GB").
- Beamo never decides by itself which disk holds the system; when two disks look like systems, the owner must choose, and if it is not clear, option (b) is not offered.
- The kept disk is identified by serial/WWN, size and model like every target (path is never identity); if it cannot be identified confirmably, option (b) is not offered.
- The kept disk is protected for the session like the boot USB: never listed as a target, never selectable, and a rediscovery that cannot re-identify it stops option (b).

## 6. Safety rules this design needs (proposed)

1. The kept disk is excluded from targets for the whole session (same strength as the boot-USB exclusion: unknown identity → no targets).
2. Native-reset guidance is information only; Beamo runs no reset, no recovery tool and no command in the installed system.
3. Every screen and the report say plainly what was **not** verified.
4. Claims: no wording that a native reset is a wipe, secure, or verified; `docs/claims.md` changes only after review (Ref 207).

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Kept disk never in `selectable_disks`; unknown or duplicate identity removes option (b) | Unit (fake discovery) |
| Rediscovery that loses or changes the kept disk stops before any nwipe | Unit |
| Option (c) runs no runner at all | Unit |
| Guidance and results never say "verified" or "wipe" for a native reset, in all languages | Unit (copy scan) |
| A two-disk QEMU guest with a fake "system" disk kept | QEMU (Ref 203) |
| Real Windows reset steps on real PCs | Physical (Ref 208), Jack's authorization |

## 8. What changes where (when approved)

| Area | Change |
|---|---|
| `wizard.py` | A kept-disk identity in the session; Pick filters it out; start-time re-check |
| `safety.py` | The kept disk added to the protected set beside the boot device |
| `copy.py`, locales | Guidance screens and result lines |
| Report (Ref 200) | "Kept, not erased" entry; option (a) records only that guidance was shown |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D192-1 | Native reset (Ref 184 D4) | Guide only / not offered | Guide only, clearly "not verified" |
| D192-2 | Which systems get reset guidance | (a) Windows 10 and 11 only; (b) also major Linux distributions | (a) in v1; Linux gets a "reinstall from its own media" pointer |
| D192-3 | When the system disk is unclear | (a) no option (b); (b) let the owner pick from all disks with a warning | (a) |
| D192-4 | Encrypted (BitLocker) system disk | Show option (a) with a key reminder / hide | Show, with the existing "find your BitLocker recovery key first" wording |
| D192-5 | Report for option (a) | Record "guidance shown" / no report | Record "guidance shown, not verified" |

## 10. Not done here

No code, screen, copy or test was changed, and nothing was spent. The Notion
row's full text should be checked against §3.
