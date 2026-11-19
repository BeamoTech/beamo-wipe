# Decision record: protecting the Beamo USB against copying and tampering (Notion Ref 183)

> **Status: first improvement implemented (stick check); hardware and trusted-boot
> options need owner decisions.** Prepared 2026-11-19 by Claude (Opus 5.5) from
> the Notion Ref 183 record and the repository at main `39d0ce5c`. No production
> key, release, media write, customer drive or physical test was used.
>
> **Numbering.** "Ref 183" is the Notion row. The repository's older `#183` is
> Restart to boot options, a different item.

## 1. Summary for the owner (plain English)

1. Anyone holding a Beamo USB can copy it. That is normal for USB sticks, and
   the GPL licences let people copy and share the software. We **cannot** make
   the stick uncopyable or tamper-proof, and we must never claim that.
2. What we **can** do is let a customer prove that a stick holds exactly what
   Beamo released, file for file, using a computer they trust and Beamo's
   published signature. That is now built: the **stick check**.
3. A stick cannot reliably check itself. A modified stick can show a fake
   "genuine" message. So the trusted check runs on another computer.
4. Stronger protection needs hardware or our own Secure Boot signing. Those cost
   money and need your decision (§6).

## 2. What the stick has today (inventory)

| Surface | Today | Protects |
|---|---|---|
| Release | Ed25519-signed `release-downloads.json` and manifest; pinned key `packaging/release-keys/keys.json` (active/retired/revoked); `SHA256SUMS` | Authenticity of downloads |
| Download check | `scripts/verify-usb-download.py` | The downloaded file only |
| Stick layout | One writable FAT32 partition; no persistence | Nothing (any OS can edit it) |
| Boot chain | Microsoft-signed shim, Debian-signed GRUB and kernel; initrd, `grub.cfg` and `filesystem.squashfs` **not** in the signed chain | Only when Secure Boot is on, and only up to the kernel |
| On-stick files | `sha256sum.txt` (unsigned), `build-identity.json`, `desktop-build.json`, `START-HERE.html` (all unsigned) | Drift and accidents only |
| Wizard | `build_identity.py` "production" status (same-squashfs hashes); nwipe accepted on `-V` text | Drift, not tampering |
| Manufacturing | `docs/manufacturing.md`: signed golden image, byte-exact copies, readback receipts, tamper-evident seals (defined, not yet run) | Factory output, sampled |
| Licences | Wrapper GPL-3.0-or-later; nwipe GPL-2.0; source offer `SOURCE.txt` on every stick | — |

## 3. Threat model

Three separate goals: **deter** copying and counterfeits, **detect** modification,
**protect** the wipe workflow. Copy deterrence is not authentication; a signature
proves origin and integrity, never that a copy is impossible.

| Threat | Can we stop it? | Can we detect it? | How |
|---|---|---|---|
| Casual copying (byte-identical) | No (and the GPL allows it) | No: a perfect copy is indistinguishable | Trademark, packaging, sold-by channel |
| Counterfeit stick with **modified** software | No | **Yes, on a trusted computer** | Stick check (signed per-file list) |
| Image or bootloader modification | No | Yes (stick check); at boot only partly (Secure Boot covers shim/GRUB/kernel) | Stick check; future trusted boot (§5 B) |
| Cloned USB serial / identity | No | No: serials are not secrets | Not used for authentication |
| Malicious replacement of nwipe or the wizard | No | Yes, stick check (they are inside the squashfs, which is listed) | Stick check |
| Rollback to an old genuine release | No | Shown: the check names the release version | User compares to the current release |
| Compromised signing key | — | Revocation in `keys.json` statuses; rotation | Release key policy |
| Fake-capacity or failing flash | No | Readback (factory); stick check finds changed/missing files | Manufacturing QA, stick check |

**Not protected (state exactly):** a modified image **booted** on any computer
can display anything, including a fake "genuine" screen, and can misbehave;
on legacy BIOS, or with Secure Boot off, nothing verifies even the bootloader.
The only trusted answer comes from checking the stick on a separate computer
you trust, with Beamo's published key fingerprint confirmed separately.

## 4. Implemented now (this change)

- **Signed per-file list.** The USB image's `img.json` (schema 2) lists every
  file on the stick with its size and SHA-256. `img.json` is itself listed by
  hash in the signed `release-downloads.json`, so the list is covered by the
  release signature without changing the publisher.
