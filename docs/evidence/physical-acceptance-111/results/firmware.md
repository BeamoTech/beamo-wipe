# Firmware results — PHY-FW

Related software matrix: [`docs/compatibility-matrix.md`](../../../compatibility-matrix.md) §4. Its QEMU/fixture rows are not physical Passes.

Expected live loaders: BIOS `syslinux`, UEFI `grub-efi` (`packaging/live`). Signed Debian EFI components still depend on the PC’s trust store ([`docs/boot-card.md`](../../../boot-card.md), [`docs/claims.md`](../../../claims.md)).

Every Secure Boot row uses **Q12**, the exact 0.2.12 ISO/USB hashes and source/build
in [the canonical cases](../../../secure-boot-acceptance.md). Record that identity
and the read-only prerequisites in [BUILD-IDENTITY](../BUILD-IDENTITY.md).
Another manufactured image requires a new component inspection. Each linked
case specifies the observable result and evidence needed; do not judge a row
from Beamo-key enrollment, a setup toggle, or USB-menu presence alone. Use
already configured states; this sheet authorizes no trust or revocation changes.

Every Result below is **NOT TESTED**. Fill Machine / firmware from the sticker and setup screen; do not guess.

| ID | Variant | Related | Expected (physical) | Machine / firmware (fill) | Result | Evidence (`photos/` or `logs/`) |
| --- | --- | --- | --- | --- | --- | --- |
| PHY-FW-01 | Legacy BIOS | FW-01 | USB appears in the firmware menu; Beamo menu then wizard is the first UI; boot USB is not a wipe target | | NOT TESTED | `photos/PHY-FW-01-*` |
| PHY-FW-02 | UEFI, Secure Boot off | FW-02, FW-04 | Same as PHY-FW-01 via the UEFI USB entry | | NOT TESTED | `photos/PHY-FW-02-*` |
| PHY-FW-03 | Q12; x64 UEFI enforcing, actual databases permit the chain | FW-03 | [SB-ACCEPT](../../../secure-boot-acceptance.md): reaches guide with validation enabled. Capture trust/revocation comparisons and actual enforcement; no erase. | | NOT TESTED | `photos/PHY-FW-03-*` and `logs/PHY-FW-03-*` |
| PHY-FW-04 | UEFI already non-enforcing on dedicated lab hardware | FW-04 | Ordinary boot as PHY-FW-02; record existing state. Not Secure Boot acceptance. Do not change it to qualify a row. | | NOT TESTED | `photos/PHY-FW-04-*` |
| PHY-FW-05 | CSM / BIOS compatibility on a UEFI PC | FW-05 | USB boots through the compatibility path if the firmware offers it; wizard first UI | | NOT TESTED | `photos/PHY-FW-05-*` |
| PHY-FW-06 | Dell boot menu | FW-06 | F12 opens the boot menu; USB can be chosen | | NOT TESTED | `photos/PHY-FW-06-*` |
| PHY-FW-07 | HP boot menu | FW-06 | F9 or Esc opens the boot menu; USB can be chosen | | NOT TESTED | `photos/PHY-FW-07-*` |
| PHY-FW-08 | Lenovo boot menu | FW-06 | F12 opens the boot menu; USB can be chosen | | NOT TESTED | `photos/PHY-FW-08-*` |
| PHY-FW-09 | ASUS / Acer / MSI / Gigabyte boot menu | FW-06 | Key from the boot card (F8/Esc, F12, F11, F12) opens the menu; USB can be chosen. Record the vendor. | | NOT TESTED | `photos/PHY-FW-09-*` |
| PHY-FW-10 | Fast Boot / USB boot disabled in firmware | — | USB missing from the menu is a firmware setting, not a Beamo bug. Record the setting you changed on **lab** hardware. | | NOT TESTED | `photos/PHY-FW-10-*` |
| PHY-FW-11 | Q12; enforcing firmware dbx explicitly denies the shim/signing chain | FW-03 | [SB-DBX](../../../secure-boot-acceptance.md): explicit policy refusal; capture exact dbx match, diagnostic and failure stage. No guide or erase. | | NOT TESTED | `photos/PHY-FW-11-*` and `logs/PHY-FW-11-*` |
| PHY-FW-12 | BitLocker recovery warning | — | If this PC might boot Windows again, confirm the recovery key is reachable **before** firmware changes. Record that you checked. | | NOT TESTED | `logs/PHY-FW-12-*` |
| PHY-FW-13 | Q12; complete enforcing db has no applicable shim authorization | FW-03 | [SB-NO-ANCHOR](../../../secure-boot-acceptance.md): explicit authentication refusal. Missing menu entry alone is inconclusive. Capture database and diagnostic. | | NOT TESTED | `photos/PHY-FW-13-*` and `logs/PHY-FW-13-*` |
| PHY-FW-14 | Q12; firmware permits shim, active shim/SBAT policy denies a component | FW-03 | [SB-SHIM](../../../secure-boot-acceptance.md): refusal at the identified shim/GRUB stage; capture generation/floor or denylist match and message. | | NOT TESTED | `photos/PHY-FW-14-*` and `logs/PHY-FW-14-*` |
| PHY-FW-15 | Q12; trust/revocation/enforcement/path unknown | FW-03 | [SB-UNKNOWN](../../../secure-boot-acceptance.md): capture startup or refusal as observed; Result Unknown, never Pass. Identify missing evidence. | | NOT TESTED | `photos/PHY-FW-15-*` and `logs/PHY-FW-15-*` |
| PHY-FW-16 | Q12 intended; artifact/component/media inspection fails | FW-03 | [SB-INSPECTION](../../../secure-boot-acceptance.md): stop qualification before boot; record command, error and identity mismatch. BLOCKED, not physical Pass. | | NOT TESTED | `logs/PHY-FW-16-*` |
| PHY-FW-17 | Q12; unsupported CPU or firmware/platform architecture | — | [SB-ARCH](../../../secure-boot-acceptance.md): Excluded with architecture/support reason; unsigned IA32 file does not qualify Secure Boot. No boot required. | | NOT TESTED | `logs/PHY-FW-17-*` |

Notes (what you saw; leave blank until a run):
