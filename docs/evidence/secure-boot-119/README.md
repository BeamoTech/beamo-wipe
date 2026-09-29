# Secure Boot expectation correction — #119

Status: source/document correction and artifact inspection complete; physical
qualification **NOT TESTED**. No dedicated safe x64 machine is attached to
this macOS arm64 development host. This task supplies no new physical receipt
and must not mark #111's physical matrix Done.

## Conflict and authoritative evidence

Before this correction, the active physical hub and firmware sheet required
refusal with Secure Boot on whenever no Beamo key was enrolled. The current
compatibility and accessibility matrices also retained an unsigned-image
assumption; the firmware sheet suggested disabling Secure Boot on lab hardware.
Those expectations conflicted with `docs/claims.md`, the helper/launcher copy,
and `packaging/live/inside-docker.sh` (`--uefi-secure-boot enable`).

The [current cases](../../secure-boot-acceptance.md) are derived from actual
published 0.2.12 bytes, not package names or a proposed build. Firmware trust
and revocations govern acceptance of the inspected Debian chain. Beamo's
publisher key has a separate role. Do not modify firmware trust to obtain a
Pass; unknown state remains unknown.

## Exact identities and provenance

| Evidence | Identity / result |
| --- | --- |
| Public release | [v0.2.12](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12), published 2026-09-28; all existing assets/descriptions preserved |
| Release source | `e986419379f512f8088f5982ee02a51dc91a9dae`, clean, tag `v0.2.12` |
| Release build | `625971a4-afef-5398-9bec-d96455192ab3`; Blacksmith; content-addressed `debian:bookworm@sha256:6ebd97fa83deb272194a2cf015b3d26a4d538e9ad3a7a79d544c8af5b0a01443` |
| ISO, GitHub asset 595626596 | 564133888 bytes; SHA-256 `73554d35aecafac7fc6dffe41d1f1efdb658b43c39da85a2f0bebfe8f1beb598` |
| USB gzip, asset 595626632 | 601441384 bytes; SHA-256 `a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972` |
| Decompressed USB | 2147483648 bytes; SHA-256 `1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b`; one FAT32 partition at sector 2048 |
| Manifest, asset 595626587 | SHA-256 `0bb56538500330086f507538e94ec68846ff5ab39ddf491dbeaf467a50cfd5b8`; strict manifest-to-actual-ISO verification passed |
| Signed download inventory | SHA-256 `2023d3aa84a84f406a1d0f0b230d38293eb1b74275cf068088408209a296511c`; signature and measured files checked |
| Publisher authentication | Manifest and inventory Ed25519 signatures verified with the repository registry, key `93caaf7ca93eff4d`, fingerprint `93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7` |
| Retained release QEMU evidence | `verification-evidence.tar.gz`, SHA-256 `36d56a104a1fef3de933d149ab288684be57b54a72128841444c71deba746f54`; summary matches source/build/ISO/USB identities; `secureboot_usb=pass` |
| Source base for this correction | Main `7e8603d588502fedce9206a735f924398d59b260`; [its existing full CI gate passed](https://github.com/BeamoTech/beamo-wipe/actions/runs/36519281288). This is baseline qualification, not a run of this new documentation/test change |

The release's in-image `build-identity.json` independently matched the manifest
source/build and recorded clean source. The delta from release source to the
correction's main base contains review-publisher infrastructure, CI handling,
and report key-release handling; it changes no boot configuration. This does
not turn a release image into a main-built image. Future candidate bytes must
be inspected again because Debian package versions are build inputs, not
immutable assumptions from a version label.

## Inspected chain and scope

[components.json](components.json) records full-file and Authenticode digests,
machine types, issuers, roles, and inspection outcomes. Selected EFI files
match across the ISO tree, El Torito FAT filesystem and decompressed USB.
USB kernel, initrd and menu configuration match the ISO bytes. All three live
menu entries select the same signed kernel and separate initrd.

| Component | Signer / issuer | Result |
| --- | --- | --- |
| `EFI/boot/bootx64.efi` (shim 16.1) | Microsoft Windows UEFI Driver Publisher / Microsoft Corporation UEFI CA 2011 / Microsoft Corporation Third Party Marketplace Root | PE digest and cryptographic signing chain verified; one 2011 signature, no 2023 signature |
| `EFI/boot/grubx64.efi` (signed CD GRUB 2.06-13+deb12u2) | Debian Secure Boot Signer 2022 - grub2 / Debian Secure Boot CA embedded in shim | PE digest and signature verified; matches installed `gcdx64.efi.signed` |
| `live/vmlinuz-6.1.0-53-amd64` (6.1.187-1) | Debian Secure Boot Signer 2022 - linux / Debian Secure Boot CA | PE digest and signature verified |
| `EFI/boot/bootia32.efi` | None; machine type IA32 | No signature; IA32 Secure Boot not qualified |
| Installed signed GRUB variants; `fbx64.efi.signed`, `mmx64.efi.signed` | Debian Secure Boot Signer 2022 - grub2 or - shim / Debian CA | Signatures verified; not separately selected by the live menu. MokManager/fallback are absent from the media's EFI boot directory |
| Installed unsigned shim/helpers/monolithic GRUB | None | Inventoried; not selected by the inspected path. Their presence does not qualify a signed boot path |
| Separate initrd, GRUB configuration, squashfs | No PE signing issuer | Outside this executable signature chain; do not claim authenticated live filesystem from Secure Boot |
| BIOS Syslinux/Isolinux, USB MBR and loader stages | Not a UEFI signature chain | Ordinary boot paths only; not Secure Boot evidence |

Shim's Debian CA DER fingerprint is
`079646974bce09b1f04da67bd722d1fb0947ae4c4010bccdbba52d5b23cbf1a2`;
its embedded certificate matched the installed Debian CA byte-for-byte.
The Microsoft UEFI CA 2011 DER fingerprint is
`48e99b991f57fc52f76149599bff0a58c47154229b9f8d603ac40d3500248507`.
The Microsoft public root was downloaded from its [official PKI endpoint](https://www.microsoft.com/pki/certs/MicCorThiParMarRoo_2010-10-05.crt),
DER SHA-256 `2848361a9c1e32df1d3e2ed6a7b9e67a525cf8a13b164f8006c9479578f746de`.
These establish component/certificate identities, not any physical firmware's
enrolled trust. Shim's vendor denylist digest and all SBAT entries are in the
receipt; active firmware/MOK/SBAT state is still unknown on untested machines.
Its two embedded SBAT policy payloads were inspected as well. Ordinary shim
boot may persist policy, so physical cases require before/after state evidence
and must not assume that successive attempts have the same policy.

## Executed inspection and verifier limits

Inspection used regular disposable files only; no mounts, firmware writes,
physical block devices, or nwipe invocations. Release metadata digests were
checked against GitHub, and publisher signatures against the source registry.
`verify_manifest` checked the actual ISO and exact sidecars; the decompressed
USB was hashed independently and matched the signed inventory and ISO binding.

Established tools: xorriso extraction, mtools readback, unsquashfs selective
extraction, OpenSSL certificate inspection, and native arm64 osslsigncode 2.14
with OpenSSL 3.6.4. The official osslsigncode 2.14 source archive SHA-256 was
`bdf249cbf23a84262dd30bb9b3a96a17109ff8de5ea30212e26af173cc8b2195`.
No tool or certificate was installed into the system trust store.

Representative executed commands (paths abbreviate disposable staging):

```sh
xorriso -osirrox on -indev beamo-wipe-0.2.12-amd64.iso -extract /EFI iso-efi
mcopy -i beamo-wipe-0.2.12-amd64.img@@1048576 ::/EFI/boot/bootx64.efi usb-bootx64.efi
mcopy -s -i iso-grub/efi.img ::/EFI eltorito-efi
unsquashfs -no-progress -d squash-selected filesystem.squashfs usr/lib/shim usr/lib/grub/x86_64-efi-signed usr/share/shim/debian-uefi-ca.der usr/share/beamo-wipe/build-identity.json
osslsigncode verify -CAfile debian-ca.pem -ignore-cdp -ignore-crl -in iso-efi/boot/grubx64.efi
osslsigncode verify -CAfile debian-ca.pem -ignore-cdp -ignore-crl -in vmlinuz
osslsigncode verify -CAfile microsoft-root.pem -ignore-timestamp -ignore-cdp -ignore-crl -time 1778716800 -in iso-efi/boot/bootx64.efi
```

Initial generic system-CA verification failed because the appropriate roots
were absent; it was not recorded as a pass or a firmware refusal. Verification
then used the explicitly identified public Microsoft root and shim's embedded
Debian CA. Shim's 2011 CA and leaf have expired under ordinary wall-clock
X.509 validation. Its offline reference time above is **2026-05-14 UTC**, for
cryptographic verification within their validity window. The timestamp server
signature was not qualified. Debian signatures verified at inspection time.
Online CRLs were not evaluated; these commands do not test firmware dbx,
shim denylist or SBAT enforcement. No firmware clock or trust was changed.
Microsoft's [Linux CA transition guidance](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/linux-distribution-guidance-handling-2023keys)
explains that an existing 2011-signed shim can still boot when the relevant
2011 trust remains and applicable revocations do not deny it. Expiry alone is
not a proven firmware rejection on a machine that has not been inspected.

The [shim](shim-signature.txt), [GRUB](grub-signature.txt), and
[kernel](kernel-signature.txt) logs preserve the successful PE/chain checks.
Disposable absolute paths and trailing whitespace are normalized in these logs.
A private copy of GRUB with one byte changed at offset 4096 failed digest
verification ([negative control](corruption-control.txt)); the altered file
was removed. Unsigned copies returned failure and were classified unsigned,
not given acceptance marks.

## Inventory and preservation

Updated authoritative material: physical hub, firmware and desktop results
templates, build-identity form, desktop checklist, compatibility and
accessibility matrices, release-verification distinction, evidence-tier
interpretation, QEMU scope, desktop-entry guidance, storage-limit summary,
and support runbook. The canonical case document
replaces duplicated binary enrollment assumptions.

Inspected and already consistent: `docs/claims.md`, `docs/boot-card.md`,
`src/beamo_wipe/compat_story.py`, translated compatibility copy, helper pages
(all shipped languages), `desktop/web/index.html`, generated START-HERE helper
injection, `release_manifest.py`, boot/build/USB scripts, CI/release workflows,
and the release-key documentation. Existing tests cover generated customer
copy; the new consistency tests cover operator expectations and case coverage.
No boot/build configuration or application code changed.

Historical audit notes (including the 2026-09-02 unsigned-image observation),
dated VM logs/receipts, source-tag release notes, and all public release
assets, checksums, manifests, signatures and descriptions remain unchanged.
The old 0.2.7 evidence index now explicitly distinguishes its historical
scope and corrects the inference that a `secureboot-usb` probe proves refusal.
Generated copies are produced by the existing helper injection; their current
firmware-dependent text needs no regeneration or release replacement.

## Physical coverage and next action

SB-ACCEPT, SB-NO-ANCHOR, SB-DBX, SB-SHIM, SB-UNKNOWN, SB-INSPECTION and SB-ARCH
are specified with exact inputs, prerequisites, observation and evidence.
Every physical result remains **NOT TESTED**. Retained QEMU used x64 OVMF
Secure Boot code, Microsoft-trusting variable template and SMM enforcement;
the guest reported `BEAMO_WIPE_SECURE_BOOT=1` and reached the guide. It did not
establish a physical db/dbx inventory, an OEM trust state, or a revoked-policy
test. No public release claims were widened.

Remaining requirement: an operator with dedicated safe hardware must capture
the actual firmware databases, shim validation/SBAT state, image/media
identity and named-machine receipts for the applicable cases. Unknown states
cannot become Pass. No firmware-key ceremony, revocation change, Secure Boot
disablement, erase, or release publication is authorized by this correction.

## Correction checks and handoff — 2026-09-29

Correction branch: `codex/secure-boot-expectations-119`, based on the exact
main revision above. Only operator documentation, inspection receipts, and
documentation regression tests change. The final commit and any hosted run
are recorded in the task handoff; the existing main gate is baseline evidence
only. No tag, release, firmware state or disk-safety behavior changed.

The new regression suite was exercised against the old guidance before editing:
five existing documents failed the obsolete-expectation checks. The completed
suite passes **16 tests**; focused physical/helper checks pass **39 tests with
6 platform skips**, and the runbook subset passes **29 tests**. All 116 relative
links/anchors in changed Markdown resolve; code fences balance and
`git diff --check` passes.

Executed local checks:

```sh
BEAMO_WIPE_DRY_RUN=1 PYTEST_ADDOPTS='-p no:cacheprovider' ./scripts/test-all.sh -o addopts='' --junitxml=<staging>/local-tests.xml
python3 -m pytest -o addopts='' -q tests/test_secure_boot_expectations.py
python3 -m ruff check --no-cache dev.py scripts/build_desktop.py scripts/agent_pr.py developer_tests
python3 -m ruff format --check --no-cache dev.py scripts/build_desktop.py scripts/agent_pr.py developer_tests
python3 -m ruff check --no-cache src/beamo_wipe tests
python3 -m ruff check --no-cache --select S102,S103,S104,S105,S106,S107,S113,S307,S501,S506,S508,S602,S604,S605,S606,S608,S609,S610,S611,S612 src/beamo_wipe
python3 -m ruff check --no-cache --select S102,S103,S104,S107,S113,S307,S501,S506,S508,S602,S604,S605,S606,S608,S609,S610,S611,S612 tests
mypy --cache-dir <staging>/mypy-cache --ignore-missing-imports src/beamo_wipe
shellcheck preview scripts/*.sh packaging/live/inside-docker.sh packaging/live/config/hooks/normal/0500-build-nwipe.hook.chroot
PYTHONPYCACHEPREFIX=<staging>/pycache python3 -m compileall -q src/beamo_wipe dev.py scripts/build_desktop.py scripts/agent_pr.py
BEAMO_WIPE_NO_OPEN=1 ./preview --web
```

Lint, formatting, security lint, typing (50 source files), shell checks and
compilation passed. The full prescribed fake-disk pytest gate completed in
1312.53 seconds: **4624 passed, 701 skipped, 10 failed**. Seven subprocess
fixtures hit their existing 2–30 second limits under host load; one Tk startup
fixture failed. All eight runnable failures passed on an unchanged, targeted
retry (**8 passed in 20.38 seconds**). The two remaining failures require
unavailable GTK/ATK `gi` bindings (`test_compat_story` and
`test_separate_footer_actions`). No timeout, test expectation, or product code
was weakened. The full Mac run is not recorded as an all-green gate.

Local execution receipts (disposable staging; hashes retained here):

| Receipt | SHA-256 |
| --- | --- |
| Full pytest log | `51ca655e637589c96e315405452681411f6acf8217df68a2be44c79327638bf8` |
| Full pytest JUnit | `7c652112aeb80d7cd7b3a5f69c4c5fdcc1de40ab01040ea2354d5e8f9d5ab593` |
| Unchanged retry log | `27805101efd0edb5abd6871ab461e22213df830151836819c48fd679e76dbf18` |
| Unchanged retry JUnit | `5f732f4efe48a9cf005d52bf787954183d00d0869b6d6f9180a1052e1b14a010` |

The fake web gallery generated successfully. Its Secure Boot hint and the
desktop/helper generated customer text match their canonical compatibility
strings. Browser rendering was unavailable: the in-app browser rejected the
local `file:` URL under its security policy. No alternate route was used to
bypass that restriction. Physical assistive-technology and firmware cases
remain NOT TESTED, independently of source/generated-copy checks.

Storage reports ran before and after inspection. Only this task's measured
temporary ISO/USB/squashfs/initrd copies were removed after receipts were
recorded (3,276,560,014 bytes); no Git work or existing releases were removed.
Before/after reports were read-only and removed nothing themselves. Small
inspection tools, certificates and local logs remain disposable staging.

## Independent automated review follow-up — 2026-09-29

[Greptile's review of the initial correction](https://github.com/BeamoTech/beamo-wipe/pull/81#issuecomment-5896967719)
identified two evidence gaps: no executable post-flash media comparison and no
test binding the operator table's hashes to the inspection receipt. The physical
procedure now requires reconnecting/re-identifying the stick and comparing its
image-length bytes read-only against the authenticated regular image. It records
the readback range, digest, device identity, command and outcome before boot.
Any missing, different, truncated or unreadable input blocks qualification.
Larger unused USB capacity is outside the comparison and receives no integrity
claim. Reflash or subsequent writes require fresh readback.

The operator table now includes the measured compressed size. The component
receipt adds the already measured ISO/raw/compressed sizes and compressed digest
from the authenticated Q12 inventory; no release byte or identity is changed.
Tests compare the displayed source/build/tag, filenames, sizes and hashes with
that receipt. Four independent displayed-hash mutations are rejected. The
original operator table fails the new identity check, and the original physical
procedure lacks the required readback command.

The documented Python readback was executed on macOS using disposable regular
files only: exact and larger media, last-chunk corruption, truncation, missing
media/reference, unset input, zero/invalid length, and wrong reference size.
Fixtures cross two 1 MiB boundaries and verify all input bytes remain unchanged.
No physical device was accessed. Focused local checks passed **70 tests with
6 platform skips**; the Secure Boot module now has **32 passing tests**. Full
and security Ruff checks passed, as did **118 relative links/anchors** and
`git diff --check`. The fresh full local run and final exact-source hosted
qualification results belong in the PR/task handoff, not the earlier commit's
CI receipt. Automated review is not the required non-author human approval.
All physical cases remain NOT TESTED.
