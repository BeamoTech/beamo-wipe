# Decision record: three-mode architecture and amended safety model (Notion Ref 184)

> **Status: PROPOSAL — owner decisions required (Jack).** Prepared 2026-11-19 by
> Claude (Opus 5.5) from the Notion Ref 184 record and the current repository.
> Jack's 2026-11-19 directive approves *preparing* this record. It does **not**
> adopt any amended safety rule. Until Jack decides §6 and approves §4, every
> rule in `AGENTS.md` and `docs/claims.md` stays exactly as it is, and no
> implementation that depends on a changed rule starts.
>
> **Numbering.** "Ref N" is the Notion row. The repository's older backlog uses
> `#183`–`#187` for different items (`#183` Restart to boot options, `#184`
> boot-menu keys). Commits and PRs for this batch say "Notion Ref N".

## 1. Summary for the owner (plain English)

1. Beamo Wipe gains three modes: **Keep my OS**, **Erase everything including
   the OS**, and **Erase and install a new OS**.
2. For a new OS, Beamo Wipe connects to the internet, downloads the new system
   to the 16 GB Beamo USB, and checks it **before** anything is erased. Only then
   does it erase, check the erase, install, and start the new system.
3. Erasing stays exactly as safe as today: pinned nwipe, one disk at a time, your
   typed confirmation, the countdown and **Erase now**. Nothing destructive ever
   happens by itself, including after a restart.
4. Some of today's rules must change to allow this: Beamo would write to its
   own USB (in a reserved area), use the network, and install a system after an
   erase. §4 lists every rule and the exact proposed wording. You approve or reject each.
5. Eleven product choices are yours (§6). Each has a recommendation.

## 2. The modes

