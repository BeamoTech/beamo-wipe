# Design record: Wi-Fi, Ethernet and phone-tethering setup in Beamo Wipe OS (Notion Ref 186)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-19 by Claude (Opus 5.5) from the Notion Ref 186 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`) and the repository at
> main `a8c5854b`. The full Notion row text was not available; §3 lists the
> requirements this record assumes.
>
> **Depends on Jack's Ref 184 decision.** Today the live system has no network
> at all, and tests enforce that. Building anything here changes shipped
> behaviour, so it waits until Jack decides the Ref 184 record. Hardening of the
> network-enabled system (firewall, kernel modules, time) is Ref 187; the
> downloader is Ref 188.
>
> **Numbering.** "Ref 186" is the Notion row. The repository's older `#186` is the
> SSD firmware-erase decision record (`docs/decisions/ssd-firmware-erase.md`), a different item.

## 1. Summary for the owner (plain English)

1. Today Beamo Wipe cannot go online, by design. Erasing never needs it.
2. To install a new system, Beamo Wipe must download it. This record proposes
   how the customer connects: a cable, Wi-Fi, or a phone plugged in by USB.
3. The network stays **off** until the customer chooses a mode that needs it and
   presses **Connect**. Erasing keeps working fully offline.
4. The erase screens never get network access. Only a small, separate
   connection helper and the downloader do.
5. Six choices are yours (§9). The main ones: which phones to support, and
   whether to add Wi-Fi firmware, which makes the image bigger.

## 2. Today (facts from main `a8c5854b`)

| Item | Today | Where |
|---|---|---|
| Network packages | Not installed; `network-manager`, `curl`, `wget`, `iproute2`, `openssh-server` and others are on a forbidden list | `tests/test_live_image.py` `FORBIDDEN_PACKAGES` |
| Network services | `NetworkManager`, `wpa_supplicant`, `systemd-networkd`, `systemd-timesyncd`, `ssh` masked | `packaging/live/config/hooks/normal/0500-build-nwipe.hook.chroot` |
| Wizard process | `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `NoNewPrivileges=yes` | `beamo-wipe-kiosk.service`; tested |
| Wi-Fi/Bluetooth firmware | None (`--firmware-chroot false`); only graphics, audio, USB-controller and microcode | `packaging/live/inside-docker.sh` |
| Kernel cmdline | `ip=frommedia`, no network boot | same |
| Network block devices | nbd and network file systems refused as targets | `src/beamo_wipe/safety.py` |
| Claims | QR summary "needs no second USB, app or internet" | `docs/claims.md` |
| Ref 184 law L14 | "Network off until needed; full erase works offline; no inbound services, telemetry or accounts; no plaintext secrets on USB" | Ref 184 record §4 |

## 3. Requirements assumed (confirm against the Notion row)

- R1 Connect by Ethernet, Wi-Fi (WPA2/WPA3 Personal) and USB phone tethering.
- R2 Off by default; on only by the customer's action, and only in a mode that needs it (Ref 184 state 3).
- R3 Erase never depends on the network, and the wizard process never gets network access.
- R4 Wi-Fi passwords are never written to the USB or a log (L14, N4); carry-over to the new OS only with consent (D7).
- R5 Clear, honest messages for no network, wrong password, captive portal, weak signal and dropped connections.
- R6 Accessible like the rest of the wizard: keyboard, Orca, high contrast and text size, translations.

## 4. Architecture

```
 Tk wizard (kiosk)              beamo-netd (new, root)             beamo-fetch (Ref 188)
 PrivateNetwork=yes  --AF_UNIX-->  owns links, Wi-Fi, DHCP   ...     network, writes only
 no network ever                   no inbound sockets               to the OS cache (Ref 185)
