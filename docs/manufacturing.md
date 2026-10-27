# Manufacturing and quality procedure (physical sticks)

**Status (2026-10-26):** defined, **not yet executed**. No real duplicator,
production lot or QA workstation has run it. `scripts/verify-usb-stick.py` has
only regular-file fixture tests (Tier 1) and has not read a physical stick.
Physical boot and hardware acceptance remain **NOT TESTED**
([physical acceptance #111](evidence/physical-acceptance-111/README.md)).
Items marked *starting point* need the owner's confirmation before the first lot.
This single procedure for producing, checking, packing and recalling sold sticks
never authorizes erasing a disk, changing firmware or Secure Boot settings, or
publishing a release.

## 1. Golden image (release identity)

- The only source is a **published, signed GitHub release**, verified with
  `scripts/verify-usb-download.py` exactly as in
  [USB image download verification](release-verification.md#usb-image-download-verification),
  using the current trusted registry and the full key fingerprint confirmed out
  of band ([key custody](../packaging/release-keys/KEYS.md)). Never duplicate a
  CI artifact, draft asset, local `dist/` build, re-compressed copy or the ISO.
- The golden file is the decompressed regular `.img` reported by
  `VERIFIED raw USB image`. Record per lot: version and tag, source commit,
  qualified build ID, raw `.img` byte size and SHA-256 (its `EXPECTED` line),
  `.img.gz` SHA-256, key fingerprint, verifier checkout commit, operator, UTC date.
- Keep the golden file read-only and re-run `verify-usb-download.py verify`
  before each lot; a failure is a stop-ship trigger (section 9).

## 2. Media requirements

- Genuine capacity must be at least the signed raw `.img` byte size. Compare
  bytes, not labels: a stick sold as "2 GB" (decimal) holds fewer bytes than a
  2 GiB image. One supplier part number (model and controller) per lot; a new
  supplier, part or controller revision starts a new first article (section 4).
- Screen for counterfeit or fake-capacity flash: on sample units of each new
  supplier shipment, run a full-capacity write/read test with an owner-selected
  tool (for example `f3write`/`f3read` on Linux). Those units ship only after
  being rewritten with the golden image and passing readback. *Starting point:*
  5 units per shipment.
- Dual USB-A/C sticks: check both connectors at first article (readback, boot).
- Some sticks report as fixed (non-removable) disks. Boot-USB exclusion ignores
  that flag ([boot exclusion signals](boot-exclusion-signals.md)); any boot effect
  is **to be validated**. Record `lsblk -o NAME,RM,TRAN,MODEL` at first article;
  reject a part only on recorded boot evidence.

## 3. Duplicator requirements

- Byte-exact raw ("full", "bit" or sector-by-sector) write of the golden `.img`
  from byte 0, or from a master stick that itself passed section 4 readback, with
  verify-after-write doing a **full byte compare** of the written range. A quick,
  sampled or CRC-only verify does not qualify.
- No "smart", "quick", "system and files", filesystem-aware, resize, format or
  partition step: partition table, FAT32 volume and boot code copy unchanged.
- Record duplicator model, firmware, mode and settings, master identity and each
  run's pass/fail log. Units it reports as failed are scrapped, or rewritten and
  fully re-checked; never mix them back unverified.

## 4. Readback QA (first article and sampling)

Use a **dedicated Linux QA workstation**, never the duplicator or a customer
machine, with desktop automount disabled (the tool refuses a mounted stick),
Python 3.10+ and a trusted reviewed checkout whose commit you record. Never
write, format or "repair" a stick there. Read the stick on this workstation, not
on the computer that wrote it, whose cache may answer the read. Name the stick
by its whole-disk by-id link, which records model and serial in the receipt:

```sh
sudo python3 scripts/verify-usb-stick.py --image "$GOLDEN_IMG" \
  --lot "$LOT" --unit "$UNIT" --receipt "$RECEIPTS/$LOT-$UNIT.json" \
  /dev/disk/by-id/usb-<model>_<serial>-0:0
```

- Never use a `-part` link. The tool only reads, compares byte 0 through the
  image length (like the [#111 post-flash readback](evidence/physical-acceptance-111/README.md#post-flash-readback)),
  and refuses partitions, mounted or held devices, the disk holding the running
  root filesystem, and character devices, directories, FIFOs and sockets.
  Identifying the right stick is still the operator's job.
- Only exit 0 with `RESULT: PASS` and a written receipt qualifies the unit.
  Exit 1 (`FAIL`: different bytes, short stick, read error, or a change during
  readback) still writes a FAIL receipt: keep it and hold the lot. Exit 2 is a
  refusal or error with no result: fix the cause and rerun; never record PASS.
- PASS covers the image bytes only; capacity beyond the image is not compared.
  Regular-file rehearsal receipts (`target_type: regular`) never qualify a unit.
  Under `sudo` the receipt is root-owned, mode 0600; file it unedited.

*Starting-point sampling plan (owner to confirm before the first lot):*

| Stage | Readback | Boot QA (section 5) |
| --- | --- | --- |
| First article: new release, part, duplicator or settings | First unit of every duplicator port; at least 5 units | 2 units, each connector |
| Each duplicator run | 1 unit per port at the start and at the end | 1 unit |
| Whole lot | At least 2% of units (minimum 3), chosen at random | At least 1 unit |

The plan accepts no failures: any FAIL is a hold (section 9). Readback does not
change the stick, so passed sample units may ship after packaging.

## 5. Boot QA on reference machines

For each lot, boot the boot-QA units on the owner's named reference machines (at
least one UEFI and one legacy BIOS machine while both are advertised) following
[physical acceptance #111 §5.1–5.3](evidence/physical-acceptance-111/README.md#5-how-to-run-on-dedicated-safe-hardware):
spare machines only, valuable disks disconnected, and no firmware, key or Secure
Boot changes ([Secure Boot cases](secure-boot-acceptance.md)).

- Boot to the wizard only. Confirm the Beamo USB is marked and not selectable on
  the pick-disk screen, then shut down without erasing. **Never erase a valuable
  disk.** The optional disposable erase in #111 is not part of manufacturing QA.
- Record machine model, firmware mode and version, Secure Boot state, port,
  connector, the #111 result marker and the photo/log path. A Pass covers that
  named machine and image only ([evidence tiers](evidence-tiers.md)).
- A lot without a boot-QA Pass for its release stays on hold.

## 6. Labeling

Stick and pack show **Beamo Wipe**, the release version (for example `v0.2.14`,
matching the lot record) and the lot ID, plus the printed [boot card](boot-card.md)
with its nwipe and license lines. Use only the allowed language in
[claims](claims.md). Never print "certified", "DoD", "NSA" or "NIST compliant",
"plug and play", "any computer", "impossible to recover", Apple Silicon or
Chromebook support, or a comparison with a named competitor.

## 7. Tamper-evident packaging and chain of custody

- After QA, seal each stick in tamper-evident packaging carrying the lot ID, and
  record numbered seal ranges per lot. A seal shows that a pack was opened; it
  does not prove the bytes are unchanged.
- Log custody from golden-image storage through duplicator, QA, packaging and
  hand-off to the warehouse or marketplace (who, when, unit counts in and out).
  A count mismatch, broken seal or unlogged hand-off holds those units; rework
  means rewriting with the golden image, full readback and a new seal.

## 8. Record retention

Keep per lot: release identity and golden verification output, media supplier
and screening results, duplicator settings and logs, every readback receipt
(PASS and FAIL), boot-QA records, label proof, seal ranges, custody log and ship
dates, for **at least 3 years after the last shipment of that release**. They tie
each shipped stick to the release and source commit that the GPL written offer in
[THIRD_PARTY.md](../THIRD_PARTY.md#corresponding-source-gpl) covers; keep that
release's corresponding-source archive as long (legal review still pending). Store
records privately; never commit images, customer data or secrets to git.

## 9. Stop-ship, hold and recall

Triggers: any readback FAIL; a pattern of duplicator verify failures; a failed
golden-image re-verification; a boot failure on a reference machine; a security
advisory affecting the shipped release ([SECURITY.md](../SECURITY.md)), including
a Secure Boot revocation of its boot chain or an nwipe defect; the release's
signing key marked `revoked` in the trusted registry
([revocation](../packaging/release-keys/KEYS.md#revocation)); counterfeit media,
custody or seal discrepancies, or a label/version mismatch.

1. **Hold:** stop duplicating and shipping affected lots; quarantine and mark
   the stock HOLD. **Record** the trigger, UTC time, evidence and lot IDs.
2. **Scope** the release, lots and units (section 8), including shipped stock.
3. The owner decides: release the hold after root cause and a new first article;
   rework with a current verified release; or scrap. For affected shipped units
   the owner also decides on customer notice or recall; support uses section 10.
4. Resume only after a new first article passes sections 4 and 5.

## 10. Customer update path

Sticks are offline and never update themselves; each keeps the release it was
written with, as shown by START-HERE.html on the stick. Only the latest published
release receives fixes ([supported versions](../SECURITY.md#supported-versions)).
Support decides:

- Advisory or recall covering the customer's release or lot: offer a replacement.
- Boot or behavior problem: collect the **Support code** and **Build** lines
  ([boot card](boot-card.md)). If a newer verified release addresses it, offer a
  replacement or, for a customer able to do it safely, re-flashing with that
  release after [verification](release-verification.md#usb-image-download-verification).
  Re-flashing replaces the stick's contents and needs the right device chosen;
  recommend replacement for non-technical customers.
- Otherwise no update is needed; an older release does not expire.

A used stick may no longer match its image byte for byte (for example after a
desktop OS wrote to its FAT volume), so a readback FAIL on a returned stick is
not by itself proof of a manufacturing defect.