| Mode | Sub-options | Promise to the user (proposed) | Never |
|---|---|---|---|
| **Keep my OS** (Ref 192) | (a) Guide to the OS's own reset ("native reset"); (b) erase *other* internal disks only; (c) nothing destructive, check and report only | "We help you use your system's own reset. We do not verify it, and it is not the same as a verified wipe." | Write to the OS disk; call a native reset "verified" |
| **Erase everything including the OS** (today's product + Ref 191) | One disk; every internal disk in one session; optional backup first (Ref 198) | "Each listed disk is overwritten by nwipe; the report says exactly which disks were verified." | Erase the Beamo USB or the backup disk; erase without the full gates |
| **Erase and install a new OS** (Refs 188, 194–197) | Linux (supported distributions); Windows 11 (owner decision D1/D2) | "We erase and verify first, then install the system we downloaded and checked." | Erase before the new OS is downloaded and verified; install after a failed or stopped erase |

**Trust boundaries.** Trusted: the signed Beamo release, the pinned nwipe, the
pinned Beamo catalog key, the person at the keyboard. Untrusted: the network,
downloaded payloads until verified, the journal and any saved state, the
computer's existing disks and firmware, any file on a non-Beamo USB.

**Failure states (every mode).** Each failure stops at a screen with *What
happened / What it means for your disk / What to do next*, keeps the computer
in a safe state, and never continues to a destructive step by itself.

## 3. End-to-end order and state machine (Erase and install)

Required order (Ref 184 record): **plan → Computer check → connect → download
and verify → readiness check → final authorization → erase → verified-outcome
gate → install → first boot → report.** Do not erase before the replacement OS is verified and available.

| # | State | Writes | Leaves on success | On failure / interruption | Restart point |
|---|---|---|---|---|---|
| 1 | Plan (goal, OS, disks) | Journal (USB state area) | 2 | Back to plan | Plan, nothing authorized |
| 2 | Computer check (read-only, Ref 189) | Journal | 3 | Report "cannot check", stop | Plan |
| 3 | Connect (off by default, Ref 186) | None (no secrets saved by default) | 4 | Offline options (Ref 204 staged media) | Plan |
| 4 | Download and verify (Ref 188) | OS cache on USB | 5 | Resume download; corrupt → delete and re-fetch | Resume download (non-destructive) |
| 5 | Readiness check (power, disks unchanged, payload verified, space) | Journal | 6 | Explain, stop | Readiness |
| 6 | Final authorization (owner box, token, 5 s, **Erase now**) | Journal records the decision for the report only | 7 | Back | **Plan — a saved decision never authorizes** |
| 7 | Erase (pinned nwipe, one disk at a time) | Target disk (nwipe only) | 8 | "Not finished", stop | **Plan; erase never resumes** |
| 8 | Verified-outcome gate (method verified, rediscovery matches) | Journal | 9 | Report; no install | Report |
| 9 | Install (pinned installer, same disk) | Target disk (installer only) | 10 | Report "install not finished"; offer a fresh **Install now** decision (D11) | Install, only after rediscovery and a fresh decision |
| 10 | First boot into new OS (Refs 196, 197) | New OS | 11 | Guidance; Beamo USB can re-check | Report |
| 11 | Report (Ref 200) | Report to chosen place (D6) | Done | — | — |

## 4. Safety laws: unchanged, amended, new

Source: the record's baseline rules (Common prompts) and `AGENTS.md`.
"Proposed wording" is offered for approval; nothing changes until approved.

| # | Current law | Class | Proposed wording / note |
|---|---|---|---|
| L1 | Pinned nwipe v0.42 at `/usr/lib/beamo-wipe/nwipe` on Debian bookworm; no custom engine or rename | **Unchanged** | — |
| L2 | No claims beyond `docs/claims.md` | **Unchanged** | Claim drafts in §8 need approval first |
| L3 | Never erase, partition or install onto the boot USB | **Amended** | "Never erase, partition, format or install onto the boot USB, and never offer it as a target. Beamo Wipe may write files **only** inside its own reserved journey-state and OS-cache file systems on the boot USB, created at manufacture (Ref 185). It never changes the USB's partition table or system area at runtime." |
| L4 | Uncertain boot identity → no targets | **Unchanged**, extended | Also: no install target and no backup destination while boot identity is uncertain |
| L5 | Only whole `/dev` disks; `BEAMO_WIPE_BOOT_DEVICE` test-only | **Unchanged** | — |
| L6 | `owner_ok`, exact token, 5 s review countdown, separate **Erase now** | **Amended** (multi-disk) | "One review screen lists every disk to be erased (model, size, last four of the serial). The owner box, the exact token, the five-second countdown and **Erase now** cover that exact set. Any change to the set cancels the authorization." |
| L7 | Rediscover before every destructive write; reject serial, size, WWN or path changes | **Unchanged**, extended | Also before every installer write |
| L8 | Journal/profile/answer file is never authorization; nothing destructive on boot | **Unchanged** | Resume may continue only non-destructive steps |
| L9 | One nwipe process and one target at a time; `--autonuke` with `--exclude=` the boot device; never `--force` | **Unchanged** | Multi-disk runs are sequential |
| L10 | Methods prng with final verification, dodshort, zero (never verified); exit 0 or 100 % alone is not success | **Unchanged** | See D11 for install after unverified methods |
| L11 | Install only after a successful erase and revalidation in the same journey; never after failure or stop without a separate explicit decision | **Unchanged** | — |
| L12 | No password, SAM or BitLocker work; no Secure Boot, TPM or Windows 11 requirement bypass; no license keys | **Unchanged** | — |
| L13 | Authoritative sources with pinned keys or hashes | **Unchanged** | — |
| L14 | Network off until needed; full erase works offline; no inbound services, telemetry or accounts; no plaintext secrets on USB | **Unchanged** | D7 (Wi‑Fi carry-over) must fit it |
| L15 | Logs never on a target; failure text format; support only beamosupport.com and `BW-{S\|R\|E\|X\|U}-TOKEN` without serials | **Unchanged** | D6 decides report storage |
| L16 | Tk at 72 DPI; GTK/Orca and curses in parity | **Unchanged** | Every new screen in all three |
| L17 | Preview, `--web`, helper pages, Go launchers and recovery menu never erase or install | **Unchanged** | — |
| L18 | No bump of nwipe, PRIOR_STABLE, Go, Debian base or claims without approval | **Unchanged** | Note: the record says Go 1.26.8; main pins go1.26.11 (merged #101, security fix). Confirm the record's copy is stale |
| N1 | — | **New** | "In Erase and install, the replacement OS must be downloaded and verified against the signed catalog **before** the final authorization screen is shown." |
| N2 | — | **New** | "The backup destination (Ref 198) is protected like the boot USB for the whole session: never a target, read-only source, written only by the backup step." |
| N3 | — | **New** | "Saved state (journal, catalog cache, downloads) is untrusted input: integrity-checked, bound to this computer and these disks, expired after a set time, and on any doubt discarded back to Plan." |
| N4 | — | **New** | "Answer files and first-boot scripts are generated in memory, contain no plaintext secrets, and are written only to the installed disk during state 9." |
| N5 | — | **New** | "No self-update, catalog update or download is applied during states 6–9." |

## 5. Threat model

| Threat | Example | Defence (proposed) | Failure behaviour |
|---|---|---|---|
| Network | Rogue Wi‑Fi, captive portal, MITM | TLS + signed catalog + pinned payload hashes; no inbound services; firewall default-deny | Stop download; offline options |
| Signed catalog | Rollback to an old catalog, freeze, key compromise | Monotonic catalog version and expiry; key rotation/revocation like release keys | Refuse; keep last good; report |
| Payloads | Tampered or wrong-edition ISO, truncated download | Hash pinned in signed catalog; size check; resume with re-verify | Delete and re-fetch; never install unverified |
| Journal | Stale, crafted, or from another computer (stick moved) | N3: bound to machine and disk identities, integrity-checked, expiring; never authorization (L8) | Discard to Plan |
| Answer files | Injection via names, secrets left on disk | N4; strict escaping; no secrets | Abort install, report |
| Secrets | Wi‑Fi passwords, user passwords | Not stored by default (L14, D7) | — |
| Malicious/stale state on target disks | Old OS, hidden partitions, RAID/VMD | Computer check reports; whole-disk targets only (L5) | Explain limits |
| Modified Beamo USB | Edited files, swapped image | Ref 183 stick check (verify on a trusted computer); Secure Boot where enabled | Stop; recovery = re-flash verified image |

## 6. Owner decisions (Jack) — none adopted

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Windows acquisition | (a) Beamo downloads from Microsoft's official site at run time and verifies against a hash Beamo publishes in the signed catalog; (b) the user supplies an official ISO, verified the same way; (c) not offered | (a) with (b) as fallback; never redistribute Windows media; no keys |
| D2 | Windows 10 availability | Offer / do not offer | **Do not offer** (outside mainstream support since 2025-10-14) |
| D3 | Arch Linux with Secure Boot | Offer only with SB off / not offer | Do not offer while Secure Boot is on (no bypass, L12); decide later |
| D4 | Native reset in Keep my OS | Guide only / not offered | Guide only, clearly "not verified" |
| D5 | Firmware sanitize | Keep Option A / evaluate (Ref 201) | Keep Option A; Ref 201 evaluates only |
| D6 | USB report storage | `/tmp` + separate USB only (today) / also the Beamo USB state area | Allow the state area, opt-in, no serials |
| D7 | Wi‑Fi carry-over to the new OS | Never / with explicit consent | Never by default; consent only, never stored on the USB in plaintext |
| D8 | New-owner default | Leave at first-run setup / create a user | Leave at the new OS's first-run setup (new owner sets it up) |
| D9 | Self-update | None / signed manual / signed automatic | Signed, manual, never during a journey (N5) |
| D10 | Telemetry | None / opt-in | **None** (default) |
| D11 | Install after an unverified method (zero) or after a restart between erase and install | Allow with a fresh decision / never | Install only after a verified method; after a restart only with rediscovery and a fresh **Install now** |

## 7. Dependencies and phased rollout

| Phase | Refs | Needs |
|---|---|---|
| 0 Decide | 184 | Jack: §4 approvals and §6 decisions |
| 1 Foundations without rule changes | 183, 189, 201, 203 (harness), 202 (budget study) | — |
| 2 Medium and network | 185, 186, 187, 188, 204, 206 | L3 amendment (185); D9 (206) |
| 3 Start and erase | 190, 191, 198, 199 | L6 amendment (191), N2 (198) |
| 4 Install | 192, 193, 194, 195, 196, 197 | N1, N3, N4, N5, D1–D4, D7, D8, D11 |
| 5 Evidence and release | 200, 202, 203, 207, 208 | D6, D10; physical authorization (208) |

## 8. Proposed amendments to approve (drafts only)

- **`docs/claims.md`**: add only after each feature is verified — e.g. "Can install
  a fresh copy of <supported Linux> or Windows 11 after a verified erase (internet
  or a USB prepared beforehand)." Keep every existing prohibition.
- **Architecture guide**: add this record as `docs/decisions/three-mode-architecture.md` (this file) and link it from `AGENTS.md` once approved.
- **Common prompts (Notion)**: replace L3 and L6 with the §4 wording and add N1–N5,
  only after approval. The agent cannot edit Notion.

## 9. Related records

- **USB Easy Use — "Research a separate choose-your-OS Beamo product"**: that is a
  separate product line. This record keeps the integrated direction inside
  Beamo Wipe and changes nothing in USB Easy Use or the Companion. Sharing a
  catalog later would be a separate owner decision.
- `docs/decisions/ssd-firmware-erase.md` (Option A) stays in force.
- `docs/decisions/usb-copy-tamper-protection.md` (Notion Ref 183, merged in #127):
  the signed per-file stick check covers the system partition only; any new
  writable areas on the USB (Ref 185) must stay outside it.
