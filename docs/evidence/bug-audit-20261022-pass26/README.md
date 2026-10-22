# Beamo Wipe: twenty-sixth comprehensive local audit

Date: 2026-10-22 UTC  
Branch: `fix/safety-audit-20261019`  
Baseline: `b4564a95a1cf30d0b7faf6f75379612b4fd293ac`

## Result

PASS24 made a remote-tag lookup the final validation before success. PASS25
then added the potentially slow `/releases/latest` response and complete asset
verification after that lookup. The tag could therefore move during the final
public-response verification window and the publisher could still report a
successful qualified release.

The protected publisher now performs another exact remote-tag lookup after the
authenticated latest-release ID check. The returned commit SHA must equal the
qualified `GITHUB_SHA`. A lookup failure or SHA drift restores and authenticates
the exact verified draft before the publisher fails. No remote API operation
now occurs between this final tag binding and the success signal.

The earlier post-promotion tag check remains in place, so the publisher checks
the tag both immediately after the state transition and after the final public
release verification.

## Reproduction evidence

The six PASS26 cases were first run against the exact PASS25 implementation.
They produced **five intended failures and one passing control** for the
existing complete latest-release verification. The failures cover final lookup
ordering, exact tag selection, rollback on lookup failure, rollback on SHA
drift and success-signal ordering. On the repaired tree all **six pass**, with
no errors or skips.

- Baseline JUnit SHA-256:
  `ded561c5498e48f81602ab84d602d0a34e3edc28d2428ca42bce82b1f89dabf7`
- Final regression JUnit SHA-256:
  `ac5bca4dcd276fccac917d1caa1c356a89433d67bd12aedde40611f8958d4183`

The broader release-focused selection contains 342 cases: **330 passed and 12
skipped**, with zero failures or errors. All skips require a manufacturing ISO;
the configured gcloud test now runs. Focused JUnit SHA-256:
`1f06afda7b5c01b991af7bc14ea668f764e620ddf910368f4e76ed50e773e2bf`.

## Exact-source full suite

The definitive suite reused PASS25's completed local environment: Node.js
24.21.0, policy-free Google Chrome 156.0.8078.47, Go 1.26.8, Google Cloud SDK
590.0.0, Atspi, ShellCheck, FAT32 tools, rsync, xorriso and isolated X11/DBus.
It ran as UID 1000 with umask `0022`, dry-run controls, Xvfb display `:200` at
1600x1000 and 72 DPI, warnings as errors, and pytest's cache provider disabled.

The JUnit contains **12,242 selected cases: 12,224 passed, 18 skipped, zero
failures and zero errors**. The remaining skips are exact environment
boundaries: twelve require the manufacturing ISO, two require generated
`lb config` artifacts, and four external Microsoft reference checks are
rejected by the enforced network policy. JUnit SHA-256:
`b8a5002009aa4d0446c39e8df525a200a18f0c5b8c3391f29672ec87ea952e9c`.

Three unchanged cases were explicitly deselected: two consume absent generated
`packaging/live/config/{bootstrap,binary}` inputs, and one host-GTK 800x600
pixel boundary differs under this GTK build. The latter passed in PASS22's
exact Docker suite, and PASS26 changes no GTK or layout source.

## Static checks and source identity

Compileall, Ruff, Ruff formatting, mypy, ShellCheck, shell syntax, whitespace
validation and source-freeze verification pass. Static transcript SHA-256:
`5d1c23ceb6773ce2c8434a520bf954e68090fb4b4f51b8e21053aa54e72c2d33`.
Go, workflow and cross-platform build source did not change; PASS22's
checksum-verified Go race/vet/fuzz/cross-build and Actionlint receipts remain
the latest checks for those unchanged surfaces.

The functional source and regression bytes were frozen before the full suite
and matched afterward:

- `scripts/publish-release-blacksmith.sh`:
  `c2b42f19f8134e51e5d6f4a81293391b7ab899894707d63647f7cf9e58ddcce9`
- `tests/test_github_release_latest_pass25_20261022.py`:
  `6c9b01b82cddca73a341bff171381046bc72d5431d38260d821659cb876b115a`
- `tests/test_github_release_final_tag_pass26_20261022.py`:
  `68159d482a36867701fa4422714bbce2279a8088b1a7eb81db3eb1bc5a819915`

The source-freeze manifest SHA-256 is
`e4d8d171856e3f66128eefeb411c0beef3774f8e82af2e04fb47d7afc63b1064`.
Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass26-20261022/root/`.

## Discarded setup evidence

The first focused run exposed one stale PASS25 source-order assertion. It
required the last textual tag lookup to precede `/releases/latest`, while
PASS26 intentionally adds another lookup afterward. The assertion was narrowed
to its original guarantee: a post-promotion tag check still occurs before the
latest-release query. PASS26 separately proves the new final lookup occurs
after that query. Product behavior did not change during this test repair, and
the complete focused selection then passed.

Docker was not used because the 32-GiB overlay has about 191 MiB free and
cannot start a useful image. Generated pytest scratch directories were removed
without touching source or retained evidence, and the complete validated host
gate ran successfully.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Exact-source
ISO/KVM, native Windows, firmware, physical-media and reconnect qualification
remain open for an authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
