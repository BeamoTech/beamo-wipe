# Design record: read-only Computer check (Notion Ref 189)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-20 by Claude (Opus 5.5) from the Notion Ref 189 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`, state 2 "Computer
> check (read-only)"), the Ref 185–188 design records and the repository at
> main `809cc11e`. The full Notion row text was not available; §3 lists the
> requirements this record assumes.
>
> **Gating.** Ref 184 places Ref 189 in Phase 1, "foundations without rule
> changes", because a read-only check needs no amended safety rule. The
> owner's standing instruction still holds: nothing after Ref 184 is built
> until Jack decides Ref 184. This record is design only.
>
> **Numbering.** "Ref 189" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. Before anything else in a journey, Beamo Wipe looks at the computer and
   says what it found: firmware type, Secure Boot, memory, disks, power,
   network hardware and the Beamo USB itself.
2. The check only reads. It never changes the computer, its firmware or any
   disk, and it never makes a disk selectable or unselectable.
3. It decides which choices make sense on this computer, for example whether
   Windows 11 can be installed. It never authorizes an erase; that still
   needs your typed confirmation, the countdown and **Erase now**.
4. If something cannot be checked, Beamo Wipe says so plainly and does not
   guess. "Cannot check" is never shown as "OK".
5. Five choices are yours (§9).

## 2. Today (facts from main `809cc11e`)

| Item | Today | Where |
|---|---|---|
| Disk discovery, boot-USB exclusion, mounted/stacked refusal | Full, fail-closed | `discover.py`, `safety.py` |
| Operating system found on a disk (Windows / other system / data / unknown) | Shown per disk, display only | `models.CONTENTS_*`, `discover.py` |
| BitLocker volume on a disk | Detected from lsblk FSTYPE, display only | `discover.py` |
| Intel VMD / RST RAID hiding the internal disk | Hint from PCI sysfs, display only | `hidden_storage.py` |
| Battery and mains power | Read-only telemetry, "never a safety gate" | `power.py` |
| Secure Boot state | Read once from the `SecureBoot` EFI variable, only to print a QEMU serial marker | `packaging/live/.../beamo-wipe-kiosk` |
| Firmware mode (UEFI or BIOS), TPM, memory, CPU, network hardware | Not read | — |
| Disk health (SMART) | Never read; `engine_checks.py` only parses nwipe's own log and must never run `smartctl` or `hdparm` | `engine_checks.py` |
| SSD and controller limits | Fixed guidance text | `storage_limits.py` |

So most disk facts already exist and are trusted for display. The check adds
a few firmware facts and turns all of them into one read-only report.

## 3. Requirements assumed (confirm against the Notion row)

- R1 Read-only: no write to any disk, firmware variable, EFI variable, TPM or device setting; no module loading.
- R2 Runs before Connect (Ref 186) and before any download (Ref 188), and again inside the readiness check (state 5).
- R3 Every item has an honest state: pass, warning, fail, unavailable or not applicable. Unavailable is never a pass (same vocabulary as `engine_checks.py`).
- R4 It never changes the disk list or any disk's eligibility; `safety.py` stays the only owner of eligibility.
- R5 Its result narrows choices (for example "Windows 11 cannot be installed here") and explains why, in plain words, in all five UI languages.
- R6 It works offline and without a network stack.
- R7 Its report holds no serial numbers or other identifiers beyond what today's result report already contains.

## 4. What the check reads

| # | Item | Read-only source | States | Used for |
|---|---|---|---|---|
| C1 | CPU is 64-bit x86 | `uname -m`, `/proc/cpuinfo` `lm` flag | pass / fail | Catalog `arch` (Ref 188) |
| C2 | Firmware mode | Presence of `/sys/firmware/efi` | UEFI / BIOS | Windows 11 needs UEFI; boot entries (Refs 196, 197) |
| C3 | Secure Boot | `SecureBoot-8be4df61-…` EFI variable, byte 4, read as the kiosk does today; `SetupMode` likewise | on / off / unavailable | Catalog `secure_boot` (Ref 188) and D3 in Ref 184 |
| C4 | TPM | `/sys/class/tpm/tpm*/` and its version file where the kernel provides one | 2.0 / 1.2 / none / unavailable | Windows 11 requirement (D189-1) |
| C5 | Memory | `/proc/meminfo` `MemTotal` | value | Catalog minimum memory per entry |
| C6 | Disks | Today's discovery result, unchanged: selectable disks, size, kind, contents, BitLocker, VMD/RAID hint | per disk | Plan; catalog minimum disk size; warnings about BitLocker and an OS that will be removed |
| C7 | Power | `power.py` reading | mains / battery % / unavailable | Readiness warning only, as today |
| C8 | Network hardware | `/sys/class/net/*` type and `wireless/` presence; USB tethering class when plugged | Ethernet / Wi-Fi / none | Which Connect options to show (Ref 186) |
| C9 | Beamo USB | Size and, once Ref 185 is built, the presence and file-system check of the state and cache areas | ok / too small / areas missing | Whether Erase and install is offered at all (Ref 185 D185-2, D185-4) |
| C10 | Boot path | Was this stick booted in UEFI or BIOS mode, from the identified boot device | value | Install target boot mode must match (Refs 196, 197) |

