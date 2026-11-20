# Design record: journey timeline, progress and time left (Notion Ref 199)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 199 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`: the state table and
> L16), the Ref 188 downloader record (progress "goes to the journey
> timeline"), the Ref 189–198 design records and the repository at main
> `1d727981`. The full Notion row text was not available; §3 lists the
> requirements this record assumes.
>
> **Gating.** Ref 184 Phase 3. Nothing here is built until Jack decides
> Ref 184.
>
> **Numbering.** "Ref 199" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. A long journey shows one timeline: what is done, what is happening now,
   and what comes next, with an honest estimate of the time left.
2. Progress never claims more than is known. 100 % or "Done" appears only
   when the step's own check has passed, exactly like today's erase screen.
3. Times are shown as ranges when they are uncertain, and say "not known"
   rather than guessing.
4. The owner can pause a download. Erases and installs are not paused; Stop
   works as today.
5. Four choices are yours (§9).

## 2. Today (facts from main `1d727981`)

| Item | Today | Where |
|---|---|---|
| Erase progress | Parsed from the pinned nwipe log: job percentage, round/pass counters, engine ETA, phase marker (Writing, Verifying, Syncing, Retrying); "presentation data", never completion evidence | `progress.py`, `docs/progress-timing.md` |
| Cap before completion | Displayed progress stays below 100 % until the completion checks pass; it never goes backwards; NaN/inf rejected | `nwipe_runner._update_progress` |
| Freshness | Based on the monotonic time of each accepted engine update; stale progress is labelled | `docs/progress-timing.md` |
| Other steps | No download or install exists | — |

## 3. Requirements assumed (confirm against the Notion row)

- R1 One timeline for the whole journey (Ref 184 states 1–11), in Tk, GTK/Orca and the console (L16).
- R2 Each step shows its own progress from its own observations; percentages are presentation only and never completion evidence.
- R3 Time-left estimates are honest: ranges, "not known", and a reason when a step is waiting (for example "waiting for the network").
- R4 Download can pause and resume (Ref 188); destructive steps cannot be paused, only stopped as today.
- R5 Screen readers announce step changes, and progress at the pace today's `progress.ProgressAnnouncer` uses for the erase (60 s interval, 5 s minimum gap).

## 4. Timeline model

| Step | Progress source | Done when |
|---|---|---|
| Plan, Computer check | Instant | The step's own result exists |
| Connect | Link state from netd (Ref 186) | Address and catalog host reachable |
| Download | Bytes verified so far / catalog size (Ref 188) | Full SHA-256/512 and size match; atomic rename to `.verified` |
| Readiness | Instant | All checks pass |
| Erase (each disk) | Today's nwipe observations, unchanged | Today's completion and verification checks |
| Install staging | Bytes written and read back / total (Refs 194, 195) | Read-back hash matches |
| First boot | Not observable from Beamo | Shown as "on the new system" (Refs 196/197) |
| Report | Write and read-back (Ref 200) | Report verified |

## 5. Time left

- **Download:** from a moving average of verified bytes per second over the last 30–60 s; shown as a range (for example "10–15 minutes"); "not known" while fewer than 30 s of samples exist or the link is down.
- **Erase:** today's nwipe ETA and timing rules, unchanged; for several disks (Ref 191), the sum of per-disk estimates shown as a range and refreshed when each disk finishes.
- **Whole journey:** shown only as "about N hours" when every remaining step has an estimate; otherwise each step's own estimate.
- No estimate ever shortens a safety wait (the 5 s review countdown is separate and fixed).

## 6. Safety rules this design needs

1. Percentages and estimates are display data only; completion stays with each step's own checks (today's rule for the erase).
2. No "Done" or 100 % before the step's check passes.
3. Pause exists only for non-destructive steps (download); destructive steps keep today's Stop behaviour.
4. Timeline text stays within `docs/claims.md` (no promised durations in listing copy).

## 7. Tests (when built)

| Test | Kind |
|---|---|
| Each step's "done" depends only on its completion check; percentages alone never mark done | Unit |
| Estimates: ranges, "not known" thresholds, link-down, resumed download | Unit (fake clock) |
| Multi-disk estimate updates per finished disk | Unit |
| Accessible announcements rate-limited; console paging of the timeline | Existing UI suites |
| Full journey timeline in QEMU with a throttled local mirror | QEMU (Ref 203) |

## 8. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D199-1 | Whole-journey estimate | Show / per-step only | Per-step, plus a whole-journey "about" only when every step has an estimate |
| D199-2 | Download pause | Offer / not offer | Offer |
| D199-3 | Sound when a long step finishes | Today's finish sound for every step / only at the end | Only at the end and when the owner is needed (for example "Remove the USB and restart") |
| D199-4 | Keep the screen awake through the whole journey | Yes (today's erase inhibitor extended) / erase only | Yes, released at the end or on Stop |

## 9. Not done here

No code, screen or test was created, and nothing was spent. The Notion row's
full text should be checked against §3.
