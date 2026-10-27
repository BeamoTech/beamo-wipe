# Beamo Wipe — boot card (print one side)

**Beamo Wipe** — this USB erases a disk with **nwipe** (open source).
You must own this PC and disk, or have written permission.

For the new desktop-readable USB image: open **Start Beamo Wipe.exe** on
Windows, or **Start Beamo Wipe Linux** on a supported Linux desktop.
On Windows, save your work, use the normal Restart command, then
choose this USB from the boot menu. On supported Linux desktops, the
application offers **Restart into Beamo Wipe** only when its checks pass;
an operating-system permission prompt may appear. If the application
cannot open, use the boot menu below.

Windows may warn that **Start Beamo Wipe.exe** has an unknown publisher
(a SmartScreen warning), because the launcher is not code-signed. If you are
unsure, do not run it: restart the PC and use the boot menu key below instead.

**Erasing still requires booting this USB.** Inserting it or opening the
application does not erase anything. Open START-HERE.html on this USB to see
this image's build. Older sticks may use different startup files.

## Open the boot menu (typical keys)

| PC | Boot menu key |
| --- | --- |
| Dell | F12 |
| HP | F9 or Esc |
| Lenovo | F12 |
| ASUS | F8 or Esc |
| Acer | F12 |
| MSI | F11 |
| Gigabyte | F12 |

Brand notes (they vary by model):

- **Lenovo:** many laptops need **Fn+F12**, or the small **Novo** button or
  pinhole (press it while the laptop is off, then choose the boot menu).
- **Acer:** on many models the F12 boot menu may first need to be turned on
  in firmware setup. That is a firmware change: read the BitLocker note below
  first, or use the Windows steps instead.

Windows 11 fallback: Settings → System → Recovery → Advanced startup →
Restart now → Use a device (UEFI).
Windows 10: Settings → Update & Security → Recovery → Advanced startup →
Restart now → Use a device (UEFI).
Those keys and menus vary by PC. Open START-HERE.html on the USB for the
full steps. If something is not working, choose the problem you see on
that page.

If you might start this Windows installation again, confirm you can reach
the BitLocker recovery key **before** changing firmware, boot order, or
Secure Boot. Those changes can trigger BitLocker recovery. Do not disable
Secure Boot as a routine step.

Plug into a **USB-A or USB-C** port on the PC, not a keyboard hub if you
can avoid it. Then restart and tap the key above.

If the stick never appears: keep it plugged in, try another port on the PC
itself, and use the Windows **Use a device** steps above. Some PCs list USB
only after firmware allows USB boot. Firmware changes are not the next
automatic step: confirm the BitLocker recovery key first, and follow
START-HERE.html or the manufacturer's startup instructions.

**Not for Apple Silicon Macs. Not for Chromebooks.** Some Intel Macs may
show this USB; many will not.

## After it boots

When the Beamo Wipe menu appears, pick **Beamo Wipe: start the erase guide**
(or **troubleshoot startup** if the PC does not start normally). Opening the
guide erases nothing by itself.

The menu also offers **Beamo Wipe: speech for screen readers** — press **S**
as soon as the menu appears. UEFI computers with a built-in speaker play two
short beeps when the menu is showing; many laptops and the older BIOS menu
make no sound, so press **S** a few times after the firmware logo. The menu waits
five seconds, then starts the ordinary guide; if that happens, press **F8**
in the guide to switch to the spoken view. Choosing either entry erases
nothing.

This is nwipe with a guide on top. Nothing is erased until you choose
**Erase now**. After a short welcome screen:

1. **Check your keyboard** — choose your language and keyboard layout.
2. **Is this your computer?** — read what erasing means, then check the
   owner box.
3. **Which disk should we erase?** — pick the disk by **size and serial**.
   The Beamo USB is marked and cannot be selected.
4. **Is this the right disk?** — type the characters shown (usually the
   disk size).
5. **Choose an erase method.**
6. **Review before erasing** — wait five seconds, then choose **Erase now**.
7. **Erasing now** — keep this USB in and the PC on wall power until
   **Finished** or another result appears.

If a diagnostic or wipe report cannot be saved, read the **Support code**
and **Build** lines on the screen and tell support those exact values.
They do not include disk serials or paths.

This image includes signed Debian EFI components. Secure Boot still depends
on the computer's trust settings and revocation updates. If firmware rejects
the USB, record its exact message and use the computer manufacturer's
guidance or contact support at **beamosupport.com**. Error
screens and START-HERE.html show the same address as text and as a phone
code. The application does not change Secure Boot settings. Older sticks
may contain a different boot image.

Some recent PCs (for example Secured-core PCs) may refuse Debian's
Microsoft-signed boot files unless firmware allows the "Microsoft 3rd-party
UEFI CA". Do not change that setting as a routine step: contact support or
follow the computer manufacturer's instructions.

Source and license: **https://github.com/BeamoTech/beamo-wipe**
(print a QR to that README, not a store page).
