# Machine intake form (#116)

Copy this file once per computer. Name the copy
`intake-<machine ID>.md`, for example `intake-M03.md`. The machine ID is a
lab label you choose (M01, M02 …). It is not a serial number.

Fill it before the first boot. Empty fields mean the computer is not ready.

## Privacy rules

- Never record customer data, account names, Wi-Fi names, file names from a
  disk, BitLocker keys, product keys or passwords.
- Serial numbers: write only the last 4 characters, like `****7Q2X`. If a
  form needs the full serial to tell two disks apart, keep that in the
  private evidence store and write only its SHA-256 here.
- Photos of stickers or setup screens must be cropped or blurred so no full
  serial, service tag or MAC address shows before they go into git.
- This computer must be a lab computer, never a customer's computer.

## Computer

| Field | Value |
| --- | --- |
| Machine ID (lab label) | |
| Intake date (UTC) and operator initials | |
| Brand (as on the case) | |
| Brand as reported by firmware or the launcher (Technical details) | |
| Model | |
| Form: laptop / desktop / all-in-one / small form factor | |
| CPU maker and model; architecture (must be x64 for support) | |
| Firmware maker and version (from the setup screen) | |
| Firmware date | |
| Modes offered: UEFI / legacy BIOS or CSM | |
| Mode as found (do not change it) | |
| Secure Boot as found: enforcing / not enforcing / not present | |
| Intel VMD or RST as found: on / off / not shown | |
| Boot-menu key that works on this model | |
| Key in `desktop/bootkeys.json` for this brand | |
| Fast Boot or USB boot disabled? | |
| BitLocker or other disk encryption on? Recovery key reachable? (yes/no only) | |
| Windows edition and version, if installed (for PHY-WIN rows) | |
| Linux distribution and desktop, if installed (for PHY-LNX rows) | |
| Built-in screen resolution and size | |
| External screens available (HDMI, DisplayPort, VGA) | |
| Graphics maker and model | |
| Speaker: built-in / none; headphone jack: yes/no | |
| Touchpad: yes/no; keyboard layout printed on keys | |
| Battery: yes/no; charger present | |
| USB ports: count of USB-A, USB-C; USB 2 and USB 3 marks | |
| Lid: yes/no | |

## Disks connected for this session

List every disk that stays connected. Valuable disks must be removed first.

| Disk ID | Bus (SATA / NVMe / USB enclosure / eMMC) | Kind (hard disk / SSD) | Model | Capacity | Serial (last 4) | Labelled `DISPOSABLE`? | Owner authorization ref |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | | | | | | | |
| D2 | | | | | | | |
| D3 | | | | | | | |

## Checks before the first boot

| Check | Yes / No |
| --- | --- |
| Valuable disks removed or disconnected | |
| Every remaining disk is listed above | |
| Beamo USB passed readback in this session (PHY-MFG-01 run ID) | |
| No firmware, key, Secure Boot or policy change is planned | |
| A virtual machine is **not** standing in for this computer | must be Yes |

Operator initials: ____ Date (UTC): ____