```

- **The wizard stays offline.** It keeps `PrivateNetwork=yes` and only talks
  to `beamo-netd` over one UNIX socket with a small, typed request set: list
  links, scan, connect, disconnect, status. No free-form commands.
- **`beamo-netd`** is a new systemd service that is **not started at boot**. The
  wizard asks systemd to start it after the customer presses Connect, and stops
  it at Disconnect, on leaving the mode, and before any erase starts.
- **Downloads** run in a separate sandboxed service (Ref 188). It may reach the
  network and write only inside the OS cache proposed in the Ref 185 record
  (`docs/decisions/usb-16gb-layout.md`).
- **Stack (D186-1).** Recommended: `iwd` for Wi-Fi plus `systemd-networkd` for
  addresses (DHCP, IPv6 RA) and `systemd-resolved`. Both ship in Debian 12 and
  are much smaller than NetworkManager. iwd's built-in DHCP is not used, so one
  component owns addresses.
- **Nothing listens.** No inbound services; a default-deny firewall (Ref 187).

## 5. Connection types

| Type | How | Notes |
|---|---|---|
| Ethernet | Link detected; DHCP only after Connect | Most reliable; recommended first in the UI |
| Wi-Fi | iwd scan, pick a network, type the password | WPA2/WPA3 Personal and open networks. Enterprise (802.1X) is out of scope for v1 (D186-4). Hidden networks by typing the name |
| Android USB tethering | Kernel `rndis_host` / `cdc_ncm` / `cdc_ether`; appears as a wired link | Customer turns on "USB tethering" on the phone; on-screen steps |
| iPhone USB tethering | Kernel `ipheth` plus `usbmuxd` for the "Trust this computer" pairing | Personal Hotspot on, cable, Trust. Adds `usbmuxd` and `libimobiledevice` (D186-2) |
| Bluetooth tethering | Not offered | No Bluetooth firmware or stack; out of scope |
| Phone hotspot over Wi-Fi | Works as normal Wi-Fi | Needs Wi-Fi firmware (D186-3) |

**Wi-Fi firmware (D186-3).** Most laptop Wi-Fi chips need firmware the image
does not have: `firmware-iwlwifi` (Intel), `firmware-realtek`,
`firmware-atheros`, `firmware-brcm80211`, MediaTek in `firmware-misc-nonfree`.
This grows the image; the exact size must be measured in Ref 202. Without it,
Wi-Fi works only on few machines, and Ethernet or tethering are the fallback.

## 6. Screens (wizard)

1. **Connect to the internet** — shows what was found: "Cable connected", Wi-Fi
   networks with signal and lock, "Phone connected by USB", and a link to
   phone-tethering steps. One primary button per choice.
2. **Wi-Fi password** — masked field with Show; never logged; held in memory
   only and handed to `beamo-netd`, which gives it to iwd. iwd's state
   directory is on tmpfs (RAM only).
3. **Checking the connection** — address, DNS, then a reachability check to the
   Beamo catalog host over HTTPS (Ref 188). Never a third-party probe.
4. **Messages** (plain words, with the next step):
   - Wrong password → try again.
   - No address from the network → try another network or the cable.
   - **Captive portal** (a hotel or café login page) → Beamo Wipe has no web
     browser, so use another network or the phone.
   - Weak signal or dropped → move closer, or use the cable; downloads resume (Ref 188).
   - Clock badly wrong → handled by Ref 187 before HTTPS starts.
5. **Disconnect** is always available. Leaving the mode disconnects and stops `beamo-netd`.

Erase screens never show network controls. The network is disconnected
before the final authorization (Ref 184 state 6) and stays down through the
erase and the install; the installer uses only the verified copy in the OS
cache (Ref 184 N5 allows no download in states 6–9).

## 7. Safety and privacy rules this design needs (proposed)

1. The wizard process keeps `PrivateNetwork=yes`; tests keep enforcing it.
2. `beamo-netd` starts only on the customer's Connect in a mode that needs it;
   never at boot, never in Erase everything or Keep my OS unless a later decision adds it.
3. Network is down before the final authorization and stays down through the
   erase and the install (states 6–9).
4. No password, network name or address is written to the USB, a log, a
   report or a support code. Logs say only "Wi-Fi connected" or the failure class.
5. Network block devices and network file systems stay unusable as targets
   (`safety.py` today; Ref 187 also blocks their kernel modules).
6. Package additions are the minimum; each new package is reviewed against the
   forbidden list, which keeps `curl`, `wget`, `openssh-server`, `nmap` and
   compilers out.

## 8. What changes where (when approved)

| Area | Change | Tests |
|---|---|---|
| `packaging/live/config/package-lists/beamo.list.chroot` | `iwd`, `systemd-resolved`, tethering packages per D186-2, firmware per D186-3 | `test_live_image.py`: allowed list replaces part of the forbidden list, with reasons |
| Build hook | Keep `NetworkManager`, `wpa_supplicant`, `ssh`, `getty` masked; `systemd-networkd` enabled only through `beamo-netd` | Hook tests |
| New `beamo-netd` service and module | Typed UNIX-socket API; systemd sandboxing | Fake-backend unit tests; malformed request tests |
| Wizard | Connect screens; copy in every language; accessibility | Tk and accessibility tests with a fake netd |
| `inside-docker.sh` | Firmware selection | ISO content tests |
| QEMU gate (Ref 203) | Ethernet via QEMU user networking; Wi-Fi via `mac80211_hwsim` virtual radios in the guest | Hosted gate, final candidate only |
| Physical (Ref 208) | Real Intel, Realtek, MediaTek, Broadcom Wi-Fi; Android and iPhone tethering | Physical rows, Jack's authorization |
| `docs/claims.md` (Ref 207) | Only after verification | — |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D186-1 | Network stack | (a) iwd + systemd-networkd; (b) NetworkManager | (a): smaller, fewer services |
| D186-2 | Phone tethering | (a) Android only; (b) Android and iPhone (`usbmuxd`) | (b), if the size fits Ref 202 |
| D186-3 | Wi-Fi firmware | (a) none (cable and tethering only); (b) main laptop vendors; (c) all of Debian's | (b), measured in Ref 202 |
| D186-4 | Enterprise Wi-Fi (802.1X) | Not in v1 / later | Not in v1 |
| D186-5 | Network in Keep my OS or Erase everything | Never / later for updates (Ref 206) | Never in v1 |
| D186-6 | IPv6 | On with IPv4 / IPv4 only | On (many phone networks are IPv6-first) |
| Ref 184 D7 | Wi-Fi carry-over to the new OS | — | Never by default; consent only |

## 10. Not done here

No package, service, screen or test was changed. No network was used. The
Notion row's full text should be checked against §3.
