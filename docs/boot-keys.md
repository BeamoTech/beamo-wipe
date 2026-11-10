# Boot-menu keys: the one table (#184)

`desktop/bootkeys.json` is the only place the boot-menu key for each brand is
kept. Every list a person reads is made from it:

| Consumer | How it uses the table |
| --- | --- |
| Go launcher (`desktop/bootkeys.go`) | Embeds the JSON, matches the computer's reported brand, and shows one line such as "Most Dell computers: press F12 at power-on." |
| Launcher page (`desktop/web/index.html`) | The full table under **Show more** (generated region `launcher-table`). |
| Boot helper (`helper/index.html`, `de`, `es`, `fr`, `it`) | The key table and the short summary in "The boot-menu key does nothing" (regions `table`, `summary`). |
| Boot card (`docs/boot-card.md`) | The printed key table and brand notes (regions `boot-card-table`, `boot-card-notes`). |

To change a key: edit `desktop/bootkeys.json`, then run

```
python scripts/gen_boot_keys.py          # rewrites every marked region
python scripts/gen_boot_keys.py --check  # exits 1 if any region drifted
```

`tests/test_boot_keys_184.py` runs the same check, so a hand edit to any
generated region, or a JSON change without regenerating, fails the tests. The
Go tests (`desktop/bootkeys_test.go`) fail if the JSON is malformed, a brand
has no source, or the brand matching changes.

## Fields

- `match`: whole words that identify the brand in the reported manufacturer,
  after lower-casing and replacing punctuation with spaces
  ("Hewlett-Packard" becomes "hewlett packard"). A string that matches two
  brands, or none, names no brand.
- `placeholders`: firmware defaults such as "To Be Filled By O.E.M." that name
  no brand. Only then does the launcher look at the motherboard vendor, which
  is how self-built computers (ASUS, MSI, Gigabyte boards) are recognized.
- `keys` and `join`: one key, keys to try (`or`), or a sequence (`then`, for
  HP: Esc opens HP's menu, then F9 opens the list of boot devices).
- `note`: an English brand note for the launcher and the boot card.
- `launcher`: false for the Intel Mac row; the launcher does not run on macOS.
- `words`: the joining words and lead-in per helper language (drafts for
  native review, like the rest of the localized helper text).

## How the launcher reads the brand

The read never needs administrator rights, never reads serial numbers, and is
bounded to 20 seconds. Tests always inject a fake reader.

| Platform | Source |
| --- | --- |
| Windows | WMI `Win32_ComputerSystem` (Manufacturer, Model) and `Win32_BaseBoard` (Manufacturer), via the built-in PowerShell |
| Linux | `/sys/class/dmi/id/sys_vendor`, `product_name`, `board_vendor` (world-readable; the serial files there are root-only and not read) |
| macOS | Not read. The launcher does not run on macOS (it plans no restart there), so no `sysctl`/`ioreg` reader was added. The Boot helper lists the Intel Mac key. |
| Preview (`--preview`) | Not read; preview reads nothing from the computer. |

If the brand is not recognized or cannot be read, the launcher shows the
full table, opened. The reported manufacturer, model and motherboard vendor
appear in **Technical details** so support can see why.

## Never certain

A key is what a brand usually uses, not what one model will do. Every surface
says so: the launcher says "Most <brand> computers" and "This is the usual key
for the brand, not a guarantee"; the tables are captioned as examples. Models
differ (many Lenovo laptops need Fn+F12 or the Novo button; ASUS laptops and
desktop boards differ; Acer may need the menu turned on in firmware setup,
which is a firmware change: see the BitLocker note in the Boot helper).

Each brand's key is tested on a real model by the PHY-<brand>-01 rows of the
[#116 packet](acceptance/physical/matrix.md).

## Sources (reviewed 2026-11-07/08)

| Brand | Source | Checked |
| --- | --- | --- |
| Dell | https://www.dell.com/support/kbdoc/en-us/000126121 ("Use the F12 one-time boot menu") | Fetched 2026-11-08 |
| HP | https://www.hp.com/my-en/tech-takes/software/how-to/how-to-boot-from-usb-drive-on-windows-10-pcs.html (Esc, then F9 for Boot Device Options; HP notes models vary) | Search result 2026-11-08 |
| Lenovo | https://support.lenovo.com/us/en/solutions/ht500207 (F12 / Fn+F12 / Novo button) | Automated fetch refused (HTTP 403) on 2026-11-08; recheck by hand |
| ASUS | https://www.asus.com/support/faq/1013017/ (Esc on notebooks and All-in-Ones; F8 on desktops) | Fetched 2026-11-08 |
| Acer | https://community.acer.com/en/kb/articles/563-why-cant-i-get-the-f12-boot-menu-to-work-on-my-notebook-or-netbook (F12 menu may need enabling) | Not refetched |
| MSI | https://www.msi.com/faq/mb-901 (F11) | Automated fetch refused (HTTP 403) on 2026-11-08; recheck by hand |
| Gigabyte | https://download.gigabyte.com/FileList/Manual/mb_manual_intel800-bios_e.pdf (F12 boot menu) | Not refetched |
| Intel Mac | https://support.apple.com/102603 (hold Option at startup) | Not refetched |

The previous lists disagreed in small ways (the helper said "HP: F9 or Esc",
"ASUS: F8 or Esc"; the launcher said "Esc, then F9"). The table keeps the
HP sequence and puts ASUS's laptop key first, matching the sources above.
