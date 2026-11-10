# Physical test procedures (#116)

These steps are for a technician at a real computer. They are not for a
developer shell or a virtual machine. Read the [packet README](README.md)
first. Each section names the matrix rows it covers.

Some topics already have one canonical procedure. This page links to it and
adds only what is missing. Do not copy steps from here into another page.

Quoted text in `code style` is the exact English text on the screen, taken
from `src/beamo_wipe/copy.py`, `outcomes.py`, `recovery.py`, `power.py` and
the launcher. If you run in another language, record the language and what
you saw. The French, German, Spanish and Italian texts are drafts.

**Stop rule for every section.** Stop and record the row as Fail or BLOCKED
when any of these happens:

- The Beamo USB is shown as a disk you can select.
- A disk you did not mean to test is connected and could be selected.
- An erase starts without you choosing **Erase now**.
- You are unsure which disk is which.
- A step would change keys, Secure Boot, firmware trust or a valuable disk.

Never continue past a stop to "see what happens".

## P0. Before every session

1. Follow [#111 §5.1](../../evidence/physical-acceptance-111/README.md#51-before-you-touch-a-computer).
   Use a spare x64 computer. Disconnect every valuable disk.
2. Fill [BUILD-IDENTITY](../../evidence/physical-acceptance-111/BUILD-IDENTITY.md)
   for the image. Verify the download as in
   [release verification](../../release-verification.md#usb-image-download-verification).
3. Flash a spare USB stick. Then do the
   [post-flash readback](../../evidence/physical-acceptance-111/README.md#post-flash-readback)
   (row PHY-MFG-01). Without `READBACK MATCH`, stop. Every boot row is BLOCKED.
4. Fill one [machine intake form](forms/machine-intake.md) per computer.
5. Start a [test run record](forms/test-run-record.md). Give it a run ID:
   `RUN-<UTC date>-<two digits>`, for example `RUN-20270115-01`.
6. Photograph each screen you judge. Name files as in
   [#111 photos](../../evidence/physical-acceptance-111/photos/README.md):
   `<row ID>-<what>-<UTC time>.jpg`.

## P1. Windows launcher

Rows: PHY-WIN-01 to PHY-WIN-12. The canonical design pages are
[Restart to boot options (#183)](../../restart-boot-options.md) and
[boot-menu keys (#184)](../../boot-keys.md). Common launcher cases stay in
[#111 desktop launch](../../evidence/physical-acceptance-111/results/desktop-usb-launch.md).

Before you start: save all work on the Windows computer. If BitLocker is on,
confirm you can reach the recovery key **before** any restart. Never write
the key in a form. Write only "reachable: yes".

1. Sign in as a standard user (PHY-WIN-01, -02) or an administrator (PHY-WIN-07).
2. Insert the Beamo USB. Open it in File Explorer.
   Expected: files are visible. Nothing starts by itself.
3. Double-click `Start Beamo Wipe.exe`. The launcher is not code-signed, so
   Windows may show a SmartScreen warning. Photograph it. Record the exact
   text and buttons.
   - Continue with **More info**, then **Run anyway**, only for a USB from
     this verified session.
   - Expected: no User Account Control (UAC) prompt. If one appears, record Fail.
4. The launcher page opens in the browser. Wait for the check to finish.
5. Brand line (PHY-WIN-03): find
   `Most <brand> computers: press <key> at power-on.`
   Compare the brand with the intake form. Compare the key with
   `desktop/bootkeys.json`. Open **Technical details**. It may show the
   maker and model. It must not show a serial number.
   On an unlisted or self-built computer (PHY-WIN-04), the full key table
   is shown, already opened.
6. Restart to boot options (PHY-WIN-05, -06, -07):
   1. Find **Restart to boot options**. If it is missing, record the reason
      the page gives. On legacy BIOS Windows (PHY-WIN-11) it must be missing.
   2. Tick `I’ve saved my work and closed my applications. Restart this computer now.`
   3. Choose **Restart to boot options**. The page says
      `Windows accepted the restart. On the blue Choose an option screen, choose Use a device, then the Beamo USB (it may be listed as EFI USB Device).`
   4. Windows restarts to **Choose an option**. Photograph it.
   5. Choose **Use a device**. Record the exact name of the USB in the list.
      Choose it. Do not choose any other tool on this screen.
   6. Expected: the Beamo menu, then the erase guide. Nothing is erased.
      Record whether Windows asked for a BitLocker recovery key (PHY-WIN-08).
   7. Choose **Shut down** in the wizard. Remove the Beamo USB when the
      computer is off. Start Windows again. Record whether it asked for a key.
7. Unsaved work (PHY-WIN-09): open Notepad, type a word, do not save. Repeat
   step 6.3. Windows asks about Notepad. Choose **Cancel**. Expected: Windows
   keeps running. Then restart Windows normally once. Record whether the
   boot options screen appears. Either answer is a valid observation.
8. Shut down right removed (PHY-WIN-10): only on a lab computer that already
   has this policy, or where the owner approved setting and restoring it.
   Expected: `Windows did not restart to the boot options. Nothing was changed and nothing was erased.`
9. Copied launcher (PHY-WIN-12): copy `Start Beamo Wipe.exe` to the desktop
   and run the copy. Expected: no restart is offered. The page says
   `Open the launcher from the original Beamo USB, not a copied application.`

Stop if the launcher offers to erase anything, asks for administrator
rights to restart, or changes a firmware setting.

## P2. Linux launcher

Row: PHY-LNX-01. The other Linux cases are #111 PHY-DESK rows.

1. On a Linux desktop, open the Beamo USB and run `Start Beamo Wipe Linux`.
   Follow the desktop's own permission prompt. Do not bypass a `noexec` block.
2. Check the brand line as in P1 step 5. The brand comes from files any user
   can read. No password prompt may appear for this read.
3. Close the launcher.

## P3. Firmware boot by brand and mode

Rows: PHY-DELL-01 to PHY-GIGA-04 and PHY-MAC-01. The canonical boot steps are
[#111 §5.3](../../evidence/physical-acceptance-111/README.md#53-firmware-boot-does-not-erase-a-pc-disk).
Secure Boot rows follow the [Secure Boot cases](../../secure-boot-acceptance.md).

**Image rule for Secure Boot.** The Secure Boot receipt (Q12) covers only the
0.2.12 image. Images built after 0.2.14 start a newer kernel. A newer image
needs its own component inspection first. Without it, every `-03` row is
BLOCKED (SB-INSPECTION). Do not judge it from the boot alone.

For each computer:

1. Record the firmware's current mode: UEFI with Secure Boot enforcing,
   UEFI without enforcing, or legacy BIOS/CSM. Do not change it to fill a
   row. A computer in one mode fills only that mode's row.
2. Key row (`-01`): turn the computer off. Insert the Beamo USB in a direct
   port. Turn it on and tap the key from the matrix row.
   - Expected: the boot menu opens. Photograph it.
   - If another key works, record that key. The row is then a Fail of the key
     table, not of the erase guide. If no key works, record what you tried.
3. Choose the USB entry. Expected: the Beamo menu with
   `Beamo Wipe: start the erase guide (nothing is erased yet)`.
   UEFI plays two short beeps only if the computer has a speaker. BIOS is silent.
4. Choose the start entry. Expected: the guide starts and asks for a
   language first. Nothing is erased.
5. Go as far as `Which disk should we erase?` Do P4 step 3 there.
6. Choose **Shut down**. Wait until the computer is fully off.

Secure Boot rows (`-03`): also capture everything in "Read-only prerequisites
and evidence" on the Secure Boot page. Use only read-only tools. If you cannot
read `db`, `dbx` or the shim/SBAT state, the result is Unknown, even if the
guide starts.

Intel Mac (PHY-MAC-01): Excluded unless the owner adds it to scope. Apple
Silicon and Chromebooks are never tested and never claimed.

## P4. Disk list and Beamo USB protection

Rows: PHY-DISK-01 to -10 and PHY-EXCL-01 to -03. Nothing is erased here.

1. Connect the disks for the row. Use a `DISPOSABLE` disk or a disk with
   nothing of value. Record each disk on the intake form.
2. Start the guide (P3 steps 2 to 4). On `Is this your computer?` tick
   `I own this computer and these disks, or I have written permission to erase them.`
   Go to `Which disk should we erase?`
3. Every time (PHY-EXCL-01): the Beamo USB shows as
   `Beamo USB — protected, cannot be erased`. It is plain text with no
   select action. Photograph it. If it can be selected, stop and record Fail.
4. Each disk row: check that the disk is listed once. Check the
   **Connection** (SATA, NVMe or USB), the size and the end of the serial
   number or hardware ID. Compare them with the label on the disk.
5. Many disks (PHY-DISK-06): select one disk. On `Is this the right disk?`
   record what you are asked to type, for example
   `Type the last 4 characters of the serial number shown above.`
   Choose **Back**. Do not go on to a method.
6. VMD/RST (PHY-DISK-07): use a computer already set to Intel VMD or RST.
   Expected: `No disk to erase`. What happened says
   `This computer's disk may be hidden by Intel VMD (RST).` Nothing is
   selectable. The [canonical description](../../storage-and-controller-limits.md#6a-disk-hidden-by-intel-vmd-or-rst-185)
   lists every rule.
7. AHCI after VMD (PHY-DISK-08): optional. Only a lab operator with written
   approval changes this firmware setting, after confirming the BitLocker key
   is reachable. Change it back after the row. Confirm Windows starts again.
8. Two Beamo USBs (PHY-EXCL-02): insert a second stick with the same image
   before you turn the computer on. Expected: no disk is selectable. A Stop
   screen such as `We could not identify the Beamo USB` appears.
9. Beamo USB plus an ordinary stick (PHY-EXCL-03): the Beamo USB stays
   protected. The other stick may appear as a USB disk. Do not select it.
10. Choose **Shut down**.

## P5. Prepare a disposable disk

Needed before any PHY-ERASE row. This section writes only to the disposable
disk, and only on a separate Linux QA workstation.

1. Get written authorization from the disk's owner for this session. Record
   it in the run record by role and date, not by name.
2. Label the disk `DISPOSABLE` on its case. Record model, capacity, bus and
   the last 4 characters of its serial number.
3. On the QA workstation, turn off desktop automount. Connect only this disk.
   Identify it with `lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,MOUNTPOINTS`
   and use its whole-disk link under `/dev/disk/by-id/`. If two disks could
   match, stop.
4. With the workstation's normal disk tool, create one partition and one
   exFAT or ext4 file system on the disposable disk. Mount it.
5. Choose a marker of 16 or more letters and digits that names the run, for
   example `BEAMO-SEED-RUN-20270115-01`. Set `SEED_FOLDER` to a new, empty
   folder on the mounted disposable disk and `MARKER` to the marker. Run:

<!-- seed-disposable-disk -->
```sh
python3 - "$SEED_FOLDER" "$MARKER" <<'PY_SEED'
import errno
import os
import sys

try:
    folder, marker = sys.argv[1:]
    if len(marker) < 16 or not marker.isascii():
        raise ValueError("marker must be 16+ ASCII characters")
    if not os.path.isdir(folder) or os.listdir(folder):
        raise ValueError("name an empty folder on the mounted DISPOSABLE disk")
    record = (marker + "|").encode("ascii")
    block = (record * (65536 // len(record) + 1))[:65536]
    written = files = 0
    try:
        while True:
            name = os.path.join(folder, f"seed-{files:05d}.bin")
            with open(name, "xb", buffering=0) as out:
                files += 1
                for _ in range(1024):  # up to 64 MiB per file
                    written += out.write(block) or 0
                os.fsync(out.fileno())
    except OSError as error:
        if error.errno != errno.ENOSPC:
            raise
    print(f"SEEDED: about {written} bytes in {files} files; marker {marker}")
except (OSError, ValueError) as error:
    print(f"STOP: {error}", file=sys.stderr)
    sys.exit(2)
PY_SEED
```

   The script writes only new files in that folder, until the disk is full.
   Expected: `SEEDED: about … bytes`. Exit 2 with `STOP:` means nothing
   useful was written; fix the cause and run it again.
6. Run `sync`. Unmount the file system. Keep the disk connected.
7. Run the P7 scanner in mode `present` with the same marker. Expected:
   `COLD READBACK PRESENT: PASS` and a large hit count. Record the count.
   Without this, a later `absent` result proves nothing.
8. Shut down the workstation's use of the disk, disconnect it and install it
   in the test computer.

## P6. Erase a disposable disk

Rows: PHY-ERASE-01 to -11. Canonical safety rules: [#111 §5.5](../../evidence/physical-acceptance-111/README.md#55-optional-authorized-erase-destructive).
This is the only section that erases. Skip it without written authorization.

1. Only the `DISPOSABLE` disk and the Beamo USB are connected. Keep the
   report USB unplugged. Laptop: wall power on and lid open.
2. Start the guide. Tick the ownership box. On `Which disk should we erase?`
   check P4 step 3 (Beamo USB protected).
3. Select the disposable disk. Match model, size and serial end with the
   label. If anything differs, stop.
4. On `Is this the right disk?` type what is asked. Choose **Choose erase method**.
5. On `Choose an erase method`, choose the row's method: **Everyday**,
   **Three overwrites** or **Quick zero**. Choose **Review before erasing**.
6. On `Review before erasing`, wait for the countdown
   (`seconds until Erase now is available.`). Expected: nothing starts at
   zero. The screen says `Erase now is available.`
7. Choose **Erase now**. Write down the UTC start time.
8. `Erasing now` is shown. Leave `Play a sound when it's finished` as it is
   (P10 tests it). Do not touch the computer until it finishes.
9. Record the headline on the result screen:
   - Everyday and Three overwrites: `Done — this disk was erased and checked`.
   - Quick zero: `Done — this disk was overwritten with zeros (not checked)`.
   - Any other headline is a Fail for the row. Photograph it.
10. Save a report (P8) if the row asks. Photograph the QR code screen.
11. Erase another disk (PHY-ERASE-10): with two disposable disks, choose
    **Erase another disk**. Expected: `Which disk should we erase?` may start
    with `You confirmed that you own these disks or have written permission to erase them.`
    and a **Change** button. The first disk shows `Erased earlier (checked)`.
12. Stop erase (PHY-ERASE-11): during `Erasing now`, choose **Stop erase**,
    then **Yes, stop erasing**. Expected: `Stopped — you stopped the erase before it finished`.
13. Choose **Shut down**. Wait until the computer is fully off. Then do P7.

A Done screen is not a certificate. On an SSD, NVMe or eMMC disk, the disk's
own controller decides what remains in hidden areas
([storage limits](../../storage-and-controller-limits.md)).

## P7. Cold readback after an erase

Rows: PHY-COLD-01 to -08. Use the [cold-readback form](forms/cold-readback.md).

"Cold" means the disk was powered off and physically reconnected before it is
read. A read on the same running session is a warm read. A warm read, a
software re-scan or a virtual disk never fills a PHY-COLD row.

1. The test computer is fully off (P6 step 13). Unplug wall power. Wait
   60 seconds.
2. Remove the disposable disk. Connect it to the Linux QA workstation with
   automount off. An NVMe disk from a laptop may use a USB-NVMe enclosure;
   record the enclosure model.
   - If the disk cannot be removed (soldered eMMC or NVMe), boot a separately
     verified, read-only Linux live USB on the same computer after the
     power-off. Record this as route B on the form. Route B is weaker.
3. Identify the disk again (P5 step 3). Never mount it. Never run a repair,
   format or partition tool on it.
4. Set `DISK` to its whole-disk `/dev/disk/by-id/` link. Run the scanner with
   the row's mode. Use `sudo` only if read access needs it.

<!-- cold-readback-scanner -->
```sh
python3 - "$MODE" "$DISK" "$MARKER" <<'PY_SCAN'
import hashlib
import os
import stat
import sys

USAGE = "usage: MODE DISK [MARKER] [--rehearsal]; MODE is zero, absent or present"
try:
    rehearsal = "--rehearsal" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a != "--rehearsal"]
    if len(args) not in (2, 3) or args[0] not in ("zero", "absent", "present"):
        raise ValueError(USAGE)
    mode, path = args[0], args[1]
    marker = args[2].encode("ascii") if len(args) == 3 else b""
    if mode != "zero" and len(marker) < 16:
        raise ValueError("absent and present need the run's marker (16+ characters)")
    info = os.stat(path)
    if stat.S_ISBLK(info.st_mode) and not rehearsal:
        name = os.path.basename(os.path.realpath(path))
        if os.path.exists(f"/sys/class/block/{name}/partition"):
            raise ValueError("this is a partition; name the whole disk")
        with open("/proc/mounts", encoding="utf-8") as mounts:
            sources = [line.split()[0] for line in mounts if line.startswith("/dev/")]
        if any(os.path.basename(os.path.realpath(s)).startswith(name) for s in sources):
            raise ValueError("the disk or one of its partitions is mounted; unmount it, do not write it")
        kind = "block device"
    elif stat.S_ISREG(info.st_mode) and rehearsal:
        kind = "REHEARSAL regular file (never qualifies a row)"
    else:
        raise ValueError("name a whole block device (or a regular file with --rehearsal)")
    digest = hashlib.sha256()
    total = hits = 0
    first_nonzero = None
    tail = b""
    with open(path, "rb", buffering=0) as disk:
        size = disk.seek(0, os.SEEK_END)
        disk.seek(0)
        while True:
            chunk = disk.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            if mode == "zero":
                if first_nonzero is None:
                    rest = chunk.lstrip(b"\0")
                    if rest:
                        first_nonzero = total + len(chunk) - len(rest)
            else:
                window = tail + chunk
                hits += window.count(marker)
                tail = window[-(len(marker) - 1):]
            total += len(chunk)
    if size <= 0 or total != size:
        raise ValueError(f"short read: {total} of {size} bytes")
    print(f"Read {total} bytes from {kind}; SHA-256 {digest.hexdigest()}")
    if mode == "zero":
        ok = first_nonzero is None
        print("All bytes zero" if ok else f"First non-zero byte at offset {first_nonzero}")
    else:
        print(f"Marker hits: {hits}")
        ok = hits == 0 if mode == "absent" else hits > 0
    print(f"COLD READBACK {mode.upper()}: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)
except (OSError, ValueError) as error:
    print(f"STOP: {error}", file=sys.stderr)
    sys.exit(2)
PY_SCAN
```

   Modes:
   - `zero` (Quick zero rows): PASS when every byte is zero. Leave out `MARKER`.
   - `absent` (Everyday and Three overwrites rows): PASS when the run's
     marker is not found anywhere on the disk.
   - `present` (P5 before the erase, and PHY-COLD-07): PASS when the marker
     is still found.
5. Exit 0 with `PASS` qualifies the row. Exit 1 with `FAIL` is a Fail: keep
   the output. Exit 2 with `STOP:` means the scan did not run. Fix the cause
   (for example a mounted partition) and scan again. Never record PASS from
   a STOP.
6. Record bytes read, the SHA-256 line, the hit count and the exit code.
7. The scanner reads only. It refuses partitions and mounted disks.
   `--rehearsal` lets it read a regular file for practice. A rehearsal never
   fills a row.

What a PASS does not prove: areas the disk hides from the computer (HPA, DCO,
spare or remapped flash) were not read. See
[storage limits](../../storage-and-controller-limits.md).

## P8. Save a report and remove the USBs

Rows: PHY-RPT-01 to -10. Canonical rules: [report shutdown](../../report-shutdown.md).
Use a sacrificial stick for every report USB.

1. Prepare one FAT32 stick (PHY-RPT-01), one exFAT stick (PHY-RPT-02), one
   NTFS stick (PHY-RPT-03) and one spare stick. Each stick holds nothing of value.
2. After P6 step 9, find `Save a report (optional)`. Its first step says
   `Insert a separate USB stick now (FAT32 or exFAT). Keep the Beamo USB and this disk connected.`
3. Insert the FAT32 stick. Expected: `Found: <model, size> (FAT32)`.
4. Choose **Save report to USB**. Expected: `Saving and checking the copy.`,
   then `Saved and checked.` and where it was saved. Then
   `You can remove the report USB now.` Remove it.
5. On another computer, open the stick. Expected folder:
   `BEAMO-WIPE-REPORTS/report-<24 letters and digits>/` with `RESULT.txt`,
   `result.json`, their `.sha256` files and `README.txt`, among others. On Linux or macOS,
   run `sha256sum -c *.sha256` (or `shasum -a 256 -c`) in that folder.
   Expected: every line `OK`. Record the output.
6. exFAT (PHY-RPT-02): repeat steps 3 to 5 with the exFAT stick, after
   another erase or on the same result screen if Save is still offered.
7. NTFS (PHY-RPT-03): insert the NTFS stick. Expected:
   `This USB is formatted NTFS — use a FAT32 or exFAT stick.` Save stays greyed.
8. Two sticks (PHY-RPT-04): insert two sticks. Expected:
   `More than one new USB stick is plugged in. Remove the extra one.`
9. Pulled during save (PHY-RPT-06): choose Save, then pull the spare stick at
   once. Expected: an error with a retry step. Insert the FAT32 stick and
   save again. The erase result must not change.
10. Diagnostic report (PHY-RPT-10): on a Stop screen (for example P4 step 8),
    choose **Save diagnostic report**. Expected: `diagnostic.json` and its
    `.sha256`. It is not erase evidence.
11. Report inserted early (PHY-RPT-05): in a new session, plug the report USB
    in before choosing a disk. Expected: the help asks you to remove only the
    report USB and choose **Check disks again**. Do not erase the report USB.
12. Shut down without saving (PHY-RPT-07): tick `I want to save a report`
    before the erase, then choose **Shut down** without saving. Expected:
    `Shut down without saving?` with **Keep session open** first, and the
    `Which USB can be removed, and when` steps. Choose **Keep session open**.
13. Removal (PHY-RPT-08): after a save, choose **Shut down**. Remove the
    Beamo USB only after the computer is fully off.
14. QR code (PHY-RPT-09): point a phone camera at the code under
    `Keep a record without a USB`. Expected: plain text with result, disk,
    serial, method and time. Blur the serial in any photo you keep.

## P9. Interruptions

Rows: PHY-INT-01 to -09. Power without an erase is #111
[power](../../evidence/physical-acceptance-111/results/power.md). Policy:
[live-session power](../../live-session-power.md). Rows marked
"Authorized" erase a seeded `DISPOSABLE` disk (P5, P6) on a lab computer.

1. Beamo USB pulled, no erase (PHY-INT-01): at `Which disk should we erase?`
   pull the Beamo USB. Record what happens. Expected: the session stops;
   nothing is erased. Reinsert it, restart, and check that the guide starts
   fresh.
2. Beamo USB pulled during an erase (PHY-INT-02): start an Everyday erase.
   After 2 minutes, pull the Beamo USB. Record what the screen shows. Turn
   the computer off. Expected: no Done screen; the next start does not
   resume. Do P7 in mode `present`. The disk counts as not erased.
3. Target pulled (PHY-INT-03): erase a disk in a USB enclosure. Pull the
   enclosure after 2 minutes. Expected: a headline that starts with
   `Not finished` or `Not confirmed`. Never Done.
4. Wall power pulled (PHY-INT-04, desktop): start an erase, then pull the
   cord. Restart from the Beamo USB. Expected: the guide starts fresh with no
   report. Do P7 (row PHY-COLD-08).
5. Battery (PHY-INT-05, laptop): start an erase on wall power. Unplug the
   charger. Expected badge: `On battery — plug in`. Plug it back. Expected:
   `Plugged in`. The erase continues. The selected disk does not change.
6. Lid (PHY-INT-06): during an erase, close the lid for 30 seconds. Open it.
   Record whether the computer slept. If it slept, the result must not be
   Done. The product tells owners to keep the lid open.
7. Short power-button press (PHY-INT-07): press once during an erase.
   Expected: nothing happens; the erase continues.
8. Held power button (PHY-INT-08): hold it during an erase. Record seconds
   held and what happened. The firmware may cut power. That is expected.
9. Screen lit (PHY-INT-09): during an erase longer than 15 minutes, do not
   touch anything. Expected: the screen stays lit. Photograph it at 15 minutes.

## P10. Accessibility, sound and display

Rows: PHY-A11Y-01 to -12. Canonical rules: [screen reader](../../screen-reader.md)
and the #111 [audio](../../evidence/physical-acceptance-111/results/audio.md)
and [monitors](../../evidence/physical-acceptance-111/results/monitors.md) sheets.

1. Orca (PHY-A11Y-01): at the Beamo menu press **S**. Expected: speech starts.
   Do a full authorized erase with your eyes off the screen if you can.
   Record each heading Orca reads, including `Save a report (optional)`.
2. Finished sound (PHY-A11Y-02): on `Erasing now`, check that
   `Play a sound when it's finished` is ticked. After an Everyday or Three
   overwrites erase, expected: the finished sound plays. It repeats each
   minute, at most five times. A key press stops it.
3. Attention sound (PHY-A11Y-03): after Quick zero or a stopped erase,
   expected: the attention sound, not the finished sound.
4. No sound (PHY-A11Y-04): on a computer with no speaker, or muted, expected:
   `Play a sound when it's finished: not available`. The box is greyed and
   says why.
5. Sound check (PHY-A11Y-05): open **Sound check**. Expected: outputs in plain
   words (Speakers, Headphones, HDMI sound). **Play speech test** is heard on
   the chosen output.
6. High contrast (PHY-A11Y-06): turn on **High contrast** on the first screen.
   Expected: `High contrast: on`. Also open **Help & settings** (F10) and
   check the same item. Photograph three screens on the real panel.
7. Text size (PHY-A11Y-07): choose **Large**, then **Extra large**. Walk to
   `Review before erasing` and back with **Back**. The main action must be
   reachable on every screen.
8. Small panel (PHY-A11Y-08): on a real 1024×600 panel, walk every screen up
   to `Review before erasing` with the keyboard. Scrolling is allowed.
9. HiDPI (PHY-A11Y-09): on a 2560×1600 or 4K panel, check that text is a
   normal reading size, also in the screen-reader view (F8).
10. Graphics (PHY-A11Y-10 to -12): at the Beamo menu press **T** for
    `Beamo Wipe: troubleshoot startup (nothing is erased yet)`. Expected: the
    guide starts. Record the graphics maker and model.

## P11. Keyboard layouts

Rows: PHY-LAY-01 to -07. The #111 [keyboards](../../evidence/physical-acceptance-111/results/keyboards.md)
sheet covers keyboard hardware.

1. Connect a keyboard with the row's printed layout (us, fr, de, gb, es,
   latam or it).
2. Choose the matching language. On `Check your keyboard`, pick the layout.
3. Press the key labelled Z at
   `Optional check: press the key labelled Z here. Nothing you type is saved.`
   Expected: a ✓ match line.
4. Go on to `Is this the right disk?` with a test disk (no erase). Type the
   requested characters. Expected: they appear as printed on the keys.
   Choose **Back**.

## P12. Kiosk recovery

Rows: PHY-KIOSK-01 to -04. Canonical rules: [kiosk recovery](../../kiosk-recovery.md).

Run these rows only when the problem happens by itself on that hardware.
Never change the stick to force a failure. A changed stick no longer matches
its readback. If the recovery screen never appears, mark the rows Excluded
with the reason "not reached".

1. If the graphical guide fails, expected: the keyboard text screens appear
   (PHY-KIOSK-01). No erase starts.
2. If `Beamo Wipe recovery` appears (PHY-KIOSK-02), photograph it. Type `3`
   and Enter. Expected: attempts used and exit codes.
3. Type `5`, then `SHUTDOWN` (PHY-KIOSK-03). Expected: the computer turns off.
4. From the speech entry (PHY-KIOSK-04), expected: the recovery text is spoken.

## P13. Manufacturing readback

Rows: PHY-MFG-02 to -05. The canonical procedure is
[manufacturing](../../manufacturing.md): §2 media, §4 readback QA, §5 boot QA.
Follow it as written. Record each receipt in the run record. A receipt with
`target_type: regular` never fills a row.

## P14. After the session

1. Leave rows you did not run as NOT TESTED.
2. Fill the [sign-off sheet](forms/sign-off.md) for the session.
3. File everything as described in the [packet README](README.md#filing-results).
