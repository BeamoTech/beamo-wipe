# Design record: hardening the network-enabled live system (Notion Ref 187)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-19 by Claude (Opus 5.5) from the Notion Ref 187 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`), the Ref 186 network
> design (`docs/decisions/network-setup.md`, merged in #130) and the repository
> at main `15513086`. The full Notion row text was not available; §3 lists the
> requirements this record assumes.
>
> **Depends on Jack's Ref 184 decision and the Ref 186 design.** No network
> exists in the image yet. These controls are built together with Ref 186 and
> must all be in place before any network code ships.
>
> **Numbering.** "Ref 187" is the Notion row. The repository's older `#187`
> (two-disk dry run with the carried ownership tick) is a different item.

## 1. Summary for the owner (plain English)

1. Today the live system cannot be reached over a network because it has none.
   Adding Wi-Fi and downloads (Refs 186, 188) creates new ways in.
2. This record lists the locks to add before any network code ships:
   - nothing on the stick listens for connections;
   - only the downloader may talk to the internet, and only to Beamo's servers;
   - the erase screens still have no network at all;
   - network storage can never be mistaken for a disk to erase.
3. A downloaded system is trusted because of Beamo's signature, not because
   the network or the website looked right.
4. Five choices are yours (§8). The main one is how the stick sets its clock,
   which secure connections need.

## 2. Today (facts from main `15513086`)

| Control | Today | Where |
|---|---|---|
| Network | None: no network packages, services masked, no Wi-Fi firmware | Ref 186 record §2; `tests/test_live_image.py` |
| Wizard sandbox | `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `NoNewPrivileges=yes`, `ProtectSystem=full`, `ProtectHome=yes`, private tmpfs `/tmp`, `PrivateMounts=yes`, `UMask=0077`; runs as root | `beamo-wipe-kiosk.service` |
| Logins | Every getty and the serial getty masked; no ssh | build hook `0500-build-nwipe.hook.chroot` |
| Magic SysRq | Disabled (`kernel.sysrq = 0`) | `etc/sysctl.d/90-beamo-kiosk.conf` |
| Compilers, git | Refused in the image by the build hook | same hook |
| Kernel module blocks | None | — |
| Firewall | None (no network) | — |
| Clock | `systemd-timesyncd` masked; the report treats the RTC as untrusted | build hook; `diagnostic_report.py` |
| Network targets | nbd and network file systems refused as erase targets | `src/beamo_wipe/safety.py` |
| Vulnerabilities | Build fails if any installed package has a fixed Debian vulnerability (`debsecan --only-fixed`) | `scripts/qemu-verify.sh` (hosted gate) |

## 3. Requirements assumed (confirm against the Notion row)

- R1 No inbound service, ever (Ref 184 L14).
- R2 Only the components that need the network get it. The wizard and nwipe never do.
- R3 Downloads are trusted only through the signed catalog and pinned hashes (Ref 188); TLS protects privacy, not authenticity.
- R4 Network storage and remote disks can never appear as erase targets.
- R5 The network is down from the final authorization through erase and install.
- R6 Nothing identifying is sent beyond what connecting needs; no telemetry (Ref 184 D10).
- R7 Every control has an automated test, and the hosted gate proves no port is open.

## 4. Controls

### 4.1 Process isolation
- **Wizard and nwipe:** keep `PrivateNetwork=yes`. A test fails the build if it is removed.
- **`beamo-netd` (Ref 186):** its own service, not started at boot.
  - Capabilities limited to `CAP_NET_ADMIN` and `CAP_NET_RAW` (for DHCP).
  - Sandboxed: `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`, `NoNewPrivileges=yes`, a `SystemCallFilter=@system-service` allow-list.
  - `RestrictAddressFamilies` limited to `AF_UNIX AF_INET AF_INET6 AF_NETLINK AF_PACKET`.
  - One UNIX socket, readable only by the wizard.
- **Downloader (Ref 188):** a separate service.
  - Runs as a dynamic non-root user (`DynamicUser=yes`), with no capabilities.
  - May write only the OS cache: `ReadWritePaths=` the cache mount only (Ref 185).
  - `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`.
  - Started only in Download (Ref 184 state 4).

### 4.2 Firewall (nftables, loaded before any link comes up)
- **Inbound:** drop everything except replies to connections we opened (`ct state established,related`), DHCP/DHCPv6 replies and the ICMPv6 needed for IPv6 to work. No other port is open.
- **Outbound:** allowed only from the `beamo-netd` and downloader identities (`meta skuid` / `meta cgroup`). Everything else is dropped and counted.
- **Download destinations:** the downloader may reach only TCP 443 and DNS through the local resolver. Host names come from the signed catalog (Ref 188), never from the network.
- **Forwarding:** off (`net.ipv4.ip_forward=0`, `net.ipv6.conf.all.forwarding=0`).

### 4.3 Kernel and sysctl
- **Blocked kernel modules** (`install <module> /bin/false` in `/etc/modprobe.d/`):
  - remote disks: `nbd`, `iscsi_tcp`, `libiscsi`, `nvme_tcp`, `nvme_rdma`, `nvme_fc`;
  - network file systems: `nfs`, `nfsv4`, `cifs`, `smb3`, `9p`;
  - Bluetooth: `bluetooth`;
  - legacy and unused protocols: `dccp`, `sctp`, `rds`, `tipc`.
  - This backs up the `safety.py` refusal (R4).
- **sysctl:**
  - `rp_filter=1`;
  - accept no redirects and no source routes;
  - `tcp_syncookies=1`;
  - `kernel.kptr_restrict=2`, `kernel.dmesg_restrict=1`;
  - `kernel.unprivileged_bpf_disabled=1`, `net.core.bpf_jit_harden=2`;
  - IPv6 RA accepted only on the active link, and only while connected.
- **Secure Boot:** with Secure Boot on, Debian's kernel enters lockdown mode by itself. Nothing here changes that.

### 4.4 Clock and TLS
- **Why the clock matters:** HTTPS certificates need a roughly correct clock, but the PC's clock can be badly wrong.
- **D187-1 options:** (a) after Connect, run `systemd-timesyncd` once against a fixed pool, then use TLS; (b) bootstrap time from the signed catalog's timestamp plus the HTTPS `Date` header, within bounds.
- **Recommended:** (b), so no unauthenticated time source decides trust.
- **Replay protection:** the signed catalog carries an issue time and expiry, so an old, revoked catalog is refused (Ref 188).
- **TLS:** Debian `ca-certificates`, verification always on, TLS 1.2 or newer. Optionally pin the catalog host's issuer (D187-2).

### 4.5 DNS and privacy
- **DNS:** `systemd-resolved` as the only resolver, used only by the downloader. No LLMNR or mDNS (`LLMNR=no`, `MulticastDNS=no`).
- **DHCP:** send no host name (`SendHostname=no`) and use a random client ID.
- **Wi-Fi MAC address:** randomized per network (`AddressRandomization=network` in iwd), D187-3.
- **No telemetry, no accounts** (Ref 184 L14, D10).

### 4.6 Lifecycle
- **Order:** the firewall and the sysctl and module blocks are active before `beamo-netd` starts.
- **Shutdown of the network:** at the final authorization the wizard stops the downloader and `beamo-netd`, then checks that no link has an address before showing **Erase now** (R5). If any link still has an address, it refuses.

### 4.7 Supply chain and updates
- **Vulnerabilities:** the existing `debsecan --only-fixed` gate stays mandatory. With a network-facing image it also covers `iwd`, `systemd-networkd`, `systemd-resolved` and the firmware packages.
- **Package size:** new packages are pinned through the normal Debian archive snapshot. Their size is reviewed in Ref 202.
- **Updating Beamo Wipe itself** over the network is Ref 206 (D9). It is not part of this record.

## 5. Threat model additions

| Threat | Control |
|---|---|
| Attacker on the same Wi-Fi scans the stick | Nothing listens; inbound drop; no mDNS/LLMNR |
| Rogue access point or man-in-the-middle | TLS; signed catalog and payload hashes; failure stops the download |
| Captive portal page | Detected; no browser; message (Ref 186) |
| Malicious DHCP or DNS answers | DNS used only by the downloader; catalog hosts fixed by signature; failure is safe |
| Remote disk made to look local (iSCSI, NVMe-oF, nbd) | Modules blocked; `safety.py` refusal stays |
| Compromised downloader | Non-root, no capabilities, writes only the cache, and the installer checks the hash again |
| Old genuine catalog replayed | Signed issue time and expiry |
| Wrong clock | Bounded time bootstrap (D187-1) |
| Tracking through the stick | No host name, random MAC address, no telemetry |

## 6. Tests (when built)

| Test | Kind |
|---|---|
| The wizard service keeps `PrivateNetwork=yes`; netd and downloader unit files keep their sandbox keys | Unit (file content) |
| nftables ruleset: default drop inbound, outbound only from the two identities | Unit (`nft -c` in the build) plus QEMU |
| Module blocks present; `modprobe nbd` fails in the guest | QEMU |
| No listening socket (`ss -lntup` empty except loopback) after Connect | QEMU with user networking |
| Network down before Erase now; refusal if a link still has an address | Unit with a fake netd; QEMU |
| Clock bootstrap bounds; expired catalog refused | Unit |
| `debsecan` gate still blocks fixed vulnerabilities | Existing hosted gate |
| Real Wi-Fi chips and phones | Physical (Ref 208), Jack's authorization |

## 7. What changes where (when approved)

| Area | Change |
|---|---|
| `packaging/live/config/includes.chroot/etc/` | `modprobe.d/beamo-network.conf`, `sysctl.d/91-beamo-network.conf`, `nftables.conf`, resolved and iwd config |
| `packaging/live/config/package-lists/beamo.list.chroot` | `nftables` (with Ref 186 packages) |
| Build hook | Load order; keep the existing masks |
| New unit files | `beamo-netd.service`, downloader service, with the sandbox above |
| `scripts/qemu-verify.sh` | Port, module and firewall checks (Ref 203) |
| `tests/` | The unit tests above |

## 8. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D187-1 | Clock source for HTTPS | (a) one NTP sync after Connect; (b) signed-catalog time plus bounded HTTPS `Date` | (b) |
| D187-2 | Pin the catalog host's certificate issuer | Yes / no | Yes, with a planned rotation path |
| D187-3 | Random Wi-Fi MAC address | Per network / off | Per network |
| D187-4 | Outbound firewall strictness | (a) by process identity only; (b) also by catalog host addresses | (a) now; (b) only if hosts have stable addresses |
| D187-5 | IPv6 | With D186-6 | Same as D186-6 |

## 9. Not done here

No package, unit, firewall rule or test was changed. No network was used. The
Notion row's full text should be checked against §3.
