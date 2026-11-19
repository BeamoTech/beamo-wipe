# Design record: 16 GB Beamo USB layout for system, OS cache and journey state (Notion Ref 185)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-19 by Claude (Opus 5.5) from the Notion Ref 185 title and the
> repository at main `62cdd345`. The full Notion row text was not available;
> where this record assumes a requirement, it says so.
>
> **Depends on Jack's Ref 184 decisions.** Any runtime write to the boot USB
> needs the **proposed L3 amendment** in the Ref 184 record
> (`docs/decisions/three-mode-architecture.md`, merged in #128 as a proposal), which is not adopted. Until
> Jack approves it, the shipped rule stands: Beamo Wipe never writes to the
> boot USB, and nothing in this record may be built.
>
> **Numbering.** "Ref 185" is the Notion row. The repository's older `#185`
> (VMD/RST hint) is a different item.

## 1. Summary for the owner (plain English)

1. Today the stick holds one 2 GiB FAT32 partition with the system. The rest of
   a 16 GB stick is empty and unused.
2. "Erase and install" needs room on the stick for a downloaded operating
   system (several GB), and the multi-restart journey needs a small, safe place
   to remember where it is.
3. Proposal: keep the system partition **exactly as it is**, and add two
   partitions behind it at manufacture: a small **journey state** area and a
   large **OS cache**. Beamo Wipe would never change the partition table while
   running.
4. Four choices are yours (§8). The biggest one is D185-1: every stick written
   from the download would then take a 16 GB write instead of a 2 GB write.

## 2. Today (facts from main `62cdd345`)

| Item | Today | Where |
|---|---|---|
| Partition table | MBR; one active entry, type `0x0C`, starting at sector 2048 | `scripts/build-usb-image.sh` |
| System partition | FAT32, label `BEAMO_WIPE`, 2 GiB − 1 MiB; whole image 2 GiB | same |
| Build guard | Readback refuses any second MBR entry (`any(mbr[462:510])`) | same |
| Release metadata | `img.json` schema 2 (per-file list, Ref 183); `layout`: "MBR, one active FAT32 partition at sector 2048" | builder, publisher, `verify-usb-download.py` |
| Live boot | `boot=live … nopersistence noswap` | `packaging/live/inside-docker.sh` |
| Boot-USB identity | Live mounts (`/run/live/medium`, …) resolved to the **parent disk**; the whole disk and every partition on it are hidden | `discover.identify_boot_path`, `should_hide` |
| Writes to the stick at runtime | None. Logs stay under `/tmp/beamo-wipe/`; the report goes to a separate USB | AGENTS.md safety boundaries |
| Manufacturing | Stick capacity must be ≥ the raw `.img` size; readback compares image bytes only | `docs/manufacturing.md` §2 |
| Stick check (Ref 183) | Verifies every file on the FAT32 system partition against the signed list | `scripts/check-beamo-stick.py` |

## 3. Requirements assumed (confirm against the Notion row)

- R1 The system partition stays verifiable file for file (Ref 183) and is never written at runtime.
- R2 One OS download (Windows 11 or a Linux ISO, Ref 188) fits in the cache with room for a partial resume.
- R3 Journey state (Ref 193) survives power loss mid-write and restart.
- R4 Stick check, boot on BIOS and UEFI, and Windows/macOS behaviour stay as they are for the system partition.
- R5 No runtime change to the partition table or system area (proposed L3).
- R6 Saved state is untrusted input (proposed N3) and never contains serials or secrets (L15).

## 4. Proposed layout (MBR, 512-byte sectors, 1 MiB aligned)

| # | Label | File system | MBR type | Start | Size | Holds | Written at runtime? |
|---|---|---|---|---|---|---|---|
| 1 | `BEAMO_WIPE` | FAT32 | `0x0C`, active | 1 MiB | 2047 MiB (unchanged) | System, as today | **Never** |
| 2 | `BEAMO_STATE` | ext4, `data=journal` | `0x83` | 2048 MiB | 256 MiB | Journey journal (Ref 193), catalog metadata (Ref 188), reports if D6 allows | Yes, files only |
| 3 | `BEAMO_CACHE` | ext4 | `0x83` | 2304 MiB | to 14 000 MiB end (≈ 11 696 MiB) | One OS download plus its partial file | Yes, files only |

- **Why MBR stays.** BIOS boot uses Syslinux MBR code; moving to GPT would
  change the boot chain on every firmware and is not needed for 3 partitions.
- **Why separate partitions, not folders on FAT32.** FAT32 cannot hold files
  over 4 GiB (Windows images can exceed it), has no journal, and writing to the
  system partition would break the Ref 183 stick check and R1.
- **Why ext4 with type `0x83`.** It is journaled. Windows and macOS do not
  normally mount type `0x83`, so customers do not see an "unreadable disk"
  drive. *To confirm on real Windows 10/11 and macOS (physical rows, Ref 208).*
- **Why a fixed end at 14 000 MiB (≈ 14.68 GB).** "16 GB" sticks vary in real
  size. The layout must fit the smallest qualified stick; the slack beyond it
  stays unused. The exact minimum is D185-2.
- **Reproducible build.** The ext4 file systems are created empty at build time
  with fixed UUIDs, fixed hash seed and fixed timestamps, and with
  `lazy_itable_init=0,lazy_journal_init=0` so the kernel does no background
  initialisation writes later. The release `sha256` stays deterministic.

## 5. Safety rules this design needs (proposed, for Jack)

1. **Find state and cache only through the boot disk.** Use them only when
   they are partitions 2 and 3 of the disk `identify_boot_path` already
   identified, with the expected PARTUUIDs and types. **Never mount by label**:
   an internal disk could carry a `BEAMO_CACHE` label. If anything does not
   match, the areas are unavailable; erase still works, install is offered
   only if D185-4 allows recovery.
2. **The boot disk stays hidden as a whole.** No change to `should_hide`; the
   new partitions inherit the existing protection. Tests must prove a 3-partition
   boot USB still yields exactly one hidden boot disk and no selectable part of it.
3. **Mount narrowly.** `nosuid,nodev,noexec`; the state area `data=journal`;
   mount points under `/run/beamo/`; unmount before restart.
4. **Write narrowly.** New files with fsync then atomic rename; cache downloads
   to `*.partial`, verified against the signed catalog before use (Ref 188);
   free-space check before starting.
5. **Untrusted on read (N3).** Every journal record has a checksum, the journey
   ID, machine and disk identities and an expiry; any doubt discards it back to
   Plan. A journal never authorizes an erase (L8).
6. **No secrets, no serials** in state or cache (L15).
7. **Degrade, never redirect.** If state or cache is missing, full or corrupt,
   Beamo Wipe never falls back to writing on an internal disk or another USB.

## 6. What changes where (when approved)

| Area | Change | Tests |
|---|---|---|
| `scripts/build-usb-image.sh` | Build partitions 2 and 3; image grows to 14 000 MiB; readback guard accepts exactly these entries | Fixture build tests; MBR entry tests; reproducibility test |
| `img.json`, publisher, `verify-usb-download.py` | New `layout` value; list partitions with offsets and sizes; schema bump | Publisher and verifier schema tests |
| Stick check (Ref 183) | Still checks partition 1 only; says so in its output | Stick check tests |
| `discover.py` | No change to boot identification; new read-only helper resolving partitions 2/3 of the identified boot disk | Fixtures with 3-partition boot USB, look-alike labels on internal disks |
| New state/cache module | Mount, journal, cache I/O as §5 | Power-loss and corruption fixtures on regular files only |
| `docs/manufacturing.md` | Capacity rule uses the new image size; qualification adds a minimum byte count | — |
| QEMU gate | Boot the 3-partition image on BIOS and UEFI | Hosted gate (final candidate only) |
| Physical (Ref 208) | Windows/macOS insertion behaviour; firmware boot with extra partitions | Physical rows, Jack's authorization |

## 7. Risks

| Risk | Mitigation |
|---|---|
| 16 GB write when people flash from the download (≈ 10–25 min on USB 3) | D185-1; publish a block map so `bmaptool` users write only used blocks |
| Some firmware lists or boots oddly with extra partitions | Physical rows before release (Ref 208) |
| Customer formats a partition in Windows Disk Management | Areas fail checks → unavailable; recovery per D185-4 |
| Flash wear from journal writes | Small, infrequent journal writes; downloads written once |
| Power loss mid-download | `*.partial` + resume + signed hash check |

## 8. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D185-1 | Which images carry the full layout? | (a) one full-layout image for everyone; (b) full layout for Beamo-sold sticks only, keep the 2 GiB download image without install; (c) runtime "prepare this stick" | (a), with a block map. (c) is rejected: it changes the partition table at runtime (proposed L3) |
| D185-2 | Minimum qualified stick size | 14 000 MiB layout end (this draft) or another value from supplier samples | Measure 5 samples per supplier; keep ≥ 2 % margin |
| D185-3 | Cache size split | One OS at a time (this draft) or two | One at a time |
| D185-4 | If a state or cache area fails its check | (a) unavailable until re-flash; (b) Beamo Wipe may re-create the file system **inside that partition only**, after a clear prompt | (b), never touching the partition table or partition 1 |
| Ref 184 L3 | Approve the amended L3 wording | — | Required before any build work |
| Ref 184 D6 | May reports be stored in the state area? | — | Opt-in only, no serials |

## 9. Not done here

No code, image, partition, mount or write was made. No physical stick was
read or written. The Notion row's full text should be checked against §3.
