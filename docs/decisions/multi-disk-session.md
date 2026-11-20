# Design record: erase every internal disk in one session (Notion Ref 191)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 191 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: the Erase everything
> mode and the **proposed L6 amendment**), the Ref 185–190 design records and
> the repository at main `809cc11e`. The full Notion row text was not
> available; §3 lists the requirements this record assumes.
>
> **Gating.** Ref 191 needs the L6 amendment (one review covering an exact set
> of disks), which is not adopted. Until Jack approves it, the shipped rule
> stands: one disk per authorization. Nothing here is built until he decides
> Ref 184.
>
> **Numbering.** "Ref 191" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. A computer with two or three internal disks can be erased in one sitting:
   pick every disk, review them all on one screen, type once, wait the five
   seconds, press **Erase now** once.
2. The disks are still erased **one at a time** by the pinned nwipe, each
   with the same checks as today. If anything about the set changes, the
   authorization is cancelled.
3. The result lists every disk separately: erased and verified, erased but
   not verified, stopped, or not started.
4. Today's one-disk path and **Erase another disk** stay as they are.
5. Five choices are yours (§9).

## 2. Today (facts from main `809cc11e`)

| Item | Today | Where |
|---|---|---|
| Disks per authorization | Exactly one: Pick → Confirm (exact token) → Method → Last chance (5 s) → **Erase now** | `wizard.py`, `safety.py` |
| Next disk | **Erase another disk** on Done; a full new authorization per disk | `wizard.py`, `copy.BTN_ERASE_ANOTHER` |
| Owner tick across disks | Carried in memory within one app run only when fresh discovery lists no erasable disk outside the confirmed set; never replaces a per-disk gate (#187) | `owner_carry.py` |
| nwipe | One process, one positional target, `--autonuke`, `--exclude=` the boot device, never `--force` | `nwipe_runner.py` |
| Before launch | Rediscovery under lock; target and boot identity re-bound | `wizard._perform_start`, `nwipe_runner` |
| Result | One disk per result and report | `evidence.py`, `result_summary.py` |

## 3. Requirements assumed (confirm against the Notion row)

- R1 The owner can choose several internal disks of this computer in one plan (Ref 190).
- R2 One review screen lists the exact set (model, size, last four of the serial) and one authorization covers exactly that set (proposed L6).
- R3 Erases run sequentially, one nwipe process at a time (L9 unchanged).
- R4 Every per-disk safety check of today still runs before each disk (L7).
- R5 The report shows each disk's own outcome; one disk's success never colours another's.
- R6 Stop is always available and never leaves a disk silently half-reported.

## 4. Flow

| Step | Change from today |
|---|---|
| Pick | Check boxes instead of one choice; "Select all internal disks" offered only when every listed disk is confirmable (identity rules of `identity.identity_confirmable`). The boot USB and protected devices stay unlisted as today |
| Confirm | One token for the set. Proposal: the token encodes the count ("ERASE 3 DISKS" style) so a wrong count cannot match; exact wording under D191-2 |
| Method | One method for the whole set (D191-3) |
| Last chance | One review listing every disk in order, with total estimated time; 5 s countdown; **Erase now** |
| Working | "Disk 2 of 3": current disk progress, then a list with done / running / waiting |
| Done | One result per disk plus a set summary; per-disk report entries |

## 5. Execution rules

1. **Snapshot.** At **Erase now** the wizard freezes the ordered set of disk identities (path is never identity).
2. **Before each disk:** full rediscovery under the lock, the boot device re-bound, and every disk in the remaining set re-matched by identity. Any added erasable disk, missing disk, or changed serial, size, WWN or path for a set member stops the run before the next disk starts (D191-4).
3. **One nwipe at a time**, the same argv validation as today for each disk. No parallel erases.
4. **After each disk:** its outcome is final and recorded before the next starts. A failed or unverified disk does not erase the remaining ones until the owner decides (D191-1).
5. **Stop:** stops the current disk as today (`_cancel_process`); the remaining disks are recorded as **not started**. No automatic resume, ever (L8).
6. **Power and sleep:** the existing inhibitor covers the whole set; power warnings repeat before each disk.

## 6. Results and report

- Per disk: today's evidence outcomes (`verified`, `completed` without verification, `failed`, `interrupted`; `evidence.ALLOWED_OUTCOMES`) and today's screen views (including stopped and indeterminate), plus one new state, **not started**, for disks after a stop or failure.
- Set summary: counts only; "All disks verified" only when every disk in the set is verified.
- The report (Ref 200) holds one entry per disk with the shared authorization record (owner source, token time, set identity list).
- The result QR summary (today one disk) either lists each disk briefly or points to the full report (D191-5).

## 7. Safety rules this design needs

- The proposed **L6** wording (Ref 184 §4), once approved.
- **L7** applies before each disk; **L9** sequential; **L8** no resume.
- A set authorization covers exactly its disks: adding, removing or reordering a disk cancels it.
- The boot USB, a backup destination (Ref 198, N2) and any disk not in the set are never targets.

## 8. Tests (when built)

| Test | Kind |
|---|---|
| Token for a set of N matches only that N; any change to the selection clears authorization | Unit |
| Rediscovery between disks: added disk, removed disk, changed identity, swapped paths each stop before the next nwipe | Unit (fake discovery) |
| Exactly one runner at a time; argv per disk passes `validate_argv` | Unit (fake runner) |
| Stop during disk 2 of 3: disk 2 cancelled, disk 3 not started, no resume after restart | Unit |
| One failed disk: owner choice per D191-1 | Unit |
| Per-disk evidence and set summary; never "all verified" with any non-verified disk | Unit |
| Two and three virtual disks, mixed SATA/NVMe | QEMU (Ref 203) |
| Real multi-disk PCs | Physical (Ref 208), Jack's authorization |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D191-1 | A disk fails or ends unverified | (a) stop the set and ask; (b) continue with the next disk automatically | (a): ask, with "Continue with the next disk" needing a fresh **Erase now** for the rest |
| D191-2 | Confirmation wording for a set | (a) one token that includes the count; (b) one token per disk on one screen | (a) |
| D191-3 | Method per set or per disk | (a) one method for the set; (b) per disk | (a) in v1 |
| D191-4 | A non-member erasable disk appears between disks | (a) stop and require a new authorization; (b) ignore it because it is not in the set | (a) |
| D191-5 | Result QR summary for several disks | (a) one short line per disk; (b) a set summary pointing to the full report | (a) while it stays readable on a phone; otherwise (b) |

## 10. Not done here

No code, screen, copy or test was changed, and nothing was spent. The Notion
row's full text should be checked against §3.
