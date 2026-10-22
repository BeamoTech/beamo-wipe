# Beamo Wipe: twenty-third comprehensive local audit

Date: 2026-10-22 UTC  
Branch: `fix/safety-audit-20261019`  
Baseline: `da75ef9ce28adc785cfc7236d2b477c24760dded`

## Result

This pass repaired the final GitHub draft-promotion boundary. Asset bytes were
already authenticated, but the publisher did not authenticate the release
record's tag, title, notes or prerelease state. A reusable draft could retain
stale metadata, and the GitHub API response passed through a predictable,
replaceable and unbounded staging path before verification.

The verifier now requires a positive numeric release ID and the exact tag,
title, body, draft state and non-prerelease state. It reads the expected notes
from `GITHUB_SHA` rather than the mutable worktree, with strict commit/version
syntax, an exact object-size check, a one-MiB limit and UTF-8 validation. The
GitHub response is consumed directly from standard input with a one-MiB limit,
duplicate-field rejection and non-finite-number rejection. The signed
inventory, detached signature and all prior exact asset digest/size checks
still gate success.

The publisher normalizes an existing draft's title, notes, draft state and
prerelease state before upload. After exact metadata and asset verification it
rechecks that the remote tag still identifies `GITHUB_SHA`, then publishes
only the verified numeric release ID through the GitHub API. A draft deleted
and recreated under the same tag can no longer redirect the final promotion
request.

## Reproduction evidence

The 14-case PASS23 regression module was replayed against a minimal exact
export of the baseline commit. It produced **13 intended failures and one
passing legacy asset-digest control**, with no errors or skips. The failures
cover five mismatched or mistyped metadata fields; acceptance of exact
metadata; duplicate and oversized streamed API responses; mutable-worktree
release notes; reusable-draft normalization; direct streamed verification;
remote-tag revalidation; and numeric release-ID promotion. On the repaired
tree all **14 cases pass**.

- Baseline JUnit SHA-256:
  `a89abd7b4f11c1fbe0d2a7f463c0705e6c9485112b165a6a8e8be53f2215d2b2`
- Final regression JUnit SHA-256:
  `7c042812ccea0e04cfffe2807b1971d67536b04d0e6426accfe9c3d5367a0737`

The broader release-focused selection contains 318 cases: **305 passed and 13
skipped**, with zero failures or errors. Twelve skips require a manufacturing
ISO and one requires gcloud. Focused JUnit SHA-256:
`af12f835208990bb0fb8bb7379f01d48eb5d2721e4ac906e5bc2d526ba343ad4`.

## Exact-source full suite

The final full suite ran as UID 1000 in dry-run mode with a private D-Bus
session and Xvfb display `:200` at 1600x1000. GTK's host-default 96-DPI scale
was corrected to the intended 72-DPI effective scale. Warnings were errors,
pytest's cache provider was disabled, the exact Go 1.26.8 binary was first on
`PATH`, and the project Python environment was pinned for child gates.

The JUnit contains **12,216 selected cases: 12,129 passed, 87 skipped, zero
failures and zero errors**. The skips comprise 42 unavailable browser or
browser-launcher cases, 22 unavailable FAT32-tool cases, 12 unavailable
manufacturing-ISO cases, four network-blocked Microsoft reference checks and
seven other unavailable local-tool/runtime cases. JUnit SHA-256:
`c612941e3aebe2534c22ba029f5497f67ff42201c108ef88bb04caedb82e3698`.

Three cases were explicitly deselected. Two consume absent generated
`packaging/live/config/{bootstrap,binary}` inputs. The third is the unchanged
`test_accessible_method_choices_visible_above_grouped_actions`, whose 800x600
pixel boundary differs under this host GTK build; it passed in PASS22's exact
Docker full suite and no GTK or layout source changed in PASS23. The other 177
tests in those two GTK modules were retained in the final selection, with one
documented `pyatspi` skip.

## Static checks and source identity

Compileall, Ruff, Ruff formatting, mypy, ShellCheck, shell syntax and
whitespace validation pass. Static transcript SHA-256:
`87f2748e5ecc47a71e24dc0a6cae1f9697e1ffde37c7658d0c2e84609f34b2cf`.
Go, workflow and cross-platform build source did not change; the checksum-
verified Go 1.26.8 race/vet/fuzz/cross-build and Actionlint receipts from
PASS22 remain the latest checks for those unchanged surfaces.

The functional source and regression bytes were frozen before the accepted
full suite and matched afterward:

- `scripts/publish-release-blacksmith.sh`:
  `9a3d8c4059d5ff1572bb2681a8b3b61d25ee8d17a62f58b80d0d9aa1361aba46`
- `scripts/fetch_github_draft_release.sh`:
  `699bde4a0742b8687945ca9b417a0c3ccdb1b135e26e8d364addf50444932e33`
- `scripts/verify_github_release_assets.py`:
  `7727c05a529170cd92ee3dc67c43a51eb2a8ad38db6af7fe149bf9807867c95f`
- `tests/test_github_release_asset_binding_pass19_20261021.py`:
  `73e5bc8e756b30aca759425f8fc108a37d1c9d4ede699f62c9fcec9c58bec593`
- `tests/test_github_release_promotion_pass23_20261022.py`:
  `d1e872cc5972431d13e1b9d2e68e3fc9a9918e34b23ce2f5e6806fc26bdc4331`

The source-freeze manifest SHA-256 is
`ac297dc5d435feaac47c9b04ca12d98f9a013d0e21056fbebc5d3ba77c2cdb73`.
Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass23-20261022/root/` to avoid committing large
runtime artifacts.

## Discarded setup attempts

Docker initially ran the small focused boundary, but its VFS storage driver
could not start later containers after the 32-GiB overlay filled. Generated
audit caches were removed, source was preserved, and final qualification used
the repository's Python 3.13/Tk 8.6 environment.

An isolated host-GTK diagnostic without the effective 72-DPI correction had
173 passes, one `pyatspi` skip and three geometry/layout failures. Correcting
the DPI resolved both startup-geometry failures; the single unchanged host-GTK
layout boundary is documented above.

The first otherwise-final full run had 12,128 passes, 87 skips and one
failure because the browser-suppression `PATH` exposed a system `python3`
without pytest to a nested hosted gate. Pinning that child command to the
project environment made the exact node pass. The complete suite was then
rerun and produced the accepted green JUnit above. The discarded JUnit
SHA-256 is
`82eda57731e6fd19aa35ba7573b84287e2422c1ef878221470115dfd8ec7ced0`.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Local tests
and cross-build evidence do not establish those acceptance boundaries.
Exact-source ISO/KVM, native Windows, firmware, physical-media and reconnect
qualification remain open for an authorized isolated worker or eligible
physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