- **Stick check** (`scripts/check-beamo-stick.py`): read-only, offline, no
  account, no fee, no root/admin, never opens a raw device. It verifies the
  signature with the pinned key, then `img.json`, then every file on a mounted
  stick. Verdicts: GENUINE AND UNMODIFIED (0), MODIFIED (1), NOT VERIFIABLE (2).
  Releases before schema 2 report NOT VERIFIABLE honestly.
- **Safety unchanged.** Nothing in the wizard, disk selection or nwipe use
  changed. A failed or impossible check never leads to any erase; it stops with
  a recovery path (§7).

## 5. Options compared

| Option | What it gives | Limits | Cost (approx.) | Recommendation |
|---|---|---|---|---|
| **A. Signed inventory + stick check** | Customer-verifiable "matches the signed release, file for file" | Needs a trusted computer; cannot detect perfect copies | None (built) | **Done** |
| **B. Trusted boot of the whole image** (own shim/MOK or signed unified kernel image carrying a dm-verity root hash for the squashfs) | Boot refuses a modified image when Secure Boot is on | Needs our own Secure Boot signing (shim review), key custody in an HSM; nothing on legacy BIOS or with Secure Boot off; repair needs re-flash | Large engineering; HSM key; review effort | Later decision (D2) |
| **C. On-boot self-check** (hash files against the list) | Catches corruption and casual edits; tells the user to re-flash | **Not authentication**: a modified stick can skip it | Small | Next, as corruption detection only (D1) |
| **D. Hardware write-protect sticks** (physical switch) | Prevents later modification (malware, accidents) | Does not stop copying; supply and price; switch can be flipped | Higher unit cost than generic sticks (supplier quotes needed) | Optional product choice (D3) |
| **E. Secure-element challenge-response stick** | Real genuineness test of the hardware | Custom hardware, supplier trust, provisioning, needs a verifier app; heavy cost; GPL installation-information questions | High | Not recommended now (D4) |
| Rejected | USB serials, hidden files, obfuscation, embedded secrets, hashes stored beside the files | Copyable or forgeable; give false confidence | — | Never use as authentication |

## 6. Owner decisions (Jack)

- **D1** Add the on-boot self-check (C), labelled "corruption check, not proof of genuineness"? Recommended: yes, as a stop-and-re-flash screen; never automatic action.
- **D2** Fund trusted boot (B)? Recommended: not now; revisit with code-signing (#182) and key custody.
- **D3** Sell write-protect-switch sticks (D)? Needs supplier quotes and packaging change.
- **D4** Secure-element hardware (E)? Recommended: no.
- **D5** Publish the release-key fingerprint on beamo.tech/usb and the packaging insert (publishing is Jack's).

## 7. Recovery (legitimate media, no accounts, no fees)

1. Run the stick check on a trusted computer.
2. If MODIFIED or NOT VERIFIABLE: download the signed release, verify it
   (`docs/release-verification.md`), re-flash, and run the stick check again.
3. Support: beamosupport.com with the BW support code; never send serials.

## 8. Licensing questions for qualified legal review

1. Does selling a USB stick with Beamo Wipe make it a GPLv3 "User Product", and
   would option B or E create "Installation Information" duties (keys or methods
   to install modified versions)?
2. How to word counterfeit warnings so they do not suggest that copying or
   modifying under GPL-3.0/GPL-2.0 is prohibited.
3. Trademark: can "Beamo" packaging and a "genuine Beamo USB" mark be protected
   while the software stays freely copyable?
4. Does a modified-but-re-signed redistribution need to remove Beamo branding?

## 9. Test coverage (record's list → status)

| Case | Status |
|---|---|
| Signed / unsigned / wrong key / bad signature | Tested (test keys, temp files) |
| Altered, missing, extra, truncated files | Tested |
| `img.json` mismatch vs signed list; old schema | Tested |
| Revoked/rotated key | Existing `release_signing` tests; stick check uses the same registry |
| Replay/rollback | Check reports the release version; no minimum-version rule yet |
| Cloned image/identity | Not detectable by design (byte-identical copy) — documented |
| Unplugged/broken hardware, interrupted updates | Not applicable to this change (no updates yet; read-only tool) |
| No network | The check is offline |
| Unsupported BIOS/UEFI | Documented in §3; no boot change made |
| Physical stick, real image build | **Not run** — needs a Linux image build (hosted gate) and separate physical authorization |
