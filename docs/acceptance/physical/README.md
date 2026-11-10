# Physical acceptance packet (#116)

**Status (2026-11-10):** ready for a human run. **Nothing in it has run.**
Every row is **NOT TESTED**. No physical result exists for any computer,
disk, port, panel or speaker.

This packet is the plan, the steps and the blank forms for testing Beamo Wipe
on real hardware. It builds on [physical acceptance #111](../../evidence/physical-acceptance-111/README.md),
which stays the home of its own rows and of the photo and log folders.

## Packet files

| File | What it is |
| --- | --- |
| [matrix.md](matrix.md) | 121 rows, each with ID, area, hardware, procedure, expected result, evidence, status and the virtual evidence that does not count |
| [matrix.csv](matrix.csv) | The same rows for a spreadsheet |
| [procedures.md](procedures.md) | Numbered steps P0 to P14 for a technician |
| [forms/machine-intake.md](forms/machine-intake.md) | One per computer |
| [forms/test-run-record.md](forms/test-run-record.md) | One per run |
| [forms/cold-readback.md](forms/cold-readback.md) | One per erased disk |
| [forms/sign-off.md](forms/sign-off.md) | One per session |

## Purpose and scope

The packet answers one question: does this exact image do what we say on
these exact computers and disks? It covers:

- Starting from the Beamo USB in UEFI with Secure Boot, UEFI without it,
  and legacy BIOS, on Dell, HP, Lenovo, ASUS, Acer, MSI and Gigabyte
  computers, with each brand's boot-menu key (#184).
- The disk list for SATA hard disks, SATA SSDs, NVMe, USB enclosures, eMMC,
  many disks, and disks hidden by Intel VMD or RST (#185).
- The Beamo USB is never selectable, and no disk is selectable when the
  Beamo USB cannot be identified.
- Each erase method, its result screen and its report, followed by a cold
  readback of the erased disk.
- Saving a report to FAT32 and exFAT sticks (#135) and when each USB may
  be removed.
- Interruptions: USB pulled, power cut, battery, lid and power button.
- The Windows launcher on Windows 10 and 11, with SmartScreen (not
  code-signed) and Restart to boot options (#183); the Linux launcher.
- Orca on real speakers, the finish sound (#133), High contrast (#179),
  small and HiDPI panels, real graphics, keyboard layouts and kiosk recovery.
- Readback of manufactured sticks.

Out of scope: Apple Silicon, Chromebooks, braille displays, and any change
to keys, Secure Boot or firmware trust. The SSD firmware erase in
[decision record #186](../../decisions/ssd-firmware-erase.md) is not built,
so it has no rows.

## Who runs it

A technician who can follow numbered steps. They do not need to code. A
second person reviews the records. The owner (Jack) authorizes erases and
decides what is claimed.

Development hosts never run it. That includes the owner's unattended Windows
computer, which must not restart and must keep its USBs connected
([remote-only development](../../remote-development.md)).

## Prerequisites

### Equipment

- Spare x64 computers. At least one per brand you will claim. At least one
  laptop with a battery and a lid, one desktop, one in each firmware mode.
- Windows 10 and Windows 11 installed on lab computers, each with a
  standard and an administrator account. One Linux desktop.
- Sacrificial USB sticks: one or more for the Beamo USB, one FAT32, one
  exFAT, one NTFS and one spare for reports.
- `DISPOSABLE` disks: a SATA hard disk, a SATA SSD, an NVMe SSD, and a disk
  in a USB-SATA or USB-NVMe enclosure. Label each one on its case.
- A separate Linux QA workstation, with automount turned off, for seeding
  and cold readback.
- A phone camera, speakers or headphones, an external monitor, keyboards
  with different printed layouts, a 1024×600 panel and a HiDPI panel if
  those claims matter.

**Never use a valuable disk.** Remove or disconnect every disk you would
miss. Never use a customer's computer.

### The image

1. Use one release image named by the owner for the session. Today the UI
   work from PR #94 (#127 to #187) is not in tag `v0.2.14`. Rows that test
   it (#133, #135, #179, #183, #184, #185, #187) need a later qualified
   release image. Until one exists, those rows are BLOCKED.
2. Get it from the published, signed GitHub release. Verify it as in
   [release verification](../../release-verification.md#usb-image-download-verification).
   Never use a CI artifact, a draft, a local build or a re-compressed copy.
3. Record in [BUILD-IDENTITY](../../evidence/physical-acceptance-111/BUILD-IDENTITY.md):
   version and tag, source commit, image file name, byte size and SHA-256,
   manifest SHA-256, signature check result, and the Secure Boot component
   receipt for this image (or "none").
4. Flash it to a spare stick, then do the
   [post-flash readback](../../evidence/physical-acceptance-111/README.md#post-flash-readback).
   A manufactured stick from a lot with a `RESULT: PASS` receipt
   ([manufacturing §4](../../manufacturing.md#4-readback-qa-first-article-and-sampling))
   also qualifies. Re-run readback after any reflash.

## Safety rules

These come from the project's safety boundaries in `AGENTS.md`. The lab
never relaxes them.

- Erasing is done only by the pinned `nwipe` v0.42 inside the wizard. Never
  run `nwipe`, `dd`, `hdparm`, `nvme` or a format tool against a test disk
  except the P5 seeding on the QA workstation.
- The Beamo USB must never be selectable. If it cannot be identified, no
  disk may be selectable. Either failure: stop and record Fail.
- An erase needs the ownership box, the typed confirmation, the
  five-second countdown and **Erase now**. Nothing starts by itself.
- No password reset, BitLocker key extraction or Secure Boot workaround.
  Do not enroll keys or change revocations, validation or Secure Boot.
- Destructive rows need written authorization and a `DISPOSABLE` target.
- Make no "certified", "DoD", "plug and play", Apple Silicon or
  Chromebook claim from any result ([claims](../../claims.md)).

## Evidence tiers: virtual never fills a physical row

[Evidence tiers](../../evidence-tiers.md) defines three tiers. Every row in
this packet is Tier 3: a named physical computer, a named disk and a
recorded image SHA-256.

QEMU, OVMF, SeaBIOS, any virtual machine, the USB simulation lab, GCP
desktop VMs, Xvfb screenshots, `./preview`, fixture tests and hosted CI are
Tier 1 or Tier 2. They are listed in the last matrix column so nobody runs
them again by mistake. They never fill a Status cell. The packet guards this
three ways:

1. Every row starts NOT TESTED.
2. A Pass, Fail or Unknown row must name a run ID and an evidence file. The
   run record asks "Physical hardware?" and the answer must be Yes.
3. `tests/test_physical_acceptance_116.py` fails if a Pass row has no run
   ID or evidence file, or if its evidence names QEMU, OVMF, SeaBIOS, a VM,
   Xvfb, the preview or CI.

## Result words

These are the #111 result words ([#111 §2](../../evidence/physical-acceptance-111/README.md#2-result-markers)).
They mean the same here.

| Word | Meaning |
| --- | --- |
| **Pass** | On the named computer, with the recorded image, the expected result happened. Evidence is filed. |
| **Fail** | The expected result did not happen. Evidence and what you saw are filed. |
| **Excluded** | This computer cannot run the row (no touchpad, no battery, no BIOS mode …). The reason is filed. |
| **NOT TESTED** | Nobody has run this row. The default. |
| **BLOCKED** | Cannot run until something named exists: hardware, an image, an inspection or an authorization. |
| **Unknown** | Something was seen, but a required fact (for example Secure Boot databases) could not be read. Never a Pass. |

A safe refusal is a Pass only for a row whose expected result is that refusal.

## Order of work

1. P0: identity, readback, intake, run record.
2. P13: manufacturing readback, if a produced lot is in scope.
3. P1, P2: launchers on Windows and Linux (no erase; may restart Windows).
4. P3: firmware boot per brand and mode (no erase).
5. P4: disk list and Beamo USB protection (no erase).
6. P10, P11: accessibility, sound, display and layouts, as far as the
   review screen (no erase). Sound rows that need a result wait for step 8.
7. #111 rows for monitors, ports, USB, keyboards, touchpads, audio and power.
8. P5, P6, P7, P8: seed, erase, cold readback, report. One disk at a time.
9. P9: interruptions during an erase, last, because they leave disks
   partly erased.
10. P12: kiosk recovery, whenever it appears by itself.
11. P14: sign-off.

Rows that do not erase come first. That way a mistake costs the least.

## Filing results

- **Forms:** put filled forms in `docs/evidence/physical-acceptance-116/<UTC date>/`
  (create it when you file). Names: `intake-<machine ID>.md`,
  `run-<run ID>.md`, `cold-<row ID>-<run ID>.md`, `signoff-<UTC date>.md`.
- **Photos and logs:** use the #111 folders
  [photos](../../evidence/physical-acceptance-111/photos/README.md) and
  [logs](../../evidence/physical-acceptance-111/logs/README.md). Name each
  file `<row ID>-<what>-<UTC time>.<ext>`, for example
  `PHY-DELL-02-beamo-menu-20270115T101500Z.jpg`.
- **Large or private files:** recordings, unredacted photos and full
  serials go to the private evidence store the owner names. Git holds only
  their file names and SHA-256.
- **Hashes:** every evidence file gets a SHA-256 in its run record.
  Linux `sha256sum`, macOS `shasum -a 256`, Windows
  `Get-FileHash -Algorithm SHA256`.
- **Matrix:** change Status in both `matrix.md` and `matrix.csv`, and add
  the run ID and file names (see [How to fill a row](matrix.md#how-to-fill-a-row)).
  Record #111 rows in the #111 sheets.
- **Redaction:** serials as last 4 characters only. No customer data, keys,
  passwords, account names or file names from a disk, ever.
- **Git:** stage explicit paths only. Never commit an image, a disk dump or a
  secret.
- **Sign-off:** the operator, a reviewer who is not the operator, and the
  owner sign [the sign-off sheet](forms/sign-off.md). #116 stays open until
  the owner accepts the results.

## Stays BLOCKED until a human runs it with hardware

All of the following remain NOT TESTED or BLOCKED today:

- Every row in this matrix (121) and every row in the #111 sheets.
- Physical Secure Boot acceptance and refusal on any firmware; for images
  after 0.2.14 also the new component inspection (SB-INSPECTION).
- The boot-menu key for each brand on a real model (#184).
- Restart to boot options on real Windows 10 and 11, the "EFI USB Device"
  name, BitLocker prompts, a vetoed restart and a removed shut down right
  (#183). SmartScreen on the unsigned launcher.
- Disk discovery on real SATA, NVMe, USB enclosure and eMMC controllers, and
  the VMD/RST hint on real hardware (#185).
- Any erase of a physical disk, any cold readback, and any report saved to a
  real FAT32 or exFAT stick (#135).
- USB pulled, power cut, battery, lid and power-button behaviour during an
  erase; the screen staying lit (#168).
- Orca and the finish sound on real speakers (#133); High contrast and text
  size on real panels (#179); 1024×600 and HiDPI panels; troubleshoot
  startup on real Intel, AMD and NVIDIA graphics.
- Physical keyboard layouts and kiosk recovery on a real console.
- Manufacturing readback and boot QA of a real produced stick.
- A release image that contains the PR #94 UI work.

## Related pages

| Page | Role here |
| --- | --- |
| [#111 physical acceptance](../../evidence/physical-acceptance-111/README.md) | Canonical safety steps, post-flash readback, result words, and the PHY-FW/MON/PORT/USB/KB/TP/AUD/PWR/DESK/DEST rows |
| [Desktop hardware acceptance](../../desktop-hardware-acceptance.md) | Launcher cases; tracked as #111 PHY-DESK |
| [Secure Boot acceptance](../../secure-boot-acceptance.md) | The SB cases used by every `-03` firmware row |
| [Compatibility matrix](../../compatibility-matrix.md) | What we intend to support; fixture and QEMU rows only |
| [Evidence tiers](../../evidence-tiers.md) | Why virtual results never count here |
| [Manufacturing](../../manufacturing.md) | Stick readback and boot QA (P13) |
| [Boot-menu keys](../../boot-keys.md) and [Restart to boot options](../../restart-boot-options.md) | #184 and #183 design |
| [Storage limits](../../storage-and-controller-limits.md) | What an erase and a readback cannot prove; VMD/RST |
| [Live-session power](../../live-session-power.md), [Kiosk recovery](../../kiosk-recovery.md), [Screen reader](../../screen-reader.md) | Behaviour the P9, P12 and P10 rows check |
| [QEMU verification](../../qemu-verify.md) | What the virtual gate covers, and what it does not |
| [Runbook](../../runbook.md) | Support steps when a row fails in the field |
