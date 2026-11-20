# Design record: Plan and "Help me choose" (Notion Ref 190)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 190 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`, state 1 "Plan"), the
> Ref 185–189 design records and the repository at main `809cc11e`. The full
> Notion row text was not available; §3 lists the requirements this record
> assumes.
>
> **Gating.** Ref 184 places Ref 190 in Phase 3 ("Start and erase"). Nothing
> here is built until Jack decides Ref 184; the three modes themselves are
> part of that decision.
>
> **Numbering.** "Ref 190" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. The first real screen asks what should happen to this computer, in
   everyday words, and turns the answer into a **plan**: which mode, which
   new system (if any) and which disks.
2. "Help me choose" explains the choices side by side, using only facts from
   the signed catalog (Ref 188) and the Computer check (Ref 189).
3. A plan is only a plan. It never starts an erase. The owner box, the typed
   confirmation, the countdown and **Erase now** stay exactly as today.
4. Nothing is recommended that this computer cannot do, and nothing is
   claimed that `docs/claims.md` does not allow.
5. Five choices are yours (§9).

## 2. Today (facts from main `809cc11e`)

| Item | Today | Where |
|---|---|---|
| Screens before the erase | Splash → Keyboard → What this does → Owner → Pick → Confirm → Method → Last chance | `models.Screen`, `wizard.py` |
| Choice of goal or mode | None: the product has one mode, erase one disk | — |
| Method choice | Three nwipe methods with plain explanations and limits | `methods.py`, `storage_limits.py` |
| Help and settings | One fixed menu on every screen (#175) | `help_menu.py` |
| Allowed product language | Fixed list | `docs/claims.md` |

## 3. Requirements assumed (confirm against the Notion row)

- R1 One question first: what will happen to this computer. Plain words, no jargon, all five UI languages, Tk / GTK-Orca / console parity (Ref 184 L16).
- R2 The answer maps to one of the three modes (Ref 184 §2) and, for Erase and install, to one catalog entry.
- R3 "Help me choose" compares only real, verified facts: catalog fields (name, version, licence, support dates, notes, Secure Boot) and the Computer check result.
- R4 A plan is never authorization (Ref 184 L8). Changing the plan later cancels anything that depended on it.
- R5 The plain "erase one disk" path stays one step away for owners who know what they want.
- R6 No account, no telemetry, works offline for the erase-only modes (L14).

## 4. The flow

| Step | Screen (proposal) | Content | Leaves to |
|---|---|---|---|
| P1 | **What will happen to this computer?** | (a) "I'm selling or giving it away" → Erase everything; (b) "I'm keeping it and want a fresh system" → Erase and install; (c) "I'm keeping it with its system" → Keep my OS; plus **Help me choose** | P2 or the chosen mode |
| P2 | **Help me choose** | Three short cards, one per mode: what happens, what is kept, how long it may take, what it does not do. Each card names the limits from `storage_limits.py` and the "not a certificate" line from `docs/claims.md` | P1 with a highlighted card |
| P3 | **Which new system?** (Erase and install only) | Catalog entries this computer can run (Computer check suitability), each with licence, support until, Secure Boot need and size; blocked entries listed separately with the reason | P4 |
| P4 | **Which disks?** | Today's Pick screen, unchanged rules; in Erase everything with Ref 191, the multi-disk list | Today's Confirm |
| P5 | **Your plan** | One summary: mode, system, disks, what will be erased, what will be installed, what is not checked. Buttons: Change, Continue | Computer check (Ref 189), then the mode's next state |

Today's Owner, Confirm, Method and Last chance screens follow unchanged; the
plan only fills in what they show.

## 5. Help me choose: content rules

- Facts come from signed catalog fields and the Computer check only; nothing is fetched to build the comparison except the catalog itself (Ref 188).
- No ranking by popularity, no "best", no comparison with a named competitor (claims file).
- A blocked choice is shown with its reason ("This computer has no TPM 2.0, which Windows 11 needs"), never hidden without explanation.
- Every card says what Beamo does **not** do in that mode (for example Keep my OS: "Beamo does not verify the system's own reset").
- Text lives in `copy.py` and the locales, with the same placeholder checks as today.

## 6. Plan record

- `{schema: "beamo-plan/1", mode, catalog_entry_id?, catalog_serial?, disks: [identity], created_monotonic}`.
- Held in memory; once the journal exists (Refs 185, 193) it may be saved, as untrusted input under N3: bound to this computer and these disk identities, expiring, and on any doubt discarded back to P1.
- A saved plan never skips Owner, Confirm, the countdown or **Erase now** (L6, L8).
- Any change of mode, system or disk set cancels downstream state (download stays cached, authorization is cleared).

## 7. Safety rules this design needs (proposed)

1. A plan never authorizes a destructive step; the existing gates run in full after it.
2. Disk choice keeps every `safety.py` rule; the plan cannot add a disk that Pick would not offer.
3. Text stays within `docs/claims.md`; new claims are added there only after verification (Ref 184 §8, Ref 207).
4. A choice the Computer check marks unavailable or blocked is never offered as available.

## 8. Tests (when built)

| Test | Kind |
|---|---|
| Each P1 answer maps to exactly one mode; Back returns without side effects | Unit (wizard model) |
| A plan with a disk not in `selectable_disks` is refused | Unit |
| Changing mode, system or disks clears authorization and downstream state | Unit |
| Saved plan from another computer, other disks, or expired is discarded to P1 | Unit (fake journal) |
| Help me choose shows only catalog/check facts; claims-file forbidden phrases absent in all locales | Unit (copy scan, existing claims tests) |
| Tk 72 DPI layout, GTK/Orca reading order, console paging for P1–P5 | Existing UI test suites |
| Full journeys per mode | QEMU (Ref 203) |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D190-1 | First question | (a) goal question (P1) for everyone; (b) start on today's erase flow with "More options" | (a), with "Just erase a disk" as the first, plainest answer |
| D190-2 | Suggest a system when the owner is unsure | (a) no suggestion, neutral list; (b) suggest one catalog entry by longest support on this computer | (b), worded as "a good starting point", never "best" |
| D190-3 | Show blocked systems | (a) list them with the reason; (b) hide them | (a) |
| D190-4 | Save the plan across a restart | (a) no; (b) yes, under N3 with expiry | (b) once Ref 193 exists; (a) before |
| D190-5 | Where comparison text comes from | (a) signed catalog `notes` plus fixed UI text; (b) fixed UI text only | (a), so the text follows the catalog without a new release |

## 10. Not done here

No code, screen, copy or test was changed, and nothing was spent. The Notion
row's full text should be checked against §3.
