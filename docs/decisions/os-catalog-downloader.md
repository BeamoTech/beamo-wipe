# Design record: signed OS catalog and verified, resumable downloader (Notion Ref 188)

> **Status: PROPOSAL — design only, nothing adopted or built.** Prepared
> 2026-11-19 by Claude (Opus 5.5) from the Notion Ref 188 title, the Ref 184
> record (`docs/decisions/three-mode-architecture.md`), the Ref 185–187 design
> records and the repository at main `809cc11e`. The full Notion row text was
> not available; §3 lists the requirements this record assumes.
>
> **Depends on Jack's Ref 184 decision** (and on D1 there: how Windows is
> acquired). Nothing here is built until he decides.
>
> **Numbering.** "Ref 188" is the Notion row, not a repository issue number.

## 1. Summary for the owner (plain English)

1. To install a new system, Beamo Wipe needs to know which systems it may
   install and exactly which file bytes are genuine. That list is the
   **catalog**, and Beamo signs it.
2. The downloader fetches the chosen system to the USB's OS cache and checks
   every byte against the signed catalog. If anything does not match, the
   file is thrown away and nothing is erased.
3. Downloads can stop and resume: a dropped Wi-Fi only costs time, never safety.
4. The erase is offered only after the download is complete and verified
   (Ref 184 rule N1).
5. Six choices are yours (§9). The main ones: who hosts the files, and whether
   Beamo signs a separate catalog key or reuses the release key.

## 2. Today (facts from main `809cc11e`)

| Item | Today | Where |
|---|---|---|
| Release signing | Ed25519 detached signatures over exact manifest bytes; key registry with `active`/`retired`/`revoked`; fails closed on unknown schema, key, digest or version below the acceptance floor | `src/beamo_wipe/release_signing.py`, `packaging/release-keys/keys.json` |
| Active key | `93caaf7ca93eff4d` | `keys.json` |
| Crypto library | `cryptography`, imported lazily; **not** in the live image (`python3-cryptography` absent). The image does ship `openssl` and `libssl3` 3.0.22-1~deb12u2 | `release_signing.py`, `package-lists/beamo.list.chroot`; image package inventory of main `384331fc` (505 packages, CI run 44594970979) |
| Consumer verification | Documented download and stick checks | `docs/release-verification.md` |
| Network, downloads | None in the image: no `curl`, `wget`, `iwd`, `nftables`, NetworkManager or DHCP client | Same inventory; Ref 186/187 records |
| OS cache | Proposed ext4 partition on the stick | Ref 185 record |

## 3. Requirements assumed (confirm against the Notion row)

- R1 A Beamo-signed catalog lists every installable OS: name, version, architecture, Secure Boot support, size, SHA-256, sources, licence and support dates.
- R2 Trust comes from the catalog signature and the pinned hash, never from TLS, the mirror or the file name.
- R3 Downloads resume after interruption and survive restarts (Ref 193).
- R4 Nothing is installed or erased unless the full payload matches the catalog (Ref 184 N1, L11).
- R5 Old, expired or revoked catalogs are refused.
- R6 Works on slow, metered and phone connections; shows progress and time left (Ref 199).
- R7 Offline media prepared at home (Ref 204) use the same catalog and checks.

## 4. The catalog

**Format.** A JSON document, `beamo-os-catalog/1`, signed with a detached
Ed25519 signature in the same format as `release_signing.py`. Fields:

| Field | Purpose |
|---|---|
| `schema`, `serial` (monotonic integer), `issued_utc`, `expires_utc` | Rollback and freshness: refuse a serial lower than the last one seen, and any expired catalog |
| `min_beamo_version` | Old Beamo Wipe sticks stop offering entries they cannot install correctly |
| `entries[]` | One per installable OS image |
| `entries[].id`, `name`, `version`, `arch` (`amd64` only) | What the customer picks |
| `entries[].secure_boot` | `signed` / `unsigned`, used by the Computer check (Ref 189) and D3 |
| `entries[].bytes`, `sha256`, `sha512` | The pinned payload identity |
| `entries[].sources[]` | HTTPS URLs (vendor and Beamo mirrors, D188-1); a hash mismatch on any source discards that copy |
| `entries[].upstream_signature` | Optional: the vendor's own signed checksum file and key fingerprint, checked as a second opinion at catalog build time |
| `entries[].licence`, `support_until`, `notes` | Shown in "Help me choose" (Ref 190) |
| `revoked[]` | Entry IDs and hashes that must never be installed again |

**Building the catalog** (release-side, not on the stick):
1. A script downloads each upstream image on a clean worker.
2. It verifies the vendor's own signature (Debian, Ubuntu and Fedora sign checksum files).
3. It records the size and hashes, and writes the catalog.
4. The protected publisher signs it.

