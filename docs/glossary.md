# Glossary — one name for each thing

Every English surface uses the name in **Use**: wizard copy (`copy.py` and
the other modules that build screen, report and error text), the web
preview, the Boot helper (`helper/index.html`, shipped as `START-HERE.html`),
the launchers (`desktop/`), the USB's `README.txt`, and the user-facing docs
(`README.md`, `helper/README.md`, `docs/screen-reader.md`). The words in
**Not** are banned there. Translations follow the same split; their words
are in [translations.md](translations.md#glossary).

`tests/test_glossary_180.py` reads the table below and fails when a banned
word appears on one of those surfaces. To add a word, add it to the table;
to make an exception, add it to that test's `ALLOWED` list with a reason.

| Use | For | Not | Notes |
|---|---|---|---|
| **erase**, **erasure** | Overwriting a disk with nwipe | wipe, wipes, wiped, wiping, shred, scrub | The product name **Beamo Wipe** and the engine name **nwipe** never change. |
| **disk** | Storage that can be erased: hard disk, SSD, NVMe, USB disk | drive, drives, hard drive, storage device, target disk, erase disk, selected erase disk | **Hard disk** and **SSD** name a kind of disk. The disk chosen to erase is **the selected disk**. |
| **computer** | The computer that starts from the Beamo USB, and the one running a launcher | PC, PCs, machine, machines | "PCs" stays only in the hardware-scope phrases that mirror [claims.md](claims.md): "Windows or Linux PCs", "Windows and Linux PCs", "x64 PCs", "UEFI PCs". |
| **Beamo USB** | The USB stick the computer starts from; it is never erased | boot USB, Beamo boot USB, startup USB, start-up USB, boot stick, original USB, live USB, Beamo stick | Code and evidence keep "boot device" for the device the kernel started from. |
| **report USB** | The separate USB stick that receives the saved report | second USB, export USB, report stick, evidence USB | "A separate USB stick" may describe it before it is inserted. |
| **USB stick** | Any USB flash storage, in general | flash drive, thumb drive, pen drive, pendrive, memory stick, USB key, USB drive | |
| **Check disks again** | Reading the disk list again (clears preparation) | refresh, refreshes, refreshed, refreshing, rescan, re-scan, scan again, reload | Code keeps `Screen.REFRESHING` and `finish_refresh`. |
| **Shut down**, **shutdown** | Turning the computer off from the wizard | power off, power down, switch off, turn the computer off, turn off the computer, turn the PC off | "Fully off" describes the state after shutdown. |
| **boot menu**, **boot-menu key** | The firmware's one-time start-up menu and the key that opens it | startup menu, start-up menu, boot selection menu, one-time boot menu | |
| **Boot helper** | The offline page: `START-HERE.html` on the USB, `helper/index.html` in the source | offline helper, helper page, boot-menu helper, start page, offline page | Its file name stays `START-HERE.html`. |
| **launcher** | `Start Beamo Wipe.exe` and `Start Beamo Wipe Linux` | | Launchers never erase. |
| **Final check** | The last screen before **Erase now** | last chance, last check, review screen | Code keeps `Screen.LAST_CHANCE`. |
| **Erase now** | The separate action that starts the erase after the countdown | | Reaching zero only enables it. |
| **Stop erase** | Asking nwipe to stop | | |
| **Support code** | `BW-{S\|R\|E\|X\|U}-TOKEN`, read aloud to support | help code, reference code, ticket number, case number | Contains no serials. |
| **Diagnostic report** | The separately labelled report when an erase cannot start | system report | Not erase evidence. |
| **Text size** | Standard, Large, Extra large | font size, zoom | |
| **High contrast** | The colours-only theme; its pair is **Standard contrast** | | Not "Standard", which is a text size. |
| **screen-reader view** | The GTK/Orca view (F8) | accessible view, accessibility view, Orca view | |
| **Help & settings** | The fixed menu first in every footer (F10) | settings menu, help menu, options menu | "Help & settings menu" is fine. |
| **Everyday**, **Three overwrites**, **Quick zero** | The three methods | quick erase, zero fill, zero-fill, three passes, three-pass | No DoD certificate claim (see [claims.md](claims.md)). |

## Not renamed

- **nwipe** (engine, binary, logs and its output text), **Beamo Wipe** (product).
- Internal identifiers and APIs: module, function, screen and field names
  (`Screen.REFRESHING`, `Screen.LAST_CHANCE`, `boot_device`, `wipe_lock`,
  `_wipe_request`), environment variables (`BEAMO_WIPE_*`) and file names.
- Some guard and engine text in `safety.py` and `nwipe_runner.py`. Both
  modules are checked like the others, and the guard messages that reach a
  screen (the Beamo USB appearing as a disk) use the names above in every
  language. Kept, each listed in the test's `ALLOWED` with its reason
  (`safety:` review, 2026-11-07):
  - nwipe's own output that the runner matches ("…not wiping it");
  - the completion summary "nwipe exited without wiping", which is saved as
    the evidence `failure_reason`;
  - refusals the owner never sees ("A wipe is already running.", the wipe
    lock messages, "Unknown wipe method.", "No target disk selected.", the
    optical-drive and log-on-target-disk refusals): the wizard shows its
    own message, such as "An erase is already running." or the preflight
    refusal, never the exception text.
- Legal text (the GPL written offer) and quoted names from other software
  (Windows **Use a device**, OVMF/QEMU options).
