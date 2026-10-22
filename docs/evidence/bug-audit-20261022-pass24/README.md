# Beamo Wipe: twenty-fourth comprehensive local audit

Date: 2026-10-22 UTC  
Branch: `fix/safety-audit-20261019`  
Baseline: `3dfd1c9fc344595d3a6007eb1772abe6a44ca966`

## Result

PASS23 authenticated the complete GitHub draft and promoted its exact numeric
release ID, but the final `PATCH` response was reduced to `.id`. The publisher
therefore did not authenticate that the response represented the intended
public state with the exact title, notes, tag, prerelease state and asset set.
It also checked the remote tag only before the state transition, leaving no
fail-closed recovery if the tag moved during that final request.

The verifier now accepts one strict expected-state selector. Only the literal
values `true` and `false` are valid; ambiguous spellings fail closed. Draft and
public responses pass through the same one-MiB, duplicate-free JSON parser,
exact committed-note check, signed inventory verification, and local/remote
asset digest and size binding.

The publisher streams the complete publication response into the verifier with
`draft=false` required and compares the authenticated response ID with the
previously verified numeric ID. It then rechecks the remote tag. A malformed or
mismatched publication response, failed tag lookup, or tag drift invokes one
rollback path that patches the same numeric release to `draft=true`, verifies
the complete rollback response and confirms the returned release ID. A failed
rollback is surfaced explicitly before the publisher exits unsuccessfully.

## Reproduction evidence

The 12-case PASS24 regression module was replayed against the exact baseline
implementation. It produced **11 intended failures and one passing legacy
draft-verification control**, with no errors or skips. The failures cover exact
public-state acceptance; draft/public mismatch rejection; strict canonical
state selection; complete publication-response verification; post-publication
tag revalidation; and authenticated exact-ID rollback. On the repaired tree all
**12 cases pass**.

- Baseline JUnit SHA-256:
  `ca13cc147bb0564b080dfe105e998121878da0a79e296b4fbd0eca7fe3609746`
- Final regression JUnit SHA-256:
  `3d3377f640e1b82956f0ce086adb49ad9bfcd816c36e31b275158e850c8683bc`

The broader release-focused selection contains 330 cases: **317 passed and 13
skipped**, with zero failures or errors. Twelve skips require a manufacturing
ISO and one requires gcloud. Focused JUnit SHA-256:
`516a12fc31f58c51c1ad30601af9f05064de225cc237618063527a78ad96e86e`.

## Exact-source full suite

The final full suite ran as UID 1000 in dry-run mode with a private D-Bus
session and Xvfb display `:200` at 1600x1000. GTK used the intended effective
72-DPI scale. Warnings were errors, pytest's cache provider was disabled, the
exact Go 1.26.8 binary was first on `PATH`, and child Python gates used the
project environment.

The JUnit contains **12,228 selected cases: 12,141 passed, 87 skipped, zero
failures and zero errors**. The skips comprise 42 unavailable browser or
browser-launcher cases, 22 unavailable FAT32-tool cases, 12 unavailable
manufacturing-ISO cases, four network-blocked Microsoft reference checks and
seven other unavailable local-tool/runtime cases. JUnit SHA-256:
`04bb136b9fb1a50057085f51da2da771254ff106121b6563290d353f76206305`.

Three unchanged cases were explicitly deselected: two consume absent generated
`packaging/live/config/{bootstrap,binary}` inputs, and one host-GTK 800x600
pixel boundary differs under this GTK build. The latter passed in PASS22's
exact Docker suite, and PASS24 changes no GTK or layout source.

## Static checks and source identity

Compileall, Ruff, Ruff formatting, mypy, ShellCheck, shell syntax and
whitespace validation pass. Static transcript SHA-256:
`a6a35bee6416c16ea8e63a42174d34b4a68902e30217d6a04b94a6c43a6ddda4`.
Go, workflow and cross-platform build source did not change; the checksum-
verified Go 1.26.8 race/vet/fuzz/cross-build and Actionlint receipts from
PASS22 remain the latest checks for those unchanged surfaces.

The functional source and regression bytes were frozen before the accepted
full suite and matched afterward:

- `scripts/publish-release-blacksmith.sh`:
  `679c5110b0d826e7df2789642b320455c4a2155b09e31ce102d6735fa15c225b`
- `scripts/verify_github_release_assets.py`:
  `373321e725b387b9074392e219422a28160a97b7d7e9c88142dcd3c1c8de86ad`
- `tests/test_github_release_promotion_pass23_20261022.py`:
  `ff2b03e1cd32fdeec19ecdd05fd55232c7fdf9892856487164f46fd02bd4678f`
- `tests/test_github_release_publication_pass24_20261022.py`:
  `382aa47208d1d6b5a075ea0062d72bf3765d056d4a073a2beb6880f1413008cc`

The source-freeze manifest SHA-256 is
`3e0393b3033dbbeb9156fd5f87bd534352827191a337a025bb90ee6cca37d9be`.
Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass24-20261022/root/`.

## Discarded setup evidence

The first focused run exposed a stale PASS23 source-order assertion after the
rollback helper moved the first textual release-ID reference above the
pre-publication tag check. The assertion was narrowed to compare the tag check
with the actual `draft=false` request. Product behavior was unchanged, and the
complete focused selection then passed.

Docker was not used for final qualification because its VFS image leaves only
about 208 MiB free on the 32-GiB overlay and cannot start a useful container.
Generated pytest scratch directories were removed without touching source, and
the complete host gate ran with the same validated Python 3.13/Tk 8.6 setup as
PASS23.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Exact-source
ISO/KVM, native Windows, firmware, physical-media and reconnect qualification
remain open for an authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
