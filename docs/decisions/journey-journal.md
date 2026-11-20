# Design record: journey journal and safe resume (Notion Ref 193)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 193 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: state table, L8 and
> the proposed **N3** and **N5**), the Ref 185 state-area layout, the Ref
> 186–192 design records and the repository at main `1d727981`. The full
> Notion row text was not available; §3 lists the requirements this record
> assumes.
>
> **Gating.** A journal that survives a restart must live on the Beamo USB's
> state area, which needs the **proposed L3 amendment** (Ref 185). Ref 184
> lists Ref 193 in Phase 4. Nothing here is built until Jack decides Ref 184.
>
> **Numbering.** "Ref 193" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. A long journey (download, erase, install) can be interrupted by a flat
   battery, a dropped cable or a restart. The journal remembers **where the
   journey was**, so Beamo Wipe can explain what happened and offer the safe
   next step.
2. The journal is a memory aid, never a permission. After any restart,
   nothing destructive continues by itself: an interrupted erase is never
   resumed, and an install needs a fresh **Install now**.
3. Only harmless steps resume automatically, for example a download picks up
   where it stopped and re-checks every byte.
4. A journal from another computer, other disks, or too old is thrown away.
5. Five choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today | Where |
|---|---|---|
| Journal | `session-recovery.json` in `/tmp/beamo-wipe`, same boot only, on tmpfs; phases `preflight` → `armed` → `terminal` | `session_recovery.py`, `docs/session-recovery.md` |
| What it may do | Display evidence after an interface crash; "never stores authority to start or resume nwipe" | `session_recovery.py` docstring |
| Storage rules | Private 0700 directory, regular 0600 single-link files, `O_NOFOLLOW`, bounded reads, pinned directory fd, temp-file + fsync + atomic replace + directory fsync, content checksum | `docs/session-recovery.md` |
| Across a power loss or reboot | Nothing survives; the next boot starts fresh | tmpfs, AGENTS.md (no write to the boot USB) |

The design keeps all of today's storage discipline and adds a second,
persistent journal on the Beamo USB's state area once that exists.

## 3. Requirements assumed (confirm against the Notion row)

- R1 The journal survives a power loss and a restart (persistent, on the Ref 185 state area).
- R2 It records the journey state (Ref 184 states 1–11), the plan, the computer and disk identities, download progress and outcomes, never secrets.
- R3 It is untrusted input on every read (N3): integrity-checked, bound to this computer and these disks, expiring.
- R4 It never authorizes a destructive step (L8): erase never resumes; install needs rediscovery and a fresh decision (D11).
- R5 Corruption or doubt falls back to Plan with a plain explanation; nothing is guessed.

## 4. Record

```
beamo-journey/1
  journey_id         random 128-bit
  created_utc, updated_utc, sequence (monotonic)
  computer           {product/board identity from DMI, CPU model, memory size}  (no serials, see D193-3)
  disks              [{serial/WWN hash, size, model}]   identity binding only
  plan               {mode, catalog_entry_id, catalog_serial}           (Ref 190)
  state              one of Ref 184 states 1-11
  download           {entry_id, offset, expected sha256}                  (Ref 188)
  erase              [{disk, outcome, evidence checksum}]                 (no authority)
  install            {disk, outcome}                                       (Ref 194/195)
  checksum           SHA-256 over the canonical body
```

- One file, `journey.json`, in the state area (Ref 185 p2), same write discipline as `session_recovery.py` (temp file, full write, fsync, atomic rename, directory fsync); `data=journal` ext4 per Ref 185.
- Bounded size (64 KiB); duplicate JSON fields refused, as `session_recovery._object` does today.
- Disk identities are stored as salted hashes (salt per journey) so the stick does not carry readable serials (R2, D193-3).

## 5. Reading the journal after a restart

| Found state | What Beamo Wipe does |
|---|---|
| None, corrupt, wrong schema, checksum mismatch | Start at Plan; say "No usable journey was found" only if a file existed |
| Different computer or a bound disk missing/changed | Start at Plan; "This stick was last used on another computer or with other disks" |
| Older than the expiry (D193-1) | Start at Plan; the download cache may be kept if its hash still verifies |
| 1–3 (plan, check, connect) | Offer to continue the plan from the start of state 2; check runs again |
| 4 (download) | Offer to resume the download; bytes on disk are re-hashed (Ref 188) |
| 5–6 (readiness, authorization) | Back to Plan; **a saved decision never authorizes** |
| 7 (erase) | "The erase did not finish." The disk is treated as unknown; the report says so; back to Plan. **Never resumes.** |
| 8 (outcome gate) | Recompute from evidence if it is still present; otherwise as 7 |
| 9 (install) | "The install did not finish." Offer a fresh **Install now** only after rediscovery matches and the erase outcome is still proven (D11) |
| 10–11 | Show the report again |

## 6. Safety rules this design needs (proposed)

1. **N3** (Ref 184): the journal is untrusted, bound, integrity-checked and expiring; on doubt, Plan.
2. **L8** unchanged: no journal state authorizes or resumes an erase; install after a restart needs rediscovery plus a fresh decision (D11).
3. **N5**: no catalog or self-update applied during states 6–9.
4. The journal never holds secrets (Wi-Fi keys, passwords) or readable serial numbers.
5. Writes go only to the state area (L3 as amended); never to a target, never to the system partition.

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Every Ref 184 state × restart → the restart point in §5 | Unit (table-driven, fake store) |
| Truncated, bit-flipped, duplicate-field, oversized, wrong-schema journals → Plan | Unit |
| Journal from another computer or with a changed disk → Plan | Unit |
| Power loss mid-write (fault injection between temp write, fsync and rename) leaves the old or the new record, never a mix | Unit (regular files) |
| State 7 after restart never starts nwipe; state 9 requires rediscovery and a fresh decision | Unit |
| Real power cut during download and during erase | QEMU (Ref 203, forced reset) and Physical (Ref 208) |

## 8. What changes where (when approved)

| Area | Change |
|---|---|
| `session_recovery.py` | Kept for same-boot interface recovery |
| New `journey_journal.py` | Persistent record, reader and restart table |
| `wizard.py` | Start screen reads the journal and offers only §5 actions |
| Ref 185 build | Creates the state area the journal lives in |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D193-1 | Journal expiry | 24 h / 7 days / 30 days | 7 days; the download cache may live longer if its hash verifies |
| D193-2 | Resume a download automatically after restart | (a) ask; (b) resume silently | (a): one plain question, because it uses the network |
| D193-3 | Computer and disk identity in the journal | (a) salted hashes only; (b) readable model and size, hashed serials | (b): readable model and size help the owner; serials only hashed |
| D193-4 | After an unfinished erase | (a) back to Plan with the disk shown as "not known to be erased"; (b) offer to start the same erase again at once | (a); a new erase needs the full gates anyway |
| D193-5 | Keep the journal after Done | (a) delete at Done; (b) keep until the next journey | (a), unless the report is stored there (Ref 184 D6) |

## 10. Not done here

No code, journal, partition or test was created, and nothing was spent. The
Notion row's full text should be checked against §3.