Not read in v1 (see D189-2): SMART or NVMe health logs, firmware passwords,
BIOS settings, vendor tools. Nothing is sent anywhere.

## 5. Result model

- One immutable record per run: `{schema: "beamo-computer-check/1", taken_monotonic, items[], offered_modes[], blocked_reasons[]}`, built only from the reads above.
- `offered_modes`: Keep my OS, Erase everything, Erase and install, with per-catalog-entry suitability (pass, warning with reason, or blocked with reason).
- A blocked reason is a fixed code plus localized text, never free text from the computer.
- The record is stale after any rediscovery, USB hotplug or resume from sleep; the readiness check (state 5) always takes a new one and compares.
- Stored only in the journal (Ref 193) once the state area exists (Ref 185); before that, in memory only.

## 6. Screens (proposal)

- **This computer** page after Plan: a short list with a status icon, words and a "What this means" line per item; no technical jargon beyond what the owner needs (for example "Secure Boot is on — Linux choices that need it off are hidden").
- Unavailable items say "Beamo could not check this" and what that changes.
- Screen reader text in GTK/Orca and the console wizard equals the Tk text.
- Shown in every mode; in Keep my OS and Erase everything it is information only.

## 7. Safety rules this design needs (proposed)

1. The check is read-only (R1). Every file is opened read-only; EFI variables are only read; no `efibootmgr`, `mokutil` changes, `tpm2_*` commands or `modprobe`.
2. It never adds, removes or reorders selectable disks and never relaxes a `safety.py` refusal.
3. It never authorizes an erase or an install; a saved check never authorizes anything after a restart (Ref 184 state table).
4. Unavailable is never a pass; a blocked item blocks only the choices that need it, never the plain erase that works today (D189-3).
5. No identifiers beyond today's report contents (R7); no TPM keys, endorsement certificates or firmware serials are read.

## 8. Tests (when built)

| Test | Kind |
|---|---|
| Each reader with fake sysfs/procfs trees: present, missing, unreadable, malformed, truncated EFI variable, unknown TPM version | Unit (temporary directories) |
| No write path: readers open with read-only flags; a fake tree marked read-only stays byte-identical | Unit |
| Disk eligibility unchanged: same discovery input gives the same selectable list with and without the check | Unit |
| Suitability table: Windows 11 entry blocked on BIOS mode, no TPM 2.0, small disk or memory; Linux entries per `secure_boot` | Unit |
| Stale check refused at readiness after a fake hotplug | Unit |
| UEFI with Secure Boot on and off, BIOS mode, with and without a virtual TPM (`swtpm`) | QEMU (Ref 203) |
| Real PCs | Physical (Ref 208), Jack's authorization |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D189-1 | Windows 11 hardware requirements | (a) block the Windows 11 choice when UEFI, Secure Boot capability, TPM 2.0, 4 GB memory or 64 GB disk is missing; (b) warn only | (a), with the reason shown; the plain erase stays available. The CPU-model list is Microsoft's and is not checked offline, so the check says so |
| D189-2 | Disk health | (a) none in v1, as today; (b) read-only `smartctl -H` / NVMe health log shown as information | (a) in v1; (b) needs its own review because it adds a tool the project rules exclude today |
| D189-3 | When the check cannot read an item | (a) block only the choices that need it; (b) stop the journey | (a) |
| D189-4 | Show the check in Keep my OS and Erase everything | Yes, information only / no | Yes, information only |
| D189-5 | Store the check in the report (Ref 200) | Yes, item states only / no | Yes, item states only, no identifiers |

## 10. Not done here

No code, screen, test or image change was made, and nothing was spent. The
Notion row's full text should be checked against §3.