Like release signing, it is gated by a separate authorization; no private key
is ever on a pull-request build.

**Key (D188-2).** Recommended: a **separate catalog key** in the same
registry format, with its own `active`/`retired`/`revoked` status. Rotating the
catalog key is then independent of the release key. The catalog key's
registry ships on the stick, inside the signed release, so the stick check
(Ref 183) covers it.

## 5. The downloader

- **Process:** a separate service, as in the Ref 187 record: non-root, no capabilities, and it writes only the OS cache.
- **Order:**
  1. Fetch the catalog and its signature.
  2. Verify against the on-stick registry.
  3. Check the serial against the last serial seen (stored in the state area, Ref 185), and the expiry.
  4. Show the choices.
- **Fetching:** HTTPS `Range` requests in chunks (e.g. 8 MiB) into `<id>.partial` in the OS cache. A small sidecar records the entry ID, the expected hash, the byte offset and a rolling SHA-256 state.
  - On resume, the downloader re-reads and re-hashes the bytes already on disk; it never trusts the sidecar alone.
  - If a server ignores `Range`, or the catalog changed, it starts again.
- **Verifying:** at the end it checks the full SHA-256 and SHA-512 and the exact size. Only then is the file atomically renamed to `<id>.verified` and recorded in the journal (Ref 193).
  - **On mismatch:** delete the file and try the next source. If every source fails, say plainly that the download could not be verified, and do not erase.
- **Re-verification:** the installer (Refs 194/195) hashes the file again right before use. The cache is trusted only through the hash.
- **Space:** the downloader checks free space before starting, and keeps only one OS at a time (D185-3).
- **Limits:** the catalog document has a size limit, as do HTTP headers and redirects. Only HTTPS is accepted, and only to catalog-listed hosts or their documented redirect hosts (D188-4).
- **Progress:** bytes, speed and time left go to the journey timeline (Ref 199). A pause and resume control is available.

## 6. Crypto on the stick (D188-3)

The live image has no Python Ed25519 library today, but its OpenSSL 3.0
(measured above) can verify Ed25519. Options:
- (a) Add `python3-cryptography`. Debian-signed, but it grows the image (size to measure in Ref 202).
- (b) Use the `openssl` command line already in the image (`pkeyutl -verify -rawin` with an Ed25519 public key). No new package, but a second verification code path that needs its own tests.

Recommended: (a) reuses the tested `release_signing` code path exactly; (b)
only if Ref 202 shows (a) does not fit.

## 7. Safety rules this design needs (proposed)

1. No erase until a catalog-verified payload is complete (Ref 184 N1).
2. A saved partial or verified file is untrusted until hashed again (Ref 184 N3).
3. Catalog rollback, expiry and revocation are enforced, and their state is kept in the state area.
4. No catalog or download change during states 6–9 (Ref 184 N5).
5. The download never writes outside the OS cache, and never to an internal disk.
6. Download failure is never an erase trigger and never changes the chosen disks.

## 8. Tests (when built)

| Test | Kind |
|---|---|
| Catalog: good, bad signature, unknown/revoked key, expired, lower serial, unknown schema, `min_beamo_version`, revoked entry | Unit (test keys) |
| Downloader: resume at random offsets, server ignoring Range, truncated/extended/corrupted bytes, wrong size, source fallback, redirect to an unlisted host, full disk | Unit with a local fake HTTPS server and temporary files |
| Power loss mid-chunk and mid-rename | Unit (fault injection on regular files) |
| End-to-end in QEMU with a local mirror | Ref 203 |
| Real networks and phones | Ref 208 (physical, Jack's authorization) |

## 9. Owner decisions (Jack) — none adopted

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D188-1 | Where payloads come from | (a) vendor mirrors only; (b) Beamo mirror only; (c) both, catalog-hash pinned | (c): vendor first, Beamo mirror as fallback. Any Beamo hosting cost needs approval (zero spend until then) |
| D188-2 | Catalog signing key | (a) separate catalog key; (b) reuse the release key | (a) |
| D188-3 | Ed25519 on the stick | (a) `python3-cryptography`; (b) `openssl` CLI | (a), subject to Ref 202 size |
| D188-4 | Redirect policy | Catalog-listed hosts only / any HTTPS | Listed hosts and their documented redirect hosts only |
| D188-5 | Catalog lifetime | 30 / 60 / 90 days | 60 days, with the serial floor |
| D188-6 | Initial OS list | — | Decided with Ref 184 D1–D3 (Windows acquisition, Windows 10, Arch) |

## 10. Not done here

No code, catalog, key, server or download was created. No network was used and
nothing was spent. The Notion row's full text should be checked against §3.
