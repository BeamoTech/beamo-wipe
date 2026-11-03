# Screen-reader operation

Shutdown actions described below now request the shared shutdown decision:
when a report was requested but no current verified export is confirmed,
**Shut down without saving?** requires a separate choice. **Keep session open**
is the safe default. Tk Enter/Escape returns; Tab and Space select an action.
The screen-reader view exposes Keep first and both native buttons, and
announces the same ordered USB-removal steps as text below the question. See
[the state, console, and recovery rules](report-shutdown.md). No report survives
live-session shutdown or power loss unless it has been exported.

The live USB offers a GTK 3 view using standard AT-SPI controls and Orca.
Press F8 in the graphical wizard before erasure, or choose **Screen-reader
view (F8)**. This checks disks again and clears the selected target, ownership
acknowledgement, typed confirmation, method, and countdown. Complete the entire
authorization flow in the new view. Switching is unavailable while an erase is
starting or running. A failed refresh leaves no stale disk selectable.

**Check disks again (F5)** first explains that reset and waits for confirm or
Back. It is not offered on the ownership screen. From Confirm, Method or
Review the dialog is guarded (#136): **Cancel** comes first, Enter on the
heading does nothing, a second F5 cannot accept it, and only the **Check disks
again** button clears your answers. In the graphical view, F8 screen-reader
handoff scans immediately from Pick and earlier; from Confirm, Method or Review
it first opens the same guarded dialog.

The live USB boot menu also offers **Beamo Wipe: speech for screen readers** —
press **S** when the menu appears. That entry passes `beamo.ui=accessible` on
the kernel command line; the kiosk supervisor then launches
`beamo-wipe --accessible` directly, so a blind owner never has to operate the
graphical wizard first. Speech (PulseAudio and Orca) is started before disk
discovery, so the startup stages are announced, and an espeak-ng cue before
the graphical server says startup is underway. If audio or Orca fails, the
view stays usable and the failure is recorded as `pulseaudio_failed` or
`orca_failed` in the diagnostic log. If the graphical view cannot start at
all, a spoken notice says the keyboard text screen is showing and that speech
is not available on it. Intentional differences: the BIOS menu has no beep
(only the UEFI menu plays two short PC-speaker beeps, and only on hardware
with a speaker), `./preview --accessible` starts no
audio or reader, and the keyboard console fallback has no speech.

Tab and Shift+Tab move focus; Space activates a focused control. The ownership
checkbox and typed confirmation still gate the next-action button. The Erase now button stays
disabled for the five-second countdown and never activates automatically.
F5 checks disks again before erasure. Escape goes back where allowed. Full
**Storage limits** are available from method selection and return to that method.
Disk identity announcements say **Serial number:** before the value, including
when a serial is missing. Hardware ID stays Hardware ID when that is the
strongest identifier.
A concise inventory count is announced as focusable text on the disk list,
empty list, and blocked screens: how many disks can be erased, that the Beamo
USB or boot disc is protected, how many other devices are not available, and
when the list could not be confirmed. It uses sentence separators for speech
and never hides uncertainty or exclusions.

**Beamo USB — protected, cannot be erased** has its own focusable, read-only
identity text before the disk-selection buttons. It is never a Select button.
**Other detected devices** is read-only text; it never offers an erase action.
Partitions and other technical components of a known parent are read-only
nested text on that disk (or on the protected USB), never a Select button.
Select buttons announce the observed **Connection** (USB, SATA, NVMe) with
the disk identity. They do not guess whether a disk is inside the computer.

On the disk list, **I'm not sure which disk** opens identification guidance
for internal or external targets. Tab to the read-only text and use normal
reader commands or Page Up/Page Down. **Back** or Escape returns with no disk
selected. **Stop and shut down** uses the report-protected shutdown decision.
Opening this help retains only the ownership acknowledgement already made;
select the disk and complete confirmation and countdown again before erasure.

On screen changes, focus moves to the screen explanation. Finished's heading
is the outcome in plain words (#134), for example “Done — this disk was erased
and checked”. Quick zero says “Done — this disk was overwritten with zeros (not
checked)”, never checked or verified. A finished result's note and its
numbered **What next** heading and list follow as separate focusable labels;
the exact status message (“Erase completed; verification was not performed.”)
and result code are under the **Technical details** expander. A verified
completion checks exposed storage only. No read-back result guarantees coverage of inaccessible,
remapped, over-provisioned, or controller-managed flash; extra overwrite passes
do not fix these limits. Failed or missing evidence remains unsuccessful or
indeterminate; failures read their plain heading, then What happened (the
exact status), What it means for your disk and What to do next. Confirmed
cancellation's status still says “Stopped by you.”

Next comes the **Save a report (optional)** heading (#135). Its state, the
numbered steps and any greyed control's reason are focusable labels; Save
report to USB and Retry evidence save are buttons inside it, and the bottom
buttons are only Erase another disk and Shut down. When the live USB line
changes, the view keeps focus where it was; if focus was inside the panel it
moves to the new status line so Orca reads it. Sound settings stay in the
Sound check utility.

On the keyboard screen, the check box is named "Optional check: press the key
labelled Z here…" (#140). Press Z: focus moves to the result, an alert Orca
reads ("✓ Letters and numbers match …" or "That looks like …. Switch to it?");
Tab reaches the Switch button. The check is optional and never blocks Continue.

After the report panel, Finished has a **Keep a record without a USB**
heading. The QR code below it is an image a sighted helper can photograph; it
is not focusable and its accessible name says the same summary follows as
text. Tab to the next label to read that summary line by line: result as its
exact status message (the Technical details line), disk, capacity, serial number, method, times, report state and
software version. It is a summary, not a certificate. It is not shown while an
erase may still be running or after a stop that could not be confirmed.

The view starts Orca and PulseAudio on the live USB. Speech requires working
audio output. Native Tk 8.6 is not claimed to expose its custom canvas controls
to screen readers. The sequential `--plain-console` view is also available for
terminal environments with an independently configured reader.

For a safe Linux preview, install the GTK/Orca packages listed in the live
package list and run `./preview --accessible`. It uses fake devices. Preview
mode does not start host audio services or an external screen reader.

Regression checks use fake disks and process output, GTK at 800×600, an external
AT-SPI client, and real Orca speech-generation diagnostics. Run with a private
D-Bus session and Xvfb at 72 DPI, as described in [CI](ci.md). These checks do not
prove physical speaker output, braille hardware behavior, or compatibility with
every sound card. No test uses host disks or audio-device passthrough.

## Sound check

The actions footer on every screen starts with a Sound check button. It
opens a dialog that lists the sound outputs in plain words (Speakers,
Headphones, HDMI sound, and so on, with the technical device name kept
as each choice's screen-reader description), shows the volume and mute
state, and offers Louder,
Quieter, Mute, and a Play speech test button that speaks through the
same chain Orca uses. Choosing an output makes it the session default
and records it, so the choice survives dialog reopens and sound-server
restarts within the session.

When no output exists, when the test cannot play, or when Orca itself
is not running, the dialog says so in words and always shows written,
offline recovery steps. The dialog uses native controls only: Tab
moves, Enter activates, Esc closes. In the developer preview, sound
devices are unreachable and the dialog says so instead of touching
host audio. Speech belongs to this path alone, but outcome earcons
are shared: the dialog also offers a Sounds off/on toggle and a Hear
sounds button that plays the finished sound then the attention sound
through the chosen output. The finished earcon plays for a
verified erase and the attention earcon for any other final outcome,
repeating every minute (at most five plays) until a key press or a
control is used; muted, missing, or preview audio stays silent. On
Working, a native check box "Play a sound when it's finished" (on by
default for each erase) follows the progress, after a focusable line
that promises the beep only when an output was found, or says sound
is not available; the box is then insensitive and its accessible
description gives the reason. Availability changes update the line
and box in place, so focus never jumps. The earcon
never changes the Done announcement, heading, or roles, and never
blocks speech: text and sound stay independent channels. Tk, console,
and gallery expose the same toggle and hear/replay actions in their
own idioms; helper has no sound UI (boot guidance, no outcome).

## Automated boot evidence

The hosted QEMU gate selects the shipped speech entry through its S hotkey
on both BIOS and UEFI USB boots. It requires the accessible-mode marker,
completed disk discovery, and a rendered GTK keyboard screen before passing.
The Linux suite separately verifies real Orca announcements through AT-SPI.
These checks do not certify audible output on every physical sound device.
