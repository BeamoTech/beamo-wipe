# Screens

Every interface uses the same Wizard authorization and validated result model.

Wayfinding uses three stages, not eight equal pages: **Preparation** (keyboard through the last review), **Erase** (the long destructive operation, including stopping), and **Result** (finished, failed, or stopped by you). The header names the stage and, while preparing, the step (#130): **Step 1 of 6 · Check keyboard**, **Confirm ownership**, **Choose a disk**, **Confirm its identity**, **Choose a method**, **Final check**. The steps are the wizard's Back order (`wizard.PREPARATION_PATH`), so the bar cannot drift from the screens; Review is the last step before Erase, so its step name is **Final check** (#166): it says this is the final step, and it does not say erase (#138). The stage stepper keeps **Preparation** highlighted, because Review is still preparation; *Preparation, step 6 of 6: Final check.* is what screen readers hear. One vocabulary (#138): the start screen's roadmap names the same stages from the same source, **Preparation (6 steps) → Erase → Result** (`copy.roadmap_parts`: `JOURNEY_LABELS` plus the `PREPARATION_PATH` count) on Tk, the screen-reader view, both consoles, the web preview and the offline helper. Screens that stand in for a step (no disks, nothing safe to pick, the final re-check after Erase now) show that step; detours (keyboard check, I'm not sure which disk, Advanced, storage limits, report help) show the step they return to; busy, recovery, erase and result screens show only their stage. The first strip segment fills step by step. Narrow windows or long translations shorten the caption to **Step 3 of 6** rather than cut it. Screen readers hear *Preparation, step 3 of 6: Choose a disk.* as the heading description; the console header shows the same text. Wipe percentage appears only on the working screen and is never the journey chrome. **Stop could not be confirmed** stays in Erase because the disk may still be erasing. Recovery overlays (refresh confirm, shut down confirm) keep their own screens.

Primary actions name the next step: **Choose a disk**, **Review this disk**, **Choose erase method**, **Review before erasing**. They never say the erase has started. **Erase now** stays on the last review after the countdown. Splash and keyboard keep **Continue**. Advanced uses **Back to methods**. The screen-reader picker has no footer Continue: choosing a disk is the next action.

| Screen | Purpose |
| --- | --- |
| Header power badge (#144) | Every screen with a header shows a power badge after the brand, from the existing non-blocking power monitor (one worker, 5 s refresh, stale readings become unknown): **Plugged in ✓** only when wall power is reported online; **On battery — plug in** (amber) when wall power is reported off and a battery is present; **Mains power** for a complete reading with no battery (desktop); otherwise **Power: unknown**. Text always states it (✓ only for plugged in; no emoji: the live fonts may lack it). It updates live (Tk redraws only the header when it changes). GTK: a focusable line read as "Power: …"; curses: "[On battery — plug in]" on the header line; web preview: a header badge. The Owner screen no longer prints the long power sentence; Review, Checking, Working and Stopping keep their power warnings. The splash has no header and no badge. |
| Owner report line (#145) | The report notice on Owner is one line: "Want a report? You can photograph a summary at the end, or save it to a second USB when asked." with a **Learn more** link that opens Need a report? (Tk: Tab reaches it after the ownership box; GTK: a button named "Learn more about saving a report"; curses: "R: learn more"; web preview: a link). Media rules (FAT32/exFAT, one volume, keep it unplugged until asked, what to do if inserted early) are in Need a report?. A wanted, unsaved report still makes Shut down ask first (#25). |
| Method: Everyday caveat off the card (#160) | "This checks only storage the disk exposes. It does not promise how long it will take. A saved report is not extra proof of hidden areas." is no longer on the main Everyday card. docs/claims.md and docs/storage-and-controller-limits.md do not require it there; the method-selection warning they do require (the storage limits notice and "Storage limits (L)") stays on the Method screen. Tk and the web preview show it under the Everyday card's own Show more (#159); GTK puts it in a collapsed Show more expander named "Show more: Everyday" (Orca reads it when expanded); the plain console prints it after the three choices as "Everyday: …" instead of inside Everyday's line; curses already pages it after the choices (Up/Down to read more). The wording is unchanged. |
| Method: cards compare at a glance (#159) | Each method card shows its title (with the Recommended / Rarely needed (#161) / No check chip), one sentence, and a time line for this disk: the existing cautious range ("Rough guide for this 256 GB SSD (not promised): 5–60 minutes.") or "Time depends on the disk." when the size is unknown. The overwrite and check counts, the Three overwrites note and the Everyday limits note sit under the card's own Show more, which only shows or hides them: it never chooses a method (click the card or press 1/2/3). Last chance still states the exact counts. GTK and both consoles keep their one-choice-per-line layout and now give every method its time line, unknown size included. Measured at 800×600: cards 140–180 px → 102–107 px. |
| Confirm: balanced layout (#157) | On a window with room to spare (1024×768, 1280×720, 1280×820, 1280×1024, 1920×1080, Large text at 1280×820) Confirm's block is centred vertically instead of leaving a large empty area under the entry. It is measured as if the wrong-entry help were showing, so nothing moves when that help appears: the space under the status line is where it appears. On short windows and larger text (800×600 at every text size, 1024×600, Extra large at 1280×820) Confirm's gaps are tighter (the warning keeps its full-size text), the #156 feedback ("You typed: 3 4 [7] 6" / "Character 3 doesn't match.") is the status line right under the entry with a "!" mark, and the view never scrolls the disk card or the #128 warning out of view: the card, the warning, the entry and its status stay visible before and after a wrong entry; the keyboard help and Change follow below (Tab or scroll). Measured before/after (gap under the status, empty Confirm): 1280×820 190→134 px with 72 px above the title (was 16), 1920×1080 391→238 with 171 above; 800×600 Extra large after a wrong entry: warning hidden → visible. |
| Confirm: keyboard help after a wrong entry (#155) | The "Keyboard: … · Language: …" line is gone from Confirm. After a wrong entry (a complete entry that does not match, or Enter/Continue on a non-matching one) Confirm shows "Not matching? Check your keyboard layout (currently QWERTY (US))." with **Change** (Tk, GTK and the web preview: a button that opens the keyboard layouts; curses: F2; plain console: K). It stays for that visit until the entry matches; a new visit starts hidden. Tk scrolls it into view on short windows and large text. Changing the layout from Confirm keeps the owner tick and the chosen disk (nothing is authorized before Method), never changes the confirmation characters (they come from the disk), clears only an entry that does not match, and returns to Confirm; method choice, the five-second review and Erase now still follow. A layout change from Method or Last chance still starts over from Owner, as before. |
| Pick a disk: encryption tag (#154) | A disk whose partitions or opened volumes lsblk already reported as FSTYPE BitLocker or crypto_LUKS gets a tag, **BitLocker (Windows encryption)** or **Encrypted (LUKS)** (both when both are present), to help an owner recognise the main disk. Nothing new is read: the tag comes from the same lsblk facts as the #147 contents line. Tk and the web preview put it on the one-line row after the connection and as an outlined tag on the selected disk's card; GTK shows it under the disk button and adds it to the spoken name; curses and the plain console print it on its own line under the serial. Display only: eligibility, identity and the confirmation characters do not change, and the copy says nothing about unlocking or recovery. A file system written to the whole disk without partitions (for example LUKS on the raw disk) is not among the components and is not tagged. |
| Key-cap hints (#153) | Footer hints show key names as key-caps (Tk on roomy windows, the web preview). Every cap has the same look: the arrow caps (↑ ↓ ← →) are drawn in the same ink as the lettered caps (Tk canvas arrow, preview SVG) instead of a font glyph that came out thin and tinted orange; the preview still names the arrow to screen readers. No hint sentence ends on a key in any language: Pick reads "Click a disk, or use ↑ ↓ to choose one. Enter reviews this disk. Esc goes back." and Confirm "Type exactly what we ask for, then press Enter to continue."; punctuation that does follow a cap sits against it. Short windows and larger text keep the plain-text hint; GTK and the consoles show key names as text. |
| Pick a disk: differing serial characters (#152) | When another eligible disk has the same displayed size, the selected disk's serial shows which characters tell it apart. Each pair of same-size disks is compared: the shared beginning and ending are set aside; if what remains has the same length on both sides only the characters that differ count, otherwise all of what remains does. A disk's marks are those characters against every look-alike, so 2, 3 or more similar disks and serials of different lengths work; a same-size serial that shares nothing with it adds no mark (and no longer hides the look-alikes' marks). Tk and the web preview show the serial in regular weight with those characters **bold and underlined** (a shape, not only a colour); GTK bolds and underlines them on the disk button; curses and the plain console keep [brackets], since terminal bold/underline can render as colour only. The note under the serial, also in Orca's name for the disk button, says where: "Differs from the other 512 GB disk at characters 7 and 11. Check the full ID before choosing." ("the similar 256 GB disks" when there are more). A serial that is a shorter copy of a look-alike's keeps "Serial number has 14 characters; other serials are longer." Display only: identity, eligibility, the confirmation characters and Confirm's own marks (#129) are unchanged. |
| Pick a disk order (#151) | Every view (Tk, GTK/Orca, curses, plain console, web preview) lists the eligible disks in one order: internal disks first, then external. Groups: NVMe, SATA, SAS or virtio disks the system does not report as removable or hot-pluggable; then the same connections reported hot-pluggable (a dock, an enclosure or a hot-swap bay; location is not guessed); then any other eligible connection; then USB. Within a group: connection (NVMe, SATA, SAS, virtio), model, serial number, WWN, capacity and, last, the device path. The order depends only on the disks, never on the order the system listed them, so Check disks again over the same disks gives the same list. ↑/↓, the plain console's numbers and the Compare disks "Disk N" numbers follow it. Selection, the confirmation characters and authorization stay bound to the disk itself (path and identity), never to a list position. The protected Beamo USB keeps its place (after the list in Tk and the web preview, first in curses, before the list in GTK). Example: NVMe SK hynix, SATA Samsung SSD, hot-plug SATA Toshiba, USB SanDisk, USB WD Elements (path order had the WD Elements second). |
| Pick a disk: double-click or Enter reviews (#150) | Double-clicking an eligible disk, or pressing Enter with it selected, does exactly what **Review this disk** does: it opens Is this the right disk? for that disk with an empty confirmation box. The owner still types the characters, chooses a method, waits out the five-second review and presses Erase now. A double-click counts only when both presses land on the same disk (by device path, since rows move when the chosen one expands), within 0.5 s and 8 px; otherwise each press is a plain click that selects the disk under it. For 0.5 s after a double-click opens the next screen, further mouse presses are ignored, so the double-click cannot also press a button there. A disk that cannot be confirmed (identity too similar to another) stays on Pick with the reason, exactly as with the button. The protected Beamo USB card and Other detected devices are never chosen; Enter in that read-only list does nothing. Tk: double-click on a row, Enter (with ↑/↓); GTK/Orca: activating a disk button (Enter, Space, click, Orca's press) is its row activation, and the rest of a mouse double-click is ignored on the next screen; curses: Enter on the highlighted disk, a held Enter cannot act again; plain console: typing the disk's number; web preview: double-click or Enter on a disk card (Space only selects). The footer hint already says "Enter reviews this disk"; no copy changed. |
| Pick a disk compact rows (#149) | In the Tk wizard and the web preview each eligible disk that is not selected is one line: model, kind and connection, the contents summary (#147) and capacity, for example **Samsung SSD 970 EVO · SSD · NVMe · "Windows" (NTFS) 255 GB · FAT 1 GB · 256 GB**. Text wraps and is never cut. Choosing a disk (click, or ↑/↓) expands only that row into the full card: serial number with the #148 marks and note, connection note, contents hint, the partitions under "On this disk (cannot be erased separately)", and, when another eligible disk has the same size, a **Compare disks** link on the heading line that opens the read-only Compare disks panel and moves focus into it. The selected row keeps its blue outline and tint. ↑/↓ move the selection through the list in its shown order (#151) and select by disk (path), never by a stored position, so a re-ordered discovery result keeps the same disk chosen. The protected Beamo USB keeps its full card with the protected banner (#61). Devices that cannot be erased stay in the read-only Other detected devices list with their reasons. Visible whole rows with six eligible disks and the same-size warning, nothing selected: 800×600 Standard 6, Large 5, Extra large 4 (French: 6, 4, 2); 1280×820 all six at every text size (French Extra large 5). With a disk selected the list keeps the expanded card in view; at 800×600 Standard 4 to 5 whole rows stay visible, and at least 3 with the fullest card (same-size note, contents hint, partitions, Compare link) while the warning is also in view. The GTK/Orca view and the curses and plain consoles keep the full identity on every disk (Orca reads one disk button at a time; the console pages its list), with the same facts and the same path-based selection. |
| Pick a disk serial, once (#148) | (Since #152 the marks are per character and bold and underlined; see that row.) The disk card shows its serial number once (since #149, on the selected disk's expanded card), after the label **Serial number**, never shortened (it wraps). When another listed disk has the same displayed size and the serials share a beginning or ending, the part that differs is in [brackets] on the card (Tk, curses, plain console, web preview), for example **S4EVNX0N[111111]**, and the note under it names only the positions: "Compare characters 9 to 14 with other disks of this size. Check the full ID before choosing." It never prints the characters again. When nothing is shared at either end there is nothing to mark, so there are no brackets and no note; the same-size warning above the list still shows. GTK/Orca reads the plain serial once in the disk button's name, then the note. The read-only **Compare disks** panel, which lists every serial again for side-by-side reading (and is the selectable, character-by-character reader in GTK), stays collapsed until opened; the plain console now opens it with **C**, like curses. Display only: confirmation characters, eligibility and identity checks are unchanged. |
| Pick a disk contents line (#147) | Each disk card says what is on it in one line after "On this disk (cannot be erased separately):", for example **Windows (NTFS) 237 GB · Recovery 1 GB · +2 more**, **"Photos" (NTFS) 1 TB**, **"home" (ext4) 247 GB · Swap 8 GB · EFI system 1 GB** or **Unknown format 32 GB**. Display only, from the lsblk JSON discovery already reads (LABEL, PARTLABEL, FSTYPE, FSVER, PARTTYPE, PARTTYPENAME); nothing is mounted or probed, and the facts never reach eligibility, exclusion or identity comparison. Per component: an OS partition type is named (EFI system, Microsoft reserved, Recovery); otherwise the volume label (or a non-default GPT name) in quotes, the friendly format (NTFS, FAT32, exFAT, ext4, APFS, HFS+, Swap, BitLocker encrypted, LUKS encrypted; Unknown format when missing or unrecognised) and the size. The single unnamed NTFS or BitLocker partition beside a Microsoft reserved or Windows recovery partition reads **Windows**; with two candidates nothing is guessed. Largest first, two shown and "+N more" (three shown when only one more would be hidden); a component with a reason (mounted, protected) is never folded away. Labels are untrusted: Unicode-normalised (NFKC), control, bidi and zero-width characters removed, whitespace collapsed, quote marks replaced, stacked accents limited, capped at 24 characters with an ellipsis, always quoted and followed by format and size, so a label such as "Beamo USB (protected)" cannot pass for interface text. Labels with control characters still make discovery leave that disk out, as before. Tk and the web preview show the line (escaped in HTML); GTK shows it as a focusable plain-text label and adds it to the disk button's accessible name, so Orca reads it; curses and the plain console print it. Same text on the protected Beamo USB card and under Other detected devices. |
| Owner platform line (#146) | "For 64-bit Intel/AMD Windows or Linux PCs that start from this USB. Not Apple Silicon Macs. Not Chromebooks." is pre-boot guidance: by the time the wizard runs, the PC has already started from this USB. Owner's main view keeps the two bullets about what is erased and backups; the platform line leads the **Show more** panel (Tk and web preview), sits in a collapsed **Show more** expander with a focusable label (GTK), and follows the supporting notes, just before the ownership box (consoles). It stays up front where it helps before boot: the desktop launchers, the offline helper pages, the boot card, README and `docs/claims.md` listing copy. `docs/claims.md` is Amazon/pack copy and does not require it on this screen. |
| Owner (#143) | While the ownership box is clear, "Tick the box above to continue." sits beside the greyed **Choose a disk** (Tk: same footer row, left of the button; GTK: a focusable line and the button's accessible description; curses: above the footer keys; web preview: beside the button with aria-describedby). Ticking the box removes it; the owner_ok gate is unchanged. The improved disabled style of #178 is not in this repo yet; the existing disabled colours are kept. |
| Splash / Keyboard | Splash opens with "Erase a disk in a few steps. Nothing is erased until you choose Erase now." (#137): it names the one control that starts an erase, so nothing starts automatically. Keyboard offers only the shipped US, UK, Spanish, Latin American and Italian QWERTY, French AZERTY, and German QWERTZ layouts (Up/Down; keys 1–7 outside the check box) plus a typing-check box that is never saved. The language comes first on that screen, before its title, in focus and on screen (#131): a *Language · Langue · Sprache · Idioma · Lingua* label and English, Français, Deutsch, Español or Italiano, each in its own name. Left/Right or Space choose a language; Enter still continues. Choosing a language re-renders every screen element (header step, footer hint, buttons) and sets that language's usual shipped layout (`keyboard.LANGUAGE_LAYOUTS`: English → QWERTY (US), French → AZERTY (French), German → QWERTZ (German), Spanish → QWERTY (Spanish), Italian → QWERTY (Italian)) with a visible line such as *Keyboard set to AZERTY (French) to match Français. Keys do not match? Choose your keyboard below.*; English names QWERTY (UK) and Spanish names QWERTY (Latin American) as the obvious alternative, and no other layout is guessed. A layout the person picked is kept (*Keyboard stays …, the layout you chose.*). When the language changes after the owner box, a disk or a typed confirmation, the layout stays so those stay valid, and the line says so; a layout change still clears them, as before. Orca speaks with its configured voice: switching Orca's speech language with the UI language is not implemented (see the task record). |
| Owner | Combined introduction: say once what the tool does (it erases everything on the disk you choose, including any Windows or Linux), remind about backup copies, give the wall-power reminder (the display-blanking note shows only on the console fallbacks: the X screen stays lit while erasing, #168; supported PCs are under Show more, #146), then require the ownership or written-permission acknowledgement. Continue stays disabled until the box is checked. Between the bullets and the power panel, Owner says the result screen shows a code to photograph (no second USB needed) and states the full report's media requirements up front: a separate FAT32 or exFAT USB with one volume, kept unplugged until the result screen asks, with already-plugged media refused, and points to Need a report? for details. |
| Pick a disk | Physical disks are primary cards. Partitions and other technical components nest under their parent when parentage is known. Keep eligible targets separate from read-only Other detected devices. Show a concise inventory count so the owner can check that expected disks were found, including zero, one, or many eligible disks, protected boot media, other devices that cannot be erased, and a fail-closed notice when the list cannot be confirmed. Show identity, the observed connection type, and deterministic exclusion reasons. Label each serial as Serial number so the value is not a bare string. Do not guess internal vs external location. Capacities use decimal GB, with an exact-tenth TB name when it does not collide; unknown media kind is labeled Type unknown. No excluded row offers a bypass. Empty or uncertain discovery gives safe support steps. When a report was requested, an info notice reminds the owner to keep the report USB unplugged until prompted, warns that extra USBs confuse the list, and gives the unplug-only-that-USB remedy; without a requested report no notice shows. |
| Confirm | Show exact device identity and one warning box naming the selected disk by model and size: everything on it will be erased (including Windows or its operating system when partitions show one), and it cannot be got back. Ask for the confirmation characters by field and count, never by printing them; they are marked in the disk card (see Confirmation characters). |
| Choose an erase method | Show a plain-language lead, then the operations below, comparison marks, and the device-specific storage notice. Everyday states it checks only exposed storage and does not promise duration. SSD and unknown-device warnings explain inaccessible, remapped, over-provisioned and controller-managed storage; additional overwrite passes do not fix those limits. |
| Supported storage limits | Full offline limits, reached directly from method selection. Back returns to the chosen method. |
| Review before erasing | Emphasize selected disk and plain method operation. The method is stated once (#164): its name and the operation summary (#33), e.g. "Everyday: One overwrite, followed by verification." or "Quick zero: One overwrite. Verification is not performed."; the pass-by-pass detail line is no longer repeated here (Working and Done keep their method lines; Advanced keeps the nwipe names). The red callout is the only erase warning: the Confirm sentence with the serial or hardware ID added. It stays above the fold at 800×600 and every text size. A small countdown marks a fresh five-second review period: zero only enables Erase now and never starts erasure. The lead says so in the owner's terms (#162): "Check the selected disk and method. Erasing starts only when you press Erase now." When the review period ends the ring shows a check mark, never "0", and "Ready" heads the caption (#163; a word, not the icon alone). GTK shows an alert "Ready. Erase now is available." without moving focus, so Orca announces it; curses says "Ready. Erase now is available.", the plain console prints "Ready. Erase now is available." before its ERASE prompt, and the web preview shows the check mark, the word and a polite status. Zero still only enables Erase now. **Enter on Review (#165)** presses only the focused button on every graphical and curses surface, and focus starts on **Back**: Tk (Erase now cannot take focus until it is enabled; Tab to it, then Enter or Space), GTK (Enter clicks only a focused, enabled action; arrival focus is the warning), and curses, which shows `[> Back <]    [ Erase now ]` with the same hint as Tk ("Esc goes back. Tab to Erase now, then Enter after the countdown."): Tab, Shift-Tab, Left or Right move the highlight, Erase now takes it only on a painted ready frame, a restarted countdown returns it to Back, and Enter on Back goes back, during or after the countdown. The plain console still requires typing ERASE (any other answer goes back). Held or auto-repeated Enter never counts as a new press on any surface. Require explicit activation. |
| Working | Keep device identity, the method summary, and progress visible. Remind the owner to leave the USB in and keep wall power connected. Choose **Stop erase** (Tk/GTK button or Escape; plain console `CANCEL` + Enter; curses Esc) to review a warning: stopping cannot restore files already erased. **Keep erasing** dismisses the confirmation. Confirm with **Yes, stop erasing** (plain console `STOP` + Enter; curses S). Progress polling continues during confirmation, and completion takes precedence over stale confirmation actions. **Stopping erase** means exit and cleanup are still pending; the stopping and stop-confirmation screens keep the same disk identity and method summary visible instead of showing timing text alone. **Stopped by you** is a confirmed interruption, not a completed erase. **Stop could not be confirmed** stays on Working with a prominent warning because the disk may still be erasing. Interruption and inability to confirm a stop remain distinct outcomes. Shut down is not offered while an erase may still be running. Progress reads at a glance (#132): a large percentage (never 100% on this screen; the result screen reports completion), then one cautious time line, then the current step, for example 23% / Running for 25 minutes / Step 1 of 2: Overwriting, and later 61% / About 40 minutes left / Step 2 of 2: Checking (verification). Three overwrites shows Step 2 of 4: Overwriting (pass 2 of 3); Quick zero has no verification step, so it shows Step 1 of 1. Before the engine reports a number the large line says Starting… over an indeterminate slide; a line with no real data (unknown phase, a step that cannot be located yet) is hidden rather than shown as "not reported". The time line shows About … left only when the estimate passes every gate in [progress timing](progress-timing.md) (rounded up, no seconds); otherwise it shows how long the erase has run, and on the first steps a small note says time left appears during the last step. The current step is located from live engine phase and pass counters cross-checked against the plan; a report that disagrees with the plan shows a warning instead of a guessed step. Verifying, Syncing, Retrying, and Finalizing add a one-line note explaining the transition and that the erase is not done until the result screen. When progress updates go stale, the percentage is marked old and a warning band says how long it has been quiet, explains that a quiet screen does not mean the erase stopped, and gives safe next steps (keep the USB in and wall power connected, do not turn off, Stop erase stays available); it never recommends restarting, unplugging, or retrying the wipe. The Stopping screen shows the last known step and the elapsed time, with no estimate. Curses shows the same three lines first; the screen-reader view puts them in one focusable label (large first line) beside a progress bar named Erase progress, and both it and the plain console change that summary when the step changes, progress goes quiet or resumes, or stopping or finishing begins, and otherwise at most once a minute. Walk away (#133): the screen offers **Play a sound when it's finished** (Tk footer check box; GTK check box; curses O key; plain console SOUNDS word) beside **Hear sounds**. It is the same session setting as the result screen's Sounds on/off: each erase turns it on unless the person has already chosen on or off themselves this session, and the state carries to the result. An availability check (unmuted output found) runs on the audio worker when Working opens and every minute after; only when it succeeds does the screen promise "You can leave the computer. It will beep when it's done." While checking, or with the toggle off, it says "You can leave the computer and check back later." With no output, a muted output, or in the preview it says "Sound isn't available on this computer — check back later.", gives the reason, and greys the toggle. The existing laptop advice (keep wall power connected, lid open) follows that line once. Nothing plays until the outcome is final. |
| Finished | Use validated evidence and the canonical explanation in `outcomes.py`. The main heading is the specific erase outcome in plain words (#134; `outcomes.plain_result`), never a generic label: **Done — this disk was erased and checked** (verified: Everyday or Three overwrites), **Done — this disk was overwritten with zeros (not checked)** (Quick zero; never "checked" or "verified"), and for other outcomes a short "Not finished — …", "Not confirmed — …", "Stopped — …" or "Nothing erased — …" line. The canonical status message (for example "Erase completed; verification passed") is unchanged and stays the technical status line: evidence, the saved report, the photo record and support keep it, and the screen shows it under **Technical details** (Tk: behind Show more; GTK: an expander; consoles: after the support identity). Failed, cancelled, and unconfirmed outcomes then show three labeled recovery sections in screen-reader order: **What happened** (the exact message), **What it means for your disk**, and **What to do next**. Technical details stay behind an on-demand control and never replace those three. Verified and Quick zero results instead show a one-line note (what the check covered, or that Quick zero was not checked; the SSD controller limit; other disks were not erased) and a numbered **What next** list: shut down when finished; remove the Beamo USB once the computer is off; keeping the computer, install an operating system if this was its main disk; giving it away, verified: ready to pass on / Quick zero: erase again with Everyday first. The list replaces the former next-step paragraph and the separate start-up note, so neither is said twice. The erase badge, message, and details stay independent of the **Save a report (optional)** panel, which identifies the report copy on its own. The erase badge uses the canonical outcome; a confirmed user stop still reads **Stopped by you** in the erase summary. The panel uses neutral information, an amber warning, or a distinct saved-copy treatment (a Saved label, a small in-panel check, report wording, and the safe-to-remove line) — never the erase-success badge or the red failure badge. Report copy checking is not disk read-back verification. The screen shows elapsed time, the method summary, the next step, the disk summary with Show more, and the guarded report instruction. Outcomes that refer the owner to support add the support destination (`beamosupport.com`) as text everywhere and a phone-scannable code on graphical surfaces; the readable report, its README, and the offline helper carry the same destination. The browser preview omits the block on its sample finished screens because those screens say nothing was erased and do not ask the owner to contact support. Failures, cancellation and indeterminate results do not claim a disk was processed. Quick zero completion explicitly says verification was not performed. Footer, live session (#135): two actions, **Erase another disk** and **Shut down** (both greyed while a report is saving or being prepared, with the reason on the line above; as before, shutdown refuses while nwipe may still be running). **Save report to USB** and **Retry evidence save** live in the report panel; **Sounds: on/off** and **Hear again** sit with the other settings utilities above the footer buttons (Tab reaches them). Footer, preview: **Close preview** and **Run again**. Key hints say exactly what Enter does (#169): preview "Enter runs the preview again." (Enter also runs it again in the web preview), live "Enter requests shutdown."; no result screen offers Esc or a way back into a completed erase. Console equivalents are the `SAVE` / `RETRY` / `SHUTDOWN` / `ANOTHER` prompts (curses: `R` and `E` shown in the panel, `A` and Enter in the footer); the screen-reader view exposes the same actions as native buttons. When sounds are on, the finished earcon plays for a verified erase and the attention earcon for any other final outcome (including Quick zero's unverified completion, interruption, and failures); it repeats every minute, at most five plays, until someone presses a key, clicks, or uses a control, turns sounds off, or leaves the result. Muted, missing, or preview audio stays silent; the curses and plain consoles ring the terminal bell instead when no output was found (not promised: many computers have no bell). Plain console rings once, because it waits for typed input. Hear again replays on demand. Unless the outcome proves nothing was erased (or is a finished outcome, whose What next list carries it), a conditional note follows the next step: if the erased disk was the one the computer starts from, the computer may not start normally and may need an operating system installed before reuse. The offline helper repeats this guidance in its after-erasing card. The **Save a report (optional)** panel (#135) guides export in five numbered steps with done/now marks: 1. insert a separate USB stick; 2. a live line from a read-only check ("Looking for a USB…", "Found: SanDisk Ultra, 16 GB (FAT32)", "More than one new USB stick is plugged in…", "This USB is formatted NTFS — use a FAT32 or exFAT stick.", or the precise refusal with its next step); 3. **Save report to USB**; 4. where it was saved and the file names; 5. remove the report USB. Save is greyed, with "Save is available when one suitable USB is found." under it, until exactly one eligible new stick is found; pressing it still runs the export's own two-scan checks. While saving, check and save read as current together because they run inside one export call; a failed save shows the precise error (What happened / What it means / What to do next) above the steps, and the live line looks for the stick again. When evidence saving failed, the panel moves up under the disk summary: the warning, **Retry evidence save** and the explanation stay in the first view. Every media rejection names the problem and the next safe step (replug, different stick, retry-then-support, retry-then-shutdown, sort-while-off, wait); reasons that already carry instructions and the diagnostic screen share the same mapping. |
| Advanced | Technician information and the report workflow guidance. |
| Shut down without saving? | Shown when a report was requested but no current verified export is confirmed. Keep session open returns; explicit discard authorizes shutdown. Below the loss text, ordered removal steps state which media can be removed, which must stay, and that the Beamo USB is safe to remove only after the computer is fully off, plus restart and unsure-media rules; the erase-another variant keeps the Beamo USB for the next erase instead. [State and recovery rules](report-shutdown.md). |

## Method operations

- Everyday: Overwrite the disk, then check the result.
- Everyday: 1 overwrite pass: random data. Then we check the last overwrite.
- Three overwrites: Overwrite the disk three times, then check the result.
- Three overwrites: 3 overwrite passes: a pattern, its inverse, then random data. Then we check the last overwrite.
- Three overwrites is marked Rarely needed (#161). Under its Show more: Three times the overwrites of Everyday, so it takes longer. Extra passes do not reach hidden storage. Everyday is the usual choice. This is not a DoD certificate.
- Quick zero: Overwrite the disk with zeros. This does not check the result.
- Quick zero: 1 overwrite pass: zeros. This method does not check the overwrite.
- Quick zero is marked No check.

Before erasure, **Check disks again** (F5) first shows that it clears the
selected disk, ownership acknowledgement, typed confirmation, method, and
countdown, and that preparation starts again from the beginning. Back keeps
those answers. Where it is offered (#136): not on What/Owner (no disk list
exists yet); on Pick and its empty, blocked and help screens as a normal
action (the dialog's Check disks again is focused; Enter or a second F5
accepts); from Confirm, Method, Review, Advanced and Limits only through a
guarded dialog — "Check disks again? This clears your confirmations and you
will start again from choosing a disk: you tick the ownership box again, then
choose the disk." — whose default focus is **Cancel**. Enter and Esc keep the
answers, a second F5 does nothing, and clearing them needs Tab to **Check
disks again** (curses: `C`; plain console: the typed words; a bare Enter
keeps them). The wizard refuses a direct rescan from those screens, so no
surface can skip the dialog. The Tk screen-reader switch (F8), which rescans,
opens the same guarded dialog there and opens the reader only after it is
accepted. Any accepted rescan still clears every confirmation exactly as
before; the automatic pre-launch rediscovery and identity comparison are
unchanged. Confirming then performs fresh discovery and boot
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

The keyboard check (#140) is guided and optional: "press the key labelled Z". The active layout turns that physical key into a character (Tk and GTK read the X keysym; the consoles compare the produced character). Z sits in a different place on QWERTY, QWERTZ and AZERTY keyboards, so one key tells them apart; within the QWERTY family letters and unshifted digits are the same, which is what the typed confirmation needs. Results: "✓ Letters and numbers match <layout>.", "That looks like <layout>. Switch to it?" with a one-click switch (curses F3, plain console SWITCH), or a hint when another key was pressed. It never switches by itself and never blocks Continue. GTK reads the prompt as the box's name and moves focus to the result (an alert) so Orca speaks it.

The layout fine print ("Only the layouts listed here are offered. The change lasts until this USB restarts. It does not change firmware or BIOS keyboards.") sits behind the shared **Show more** control under the chosen layout's note (#141): Tab reaches it between the layouts and the check box, and focus stays on it when it opens. GTK uses a collapsed expander named Show more with a focusable label inside; the web preview uses the same Show more link. The consoles have no disclosure control, so they print it after the layout list instead of before it.

Layout cards show their 1–7 number badges only while a card has keyboard focus, or once Up/Down or a digit has chosen a layout on this visit (#142); the cards keep their height either way. The shortcuts always work, the footer hint says "Up/Down or 1–7 chooses a layout", and GTK's button names keep the number ("1 QWERTY (US) (selected)"). The web preview hides them until the list has focus.

The keyboard screen also offers Standard, Large, and Extra large text. The
screen has three labelled parts in the order people need them (#139):
**Language**, then **Text size**, then **Check your keyboard** (layouts and
the typing check). Tab follows the same order on Tk; GTK marks Text size and
the keyboard part as headings; the consoles explain that text size applies
only to the graphical screens before the keyboard part. One screen rather
than two: a split would add a seventh Preparation step and an extra Continue
for everyone, and the reorder already gives each job its own section. The
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
disk details and check warnings.

### Save a report panel (#135)

Report saving is one guided panel on the result screen, offered only after the
result and only when the evidence gate allows a save. Detection runs on a
background thread every 1.5 seconds while a save is possible: one read-only
`lsblk` scan through the same baseline (boot USB and erased disk required) and
the same `select_export_volume` rules the export uses. It never mounts, opens
or writes a device and never blocks the UI; it stops while saving and after a
save. Only whole new removable USB disks with exactly one FAT32 or exFAT 1.0
volume are found; the boot USB and the erased disk never are. The owner sees a
model and size, never a device path or serial. The kiosk alone runs the live
check: previews and dry runs have none, and a test that injects an exporter
gets none unless it injects a probe (Save then checks the USB itself, as
before). A live change redraws the screen and keeps keyboard focus where it
was (GTK: from inside the panel, Orca moves to the new status line). The GTK screen-reader interface exposes explicit
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
the 80×24 curses console join each label to its body on one line so the
**Save a report** panel, the post-erase start note, and report-USB next steps
stay in the first viewport; stacked labels remain the full-height Tk, GTK/Orca, gallery,
helper, and plain-console layout. Tk Finished uses the outcome heading as
What happened (no second copy of that sentence) and shows the Result code as
a muted line rather than a button, so Tab still reaches **Save report to USB**
after **Show more**. GTK, gallery, and the helper keep an expander. Curses
pages the Result code after the report panel so the first 80×24 page keeps
the **Save a report** heading and its steps. Labeled meaning is in that paged tail;
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
- **Wrong entry (#156).** After a wrong entry (the #155 timing) Confirm shows
  what was typed with the wrong characters in [brackets] and says which:
  "You typed: 3 4 [7] 6" / "Character 3 doesn't match.", "1 character is
  missing.", "1 character too many.". A typed space is shown as ␣ and
  marked on its own ("Spaces between characters count; remove them.") so
  the characters after it are still compared in order. It never prints an
  expected character; the card already shows them. Display only
  (token_feedback.py, read through Wizard.confirm_feedback): the gate is
  token_matches. Tk shows it in the status line under the entry (#157) and the
  web preview above the keyboard hint;
  GTK as a focusable label whose spoken name lists the characters without
  brackets; curses and the plain console as two lines.
- **Binding.** Erase now recomputes the characters from the rediscovered
  disk list. A changed serial, size, hardware ID or path is rejected as
  before; a newly listed disk that shares the ending makes the typed
  characters too short, so authorization fails closed.
- The token is never logged, exported or placed in a support code.
