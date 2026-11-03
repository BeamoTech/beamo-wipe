# Screens

Every interface uses the same Wizard authorization and validated result model.

Wayfinding uses three stages, not eight equal pages: **Preparation** (keyboard through the last review), **Erase** (the long destructive operation, including stopping), and **Result** (finished, failed, or stopped by you). The header names the stage and, while preparing, the step (#130): **Step 1 of 6 · Check keyboard**, **Confirm ownership**, **Choose a disk**, **Confirm its identity**, **Choose a method**, **Review and erase**. The steps are the wizard's Back order (`wizard.PREPARATION_PATH`), so the bar cannot drift from the screens; Review is the last step before Erase (#166). The start screen's roadmap uses the same names from Choose a disk on (#138). Screens that stand in for a step (no disks, nothing safe to pick, the final re-check after Erase now) show that step; detours (keyboard check, I'm not sure which disk, Advanced, storage limits, report help) show the step they return to; busy, recovery, erase and result screens show only their stage. The first strip segment fills step by step. Narrow windows or long translations shorten the caption to **Step 3 of 6** rather than cut it. Screen readers hear *Preparation, step 3 of 6: Choose a disk.* as the heading description; the console header shows the same text. Wipe percentage appears only on the working screen and is never the journey chrome. **Stop could not be confirmed** stays in Erase because the disk may still be erasing. Recovery overlays (refresh confirm, shut down confirm) keep their own screens.

Primary actions name the next step: **Choose a disk**, **Review this disk**, **Choose erase method**, **Review before erasing**. They never say the erase has started. **Erase now** stays on the last review after the countdown. Splash and keyboard keep **Continue**. Advanced uses **Back to methods**. The screen-reader picker has no footer Continue: choosing a disk is the next action.

| Screen | Purpose |
| --- | --- |
| Splash / Keyboard | Splash explains that nothing starts automatically. Keyboard offers only the shipped US, UK, Spanish, Latin American and Italian QWERTY, French AZERTY, and German QWERTZ layouts (Up/Down; keys 1–7 outside the check box) plus a typing-check box that is never saved. The language comes first on that screen, before its title, in focus and on screen (#131): a *Language · Langue · Sprache · Idioma · Lingua* label and English, Français, Deutsch, Español or Italiano, each in its own name. Left/Right or Space choose a language; Enter still continues. Choosing a language re-renders every screen element (header step, footer hint, buttons) and sets that language's usual shipped layout (`keyboard.LANGUAGE_LAYOUTS`: English → QWERTY (US), French → AZERTY (French), German → QWERTZ (German), Spanish → QWERTY (Spanish), Italian → QWERTY (Italian)) with a visible line such as *Keyboard set to AZERTY (French) to match Français. Keys do not match? Choose your keyboard below.*; English names QWERTY (UK) and Spanish names QWERTY (Latin American) as the obvious alternative, and no other layout is guessed. A layout the person picked is kept (*Keyboard stays …, the layout you chose.*). When the language changes after the owner box, a disk or a typed confirmation, the layout stays so those stay valid, and the line says so; a layout change still clears them, as before. Orca speaks with its configured voice: switching Orca's speech language with the UI language is not implemented (see the task record). |
| Owner | Combined introduction: say once what the tool does (it erases everything on the disk you choose, including any Windows or Linux), remind about backup copies, give the wall-power reminder, display blanking, and supported PCs, then require the ownership or written-permission acknowledgement. Continue stays disabled until the box is checked. Between the bullets and the power panel, Owner says the result screen shows a code to photograph (no second USB needed) and states the full report's media requirements up front: a separate FAT32 or exFAT USB with one volume, kept unplugged until the result screen asks, with already-plugged media refused, and points to Need a report? for details. |
| Pick a disk | Physical disks are primary cards. Partitions and other technical components nest under their parent when parentage is known. Keep eligible targets separate from read-only Other detected devices. Show a concise inventory count so the owner can check that expected disks were found, including zero, one, or many eligible disks, protected boot media, other devices that cannot be erased, and a fail-closed notice when the list cannot be confirmed. Show identity, the observed connection type, and deterministic exclusion reasons. Label each serial as Serial number so the value is not a bare string. Do not guess internal vs external location. Capacities use decimal GB, with an exact-tenth TB name when it does not collide; unknown media kind is labeled Type unknown. No excluded row offers a bypass. Empty or uncertain discovery gives safe support steps. When a report was requested, an info notice reminds the owner to keep the report USB unplugged until prompted, warns that extra USBs confuse the list, and gives the unplug-only-that-USB remedy; without a requested report no notice shows. |
| Confirm | Show exact device identity and one warning box naming the selected disk by model and size: everything on it will be erased (including Windows or its operating system when partitions show one), and it cannot be got back. Ask for the confirmation characters by field and count, never by printing them; they are marked in the disk card (see Confirmation characters). |
| Choose an erase method | Show a plain-language lead, then the operations below, comparison marks, and the device-specific storage notice. Everyday states it checks only exposed storage and does not promise duration. SSD and unknown-device warnings explain inaccessible, remapped, over-provisioned and controller-managed storage; additional overwrite passes do not fix those limits. |
| Supported storage limits | Full offline limits, reached directly from method selection. Back returns to the chosen method. |
| Review before erasing | Emphasize selected disk and plain method operation above technical pass details. The red callout is the only erase warning: the Confirm sentence with the serial or hardware ID added. It stays above the fold at 800×600 and every text size. A small countdown marks a fresh five-second review period: zero only enables Erase now and never starts erasure. Require explicit activation. |
| Working | Keep device identity, the method summary, and progress visible. Remind the owner to leave the USB in and keep wall power connected. Choose **Stop erase** (Tk/GTK button or Escape; plain console `CANCEL` + Enter; curses Esc) to review a warning: stopping cannot restore files already erased. **Keep erasing** dismisses the confirmation. Confirm with **Yes, stop erasing** (plain console `STOP` + Enter; curses S). Progress polling continues during confirmation, and completion takes precedence over stale confirmation actions. **Stopping erase** means exit and cleanup are still pending; the stopping and stop-confirmation screens keep the same disk identity and method summary visible instead of showing timing text alone. **Stopped by you** is a confirmed interruption, not a completed erase. **Stop could not be confirmed** stays on Working with a prominent warning because the disk may still be erasing. Interruption and inability to confirm a stop remain distinct outcomes. Shut down is not offered while an erase may still be running. Progress reads at a glance (#132): a large percentage (never 100% on this screen; the result screen reports completion), then one cautious time line, then the current step, for example 23% / Running for 25 minutes / Step 1 of 2: Overwriting, and later 61% / About 40 minutes left / Step 2 of 2: Checking (verification). Three overwrites shows Step 2 of 4: Overwriting (pass 2 of 3); Quick zero has no verification step, so it shows Step 1 of 1. Before the engine reports a number the large line says Starting… over an indeterminate slide; a line with no real data (unknown phase, a step that cannot be located yet) is hidden rather than shown as "not reported". The time line shows About … left only when the estimate passes every gate in [progress timing](progress-timing.md) (rounded up, no seconds); otherwise it shows how long the erase has run, and on the first steps a small note says time left appears during the last step. The current step is located from live engine phase and pass counters cross-checked against the plan; a report that disagrees with the plan shows a warning instead of a guessed step. Verifying, Syncing, Retrying, and Finalizing add a one-line note explaining the transition and that the erase is not done until the result screen. When progress updates go stale, the percentage is marked old and a warning band says how long it has been quiet, explains that a quiet screen does not mean the erase stopped, and gives safe next steps (keep the USB in and wall power connected, do not turn off, Stop erase stays available); it never recommends restarting, unplugging, or retrying the wipe. The Stopping screen shows the last known step and the elapsed time, with no estimate. Curses shows the same three lines first; the screen-reader view puts them in one focusable label (large first line) beside a progress bar named Erase progress, and both it and the plain console change that summary when the step changes, progress goes quiet or resumes, or stopping or finishing begins, and otherwise at most once a minute. Walk away (#133): the screen offers **Play a sound when it's finished** (Tk footer check box; GTK check box; curses O key; plain console SOUNDS word) beside **Hear sounds**. It is the same session setting as the result screen's Sounds on/off: each erase turns it on unless the person has already chosen on or off themselves this session, and the state carries to the result. An availability check (unmuted output found) runs on the audio worker when Working opens and every minute after; only when it succeeds does the screen promise "You can leave the computer. It will beep when it's done." While checking, or with the toggle off, it says "You can leave the computer and check back later." With no output, a muted output, or in the preview it says "Sound isn't available on this computer — check back later.", gives the reason, and greys the toggle. The existing laptop advice (keep wall power connected, lid open) follows that line once. Nothing plays until the outcome is final. |
| Finished | Use validated evidence and the canonical explanation in `outcomes.py`. The main heading is the specific erase outcome in plain words (#134; `outcomes.plain_result`), never a generic label: **Done — this disk was erased and checked** (verified: Everyday or Three overwrites), **Done — this disk was overwritten with zeros (not checked)** (Quick zero; never "checked" or "verified"), and for other outcomes a short "Not finished — …", "Not confirmed — …", "Stopped — …" or "Nothing erased — …" line. The canonical status message (for example "Erase completed; verification passed") is unchanged and stays the technical status line: evidence, the saved report, the photo record and support keep it, and the screen shows it under **Technical details** (Tk: behind Show more; GTK: an expander; consoles: after the support identity). Failed, cancelled, and unconfirmed outcomes then show three labeled recovery sections in screen-reader order: **What happened** (the exact message), **What it means for your disk**, and **What to do next**. Technical details stay behind an on-demand control and never replace those three. Verified and Quick zero results instead show a one-line note (what the check covered, or that Quick zero was not checked; the SSD controller limit; other disks were not erased) and a numbered **What next** list: shut down when finished; remove the Beamo USB once the computer is off; keeping the computer, install an operating system if this was its main disk; giving it away, verified: ready to pass on / Quick zero: erase again with Everyday first. The list replaces the former next-step paragraph and the separate start-up note, so neither is said twice. The erase badge, message, and details stay independent of the **Report status** area, which identifies the report copy on its own. The erase badge uses the canonical outcome; a confirmed user stop still reads **Stopped by you** in the erase summary. Report status uses neutral information, an amber warning, or a distinct saved-copy treatment (a Saved label, a small in-panel check, report wording, and the safe-to-remove line) — never the erase-success badge or the red failure badge. Report copy checking is not disk read-back verification. The screen shows elapsed time, the method summary, the next step, the disk summary with Show more, and the guarded report instruction. Outcomes that refer the owner to support add the support destination (`beamosupport.com`) as text everywhere and a phone-scannable code on graphical surfaces; the readable report, its README, and the offline helper carry the same destination. The browser preview omits the block on its sample finished screens because those screens say nothing was erased and do not ask the owner to contact support. Failures, cancellation and indeterminate results do not claim a disk was processed. Quick zero completion explicitly says verification was not performed. Footer, live session: **Save report to USB** (enabled only when the evidence gate allows saving), **Shut down** (disabled while exporting or saving evidence), and **Retry evidence save** when evidence saving failed. Footer, preview: **Close preview** and **Run again**. Console equivalents are the `SAVE` / `RETRY` / `SHUTDOWN` prompts; the screen-reader view exposes the same actions as native buttons. When sounds are on, the finished earcon plays for a verified erase and the attention earcon for any other final outcome (including Quick zero's unverified completion, interruption, and failures); it repeats every minute, at most five plays, until someone presses a key, clicks, or uses a control, turns sounds off, or leaves the result. Muted, missing, or preview audio stays silent; the curses and plain consoles ring the terminal bell instead when no output was found (not promised: many computers have no bell). Plain console rings once, because it waits for typed input. Hear again replays on demand. Unless the outcome proves nothing was erased (or is a finished outcome, whose What next list carries it), a conditional note follows the next step: if the erased disk was the one the computer starts from, the computer may not start normally and may need an operating system installed before reuse. The offline helper repeats this guidance in its after-erasing card. The report-status area guides export through five numbered stages (insert, check, save, verify, safe removal) with done/now marks and one current-step line instead of long paragraphs; check/save/verify read as current together because they run inside one export call, and failures show the precise error with retry guidance and no stage marks. Every media rejection names the problem and the next safe step (replug, different stick, retry-then-support, retry-then-shutdown, sort-while-off, wait); reasons that already carry instructions and the diagnostic screen share the same mapping. |
| Advanced | Technician information and the report workflow guidance. |
| Shut down without saving? | Shown when a report was requested but no current verified export is confirmed. Keep session open returns; explicit discard authorizes shutdown. Below the loss text, ordered removal steps state which media can be removed, which must stay, and that the Beamo USB is safe to remove only after the computer is fully off, plus restart and unsure-media rules; the erase-another variant keeps the Beamo USB for the next erase instead. [State and recovery rules](report-shutdown.md). |

## Method operations

- Everyday: Overwrite the disk, then check the result.
- Everyday: 1 overwrite pass: random data. Then we check the last overwrite.
- Three overwrites: Overwrite the disk three times, then check the result.
- Three overwrites: 3 overwrite passes: a pattern, its inverse, then random data. Then we check the last overwrite.
- Three overwrites is marked More overwrites. Three times the overwrites of Everyday. Extra passes do not reach hidden storage.
- Quick zero: Overwrite the disk with zeros. This does not check the result.
- Quick zero: 1 overwrite pass: zeros. This method does not check the overwrite.
- Quick zero is marked No check.

Before erasure, **Check disks again** (F5) first shows that it clears the
selected disk, ownership acknowledgement, typed confirmation, method, and
countdown, and that preparation starts again from the beginning. Back keeps
those answers. Confirming then performs fresh discovery and boot
identification and requires the full flow again. The inventory count is taken
from that new discovery. A failed refresh leaves no
stale target selectable. Refresh is disabled once starting or running.
Returning to a disk never automatically selects or authorizes it.
The checking screen paints immediately and discovery runs off the UI thread,
so repaint and input continue during the scan; pressing F5 again while
checking is ignored until the scan lands, so only one scan ever runs.

The keyboard screen is required after splash. Only US QWERTY, French AZERTY,
German QWERTZ, UK QWERTY, Spanish QWERTY, Latin American QWERTY and Italian
QWERTY are offered (XKB `us fr de gb es latam it`; console-data maps
`us fr de uk es la-latin1 it`). Tk shows them as compact cards, two columns
when the window is wide enough and one column for narrow windows or larger
text, with the selected layout's note below; Up/Down choose them even while
the check box has focus (the footer hint names these), and keys 1–7 when focus
is not in the check box. The plain console takes a lone digit; the curses
console uses Left/Right so every digit stays available for the typing
check. Choosing a language never changes or applies a
layout. A successful layout change clears typed
confirmations, the ownership acknowledgement, the selected disk, and last-chance
authorization, and requires that flow again. A failed or unknown layout leaves
the previous layout and is shown as an error; it does not silently substitute
another map. The typing-check box is not a password, is not logged, and is not
written to evidence. A kiosk restart returns to the shipped US QWERTY default.

The keyboard screen also offers Standard, Large, and Extra large text. The
choice stays for this USB session. Tk still pins `tk scaling 1.0` so display
DPI cannot enlarge type on its own. Extra large wraps and scrolls; footer
actions stay reachable at 800×600. The 80×24 console cannot grow glyphs.

The graphical wizard uses real layouts at 800×600, 1024×600, and 1280×720 as
well as 1024×740 and larger. Short windows may scroll the body; identity,
warnings, and footer actions stay reachable. On Pick, short windows (under
740 px tall) keep warnings first, then the disks, then the notes about the
selection, the protected boot USB and Compare disks. Their disk rows are
denser (tighter padding, nested partitions on one wrapped line) so the first
whole row shows without scrolling at 800×600 and 1024×600; every fact stays
in the row. Type enlarges slightly on large
windows. Tk scaling stays pinned so X DPI does not change the layout. The
window never opens taller than the panel. When type is enlarged, cards,
warnings, comparison, progress, and footers wrap to their parent width and
stack instead of clipping into fixed canvases.

Footer actions are two regions. Help and extra actions (keyboard layout,
check disks again, report help, screen-reader view, diagnostic, Advanced,
and keyboard hints) sit above a hairline. The navigation row is Back or
another secondary action on the left and the primary action on the right.
Keyboard hints never sit between Back and Continue or Erase. GTK names the
same two regions for AT-SPI and has no key-cap hint bar because each native
control is already named. The 80×24 console prints primary actions first
and drops extra chrome before an action is clipped. The boot helper has no
wizard footer.

Buttons, compact check rows, refresh, diagnostics, storage limits, and report
preferences share hover, press, focus, checked, and disabled treatment.
Disabled ghosts stay quiet. GTK keeps native check and radio roles.

Tk and the keyboard console support Tab, Enter, Escape, disk-selection arrows,
1–2–3 for keyboard layouts and methods. L opens full limits from method selection. The 80×24
console uses the same customer screen titles as Tk and the gallery, wraps every identity
field to the terminal's display columns, and pages with Up/Down and PgUp/PgDn so a serial
longer than the window is never cut off. It omits the graphical step strip to keep identity
and recovery actions on 24 rows. On terminals shorter than 20 rows it also drops Compare,
Other devices, and Keyboard footer hints so a serial still fits; C, O, B, and K still work.
The console shows the same inventory count and offers O for the read-only excluded inventory. The sequential console
accepts `CHECK DISKS AGAIN` at its pre-erase prompts.
On the Last chance screen the interfaces differ by design: Tk starts erasure
only from the focused, countdown-enabled Erase control (Enter, Space, or
click); the curses console erases on Enter once the countdown lapses with Esc
as the way back; the sequential console requires typing `ERASE`.

On Linux, F8 before erasure opens the GTK screen-reader view after clearing
prior authorization through refresh. Use Tab, Shift+Tab, Space and Orca reading
commands; see [screen-reader operation](screen-reader.md).

Local previews use fake devices and never erase disks. The browser gallery is
a preview; the shipped graphical views are native windows. Gallery Show more
uses the same disclosure label and system-path note as Tk. Working, stopping,
stale, unknown, mismatch, and verifying copy come from `ProgressView` (the
same object Tk and the console already paint). The gallery does not guess a
stage from an overall percent, and it never paints 100% on the working
screen. Console has no Show more control: identity including the system path
stays in the paginated body. The desktop launcher’s Technical details
disclosure is pre-boot readiness, not erase progress. The gallery count is a
static snapshot per preview scenario; native Check disks again updates the
live count. The offline helper never shows wipe progress.

Deep links for preview checks: `#s=working&disk=0&progress=preparing|writing|stale|verifying|mismatch|unknown`,
`#s=working&disk=0&pct=42`, `#s=working&disk=0&more=1`, and the stop hashes
below. Color-token tests are not a substitute for those states.

The shipped live supervisor also has a [terminal recovery menu](kiosk-recovery.md)
after repeated startup failures or a normal interface close. It is outside the
Python wizard so missing graphical/Python dependencies cannot hide it. Browser
and native previews retain the wizard's own diagnostic screens; the offline
helper explains the live-only recovery choices and accessibility limits.

### Erase and report status (#96)

Every completion view separates erase status from report status. Report save,
check, and retry messages never replace the erase outcome. A saved receipt means
only that the report copy was checked and the report USB safely unmounted; it does
not confirm erase success. Existing evidence validation remains conservative:
when evidence preparation fails, completion cannot be confirmed, even if the
process reported completion. Retry does not run the erase again.

Tk places the report panel directly below the erase summary, before scrollable
disk details and check warnings. The GTK screen-reader interface exposes explicit
ATK headings and focusable report text; arrival focus stays on the specific
erase heading (the announcement on success, the outcome message on failure). Console uses text headings without relying on color. The browser
and native previews show the same two areas but explicitly state that no report
was saved; the gallery does not simulate report export or offer a real save action.

### Error recovery sections (#107)

Every failure surface uses the same three customer sections, then technical
detail on demand: diagnostic, blocked, empty, keyboard/layout, last-chance,
working, finished, report-USB refusal, and evidence-save failure. Unknown
errors keep the original message, say the result is unconfirmed, and tell the
owner not to bypass protection. RESULT.txt adds the labeled fields after
Result for non-success outcomes only; Limitations is unchanged. Short Tk and
the 80×24 curses console join each label to its body on one line so **Report
status**, the post-erase start note, and report-USB next steps stay in the
first viewport; stacked labels remain the full-height Tk, GTK/Orca, gallery,
helper, and plain-console layout. Tk Finished uses the outcome heading as
What happened (no second copy of that sentence) and shows the Result code as
a muted line rather than a button, so Tab still reaches **Save report to USB**
after **Show more**. GTK, gallery, and the helper keep an expander. Curses
pages the Result code after report aftercare so the first 80×24 page keeps
**Report status** and export stages. Labeled meaning is in that paged tail;
the outcome heading is What happened and the next-step paragraph is What to
do next. The live USB supervisor recovery
menu is an intentional difference: it is outside the Python wizard, so its
**Technical details and logs** choice is not this three-section layout. The
offline helper explains both.

### Stop controls and fallback differences

Tk/GTK window close during an erase opens the same confirmation. Escape in that confirmation keeps erasing. Confirmation uses a separate control and safe arrival focus; repeated initiating clicks or keys cannot confirm a stop. In the plain console, Ctrl-C opens confirmation; repeated CANCEL does not confirm. EOF or a broken terminal still requests an immediate system stop because input is unavailable. UI failure also keeps the existing system-stop recovery. These emergency paths cannot offer interactive confirmation.

The browser preview simulates confirmation, stopping, and stopped states; no disk is touched. Its sample erase may finish while confirmation is open. Deep links `#s=stop_confirm&disk=0`, `#s=stopping&disk=0`, `#s=stopped&disk=0`, and `#s=stop_unconfirmed&disk=0` show the states; stop-unconfirmed is a static failure example, not an engine test. Native preview results retain their explicit “nothing erased” evidence contract. A power or process loss never implies a completed erase or restores files; recovered evidence remains authoritative.

### Support code when a report cannot be saved (#106)

Blocked, empty, diagnostic, last-chance start failures, graphical-unavailable What, and live Finished screens where the report was not saved show a **Support code** and **Build** line in monospace, plus a **Save code** when the on-screen refusal is a known export failure. The values are non-sensitive: no disk serial, path, or translated problem text. Labels follow the chosen language; the code (`BW-` family token) and build id never do. Progress copy (checking, verifying, saving) does not become a save code. Browser preview shows sample codes on blocked/empty only; its Finished screens stay preview and do not simulate a live export failure. Console and the screen-reader view use the same text, without a QR of the code. The offline helper tells the owner to read those on-screen lines. Kiosk recovery cannot generate them.

### Photo record of the erase (#127)

Live Finished screens show **Keep a record without a USB**: a QR code plus the
same summary as text, so an owner without a second USB can photograph it. A
phone camera shows the code as plain text; it holds no link, needs no app or
network, and is never written anywhere (not the target, not `/tmp`). Lines, in
the session language and with the labels RESULT.txt uses: a header saying it is
a summary, not a certificate; **Result** (the on-screen outcome exactly, never
shortened; Quick zero says verification was not performed); **Disk**,
**Capacity** and the identifier the disk card shows (**Serial number**, or
**Hardware ID** when the disk reports no usable serial); **Method**;
**Started**/**Ended (clock not verified)** from validated evidence when the
clock reading is available; the on-screen **Elapsed** line when known;
**Report** (saved to USB with the first 12 characters of the result.json
checksum, saved as a sharing copy, not saved, or could not be stored); and the
Beamo Wipe version, short build id and nwipe version. Values come from this
session's validated evidence and the result-screen disk card; untrusted text is
flattened to one line and capped at 64 characters with a visible
"(truncated)" marker. The code uses error correction M, a 4-module quiet zone
and a UTF-8 ECI header so accented languages decode correctly.

It appears only on DONE once the outcome is final: not while evidence is being
prepared, not when **Stop could not be confirmed**, and not while any pinned
nwipe may still be running. If the on-screen result cannot be repeated exactly,
no record is shown. When evidence cannot be saved, the record repeats the
downgraded on-screen result and says the full report could not be stored.
After a verified USB export the record updates to name the saved report.
Preview shows a sample that says nothing was erased and holds no disk identity.

Tk draws the code at 4 px per module (smaller only if the content column is
narrower than the code) beside or above the text, after the next steps and
any check warnings for every outcome, so it never pushes guidance or a
"not a pass" warning further down. Nothing in it is a Tab stop, so Shut down →
Show more → Save report stays two Tabs. The GTK screen-reader view adds a
**Keep a record without a USB** heading, the code image (accessible name says
the text follows, not focusable) and one focusable label with the summary.
Curses pages the text summary after the report status and warnings; the plain
console prints it verbatim. Neither draws a terminal QR, which does not fit
80×25 reliably. The browser preview shows the same sample record.

### Confirmation characters (#129)

Confirm asks the owner to type characters they must read from the selected
disk's card, so a copied number cannot stand in for checking the disk. The
rule lives in `safety.confirm_spec`; every surface uses it.

- **Field.** The identifier the card shows: the reported serial number, or
  the hardware ID (WWN, as lsblk printed it) when no serial is reported.
- **Count.** The last 4 characters. If another listed disk (including the
  protected Beamo USB) has a serial or hardware ID ending with the same
  characters, or the ending equals another disk's size label, full
  identifier or a kernel name, take one more character until it is unique.
  The prompt then adds "Another listed disk ends with the same last 4
  characters, so more are needed." When every character is needed it asks
  for the whole serial number or hardware ID.
- **Characters.** ASCII letters and digits only. An identifier that is
  missing, shorter than 4, or whose ending contains a space, punctuation or
  a non-ASCII character keeps the older rule, which prints the token in the
  prompt: the size label, or for same-size disks a unique serial ending,
  full serial or hardware ID. If nothing is unique the disk cannot be
  confirmed. A fallback is never weaker than before.
- **Prompt.** "Type the last 4 characters of the serial number shown
  above." (or hardware ID), never the characters themselves.
- **Mark.** Tk boxes and underlines the characters in place over the card's
  serial, with a pale fill. GTK underlines (double), bolds and tints them in
  the identity text, which is focusable on Confirm so Orca can read the
  serial character by character; the entry's accessible name is the full
  instruction. Curses, the plain console and text fallbacks put them in
  [brackets]. The web preview uses a `<mark>` with outline and underline.
- **Comparison (#156).** Leading and trailing whitespace is ignored and case
  does not matter. Nothing else is relaxed: no partial match, no inner
  spaces, no auto-fill, and another disk's characters never match.
- **Binding.** Erase now recomputes the characters from the rediscovered
  disk list. A changed serial, size, hardware ID or path is rejected as
  before; a newly listed disk that shares the ending makes the typed
  characters too short, so authorization fails closed.
- The token is never logged, exported or placed in a support code.
