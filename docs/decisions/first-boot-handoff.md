# Design record: first boot into the new system and hand-off (Notion Refs 196 and 197)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Ref 184 record
> (`docs/decisions/three-mode-architecture.md`, state 10 "First boot into new
> OS (Refs 196, 197)", N4, D7, D8), the Ref 194 and 195 install records and
> the repository at main `1d727981`. The Notion rows' full texts were not
> available, and the repository does not say how state 10 is split between
> Ref 196 and Ref 197. This record covers state 10 as a whole; §3 lists the
> requirements it assumes, and the split must be checked against Notion.
>
> **Gating.** Ref 184 Phase 4 (N4, D7, D8, D11). Nothing here is built until
> Jack decides Ref 184.
>
> **Numbering.** "Ref 196" and "Ref 197" are Notion rows, not repository
> issue numbers.

## 1. Summary for the owner (plain English)

1. After the new system's installer finishes (Refs 194, 195), the computer
   starts that system for the first time. Its own welcome screen asks the
   new owner for language, account and privacy choices.
2. Beamo does not create accounts, set passwords or carry personal data
   across. By default it carries nothing at all (D7, D8).
3. If the owner starts the Beamo USB again afterwards, Beamo Wipe recognises
   the installed system, finishes its report and says what was and was not
   checked.
4. Five choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today |
|---|---|
| Installed systems | Not created; Beamo only erases |
| Recognising a system on a disk | Display-only contents line (#147): Windows, other system, data, unknown |
| Report after the erase | Result screen, QR summary and optional report USB (`support_export.py`) |
| Boot order and firmware | Never changed |

## 3. Requirements assumed (confirm against the Notion rows)

- R1 The new system first starts at its own first-run setup (D8); Beamo creates no user.
- R2 Nothing from the old system or the Beamo session is copied into the new one unless the owner explicitly chooses it (D7), and never secrets in plaintext (L14, N4).
- R3 Beamo never changes boot order or firmware settings to make the new system start; the owner removes the Beamo USB and restarts.
- R4 The journey's report records the install honestly: "installer finished" only when Beamo can see the installed system, otherwise "not known".
- R5 First-boot scripts, if any, are generated in memory, carry no secrets and run once (N4).

## 4. Hand-off steps

| # | Step | Who |
|---|---|---|
| H1 | Installer finishes (Ref 194/195) | Vendor installer |
| H2 | "Remove the Beamo USB and restart" screen, with the boot-menu key help Beamo already ships | Beamo (before H1) and the owner |
| H3 | New system starts at its welcome screen | Vendor system |
| H4 | Optional: restart into the Beamo USB to **finish the report** | Owner |
| H5 | Beamo rediscovers the disk, recognises the installed system from its partition layout (read-only), and closes the journey (Ref 193) with a report entry (Ref 200) | Beamo |

## 5. What Beamo can and cannot say afterwards

| Claim in the report | When |
|---|---|
| "Erase verified by nwipe" | Only from the erase evidence (unchanged rules) |
| "<System> installer was staged and its files verified" | Staging read-back passed (Refs 194, 195) |
| "An installed <system> was found on the disk" | H5 recognised it read-only |
| "Install result not known" | H4 never happened, or nothing was recognised |
| Never | "Installed and working", "activated", "secure", or anything about the new system's own settings |

## 6. Optional carry-over (D7)

- Default: nothing.
- If Jack allows Wi-Fi carry-over: only the network name and key the owner typed in this session, only with an explicit "Use this Wi-Fi in the new system" choice, written only into the answer file (N4) and never stored on the Beamo USB in plaintext.
- No browser data, files or accounts are ever carried; Beamo Wipe has none.

## 7. Safety rules this design needs (proposed)

1. No account creation, no passwords, no product keys (D8, L12).
2. No firmware or boot-order change; the owner restarts.
3. First-boot scripts only from fixed templates, run once, no secrets (N4); the Windows staging cleanup (Ref 195) is the only planned one.
4. Report wording follows §5; nothing about the new system is claimed beyond what Beamo saw.

## 8. Tests (when built)

| Test | Kind |
|---|---|
| Report wording per §5 for every combination of staging, recognition and H4 | Unit |
| No answer file or first-boot script contains a user, password, key or (by default) Wi-Fi secret | Unit |
| Recognition of installed Linux and Windows layouts from fake lsblk data; unknown layouts stay "not known" | Unit |
| Install, restart, welcome screen reached; Beamo restart closes the journey | QEMU (Ref 203) |
| Real PCs | Physical (Ref 208), Jack's authorization |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D196-1 | New-owner default (Ref 184 D8) | First-run setup / create a user | First-run setup |
| D196-2 | Wi-Fi carry-over (Ref 184 D7) | Never / with explicit consent | Never by default; consent only, never stored in plaintext |
| D196-3 | Ask the owner to restart into Beamo to finish the report | Recommended / optional / never | Optional, with a clear note that the report otherwise says "install result not known" |
| D196-4 | Language and keyboard pre-set in the new system | Yes / no | Yes (no other personal data) |
| D196-5 | How Refs 196 and 197 divide this work | Per Notion | Confirm from the Notion rows; this record can be split without content changes |

## 10. Not done here

No code, script or test was created, and nothing was spent. The Notion rows'
full texts should be checked against §3 and D196-5.
